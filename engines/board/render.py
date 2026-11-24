"""CLI render engine board — chia đoạn theo số core rồi nối (như hướng dẫn của kaz-documentary), CRF theo cấu hình.

  python -m engines.board.render <board.json> full <out.mp4> [--workers N] [--crf 17]
  python -m engines.board.render <board.json> range <f0> <f1> <out.mp4> [--crf 17]
  python -m engines.board.render <board.json> stills <f1,f2,…> <thư_mục>        (JPEG fNNNNN.jpg)
  python -m engines.board.render <board.json> frames <f0> <f1> <thư_mục>        (JPEG fNNNN.jpg, đánh số từ 0)
  python -m engines.board.render <board.json> insert <id> <out.mp4> [--sec 4]   (đoạn phim câm đứng riêng)
Chạy từ gốc repo (cần import lib.motion). Frame nội bộ là BGR → ffmpeg nhận -pix_fmt bgr24.
"""
import json
import os
import shutil
import subprocess
import sys
import time

import cv2

from . import fonts
from .scene import Scene

ROOT = fonts.ROOT


def ffmpeg():
    try:
        from vidlib.common import ffbin  # noqa: PLC0415
        return ffbin("ffmpeg")
    except Exception:  # noqa: BLE001 — engine chạy độc lập
        return shutil.which("ffmpeg") or "ffmpeg"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def encoder(out, W, H, fps, crf, kind="master"):
    """kind master = file giao (trần bitrate VBV) · intermediate = đoạn của render_full (gần như không mất, không VBV)."""
    from vidlib import encode  # noqa: PLC0415 — tham số H.264 chung (BT.709, GOP, trần bitrate)

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    va = encode.video_args(kind, fps, crf if kind == "master" else None)
    return subprocess.Popen([ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                             "-r", str(fps), "-i", "-", "-vf", encode.RGB_TO_YUV, *va,
                             "-r", str(fps), out], stdin=subprocess.PIPE)


def _apply_caption_bgr(bgr, cap_layer, t_abs):
    """Đốt phụ đề auto-captions (Zone C) trực tiếp lên frame BGR của board khi có từ đang đọc."""
    if cap_layer is None:
        return bgr
    _, ch = cap_layer._active_chunk_with_idx(t_abs)
    if not ch:
        return bgr
    import numpy as np  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    im = Image.fromarray(bgr[:, :, ::-1])
    im = cap_layer.draw(im, t_abs)
    return np.ascontiguousarray(np.asarray(im)[:, :, ::-1])


def render_range(board_path, f0, f1, out, crf=19, kind="master", captions_json=None):
    b = load(board_path)
    sc = Scene(b)
    cap_layer = None
    if captions_json and os.path.exists(captions_json):
        cfg_cap = load(captions_json)
        if cfg_cap.get("preset") and cfg_cap["preset"] != "off" and cfg_cap.get("vo"):
            from vidlib import autocaptions  # noqa: PLC0415

            cap_layer = autocaptions.Layer(cfg_cap["vo"], cfg_cap["preset"], cfg_cap.get("style"))
    t0 = time.time()
    enc = encoder(out, sc.W, sc.H, sc.fps, crf, kind)
    try:
        for fi in range(f0, f1):
            fr = sc.frame(fi)
            if cap_layer is not None:
                fr = _apply_caption_bgr(fr, cap_layer, fi / sc.fps)
            enc.stdin.write(fr.tobytes())
    finally:
        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError(f"ffmpeg lỗi khi ghi {out}")
    return {"frames": f1 - f0, "sec": round(time.time() - t0, 2)}


def render_full(board_path, out, workers=0, crf=19, log=print, captions=None, maxrate=None):
    """Chia [0, frames) thành `workers` đoạn → mỗi đoạn một tiến trình → nối bằng concat (-c copy)."""
    b = load(board_path)
    n = int(b["frames"])
    workers = workers or max(1, min(12, (os.cpu_count() or 2) - 2))
    workers = max(1, min(workers, n // 15 or 1))
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "_parts")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    cap_file = None
    if isinstance(captions, dict) and captions.get("preset") and captions["preset"] != "off" and captions.get("vo"):
        cap_file = os.path.join(tmp, "captions.json")
        with open(cap_file, "w", encoding="utf-8") as cf:
            json.dump(captions, cf, ensure_ascii=False)
    bounds = [round(n * k / workers) for k in range(workers + 1)]
    t0 = time.time()
    procs = []
    for k in range(workers):
        part = os.path.join(tmp, f"part_{k:02d}.mp4")
        env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
               "BOARD_CV_THREADS": "1"}  # nhiều tiến trình: mỗi tiến trình 1 luồng, tránh tranh CPU
        cmd = [sys.executable, "-m", "engines.board.render", os.path.abspath(board_path),
               "range", str(bounds[k]), str(bounds[k + 1]), part, "--crf", str(crf), "--kind", "intermediate"]
        if cap_file:
            cmd += ["--captions", cap_file]
        procs.append((part, subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)))
    errs = []
    limit = max(600.0, n * 3.0)                          # AUD-204: tối đa ~3 s/frame rồi dừng, không treo vô hạn
    for _part, p in procs:
        try:
            _, e = p.communicate(timeout=limit)
        except subprocess.TimeoutExpired:
            for _, q in procs:
                q.kill()
            raise RuntimeError(f"Render board quá {limit:.0f}s — đã dừng các tiến trình.") from None
        if p.returncode != 0:
            errs.append(e.decode("utf-8", "replace")[-1500:])
    if errs:
        raise RuntimeError("Render board lỗi:\n" + errs[0])
    lst = os.path.join(tmp, "list.txt")
    fps = int(b.get("fps") or 30)
    with open(lst, "w", encoding="utf-8") as f:
        for k, (part, _) in enumerate(procs):
            # độ dài CHÍNH XÁC của đoạn (số frame / fps): không khai thì concat tự đoán từ container (có trễ B-frame,
            # không edit list) → mỗi chỗ nối hụt vài tick, video ra 30.015 fps và cổng QA "fps" đỏ
            f.write(f"file '{os.path.basename(part)}'\nduration {(bounds[k + 1] - bounds[k]) / fps:.9f}\n")
    from vidlib import encode  # noqa: PLC0415

    part_out = os.path.abspath(out) + ".part.mp4"           # ghi tạm rồi đổi tên: bị ngắt không để lại file hỏng
    joined = os.path.join(tmp, "joined.mp4")
    r = subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        *encode.mux_args(), joined], cwd=tmp, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[-1500:])
    # encode master MỘT lượt trên cả video: trần bitrate VBV tính liền mạch (≤ 10 Mb/s giúp video 40s ~35 MB chuẩn TikTok).
    r = subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", joined, "-map", "0:v:0", "-an",
                        *encode.video_args("master", fps, crf, maxrate=maxrate), "-r", str(fps), "-frames:v", str(n),
                        *encode.mux_args(), part_out], cwd=tmp, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[-1500:])
    from vidlib.common import replace_retry  # noqa: PLC0415
    replace_retry(part_out, os.path.abspath(out))
    shutil.rmtree(tmp, ignore_errors=True)
    sec = time.time() - t0
    return {"frames": n, "workers": workers, "sec": round(sec, 2), "sec_per_frame": round(sec / max(n, 1), 4),
            "sec_per_frame_per_worker": round(sec * workers / max(n, 1), 4)}


def stills(board_path, frames, out_dir, scene=None):
    sc = scene or Scene(load(board_path))
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for fi in frames:
        p = os.path.join(out_dir, f"f{fi:05d}.jpg")
        cv2.imwrite(p, sc.frame(fi), [cv2.IMWRITE_JPEG_QUALITY, 92])
        out.append(p)
    return out


def frames(board_path, f0, f1, out_dir, quality=95):
    sc = Scene(load(board_path))
    os.makedirs(out_dir, exist_ok=True)
    for k, fi in enumerate(range(f0, f1)):
        cv2.imwrite(os.path.join(out_dir, f"f{k:04d}.jpg"), sc.frame(fi), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return f1 - f0


def insert_standalone(board_path, iid, out, sec=None, crf=17):
    """Đoạn phim câm đứng riêng (iris mở từ đen, đóng về đen) — để xem/duyệt riêng hoặc dùng lại."""
    from . import vintage  # noqa: PLC0415
    import lib.motion as M  # noqa: PLC0415
    b = load(board_path)
    ins = next((x for x in b.get("inserts") or [] if x["id"] == iid), None)
    if ins is None:
        raise SystemExit(f"Không có đoạn chèn {iid} trong {board_path}")
    W, H, fps = int(b["width"]), int(b["height"]), int(b["fps"])
    n = int(round((sec or ins["n"] / fps) * fps))
    v = vintage.Insert(ins["spec"], W, H, fps, n, ins.get("tokens") or b.get("surface") or {})
    enc = encoder(out, W, H, fps, crf)
    import numpy as np  # noqa: PLC0415
    black = np.zeros((H, W, 3), np.uint8)
    try:
        for j in range(n):
            lt = j / fps
            k = min(1.0, M.smooth(lt / ins.get("iris_in", 0.3)), M.smooth((n - 1 - j) / fps / ins.get("iris_out", 0.35)))
            enc.stdin.write(vintage.iris(v.frame(j), black, k).tobytes())
    finally:
        enc.stdin.close()
        enc.wait()
    return {"frames": n, "sec": n / fps}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) < 2:
        print(__doc__)
        return 2
    crf = 19
    workers = 0
    sec = None
    kind = "master"
    captions_json = None
    for flag in ("--crf", "--workers", "--sec", "--kind", "--captions"):
        if flag in a:
            i = a.index(flag)
            v = a[i + 1]
            del a[i:i + 2]
            if flag == "--crf":
                crf = int(v)
            elif flag == "--workers":
                workers = int(v)
            elif flag == "--kind":
                kind = v
            elif flag == "--captions":
                captions_json = v
            else:
                sec = float(v)
    bp, mode = a[0], a[1]
    if os.environ.get("BOARD_CV_THREADS"):
        cv2.setNumThreads(int(os.environ["BOARD_CV_THREADS"]))
    if mode == "range":
        print(json.dumps(render_range(bp, int(a[2]), int(a[3]), a[4], crf, kind, captions_json=captions_json)))
    elif mode == "full":
        print(json.dumps(render_full(bp, a[2], workers, crf)))
    elif mode == "stills":
        print("\n".join(stills(bp, [int(x) for x in a[2].split(",") if x], a[3])))
    elif mode == "frames":
        print(frames(bp, int(a[2]), int(a[3]), a[4]))
    elif mode == "insert":
        print(json.dumps(insert_standalone(bp, a[2], a[3], sec, crf)))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
