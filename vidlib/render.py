"""Render: một lượt encode duy nhất cho toàn video.

Mỗi frame: nguồn (clip Flow đã trim / frame engine code-shot / ảnh start / khung tạm)
→ camera ảo (vcam: creep, punch-in, kick, quán tính qua điểm cắt, payoff) — chỉ cho nguồn KHÔNG phải engine
   (engine tự có camera camFromKeys cùng thư viện lib/motion)
→ transition → chữ text_fx (Tầng 1, neo vật, có occlusion) → x264.
Âm thanh ghép sau bằng mix.master (gain tuyến tính + limiter true-peak). Thu mẫu frame quanh điểm cắt cho QA.
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from . import codeshot, fx, outro, vcam
from .common import FPS, H, W, StudioError, color, ffbin, font, replace_retry, wrap

QA_SIZE = (108, 192)
AGENCY_TRANSITIONS = ("iris_match", "whip_match", "tape_stop")
IRIS_OUT_FRAMES = 6
IRIS_IN_FRAMES = 6
WHIP_MATCH_FRAMES = 6
WHIP_OUT_FRAMES = 2
TAPE_STOP_FRAMES = 4
_RADIAL_CACHE = {}


def _ease_out_cubic(p):
    p = min(1.0, max(0.0, float(p)))
    return 1.0 - (1.0 - p) ** 3


def _ease_in_cubic(p):
    p = min(1.0, max(0.0, float(p)))
    return p ** 3


def _smoothstep(p):
    p = min(1.0, max(0.0, float(p)))
    return p * p * (3.0 - 2.0 * p)


def _radial_mask(w, h):
    key = (w, h)
    m = _RADIAL_CACHE.get(key)
    if m is None:
        yy = (np.arange(h, dtype=np.float32) - h * 0.5) / (min(w, h) * 0.55)
        xx = (np.arange(w, dtype=np.float32) - w * 0.5) / (min(w, h) * 0.55)
        r2 = yy[:, None] ** 2 + xx[None, :] ** 2
        m = np.clip(1.0 - r2, 0.0, 1.0)[..., None] ** 2
        _RADIAL_CACHE[key] = m
    return m


def _scale_center(img, scale):
    """Phóng/thu tất định quanh tâm khung (scale >= 1: crop-zoom subpixel; scale < 1: thu + edge-pad không viền đen)."""
    if abs(scale - 1.0) < 1e-4:
        return img
    w, h = img.size
    if scale > 1.0:
        inv = 1.0 / scale
        dx = w * 0.5 * (1.0 - inv)
        dy = h * 0.5 * (1.0 - inv)
        return img.transform((w, h), Image.AFFINE, (inv, 0.0, dx, 0.0, inv, dy), resample=Image.BICUBIC)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    small = np.asarray(img.resize((nw, nh), Image.BICUBIC))
    pad_l = (w - nw) // 2
    pad_r = w - nw - pad_l
    pad_t = (h - nh) // 2
    pad_b = h - nh - pad_t
    return Image.fromarray(np.pad(small, ((pad_t, pad_b), (pad_l, pad_r), (0, 0)), mode="edge"))


def _add_radial_lift(img, strength):
    if strength <= 0.5:
        return img
    w, h = img.size
    arr = np.asarray(img, dtype=np.float32)
    out = np.clip(arr + _radial_mask(w, h) * float(strength), 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(out)


def _contrast_and_flash(img, contrast=1.0, flash=0.0):
    arr = np.asarray(img, dtype=np.float32)
    if abs(contrast - 1.0) > 1e-3:
        arr = (arr - 127.5) * contrast + 127.5
    if flash > 1e-3:
        arr = arr * (1.0 - flash) + 255.0 * flash
    return Image.fromarray(np.clip(arr, 0.0, 255.0).astype(np.uint8))


def apply_transition_out(img, next_kind, i, n):
    """Hiệu ứng phần đuôi shot A ngay trước điểm cắt (iris_match: 6f cuối zoom 1.0→1.42x; whip_match: 2f lấy đà)."""
    if not next_kind or n <= 0:
        return img
    rem = n - i
    if next_kind == "iris_match":
        win = min(IRIS_OUT_FRAMES, max(1, n // 2))
        if rem > win:
            return img
        k = win - rem  # 0 .. win-1
        e = _ease_in_cubic((k + 1) / win)
        out = _scale_center(img, 1.0 + 0.42 * e)
        return _add_radial_lift(out, 46.0 * e)
    if next_kind == "whip_match":
        win = min(WHIP_OUT_FRAMES, max(1, n // 3))
        if rem > win:
            return img
        k = win - rem  # 0 .. win-1
        p = (k + 1) / (win + 1)
        w = img.size[0]
        arr = np.asarray(img)
        shift = max(1, int(round(p * p * w * 0.22)))
        shifted = np.empty_like(arr)
        shifted[:, : w - shift] = arr[:, shift:]
        shifted[:, w - shift:] = arr[:, -1:]
        return Image.fromarray(fx._hblur(shifted, 24.0 + 42.0 * p))
    return img


def apply_transition_in(img, prev, kind, i):
    """Áp transition vào frame thứ i của shot B (hỗ trợ 3 Agency Transitions mới + giữ nguyên các transition cũ)."""
    if kind == "iris_match":
        if i >= IRIS_IN_FRAMES:
            return img
        e = _ease_out_cubic(i / IRIS_IN_FRAMES)
        scale = 0.85 + 0.15 * e
        out = _scale_center(img, scale)
        if prev is not None and i == 0:
            prev_z = prev if prev.size == out.size else prev.resize(out.size, Image.BICUBIC)
            out = Image.blend(out, prev_z, 0.20)
        return _add_radial_lift(out, 26.0 * (1.0 - e))
    if kind == "whip_match":
        if prev is None or i >= WHIP_MATCH_FRAMES:
            return img
        p = _ease_out_cubic((i + 1) / (WHIP_MATCH_FRAMES + 1))
        w = img.size[0]
        prev_im = prev if prev.size == img.size else prev.resize(img.size, Image.BICUBIC)
        a_prev, a_new = np.asarray(prev_im), np.asarray(img)
        off = max(1, min(w - 1, int(round(p * w))))
        comp = np.empty_like(a_new)
        comp[:, : w - off] = a_prev[:, off:]
        comp[:, w - off:] = a_new[:, :off]
        # vận tốc đỉnh ngay tại điểm cắt rồi giảm mượt về 0 — không dip đen
        vel = (1.0 - i / WHIP_MATCH_FRAMES) ** 1.3
        return Image.fromarray(fx._hblur(comp, 12.0 + 84.0 * vel))
    if kind == "tape_stop":
        if i >= TAPE_STOP_FRAMES:
            return img
        prev_im = (prev if prev.size == img.size else prev.resize(img.size, Image.BICUBIC)) if prev is not None else None
        if i == 0:
            base = _scale_center(prev_im if prev_im is not None else img, 1.07)
            a = np.asarray(base).copy()
            h = a.shape[0]
            a[..., 0] = np.roll(a[..., 0], 11, axis=1)
            a[..., 2] = np.roll(a[..., 2], -11, axis=1)
            a[int(h * 0.28):int(h * 0.34)] = np.roll(a[int(h * 0.28):int(h * 0.34)], 22, axis=1)
            a[int(h * 0.64):int(h * 0.69)] = np.roll(a[int(h * 0.64):int(h * 0.69)], -18, axis=1)
            return _contrast_and_flash(Image.fromarray(a), contrast=1.28, flash=0.46)
        if i == 1:
            base = Image.blend(prev_im, img, 0.55) if prev_im is not None else img
            base = _scale_center(base, 1.04)
            a = np.asarray(base).copy()
            h = a.shape[0]
            a[..., 0] = np.roll(a[..., 0], -7, axis=1)
            a[..., 2] = np.roll(a[..., 2], 7, axis=1)
            a[int(h * 0.44):int(h * 0.49)] = np.roll(a[int(h * 0.44):int(h * 0.49)], -14, axis=1)
            return _contrast_and_flash(Image.fromarray(a), contrast=1.22, flash=0.24)
        if i == 2:
            base = _scale_center(img, 1.03)
            a = np.asarray(base).copy()
            a[..., 0] = np.roll(a[..., 0], 4, axis=1)
            a[..., 2] = np.roll(a[..., 2], -4, axis=1)
            return _contrast_and_flash(Image.fromarray(a), contrast=1.12, flash=0.10)
        return _contrast_and_flash(_scale_center(img, 1.01), contrast=1.04, flash=0.0)
    return fx.transition(img, prev, kind, i)


def apply_loop_bridge(img, first_frame, k):
    """k ∈ [0, 1]: cầu nối cross-motion/zoom mượt ở cuối shot cuối nối thẳng về frame 0 shot đầu (seamless_loop)."""
    s = _smoothstep(k)
    if s <= 1e-4 or first_frame is None:
        return img
    target = first_frame if first_frame.size == img.size else first_frame.resize(img.size, Image.BICUBIC)
    a = _scale_center(img, 1.0 + 0.12 * s)
    b = _scale_center(target, 0.94 + 0.06 * s)
    return Image.blend(a, b, s)


class ClipSource:
    """Đọc cửa sổ [t_in, t_out) của clip đã ingest, resample đúng n frame (speed = độ dài nguồn / n)."""

    def __init__(self, path, t_in, t_out, n):
        self.src_n = max(1, int(round((t_out - t_in) * FPS)))
        self.n = n
        cmd = [ffbin("ffmpeg"), "-v", "error", "-ss", f"{max(t_in, 0):.4f}", "-i", path, "-an",
               "-frames:v", str(self.src_n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.idx = -1
        self.cur = None

    def frame(self, j):
        want = min(self.src_n - 1, int(j * self.src_n / max(self.n, 1)))
        size = W * H * 3
        while self.idx < want and self.p:
            buf = self.p.stdout.read(size)
            if len(buf) < size:
                self.close()
                break
            self.cur = Image.frombytes("RGB", (W, H), buf)
            self.idx += 1
        return self.cur.copy() if self.cur else Image.new("RGB", (W, H), color("bg"))

    def close(self):
        if self.p:
            self.p.stdout.close()
            self.p.kill()
            self.p.wait()
            self.p = None


class ImageSource:
    """Chưa có clip nhưng có ảnh Start: dùng ảnh tĩnh (camera ảo vẫn creep nên không đứng hình)."""

    def __init__(self, path, n):
        src = Image.open(path).convert("RGB")
        s = max(W / src.width, H / src.height)
        self.img = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
        if self.img.size != (W, H):
            x, y = (self.img.width - W) // 2, (self.img.height - H) // 2
            self.img = self.img.crop((x, y, x + W, y + H))
        self.n = n

    def frame(self, j):
        return self.img.copy()

    def close(self):
        pass


class Placeholder:
    def __init__(self, shot, n):
        img = Image.new("RGB", (W, H), color("bg"))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([90, 640, W - 90, 1180], 30, outline=color("fill"), width=4)
        d.text((W / 2, 700), f"{shot['id']} · CHƯA CÓ CLIP", font=font(54, "black"), fill=color("accent_glow"), anchor="ma")
        for i, ln in enumerate(wrap(shot.get("start_frame", {}).get("desc", ""), font(34, "semibold"), W - 260)[:7]):
            d.text((W / 2, 800 + i * 48), ln, font=font(34, "semibold"), fill=color("fill"), anchor="ma")
        self.img = img
        self.n = n

    def frame(self, j):
        return self.img.copy()

    def close(self):
        pass


class EngineSource:
    """Frame đã render bởi engine three.js (work/code/<sid>/frames/fNNNN.jpg)."""

    def __init__(self, d, n):
        self.d, self.n = d, n
        missing = [f for f in range(n) if not os.path.exists(os.path.join(d, f"f{f:04d}.jpg"))]
        if missing:
            raise StudioError(f"Thiếu {len(missing)} frame code-shot trong {d} (chạy stage `code`).")

    def frame(self, j):
        im = Image.open(os.path.join(self.d, f"f{min(j, self.n - 1):04d}.jpg")).convert("RGB")
        return im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS)

    def close(self):
        pass


def make_source(proj, shot, seg, trims, ingested):
    if codeshot.is_3d(shot):
        return EngineSource(codeshot.frames_dir(proj, shot["id"]), seg["n"]), "code3d"
    if codeshot.is_board(shot):
        return EngineSource(codeshot.board_frames_dir(proj, shot["id"]), seg["n"]), "board"
    vid = ingested(shot["id"])
    if vid and os.path.exists(vid) and shot["id"] in trims:
        tr = trims[shot["id"]]
        return ClipSource(vid, tr["in"], tr["out"], seg["n"]), "clip"
    img = os.path.join(proj, shot["start_frame"]["file"])
    if os.path.exists(img):
        return ImageSource(img, seg["n"]), "image"
    return Placeholder(shot, seg["n"]), "placeholder"


def _gray_small(img):
    return np.asarray(img.convert("L").resize(QA_SIZE, Image.BILINEAR), np.float32)


def _whip_to(img, target, k):
    """k ∈ [0,1]: lia ngang từ img sang target (nối loop về frame đầu)."""
    a, b = np.asarray(img), np.asarray(target)
    off = int(k * W)
    comp = np.empty_like(a)
    comp[:, : W - off] = a[:, off:]
    comp[:, W - off:] = b[:, :off]
    return Image.fromarray(fx._hblur(comp, 110 * (1 - abs(2 * k - 1)) + 12))


def spine_shot_ids(proj, sb):
    """Shot (kể cả OUTRO) dựng bằng engine html trong một cú máy liền — đọc từ job.json (nguồn sự thật của lần render)."""
    import json  # noqa: PLC0415
    out = set()
    for sid in [s["id"] for s in sb.get("shots", [])] + ["OUTRO"]:
        jp = os.path.join(codeshot.code_dir(proj, sid), "job.json")
        if os.path.exists(jp):
            with open(jp, encoding="utf-8") as fh:
                if json.load(fh).get("spine"):
                    out.add(sid)
    return out


def render(proj, sb, tl, layer, trims, ingested, cams, out_video=None, stills_at=None, captions=None):
    """Render video (out_video). stills_at={frame_abs: nhãn} → thu ảnh cho contact sheet. Trả về thống kê + mẫu QA."""
    shots = {s["id"]: s for s in sb["shots"]}
    enc = None
    if out_video:
        os.makedirs(os.path.dirname(out_video), exist_ok=True)
        tmp = out_video + ".part.mp4"
        from . import encode  # noqa: PLC0415
        enc = subprocess.Popen([ffbin("ffmpeg"), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", encode.RGB_TO_YUV,
                                *encode.video_args("master", FPS), "-r", str(FPS), *encode.mux_args(), tmp],
                               stdin=subprocess.PIPE)
    kinds, samples, stills = {}, [], []
    prev_clean, first_frame, first_rendered = None, None, None
    outro_dir = codeshot.frames_dir(proj, "OUTRO")
    spine_ids, prev_sid = spine_shot_ids(proj, sb), None
    style_res = sb.get("style_resolved") or sb.get("style")
    prev_eng = None
    segs = tl["segments"]
    outro_cfg = sb.get("outro") or {}
    seamless_loop = bool(tl.get("seamless_loop")) or outro_cfg.get("mode") == "loop" or (
        outro_cfg.get("enabled") is False and bool(outro_cfg.get("loop"))
    )
    loop_bridge_n = int(tl.get("loop_bridge_frames") or outro_cfg.get("bridge_frames") or 8) if seamless_loop else 0
    try:
        for seg_idx, seg in enumerate(segs):
            is_outro = seg["sid"] == "OUTRO"
            is_last = seg_idx == len(segs) - 1
            shot = shots.get(seg["sid"])
            cur_eng = codeshot.engine_of(shot, style_res) if (shot and codeshot.is_3d(shot)) else None
            cam = cams.get(seg["sid"]) if cams else None
            if is_outro and os.path.exists(os.path.join(outro_dir, f"f{seg['n'] - 1:04d}.jpg")):
                src, kind, draw = EngineSource(outro_dir, seg["n"]), "outro_code", None
            elif is_outro:
                draw = outro.shorts_drawer(sb, seg["n"], first_frame)
                src, kind = None, "outro"
            else:
                src, kind = make_source(proj, shot, seg, trims, ingested)
                draw = None
            kinds[kind] = kinds.get(kind, 0) + 1
            head_c, head_f, tail_c, tail_f = [], [], [], []
            n_loop = 5 if (is_outro and kind == "outro_code" and outro_cfg.get("loop", True)) else 0
            bridge_n = max(1, min(loop_bridge_n, max(1, seg["n"] // 2))) if (
                seamless_loop and is_last and not is_outro and loop_bridge_n > 0
            ) else 0
            # đổi engine 2D html ↔ 3D three.js: chuyển êm bằng 'dip' cho cut/whip, giữ nguyên các Agency Transitions
            cross_eng = bool(prev_eng and cur_eng and prev_eng != cur_eng and {prev_eng, cur_eng} == {"html", "three"})
            trans = "dip" if (cross_eng and seg["transition"] in ("cut", "whip")) else seg["transition"]
            next_seg = segs[seg_idx + 1] if seg_idx + 1 < len(segs) else None
            next_trans = next_seg["transition"] if next_seg else None
            skip_in = bool(spine_ids and seg["sid"] in spine_ids and prev_sid in spine_ids
                           and trans not in AGENCY_TRANSITIONS)
            skip_out = bool(next_seg and spine_ids and seg["sid"] in spine_ids and next_seg["sid"] in spine_ids
                            and next_trans not in AGENCY_TRANSITIONS)
            for i in range(seg["n"]):
                fa = seg["start_f"] + i
                t_abs = fa / FPS
                if draw is not None:
                    img = draw(i)
                    clean = img
                else:
                    img = src.frame(i)
                    if kind in ("clip", "image", "placeholder") and cam is not None:
                        img = vcam.apply(img, *cam.frame(i))
                    clean = img
                # cú máy liền: không chồng transition thường, nhưng vẫn giữ các Agency Transitions chủ đích
                if not skip_in:
                    img = apply_transition_in(img, prev_clean, trans, i)
                if next_trans and not skip_out:
                    img = apply_transition_out(img, next_trans, i, seg["n"])
                if not is_outro:
                    img = layer.draw(img.copy() if img is clean else img, clean, seg, shot, fa, t_abs)
                    if captions is not None:
                        img = captions.draw(img, t_abs, shot=shot)
                if first_frame is None:
                    first_frame = clean.copy()
                if first_rendered is None:
                    first_rendered = img.copy()
                if bridge_n and i >= seg["n"] - bridge_n and first_rendered is not None:
                    k_br = (i - (seg["n"] - bridge_n) + 1) / (bridge_n + 1)
                    img = apply_loop_bridge(img, first_rendered, k_br)
                elif n_loop and i >= seg["n"] - n_loop and first_frame is not None:
                    img = _whip_to(img, first_frame, (i - (seg["n"] - n_loop) + 1) / (n_loop + 1))
                if i < 3:
                    head_c.append(_gray_small(clean))
                    head_f.append(img.resize((270, 480)))
                if i >= seg["n"] - 3:
                    tail_c.append(_gray_small(clean))
                    tail_f.append(img.resize((270, 480)))
                if stills_at and fa in stills_at:
                    stills.append((stills_at[fa], fa, img.copy()))
                if enc:
                    enc.stdin.write(img.tobytes())
            prev_clean, prev_sid, prev_eng = clean, seg["sid"], cur_eng
            if src:
                src.close()
            samples.append({"sid": seg["sid"], "start_f": seg["start_f"], "transition": seg["transition"],
                            "head_clean": head_c, "head_final": head_f, "tail_clean": tail_c, "tail_final": tail_f})
    finally:
        if enc:
            enc.stdin.close()
            if enc.wait() != 0:
                raise StudioError("Lỗi khi encode video.")
    if out_video:
        replace_retry(out_video + ".part.mp4", out_video)
    return {"kinds": kinds, "samples": samples, "first_frame": first_frame, "stills": stills}


def sheet(items, path, cols=6, cell=(270, 480)):
    """Contact sheet: items = [(nhãn, PIL)]."""
    cw, ch = cell
    rows = max(1, math.ceil(len(items) / cols))
    out = Image.new("RGB", (cols * cw, rows * ch), (14, 14, 16))
    for k, it in enumerate(items):
        label, im = it[0], it[1]
        im = im.resize((cw, ch))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, cw, 30], fill=(0, 0, 0))
        d.text((6, 4), label, font=font(20, "bold"), fill=(255, 255, 255))
        out.paste(im, ((k % cols) * cw, (k // cols) * ch))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path, quality=88)
    return path


class NearestFrames:
    """Cho contact sheet: shot code mới render vài frame → lấy frame có sẵn gần nhất."""

    def __init__(self, d, n):
        self.d = d
        self.have = sorted(int(f[1:5]) for f in os.listdir(d) if f.startswith("f") and f.endswith(".jpg")) \
            if os.path.isdir(d) else []
        self.n = n

    def frame(self, j):
        if not self.have:
            return Image.new("RGB", (W, H), color("bg"))
        k = min(self.have, key=lambda x: abs(x - j))
        im = Image.open(os.path.join(self.d, f"f{k:04d}.jpg")).convert("RGB")
        return im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS)

    def close(self):
        pass


def look_stills(proj, sb, tl, layer, trims, ingested, cams, stills_at, captions=None):
    """Ảnh cho contact sheet (giữa mỗi shot + hai phía điểm cắt), có camera ảo + transition + text_fx (+ captions)
    như bản cuối. Không encode; clip chỉ đọc tới frame cần."""
    shots = {s["id"]: s for s in sb["shots"]}
    items, prev_clean = [], None
    spine_ids, prev_sid = spine_shot_ids(proj, sb), None
    for seg in tl["segments"]:
        want = sorted(f - seg["start_f"] for f in stills_at if seg["start_f"] <= f < seg["start_f"] + seg["n"])
        if not want:
            continue
        sid = seg["sid"]
        shot = shots.get(sid)
        cam = cams.get(sid) if cams else None
        draw, kind = None, "clip"
        if sid == "OUTRO":
            d = codeshot.frames_dir(proj, "OUTRO")
            if os.path.isdir(d) and os.listdir(d):
                src, kind = NearestFrames(d, seg["n"]), "outro_code"
            else:
                src, kind = None, "outro"
                draw = outro.shorts_drawer(sb, seg["n"], None)
        elif codeshot.is_3d(shot):
            src, kind = NearestFrames(codeshot.frames_dir(proj, sid), seg["n"]), "code3d"
        elif codeshot.is_board(shot):
            src, kind = NearestFrames(codeshot.board_frames_dir(proj, sid), seg["n"]), "board"
        else:
            src, kind = make_source(proj, shot, seg, trims, ingested)
        clean = None
        for i in range(max(want) + 1):
            if draw is None and kind == "clip":
                img = src.frame(i)          # clip phải đọc tuần tự
            elif i in want:
                img = draw(i) if draw else src.frame(i)
            if i not in want:
                continue
            if kind in ("clip", "image", "placeholder") and cam is not None:
                img = vcam.apply(img, *cam.frame(i))
            clean = img
            fa = seg["start_f"] + i
            if not (seg["sid"] in spine_ids and prev_sid in spine_ids and seg["transition"] not in AGENCY_TRANSITIONS):
                img = apply_transition_in(img, prev_clean, seg["transition"], i)
            if sid != "OUTRO":
                t_abs = fa / FPS
                img = layer.draw(img.copy() if img is clean else img, clean, seg, shot, fa, t_abs)
                if captions is not None:
                    img = captions.draw(img, t_abs, shot=shot)
            items.append((f"{stills_at[fa]} {fa / FPS:.1f}s", img, sid, kind))
        prev_clean, prev_sid = clean, seg["sid"]
        if src:
            src.close()
    return items
