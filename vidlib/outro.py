"""Outro dạng template code có tham số (cùng style bible).

Shorts/Reels (2–3s): "<copy.next_prefix> …?" + avatar bật lên + "<copy.follow>" (chuỗi theo ngôn ngữ kênh).
Mặc định outro Shorts dựng bằng engine code (engines/three/scenes/outro.js); file này là phương án 2D dự phòng.
  loop=True: 5 frame cuối whip sang frame ĐẦU của video → khi nền tảng phát lại, chuyển động nối liền.
YouTube dài (10–20s): khung end-screen 16:9 chừa đúng chỗ 2 ô video (613×343) + vòng Subscribe (298px),
  vùng an toàn x 192–1728, y 108–972 (support.google.com/youtube/answer/6388789 + đo bởi bên thứ ba).
Tuỳ chọn: clip nền assets/brand/outro/outro_bg.mp4 (tạo 1 lần trong Flow, prompt ở scripts.html).
"""
import contextlib
import math
import os
import subprocess

from PIL import Image, ImageDraw

import lib.motion as M

from . import fx, lang
from .common import (ASSETS_DIR, FPS, H, ROOT, W, StudioError, channel, clamp, color, ease_out, ffbin, font, replace_retry,
                     run, wrap)

AVATAR = os.path.join(ASSETS_DIR, "brand", "avatar.png")


def _avatar(size):
    im = Image.open(AVATAR).convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], size // 5, fill=255)
    im.putalpha(mask)
    return im


class BgClip:
    """Đọc tuần tự clip nền outro (nếu có), lặp lại khi hết."""

    def __init__(self, path, n):
        self.frames = []
        if not path or not os.path.exists(path):
            return
        cmd = [ffbin("ffmpeg"), "-v", "error", "-i", path, "-an", "-vf",
               f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
               "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        out = subprocess.run(cmd, capture_output=True).stdout
        k = len(out) // (W * H * 3)
        self.frames = [Image.frombytes("RGB", (W, H), out[i * W * H * 3:(i + 1) * W * H * 3]) for i in range(k)]

    def get(self, i):
        if not self.frames:
            return Image.new("RGB", (W, H), color("bg"))
        return self.frames[i % len(self.frames)].copy()


def shorts_drawer(sb, n_frames, first_frame=None):
    """Trả về draw(i) → ảnh RGB frame thứ i của outro Shorts."""
    cfg = channel()["outro"]
    o = sb.get("outro", {})
    teaser = (o.get("teaser") or "").strip()
    follow = o.get("follow_text") or lang.copy("follow")
    bg = BgClip(os.path.join(ROOT, cfg["bg_clip"]), n_frames)
    av = _avatar(300)
    f_pre = font(46, "display")
    f_teaser = font(84, "display")
    f_follow = font(50, "display")
    lines = wrap(teaser.upper(), f_teaser, 860)[:3]
    loop = o.get("loop", cfg["loop"]) and first_frame is not None
    n_loop = 5 if loop else 0

    def draw(i):
        img = bg.get(i)
        d = ImageDraw.Draw(img)
        # teaser (0.0s →)
        if teaser:
            k = 0.6 + 0.4 * M.back(i / 7)
            y = 470
            d.text((W / 2, y - 70), lang.copy("next_prefix").upper(), font=f_pre, fill=color("fill"),
                   anchor="mm")
            for j, ln in enumerate(lines):
                sp = _line_sprite(ln, f_teaser, j == len(lines) - 1)
                w, h = int(sp.width * k), int(sp.height * k)
                sp2 = sp.resize((max(1, w), max(1, h)), Image.BICUBIC)
                img.paste(sp2, (int(W / 2 - w / 2), int(y + j * 100 - h / 2)), sp2)
        # avatar + follow (0.45s →)
        fa = i - int(0.45 * FPS)
        if fa >= 0:
            s = 0.3 + 0.7 * M.back(fa / 9)
            a2 = av.resize((max(1, int(300 * s)), max(1, int(300 * s))), Image.BICUBIC)
            cy = 980
            img.paste(a2, (int(W / 2 - a2.width / 2), int(cy - a2.height / 2)), a2)
            ff = i - int(0.7 * FPS)
            if ff >= 0:
                al = clamp(ff / 4)
                yy = 1200 + (1 - ease_out(ff / 6)) * 40
                d.text((W / 2, yy), follow, font=f_follow, fill=tuple(int(c * al) for c in color("ink")), anchor="mm")
                # chấm xanh motif chạy dưới chữ
                bw = f_follow.getlength(follow)
                prog = ease_out(ff / 10)
                x0 = W / 2 - bw / 2
                d.line([(x0, yy + 44), (x0 + bw * prog, yy + 44)], fill=color("ink"), width=8)
                r = 12
                d.ellipse([x0 - 34 - r, yy + 44 - r, x0 - 34 + r, yy + 44 + r], fill=color("accent"))
        if loop and i >= n_frames - n_loop:
            prev = img
            img = fx.transition(first_frame.copy(), prev, "whip", i - (n_frames - n_loop))
        return img

    return draw


def _line_sprite(text, f, last):
    x0, t, r, b = f.getbbox(text, stroke_width=8)
    im = Image.new("RGBA", (r - x0 + 40, b - t + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if last and text.endswith("?"):
        body = text[:-1]
        d.text((20 - x0, 20 - t), body, font=f, fill=color("ink"), stroke_width=8, stroke_fill=(0, 0, 0))
        d.text((20 - x0 + f.getlength(body), 20 - t), "?", font=f, fill=color("accent_glow"), stroke_width=8,
               stroke_fill=(0, 0, 0))
    else:
        d.text((20 - x0, 20 - t), text, font=f, fill=color("ink"), stroke_width=8, stroke_fill=(0, 0, 0))
    return im


# ------------------------------------------------------------------ YouTube end screen
YT = {"w": 1920, "h": 1080, "safe": (192, 108, 1728, 972), "video": (613, 343), "sub": 298}


def endscreen_layout():
    """Ô dành cho phần tử end screen của YouTube (toạ độ khung 1920×1080)."""
    x0, y0, x1, y1 = YT["safe"]
    vw, vh = YT["video"]
    gap = 60
    top = 300
    v1 = (x0 + 40, top, x0 + 40 + vw, top + vh)
    v2 = (v1[2] + gap, top, v1[2] + gap + vw, top + vh)
    cx = (v2[2] + x1) / 2 + 10
    cy = top + vh / 2
    r = YT["sub"] / 2
    sub = (cx - r, cy - r, cx + r, cy + r)
    return {"video_1": v1, "video_2": v2, "subscribe": sub}


def render_endscreen(sb, out_mp4, out_guide, seconds=None):
    """Video 16:9 nền đen + motif bậc thang, CHỪA TRỐNG các ô phần tử. Kèm ảnh guide có viền ô."""
    seconds = seconds or channel()["outro"]["youtube_duration_sec"]
    w, h = YT["w"], YT["h"]
    lay = endscreen_layout()
    n = int(seconds * FPS)
    f_t = font(64, "display")
    f_s = font(34, "display")
    teaser = (sb.get("outro", {}).get("teaser") or "").strip()
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    from . import encode  # noqa: PLC0415
    tmp = out_mp4 + ".part.mp4"          # ghi tạm → kiểm mã thoát → đổi tên (AUD-203/307: không để lại file 48 byte)
    cmd = [ffbin("ffmpeg"), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
           "-i", "-", "-f", "lavfi", "-t", f"{seconds}", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
           "-vf", encode.RGB_TO_YUV, *encode.video_args("master", FPS), *encode.audio_args(), *encode.mux_args(), tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    guide = None
    for i in range(n):
        img = Image.new("RGB", (w, h), color("bg"))
        d = ImageDraw.Draw(img)
        d.text((w / 2, 150), lang.copy("endscreen_title"), font=f_t, fill=color("ink"), anchor="mm")
        if teaser:
            line = f"{lang.copy('next_prefix')} {teaser}"
            d.text((w / 2, 840), line, font=f_s, fill=color("fill"), anchor="mm")
        # motif bậc thang chạy dọc đáy, chấm xanh leo bậc
        steps = 6
        sx, sy, stw, sth = 260, 1010, 230, 22
        pts = []
        for k in range(steps):
            pts += [(sx + k * stw, sy - k * sth), (sx + (k + 1) * stw, sy - k * sth)]
        d.line(pts, fill=color("ink"), width=10)
        prog = (i / FPS * 0.8) % steps
        kx = int(prog)
        hop = abs(math.sin(math.pi * (prog - kx)))
        bx = sx + kx * stw + (prog - kx) * stw
        by = sy - kx * sth - 26 - hop * 40
        d.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=color("accent"))
        if i == 0:
            guide = img.copy()
        p.stdin.write(img.tobytes())
    p.stdin.close()
    if p.wait(timeout=600) != 0:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise StudioError(f"ffmpeg lỗi khi ghi endscreen {out_mp4}")
    replace_retry(tmp, out_mp4)
    gd = ImageDraw.Draw(guide)
    for k, box in lay.items():
        if k == "subscribe":
            gd.ellipse(box, outline=(255, 45, 45), width=4)
        else:
            gd.rectangle(box, outline=(255, 45, 45), width=4)
        gd.text((box[0] + 12, box[1] + 10), k, font=f_s, fill=(255, 45, 45))
    gd.rectangle(YT["safe"], outline=(63, 107, 255), width=2)
    guide.save(out_guide)
    run(["ffprobe", "-v", "error", out_mp4], "ffprobe")
    return out_mp4, out_guide, lay

