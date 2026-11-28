"""Render shot code bằng engine three.js (engines/three/) trong Edge/Chromium headless qua Playwright — không cần Node.

Sửa lỗ hổng "render chậm" của cartoon-short-kit (CPU WebGL swiftshader 3–10 s/frame, một tiến trình):
- N worker song song (mặc định 2 — đo trên máy thật: nhiều hơn chỉ tranh GPU), mỗi worker một trình duyệt;
- RESUME: frame đã có (cùng hash job) được bỏ qua — chạy lại sau khi bị ngắt không mất gì;
- GPU: "high" ép card rời (RTX…), "auto" dùng GPU mặc định (ANGLE/D3D11), "off" ép swiftshader; ghi renderer GL;
- chỉ render shot có mode "code" (không render cả video).
Engine lấy file qua một HTTP server cục bộ phục vụ thư mục repo.
"""
import argparse
import contextlib
import functools
import hashlib
import http.server
import json
import os
import subprocess
import sys
import threading
import time

from .common import ROOT, StudioError, channel, save_json

GPU_ARGS = {"on": ["--use-angle=d3d11", "--ignore-gpu-blocklist", "--enable-gpu-rasterization"],
            "high": ["--use-angle=d3d11", "--ignore-gpu-blocklist", "--force_high_performance_gpu"],
            "off": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]}


class _Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".mjs": "text/javascript", ".json": "application/json", ".ttf": "font/ttf", ".otf": "font/otf",
                      ".wasm": "application/wasm", ".riv": "application/octet-stream", ".lottie": "application/zip"}

    def log_message(self, *a):  # im lặng
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class _Server(http.server.ThreadingHTTPServer):
    request_queue_size = 256  # mặc định 5: nhiều trình duyệt mở cùng lúc làm tràn backlog → trang treo không lỗi
    daemon_threads = True


@contextlib.contextmanager
def serve(root=ROOT):
    srv = _Server(("127.0.0.1", 0), functools.partial(_Handler, directory=root))
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield srv.server_address[1]
    finally:
        srv.shutdown()
        srv.server_close()


def url_for(port, job_path):
    rel = os.path.relpath(os.path.abspath(job_path), ROOT).replace(os.sep, "/")
    page = "engines/three/index.html"   # job["page"]: engine khác dùng chung harness (engines/html/index.html)
    with contextlib.suppress(OSError, ValueError), open(job_path, encoding="utf-8") as fh:
        page = json.load(fh).get("page") or page
    return f"http://127.0.0.1:{port}/{page}?job=/{rel}"


def cfg():
    c = channel().get("code_render", {})
    # đo (docs/PERF.md): 2 worker nhanh nhất trên GPU; nhiều hơn chỉ tranh GPU (> 8 Edge còn làm trang tải quá hạn)
    w = int(c.get("workers") or 0) or 2
    return {"channel": c.get("browser_channel", "msedge"), "workers": w, "gpu": c.get("gpu", "auto"),
            "resume": c.get("resume", True), "quality": float(c.get("jpeg_quality", 0.95))}


def _launch(p, channel_name, gpu):
    args = GPU_ARGS["off" if gpu == "off" else ("high" if gpu == "high" else "on")]
    try:
        return p.chromium.launch(channel=channel_name or None, headless=True, args=args)
    except Exception:  # noqa: BLE001 — không có Edge: dùng Chromium của Playwright nếu đã cài
        return p.chromium.launch(headless=True, args=args)


def _open(p, url, channel_name, gpu):
    b = _launch(p, channel_name, gpu)
    pg = b.new_page(viewport={"width": 540, "height": 960})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.text.startswith("ERR") else None)
    pg.goto(url, timeout=180000)
    try:
        pg.wait_for_function("window.ready || window.err", timeout=90000)
    except Exception as ex:  # noqa: BLE001
        st = pg.evaluate("window.stage || '(chưa chạy module)'")
        b.close()
        raise StudioError(f"Engine không sẵn sàng sau 90s (kẹt ở bước '{st}'): {' | '.join(errs[:3])}") from ex
    err = pg.evaluate("window.err || null")
    if err:
        b.close()
        raise StudioError(f"Engine lỗi: {err} {' | '.join(errs[:3])}")
    gl = pg.evaluate("window.glInfo || ''")
    if gpu == "auto" and "SwiftShader" in gl:
        pass  # máy không có GPU dùng được → vẫn chạy (chậm), thống kê sẽ ghi rõ
    return b, pg, gl


def parse_frames(spec):
    out = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = (int(x) for x in part.split("-"))
            out += list(range(a, b + 1))
        else:
            out.append(int(part))
    return out


def worker(url, out_dir, frames, quality, channel_name, gpu, resume):
    """Tiến trình con: mở engine, render danh sách frame → out_dir/fNNNN.jpg. In 'F n' sau mỗi frame."""
    import base64  # noqa: PLC0415

    from playwright.sync_api import sync_playwright  # noqa: PLC0415
    os.makedirs(out_dir, exist_ok=True)
    with sync_playwright() as p:
        b, pg, gl = _open(p, url, channel_name, gpu)
        print(f"GL {gl}", flush=True)
        t0, n = time.time(), 0
        for f in frames:
            dst = os.path.join(out_dir, f"f{f:04d}.jpg")
            if resume and os.path.exists(dst) and os.path.getsize(dst) > 0:
                continue
            d = pg.evaluate("([f, q]) => { window.renderFrame(f); "
                            "return (window.outCanvas || document.getElementById('c')).toDataURL('image/jpeg', q); }",
                            [f, quality])
            tmp = dst + ".tmp"
            with open(tmp, "wb") as fh:
                fh.write(base64.b64decode(d.split(",", 1)[1]))
            os.replace(tmp, dst)
            n += 1
            print(f"F {f}", flush=True)
        dt = time.time() - t0
        print(f"DONE {n} {dt:.3f}", flush=True)
        b.close()


def job_hash(job):
    return hashlib.sha1(json.dumps(job, sort_keys=True).encode()).hexdigest()[:12]


def render(job_path, out_dir, frames=None, workers=None, log=print, gpu=None):
    """Render các frame của một job (mặc định tất cả).
    Trả về thống kê {frames, rendered, sec, sec_per_frame, workers, gl}."""
    c = cfg()
    with open(job_path, encoding="utf-8") as fh:
        job = json.load(fh)
    frames = frames if frames is not None else list(range(int(job["frames"])))
    h = job_hash(job)
    os.makedirs(out_dir, exist_ok=True)
    stamp = os.path.join(out_dir, "_job.hash")
    if not os.path.exists(stamp) or open(stamp).read().strip() != h:  # job đổi → bỏ frame cũ
        for fn in os.listdir(out_dir):
            if fn.endswith(".jpg"):
                os.remove(os.path.join(out_dir, fn))
        with open(stamp, "w") as fh:
            fh.write(h)
    todo = [f for f in frames if not (c["resume"] and os.path.exists(os.path.join(out_dir, f"f{f:04d}.jpg")))]
    if not todo:
        return {"frames": len(frames), "rendered": 0, "sec": 0.0, "sec_per_frame": None, "workers": 0, "gl": "(resume)"}
    nw = max(1, min(workers or c["workers"], len(todo), 16))
    chunks = [todo[i * len(todo) // nw:(i + 1) * len(todo) // nw] for i in range(nw)]
    t0 = time.time()
    gl, done, procs = "", 0, []
    with serve() as port:
        url = url_for(port, job_path)
        for ch in chunks:
            spec = ",".join(str(x) for x in ch)
            cmd = [sys.executable, "-m", "vidlib.coderender", "worker", "--url", url, "--out", out_dir, "--frames", spec,
                   "--quality", str(c["quality"]), "--channel", c["channel"], "--gpu", gpu or c["gpu"]]
            logf = open(os.path.join(out_dir, f"_worker{len(procs)}.log"), "w", encoding="utf-8")  # noqa: SIM115
            pr = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=logf, text=True,
                                  encoding="utf-8", errors="replace")
            pr.logf = logf
            procs.append(pr)
        lock = threading.Lock()
        errs = []
        last = [time.time()]
        stall = float((channel().get("timeouts") or {}).get("render_stall", 240))

        def pump(pr):
            nonlocal gl, done
            for line in pr.stdout:
                last[0] = time.time()
                if line.startswith("GL "):
                    gl = line[3:].strip()
                elif line.startswith("F "):
                    with lock:
                        done += 1
                        if done % 30 == 0 or done == len(todo):
                            el = time.time() - t0
                            log(f"    {done}/{len(todo)} frame · {el / done * nw:.2f} s/frame/worker · {nw} worker")
            rc = pr.wait()
            pr.logf.close()
            if rc != 0:
                with open(pr.logf.name, encoding="utf-8", errors="replace") as fh:
                    errs.append(fh.read()[-800:])

        ths = [threading.Thread(target=pump, args=(pr,), daemon=True) for pr in procs]
        for th in ths:
            th.start()
        while any(th.is_alive() for th in ths):            # canh treo (AUD-204/808): không frame mới quá lâu → dừng
            time.sleep(0.5)
            if time.time() - last[0] > stall:
                for pr in procs:
                    with contextlib.suppress(OSError):
                        pr.kill()
                for th in ths:
                    th.join(timeout=5)
                raise StudioError(f"Render code-shot đứng {stall:.0f}s không ra frame mới (Edge/GPU treo?) — đã dừng "
                                  f"worker. Chạy lại để RESUME từ frame {done}/{len(todo)}.")
    if errs:
        raise StudioError("Render code-shot lỗi (chạy lại để RESUME):\n" + "\n".join(errs))
    dt = time.time() - t0
    st = {"frames": len(frames), "rendered": len(todo), "sec": round(dt, 2), "sec_per_frame": round(dt / len(todo), 3),
          "sec_per_frame_per_worker": round(dt * nw / len(todo), 3), "workers": nw, "gl": gl}
    save_json(os.path.join(out_dir, "_stats.json"), st)
    return st


def text_audit(job_path, frames):
    """Render các frame và trả về {crops, overlaps, boxes} — cho QA OCR, cổng ĐỎ chống chồng chữ & Zone C clearance."""
    import base64  # noqa: PLC0415
    import io  # noqa: PLC0415

    from PIL import Image  # noqa: PLC0415
    from playwright.sync_api import sync_playwright  # noqa: PLC0415
    c = cfg()
    crops, overlaps, boxes, on_object = [], [], [], []
    with serve() as port, sync_playwright() as p:
        b, pg, _gl = _open(p, url_for(port, job_path), c["channel"], c["gpu"])
        for f in frames:
            d = pg.evaluate("(f) => { window.renderFrame(f); "
                            "return [(window.outCanvas || document.getElementById('c')).toDataURL('image/png'), "
                            "window.textBoxes(), "
                            "typeof window.overlapPairs === 'function' ? window.overlapPairs() : []]; }", f)
            im = Image.open(io.BytesIO(base64.b64decode(d[0].split(",", 1)[1]))).convert("RGB")
            for pair in d[2] or []:
                overlaps.append({"frame": int(f), "a": str(pair.get("a", "")), "b": str(pair.get("b", "")),
                                 "ratio": float(pair.get("ratio", 0.0))})
            for t in d[1] or []:
                x0, y0, x1, y1 = t["box"]
                boxes.append({"frame": int(f), "text": str(t.get("text", "")),
                              "box": [float(x0), float(y0), float(x1), float(y1)]})
                pad = 10
                box = (max(0, int(x0) - pad), max(0, int(y0) - pad),
                       min(im.width, int(x1) + pad), min(im.height, int(y1) + pad))
                if box[2] - box[0] > 8 and box[3] - box[1] > 8:
                    tex = None
                    if t.get("tex"):  # texture phẳng của chữ, nền trong suốt → đặt lên nền đen
                        ti = Image.open(io.BytesIO(base64.b64decode(t["tex"].split(",", 1)[1]))).convert("RGBA")
                        tex = Image.new("RGB", ti.size, (0, 0, 0))
                        tex.paste(ti, (0, 0), ti)
                    crops.append((f, t["text"], im.crop(box), tex))
        if frames:   # vòng 23: phần chữ còn đè hình (beat tự báo sau khi đã vẽ ít nhất một frame)
            on_object = pg.evaluate("typeof window.labelReport === 'function' ? window.labelReport() : []") or []
        b.close()
    return {"crops": crops, "overlaps": overlaps, "boxes": boxes, "on_object": on_object}


def text_crops(job_path, frames):
    """Render các frame và trả về [(frame, chữ khai báo, ảnh PIL cắt quanh chữ, texture)] — cho QA OCR chữ trong cảnh."""
    return text_audit(job_path, frames)["crops"]


def meta(job_path):
    """Đọc metadata cảnh (cues SFX, chữ diegetic) mà không render."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415
    c = cfg()
    with serve() as port, sync_playwright() as p:
        b, pg, gl = _open(p, url_for(port, job_path), c["channel"], c["gpu"])
        m = pg.evaluate("window.meta")
        b.close()
    return m


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m vidlib.coderender")
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("worker")
    w.add_argument("--url", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--frames", required=True)
    w.add_argument("--quality", type=float, default=0.95)
    w.add_argument("--channel", default="msedge")
    w.add_argument("--gpu", default="auto")
    w.add_argument("--no-resume", action="store_true")
    r = sub.add_parser("render", help="render một job.json")
    r.add_argument("job")
    r.add_argument("out")
    r.add_argument("--frames")
    r.add_argument("--workers", type=int)
    r.add_argument("--gpu")
    a = ap.parse_args(argv)
    if a.cmd == "worker":
        worker(a.url, a.out, parse_frames(a.frames), a.quality, a.channel, a.gpu, not a.no_resume)
        return 0
    st = render(a.job, a.out, parse_frames(a.frames) if a.frames else None, a.workers, gpu=a.gpu)
    print(json.dumps(st, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
