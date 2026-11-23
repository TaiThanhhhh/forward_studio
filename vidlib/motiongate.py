"""Cổng "cảm giác slide PowerPoint": đo tỉ lệ khung hình có chuyển động nhanh trong video cuối.

Cách đo học từ `film_gate` của huashu-art-motion (MIT, scripts/film_gate.py — đọc để hiểu, viết lại): video 12 fps,
thu nhỏ 320 px, xám; một cặp frame liền nhau "chuyển động nhanh" khi độ lệch xám trung bình ≥ 9; cặp lệch quá lớn (cắt
cảnh cứng) không tính. Tỉ lệ thấp = hình đứng như slide, chỉ có chữ/đạo cụ hiện lên rồi đứng yên.

Ngưỡng (config/channel.json → qa.motion_red / motion_yellow): < 3.5% đỏ (CẦN XEM), < 6% vàng (cảnh báo). Đo trên kênh:
video Flow ~55%, phim demo MG Styles 26–39%, engine html bản slide cũ 1–4%, bản "một cú máy liền" ~11%.
"""

import subprocess

import numpy as np

from .common import channel, ffbin


def measure(path, fps=12, width=320):
    """{rapid, median_diff, frames} — rapid = tỉ lệ cặp frame chuyển động nhanh (không tính cắt cứng)."""
    pr = subprocess.run([ffbin("ffprobe"), "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0", path], capture_output=True, text=True)
    w0, h0 = (int(x) for x in pr.stdout.strip().split(",")[:2])
    h = int(round(width * h0 / w0 / 2) * 2)
    raw = subprocess.run([ffbin("ffmpeg"), "-v", "error", "-i", path, "-vf", f"fps={fps},scale={width}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, width).astype(np.int16)
    if len(fr) < 3:
        return {"rapid": 0.0, "median_diff": 0.0, "frames": len(fr)}
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    cut = d > 60
    rapid = float(((d >= 9) & ~cut).sum() / max(1, (~cut).sum()))
    return {"rapid": round(rapid, 3), "median_diff": round(float(np.median(d)), 2), "frames": int(len(fr))}


def verdict(m):
    """(nhãn, đạt?) — đỏ → không đạt; vàng → đạt kèm cảnh báo."""
    q = channel().get("qa", {})
    red, yellow = float(q.get("motion_red", 0.035)), float(q.get("motion_yellow", 0.06))
    r = m["rapid"]
    if r < red:
        return f"{r:.1%} — như slide (< {red:.1%})", False
    if r < yellow:
        return f"{r:.1%} — hơi tĩnh (< {yellow:.1%})", True
    return f"{r:.1%}", True
