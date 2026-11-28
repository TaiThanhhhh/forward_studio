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
    dd = np.abs(np.diff(fr, axis=0))
    d = dd.mean(axis=(1, 2))
    cut = d > 60
    n = max(1, (~cut).sum())
    bright = float(fr.mean())
    # vòng 23: ngưỡng "chuyển động nhanh" theo độ sáng của video — look tối (HUD, halftone) chuyển động thật vẫn có độ
    # lệch trung bình nhỏ vì phần lớn khung là đen; 9 mức xám ở video sáng ~25 → hạ tỉ lệ, sàn 3.
    thr = max(3.0, min(9.0, 9.0 * bright / 25.0))
    rapid = float(((d >= thr) & ~cut).sum() / n)
    still = float((((dd > 20).mean(axis=(1, 2)) < 0.002) & ~cut).sum() / n)   # cặp khung gần như không đổi điểm ảnh nào
    return {"rapid": round(rapid, 3), "median_diff": round(float(np.median(d)), 2), "frames": int(len(fr)),
            "brightness": round(bright, 1), "threshold": round(thr, 2), "still": round(still, 3)}


def brightness_verdict(m):
    """Vòng 23: video quá tối (trung bình < 8/255) trông như màn hình tắt trên điện thoại → chặn."""
    b = m.get("brightness")
    if b is None:
        return "không đo", None
    return (f"{b:.1f}/255 — quá tối, nền đêm/vật gần như biến mất" if b < 8 else f"{b:.1f}/255"), b >= 8


def verdict(m):
    """(nhãn, đạt?) — đỏ → không đạt; vàng → đạt kèm cảnh báo."""
    q = channel().get("qa", {})
    red, yellow = float(q.get("motion_red", 0.035)), float(q.get("motion_yellow", 0.06))
    r = m["rapid"]
    if m.get("still", 0) > 0.25:
        return f"{m['still']:.0%} cặp khung đứng yên — như slide", False
    if r < red:
        return f"{r:.1%} — như slide (< {red:.1%})", False
    if r < yellow:
        return f"{r:.1%} — hơi tĩnh (< {yellow:.1%})", True
    return f"{r:.1%}", True
