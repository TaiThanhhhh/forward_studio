"""Engine `manim` — sơ đồ vật lý/toán bằng Manim Community Edition (pip install manim; KHÔNG cần LaTeX: chữ dùng Pango).

Cùng giao diện với các engine khác (engines/adapter.py): job.json → thư mục frame fNNNN.jpg đúng số frame. Manim dựng cả
cảnh một lượt trong tiến trình con (`python -m engines.manim.run`), sau đó ffmpeg tách frame. Mã cảnh: scenes.py — không
chứa nội dung video; dữ liệu (điểm đồ thị, vector, dòng phương trình, chữ) đến từ job.params (storyboard).
"""

import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEATS = ("title", "graph", "vectors", "equation", "counter", "compare", "fact", "outro")
PARAMS = {
    "title": ((), "kicker, title, sub"),
    "graph": (
        ("points",),
        "points[[x,y]…], x_label, y_label, y_unit, marks[{x,label}], decimals, title — đường cong + chấm chạy + số đọc",
    ),
    "vectors": (("vectors",), "title, object{label,role}, vectors[{label,dir:[x,y],mag,role}] — vật + các vector lực"),
    "equation": (
        ("lines",),
        "title, lines[{text,role}], result — phương trình hiện từng dòng, dòng kết quả được đóng khung",
    ),
    "counter": (("to",), "title, from, to, suffix, unit, label, decimals"),
    "compare": (("left", "right"), "title, left/right{label,value,unit,role}"),
    "fact": (("text",), "kicker, text, em"),
    "outro": ((), "teaser, follow, next_prefix"),
}
DEFAULT_TOKENS = {
    "font": "Montserrat-Variable.ttf",
    "stroke": 6,
    "creep": 0.03,
    "palette": {
        "bg": "#000000",
        "ink": "#ECECEC",
        "hot": "#FF6B3D",
        "cold": "#58C4DD",
        "accent": "#FFD866",
        "dim": "#6B6B6B",
    },
}


def available():
    try:
        import manim  # noqa: F401, PLC0415

        return True
    except Exception:  # noqa: BLE001
        return False


def validate(scene, params):
    if scene not in BEATS:
        return [f"beat manim '{scene}' không có (có: {', '.join(BEATS)})."]
    miss = [k for k in PARAMS[scene][0] if (params or {}).get(k) in (None, "", [], {})]
    return [f"beat manim '{scene}' thiếu params: {', '.join(miss)} ({PARAMS[scene][1]})."] if miss else []


def job(spec, rev):
    from PIL import ImageFont  # noqa: PLC0415

    from engines import adapter  # noqa: PLC0415
    from vidlib import lang, textstyle  # noqa: PLC0415

    st = textstyle.load_style(spec.style)
    mtok = {k: v for k, v in adapter.style_tokens(spec.style, "manim").items() if not k.startswith("_")}
    if not mtok:
        pal = (st.get("html") or {}).get("palette") or st.get("palette") or {}
        ink = _lift(pal.get("ink") or "#ECECEC")
        a = _lift(pal.get("a") or "#FF6B3D")
        b = _lift(pal.get("b") or "#58C4DD")
        c = _lift(pal.get("c") or a)
        mtok = {
            "font": st.get("font") or DEFAULT_TOKENS["font"],
            "palette": {"bg": "#000000", "ink": ink, "hot": a, "cold": b, "accent": c, "dim": "#6B6B6B"},
        }
    tok = {**DEFAULT_TOKENS, **mtok}
    fpath = os.path.join(ROOT, "assets", "fonts", tok["font"])
    return {
        "engine": "manim",
        "scene": spec.scene,
        "params": spec.params or {},
        "frames": int(spec.frames),
        "fps": spec.fps,
        "width": spec.width,
        "height": spec.height,
        "tokens": tok,
        "font": {"file": "assets/fonts/" + tok["font"], "family": ImageFont.truetype(fpath, 20).getname()[0]},
        "preroll": int(tok.get("preroll", 14)),  # dựng dư vài frame đầu rồi bỏ → frame 0 của shot đã có hình
        "locale": lang.locale().replace("_", "-"),
        "style": spec.style,
        "shot": spec.sid,
        "beat": spec.beat,
        "engine_rev": rev,
    }


def _hash(job_path):
    from engines import adapter  # noqa: PLC0415

    return adapter.job_hash(adapter.load_job(job_path))


def render(job_path, frames_dir, log=print):
    """Dựng cả cảnh (Manim không render lẻ frame) → frames_dir/fNNNN.jpg đúng job.frames. RESUME theo hash job."""
    from engines import adapter  # noqa: PLC0415
    from vidlib.common import StudioError, ffbin  # noqa: PLC0415

    j = adapter.load_job(job_path)
    n, h = int(j["frames"]), _hash(job_path)
    stamp = os.path.join(frames_dir, "_job.hash")
    if os.path.exists(stamp) and open(stamp).read().strip() == h and adapter.have_all(frames_dir, n):
        return {"frames": n, "rendered": 0, "sec": 0.0, "sec_per_frame": None, "workers": 0, "gl": "(resume)"}
    if not available():
        raise StudioError("Engine manim chưa cài: python -m pip install manim (xem docs/STYLE_AUDIT.md).")
    work = os.path.dirname(os.path.abspath(job_path))
    mp4 = os.path.join(work, "manim.mp4")
    t0 = time.time()
    env = {**os.environ, "PYTHONUTF8": "1"}
    limit = max(300.0, float(j.get("frames") or 90) * 3.0)     # AUD-204: Manim ~0.3–0.6 s/frame → trần 3 s/frame
    try:
        pr = subprocess.run(
            [sys.executable, "-m", "engines.manim.run", job_path, mp4],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=limit,
        )
    except subprocess.TimeoutExpired as e:
        raise StudioError(f"Manim quá {limit:.0f}s ở shot {j.get('shot')} — đã dừng.") from e
    if pr.returncode != 0 or not os.path.exists(mp4):
        raise StudioError(f"Manim lỗi ở shot {j.get('shot')} ({j['scene']}):\n{(pr.stderr or pr.stdout)[-1200:]}")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)
    subprocess.run(
        [
            ffbin("ffmpeg"),
            "-y",
            "-v",
            "error",
            "-i",
            mp4,
            "-start_number",
            "0",
            "-q:v",
            "2",
            os.path.join(frames_dir, "f%04d.jpg"),
        ],
        check=True,
    )
    pre = int(j.get("preroll", 0))
    allf = sorted(f for f in os.listdir(frames_dir) if f.endswith(".jpg"))
    for f in allf[:pre]:  # bỏ pre-roll rồi đánh số lại từ 0
        os.remove(os.path.join(frames_dir, f))
    for k, f in enumerate(allf[pre:]):
        os.replace(os.path.join(frames_dir, f), os.path.join(frames_dir, f"f{k:04d}.jpg"))
    got = sorted(f for f in os.listdir(frames_dir) if f.endswith(".jpg"))
    for f in got[n:]:  # thừa frame → bỏ; thiếu → lặp frame cuối (lệch ≤ 1–2 frame do làm tròn)
        os.remove(os.path.join(frames_dir, f))
    for k in range(len(got), n):
        shutil.copyfile(os.path.join(frames_dir, got[-1]), os.path.join(frames_dir, f"f{k:04d}.jpg"))
    _travel(j, frames_dir, n)
    with open(stamp, "w") as fh:
        fh.write(h)
    dt = time.time() - t0
    if abs(len(got) - n) > 2:
        log(f"  ⚠ manim {j.get('shot')}: dựng {len(got)} frame, cần {n} (đã cắt/lặp cho khớp)")
    return {
        "frames": n,
        "rendered": n,
        "sec": round(dt, 2),
        "sec_per_frame": round(dt / n, 3),
        "workers": 1,
        "gl": "manim/cairo",
        "native_frames": len(got),
    }


def _lift(hx, min_l=0.28):
    """Màu của style html dùng cho Manim (video trộn engine): nét mảnh trên nền đen cần đủ sáng — màu tối (xanh navy…)
    được pha trắng tới khi độ sáng tương đối ≥ min_l, giữ sắc độ."""
    h = hx.lstrip("#")
    if len(h) != 6:
        return hx
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def lum(c):
        lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    k = 0.0
    while lum([x + (1 - x) * k for x in rgb]) < min_l and k < 1:
        k += 0.05
    return "#" + "".join(f"{round((x + (1 - x) * k) * 255):02X}" for x in rgb)


def _travel(j, frames_dir, n):
    """"Một cú máy liền": frame trong chặng bay đầu/cuối shot được warp affine theo đúng camera của engine html
    (vidlib/spine.travel_matrix) — chuỗi shot Manim/html bay liền qua điểm cắt thay vì đứng như slide."""
    sp = j.get("spine")
    if not sp:
        return
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    from vidlib import spine  # noqa: PLC0415
    for f in range(n):
        M = spine.travel_matrix(sp, f, n, j["width"], j["height"])
        if M is None:
            continue
        p = os.path.join(frames_dir, f"f{f:04d}.jpg")
        im = cv2.imread(p)
        bg = tuple(int(x) for x in im[2, 2])            # nền của style (góc khung luôn là nền)
        out = cv2.warpAffine(im, np.array(M, dtype=np.float64), (im.shape[1], im.shape[0]), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=bg)
        cv2.imwrite(p, out, [cv2.IMWRITE_JPEG_QUALITY, 95])


def _warp_box(box, M):
    if M is None:
        return box
    xs, ys = [], []
    for x, y in ((box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])):
        xs.append(M[0][0] * x + M[0][1] * y + M[0][2])
        ys.append(M[1][0] * x + M[1][1] * y + M[1][2])
    return [min(xs), min(ys), max(xs), max(ys)]


def meta(job_path):
    """Cue SFX + chữ khai báo — tính thuần Python (không cần dựng cảnh)."""
    from engines import adapter  # noqa: PLC0415

    j = adapter.load_job(job_path)
    p, n, s = j["params"], int(j["frames"]), j["scene"]
    cues = [{"f": 2, "name": "whoosh_soft"}]
    sp = j.get("spine") or {}
    if sp.get("next"):                                   # chặng bay sang shot sau (giống engine html)
        cues.append({"f": max(0, n - max(4, int(sp.get("L", 9)))), "name": "whoosh"})
    if s == "graph":
        cues += [{"f": int(n * 0.8), "name": "ding"}]
    elif s in ("counter", "compare", "fact", "equation"):
        cues += [{"f": int(n * 0.6), "name": "ding" if s == "counter" else "hit"}]
    elif s == "vectors":
        k = max(1, len(p.get("vectors") or []))
        cues += [{"f": int(n * (0.25 + 0.5 * i / k)), "name": "pop"} for i in range(k)]
    texts = [str(p[k]) for k in ("kicker", "title", "sub", "text", "em", "teaser", "follow", "label") if p.get(k)]
    return {"cues": cues, "texts": texts or [s], "frames": n, "scene": s, "engine": "manim"}


def adapter_pre(job_path):
    from engines import adapter  # noqa: PLC0415

    return adapter.load_job(job_path).get("preroll", 0)


def text_crops(job_path, frames):
    """[(frame, chữ, ảnh cắt quanh chữ, None)] — khung bao do scenes.py ghi ra boxes.json lúc dựng."""
    from PIL import Image  # noqa: PLC0415

    work = os.path.dirname(os.path.abspath(job_path))
    fdir = os.path.join(work, "frames")
    render(job_path, fdir, log=lambda m: None)
    bp = os.path.join(work, "boxes.json")
    if not os.path.exists(bp):
        return []
    with open(bp, encoding="utf-8") as fh:
        boxes = json.load(fh)
    from engines import adapter  # noqa: PLC0415
    from vidlib import spine  # noqa: PLC0415

    j = adapter.load_job(job_path)
    out = []
    for f in frames:
        im = Image.open(os.path.join(fdir, f"f{f:04d}.jpg")).convert("RGB")
        M = spine.travel_matrix(j.get("spine"), f, int(j["frames"]), im.width, im.height)
        for b in boxes:
            if b["from_f"] - int(adapter_pre(job_path)) <= f <= b.get("to_f", 10**9):
                x0, y0, x1, y1 = _warp_box(b["box"], M)
                pad = 34  # camera trôi nhẹ giữa lúc ghi khung và frame đang xét
                box = (
                    max(0, int(x0) - pad),
                    max(0, int(y0) - pad),
                    min(im.width, int(x1) + pad),
                    min(im.height, int(y1) + pad),
                )
                if box[2] - box[0] > 8 and box[3] - box[1] > 8:
                    out.append((f, b["text"], im.crop(box), None))
    return out
