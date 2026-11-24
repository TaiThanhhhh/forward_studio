"""QA: điểm cắt + velocity mismatch, đồ thị auto-trim, ffprobe, freeze/black/loudness (gộp từ finish.sh của kit),
qa_sheet, OCR chữ (text_fx + chữ trong cảnh của shot code), so palette/độ dày nét code↔Flow, .srt, publish.md,
qa/report.md + qa/report.html (giao diện tiếng Việt)."""
import os

import numpy as np
from PIL import Image, ImageDraw

from . import motion
from .common import FPS, channel, font, probe


def cut_strips(samples, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    f = font(20, "bold")
    for k in range(len(samples) - 1):
        a, b = samples[k], samples[k + 1]
        if not a["tail_final"] or not b["head_final"]:
            continue
        frames = [a["tail_final"][-2] if len(a["tail_final"]) > 1 else a["tail_final"][-1], a["tail_final"][-1],
                  b["head_final"][0], b["head_final"][min(1, len(b["head_final"]) - 1)]]
        labels = [f"{a['sid']} −2", f"{a['sid']} −1", f"{b['sid']} 0", f"{b['sid']} +1"]
        score, det = motion.velocity_mismatch(np.stack(a["tail_clean"]), np.stack(b["head_clean"]))
        strip = Image.new("RGB", (4 * 270 + 5 * 8, 480 + 60), (20, 20, 24))
        d = ImageDraw.Draw(strip)
        for i, (im, lb) in enumerate(zip(frames, labels)):
            x = 8 + i * 278
            strip.paste(im, (x, 52))
            d.text((x + 4, 56), lb, font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        col = (60, 207, 122) if score < 0.35 else (255, 176, 32) if score < 0.6 else (255, 77, 77)
        d.text((8, 12), f"Cắt {a['sid']} → {b['sid']} · {b['transition']} · velocity mismatch {score:.2f}",
               font=font(24, "black"), fill=col)
        d.line([(8 + 2 * 278 - 4, 48), (8 + 2 * 278 - 4, 540)], fill=(63, 107, 255), width=4)
        name = f"cut_{k + 1:02d}_{a['sid']}-{b['sid']}.png"
        strip.save(os.path.join(out_dir, name))
        rows.append({"cut": k + 1, "from": a["sid"], "to": b["sid"], "transition": b["transition"],
                     "at_sec": round(b["start_f"] / FPS, 3), "mismatch": score, "file": name, **det})
    return rows


def trim_plot(sid, a, tr, path):
    """Đồ thị motion energy: vùng đầu tĩnh / đuôi giảm tốc (xám), cửa sổ dùng (xanh), scene cut (đỏ)."""
    e = np.asarray(a["energy"], float)
    w, h, pad = 900, 260, 30
    img = Image.new("RGB", (w, h), (16, 16, 20))
    d = ImageDraw.Draw(img)
    n = max(len(e), 2)
    mx = float(e.max()) or 1.0

    def X(i):
        return pad + (w - 2 * pad) * i / (n - 1)

    def Y(v):
        return h - pad - (h - 2 * pad) * v / mx
    def band(a0, a1, col):  # clip có thể không có đầu tĩnh/đuôi giảm tốc → bỏ qua dải rỗng
        a0, a1 = max(0, min(a0, n - 1)), max(0, min(a1, n - 1))
        if a1 > a0:
            d.rectangle([X(a0), pad, X(a1), h - pad], fill=col)
    band(0, a["head_end"], (50, 50, 56))
    band(a["tail_start"], n - 1, (50, 50, 56))
    band(tr["in"] * FPS, tr["out"] * FPS, (24, 45, 110))
    for c in a["cuts"]:
        d.line([(X(c), pad), (X(c), h - pad)], fill=(255, 77, 77), width=3)
    d.line([(X(i), Y(v)) for i, v in enumerate(e)], fill=(255, 255, 255), width=2)
    d.text((pad, 6), f"{sid}: đầu tĩnh {a['head_end']}f · đuôi giảm tốc từ {a['tail_start']}f/{n}f · "
                     f"dùng {tr['in']:.2f}–{tr['out']:.2f}s ({tr['how']})", font=font(16, "bold"), fill=(220, 220, 230))
    img.save(path)


def check_final(path, expect_audio=1):
    info = probe(path)
    W_, H_, F_ = channel()["format"]["width"], channel()["format"]["height"], channel()["format"]["fps"]
    checks = {
        "kích thước": (f"{info['width']}x{info['height']}", info["width"] == W_ and info["height"] == H_),
        "fps": (info["fps"], abs(info["fps"] - F_) < 0.01),
        "số audio track": (info["audio_streams"], info["audio_streams"] == expect_audio),
        "codec": (info["video_codec"], info["video_codec"] == "h264"),
    }
    return info, checks




# Báo cáo/QA mở rộng nằm ở qareport.py (giữ tên cũ qa.write_report… cho pipeline)
from .qareport import (freeze_black, hold_spans, look_metrics, look_summary, ocr_report, qa_sheet,  # noqa: E402,F401
                       studio_checks, write_html, write_publish, write_report, write_srt)
