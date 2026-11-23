"""Dữ liệu giả cho --dry-run và test: clip "giống Flow", lời đọc giả, nhạc giả.

Clip giả: nền đen, một khối trắng + chấm xanh chạy ngang, có
  - đầu TĨNH (head_sec), chuyển động đều, đuôi GIẢM TỐC (decel_sec, ease-out tới 0) rồi đứng yên (hold_sec)
  - tuỳ chọn một scene cut giữa clip (cut_at)
  - audio RÁC (sine + noise) để chứng minh ingest bỏ được tiếng.
Trả về ground truth để test so sánh.
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

from .common import FPS, StudioError, color, ffbin, font


def _pos(t, head, move_end, decel, speed, x0):
    """Vị trí x theo thời gian: đứng yên → đều → ease-out về 0."""
    if t <= head:
        return x0
    if t <= move_end:
        return x0 + speed * (t - head)
    d = min(t - move_end, decel)
    u = d / decel
    # tích phân vận tốc v(u) = speed·(1−u)² trên [0, d]
    return x0 + speed * (move_end - head) + speed * decel * (u - u * u + u ** 3 / 3)


def make_clip(path, duration=5.0, size=(720, 1280), head_sec=0.6, decel_sec=1.1, hold_sec=0.35, cut_at=None,
              label="", seed=0, audio=True, fps=None):
    fps = fps or FPS
    w, h = size
    n = int(round(duration * fps))
    move_end = duration - decel_sec - hold_sec
    x0 = w * 0.18
    dist = w * 0.62
    speed = dist / max((move_end - head_sec) + decel_sec / 3, 0.1)
    rng = np.random.default_rng(seed)
    accent = color("accent")
    lab_font = font(int(h * 0.03), "bold")
    cmd = [ffbin("ffmpeg"), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
           "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-f", "lavfi", "-t", f"{duration:.3f}", "-i", "sine=frequency=440:sample_rate=48000",
                "-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anoisesrc=color=pink:amplitude=0.25:sample_rate=48000",
                "-filter_complex", "[1:a][2:a]amix=inputs=2[a]", "-map", "0:v", "-map", "[a]", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", "-shortest", path]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    yb = h * (0.42 + 0.05 * rng.random())
    r = int(w * 0.09)
    try:
        for i in range(n):
            t = i / fps
            img = Image.new("RGB", (w, h), (0, 0, 0))
            d = ImageDraw.Draw(img)
            x = _pos(t, head_sec, move_end, decel_sec, speed, x0)
            after_cut = cut_at is not None and t >= cut_at
            if after_cut:  # "cảnh mới": khối lớn ở chỗ khác + hình nền khác
                d.rectangle([w * 0.1, h * 0.15, w * 0.9, h * 0.32], fill=(200, 200, 200))
                x = w - x
            d.line([(w * 0.08, yb + r + 6), (w * 0.92, yb + r + 6)], fill=(255, 255, 255), width=max(3, w // 90))
            sq = 1.0 + 0.25 * math.sin(t * 9) * (head_sec < t < move_end)
            d.ellipse([x - r * sq, yb - r / sq, x + r * sq, yb + r / sq], fill=(255, 255, 255))
            d.ellipse([x - r * 0.35, yb - r * 0.35, x + r * 0.35, yb + r * 0.35], fill=accent)
            if label:
                d.text((w * 0.05, h * 0.05), label, font=lab_font, fill=(90, 90, 90))
            p.stdin.write(img.tobytes())
    finally:
        p.stdin.close()
        err = p.stderr.read().decode("utf-8", "replace")
        p.stderr.close()
        p.wait()
    if p.returncode != 0:
        raise StudioError("Không tạo được clip giả: " + err[-400:])
    return {"frames": n, "head_end": int(round(head_sec * fps)), "decel_start": int(round(move_end * fps)),
            "stop": int(round((move_end + decel_sec) * fps)), "cut": int(round(cut_at * fps)) if cut_at else None,
            "has_audio": audio}


def frames_like(duration=5.0, head_sec=0.6, decel_sec=1.1, hold_sec=0.35, cut_at=None, size=(108, 192), fps=None):
    """Bản numpy (không qua ffmpeg) cho test nhanh: trả về (frames xám, ground truth)."""
    fps = fps or FPS
    w, h = size
    n = int(round(duration * fps))
    move_end = duration - decel_sec - hold_sec
    x0, dist = w * 0.18, w * 0.62
    speed = dist / max((move_end - head_sec) + decel_sec / 3, 0.1)
    yy, xx = np.mgrid[0:h, 0:w]
    out = np.zeros((n, h, w), np.float32)
    r = w * 0.09
    for i in range(n):
        t = i / fps
        x = _pos(t, head_sec, move_end, decel_sec, speed, x0)
        f = np.zeros((h, w), np.float32)
        if cut_at is not None and t >= cut_at:
            f[int(h * 0.15):int(h * 0.32), int(w * 0.1):int(w * 0.9)] = 200
            x = w - x
        f[(xx - x) ** 2 + (yy - h * 0.45) ** 2 <= r * r] = 255
        out[i] = f + np.random.default_rng(i).normal(0, 0.6, (h, w))  # nhiễu nén nhẹ
    gt = {"head_end": int(round(head_sec * fps)), "decel_start": int(round(move_end * fps)),
          "stop": int(round((move_end + decel_sec) * fps)), "cut": int(round(cut_at * fps)) if cut_at else None}
    return out, gt


def write_wav(path, stereo, sr=48000):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wv:
        wv.setnchannels(2)
        wv.setsampwidth(2)
        wv.setframerate(sr)
        wv.writeframes(data.tobytes())
    return path


def make_vo(path, lines, sr=48000, syl_sec=0.17, micro_gap=0.035, line_gap=0.45, lead=0.05):
    """Lời đọc giả: mỗi âm tiết là một tiếng 'ba' có cao độ, giữa các câu lặng line_gap giây.
    Trả về ground truth thời gian từng câu (giây, trước xử lý)."""
    from .lang import syllables_spoken as spoken_syllables
    rng = np.random.default_rng(3)
    t = np.arange(int(syl_sec * sr)) / sr
    env = np.sin(np.pi * t / syl_sec) ** 0.6
    parts = [np.zeros(int(lead * sr))]
    cur = lead
    truth = []
    for li, line in enumerate(lines):
        n = max(1, spoken_syllables(line))
        start = cur
        for k in range(n):
            f0 = 170 + 25 * math.sin(k * 1.3 + li)
            tone = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in (1, 2, 3, 4))
            parts.append((tone * 0.25 + rng.normal(0, 0.02, len(t))) * env)
            parts.append(np.zeros(int(micro_gap * sr)))
            cur += syl_sec + micro_gap
        truth.append({"start": round(start, 3), "end": round(cur - micro_gap, 3), "syllables": n})
        parts.append(np.zeros(int(line_gap * sr)))
        cur += line_gap
    mono = np.concatenate(parts).astype(np.float32)
    write_wav(path, np.stack([mono, mono], 1), sr)
    return truth


def make_music(path, seconds=60.0, bpm=120, sr=48000):
    """Nhạc giả: kick mỗi phách + pad, để kiểm tra ducking và bắt beat."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    pad = 0.08 * (np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 165 * t))
    beat = 60.0 / bpm
    kick = np.zeros(n, np.float32)
    kt = np.arange(int(0.18 * sr)) / sr
    k = np.sin(2 * np.pi * (55 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 18)
    for b in np.arange(0, seconds, beat):
        i = int(b * sr)
        kick[i:i + len(k)] += k[: max(0, min(len(k), n - i))]
    mono = (pad + 0.6 * kick).astype(np.float32)
    write_wav(path, np.stack([mono, mono], 1), sr)
    return {"bpm": bpm}
