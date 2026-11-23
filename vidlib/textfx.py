"""Chữ trong thế giới phim (Tầng 1): kinetic typography neo vào vật, có chiều sâu, tương tác với hành động.

Mỗi shot có `text_fx` (1 cụm chữ chính 1–4 từ, + tối đa 1 chữ tượng thanh / tag):
  {"text", "tier": 1|2, "role": "main|sfx|tag", "anchor": "object:<id>|above:<id>|below:<id>|left:<id>|right:<id>|
   character_hand|world_xy", "layer": "front|behind", "behavior": [...], "t_in", "t_out", "sync": "vo_word:x | motion_peak",
   "pos": [x, y] (world_xy), "from": số bắt đầu (count_up), "style_override": "<style>"}
Tầng 2 (chữ in trên đồ vật, AI vẽ + OCR) xử lý ở tier2.py; ở đây chỉ bỏ qua các mục tier 2.
"""
import math
import re
import unicodedata

import cv2
import numpy as np
from PIL import Image, ImageDraw

import lib.motion as M

from . import lang, textstyle, track
from .common import FPS, H, W, channel, clamp, color, ease_out

BEHAVIORS = ("pop_from", "slam", "shake_on_impact", "settle", "heat_wobble", "frost", "melt", "blast_away",
             "write_on", "count_up", "follow_path")
# Easing (lib/motion — cùng thư viện với engine code-shot): pop = back · slam = anticip → back + 2 frame nén ·
# shake_on_impact = kick 7 frame · settle = spring.
SLAM_LAND = 6  # frame chữ "slam" chạm đất (trước đó là anticip → back)


def react_lead():
    """Phản ứng hình ảnh đặt sớm hơn từ khoá N frame (config vo.react_lead_default, giới hạn 0–3)."""
    lo, hi = channel()["vo"].get("react_lead_frames", [0, 3])
    return clamp(channel()["vo"].get("react_lead_default", 2), lo, hi) / FPS
INTRO_BEHAVIORS = ("pop_from", "slam", "write_on")
LAYERS = ("front", "behind")
ROLES = ("main", "sfx", "tag")
ANCHOR_RE = re.compile(r"^(?:(object|above|below|left|right):([\w-]+)|character_hand|world_xy)$")
NUM_RE = re.compile(r"(\d[\d.,]*)")


# ------------------------------------------------------------------ schema
def _norm_fx(fx):
    fx = dict(fx)
    fx.setdefault("text", "")
    fx["tier"] = int(fx.get("tier") or 1)
    fx.setdefault("role", "main")
    fx.setdefault("anchor", "world_xy")
    fx.setdefault("layer", "front")
    b = fx.get("behavior") or []
    fx["behavior"] = [b] if isinstance(b, str) else list(b)
    fx.setdefault("t_in", 0.2)
    fx.setdefault("t_out", None)
    fx.setdefault("sync", None)
    fx.setdefault("style_override", None)
    fx.setdefault("pos", None)
    return fx


def legacy_onscreen(onscreen):
    """onscreen (vòng trước) → text_fx. Caption chạy liên tục đã bị bỏ."""
    out = []
    for o in onscreen or []:
        k = o.get("kind")
        t = float(o.get("t", 0) or 0)
        if k == "caption":
            continue
        if k == "counter":
            v = o.get("value", 0)
            vs = lang.fmt_number(v)
            out.append({"text": f"{vs}{o.get('unit', '')}", "behavior": ["pop_from", "count_up"], "t_in": t,
                        "from": o.get("from", 0), "pos": o.get("pos")})
        elif k == "tag":
            out.append({"text": o.get("text", ""), "role": "tag", "behavior": ["write_on"], "t_in": t,
                        "pos": [0.3, 0.14]})
        elif k == "compare":
            out.append({"text": o.get("text", ""), "behavior": ["slam", "shake_on_impact"], "t_in": t,
                        "pos": o.get("pos")})
        else:  # label / arrow / circle
            out.append({"text": o.get("text", ""), "behavior": ["pop_from"], "t_in": t, "pos": o.get("pos") or o.get("to")})
    return out


def shot_fx(shot):
    raw = shot.get("text_fx")
    if raw is None:
        raw = legacy_onscreen(shot.get("onscreen"))
    return [_norm_fx(f) for f in raw if (f or {}).get("text")]


def validate_fx(shot, objects):
    errs = []
    tag = shot.get("id", "?")
    for f in shot_fx(shot):
        if f["tier"] not in (1, 2):
            errs.append(f"{tag}: text_fx '{f['text']}' tier {f['tier']} không hợp lệ (1|2).")
        if f["layer"] not in LAYERS:
            errs.append(f"{tag}: text_fx '{f['text']}' layer '{f['layer']}' không hợp lệ (front|behind).")
        if f["role"] not in ROLES:
            errs.append(f"{tag}: text_fx '{f['text']}' role '{f['role']}' không hợp lệ (main|sfx|tag).")
        for b in f["behavior"]:
            if b not in BEHAVIORS:
                errs.append(f"{tag}: behavior '{b}' không có. Có: {', '.join(BEHAVIORS)}.")
        m = ANCHOR_RE.match(f["anchor"]) if f["tier"] == 1 else None
        if f["tier"] == 1 and not m:
            errs.append(f"{tag}: anchor '{f['anchor']}' không hợp lệ (object:<id>|above:<id>|character_hand|world_xy).")
        if m and m.group(2) and m.group(2) not in objects:
            errs.append(f"{tag}: anchor tham chiếu vật '{m.group(2)}' chưa khai báo trong 'objects'.")
        if f["anchor"] == "character_hand" and "character" not in objects:
            errs.append(f"{tag}: anchor character_hand cần vật 'character' trong 'objects'.")
        if f["tier"] == 2 and not (f.get("plane") or f.get("object")):
            errs.append(f"{tag}: chữ Tầng 2 '{f['text']}' cần 'object' (vật mang chữ) hoặc 'plane' (4 góc).")
        if f["tier"] == 2 and f.get("object") and f["object"] not in objects:
            errs.append(f"{tag}: chữ Tầng 2 tham chiếu vật '{f['object']}' chưa khai báo trong 'objects'.")
    return errs


def shot_objects(sb, shot):
    return {**(sb.get("objects") or {}), **(shot.get("objects") or {})}


# ------------------------------------------------------------------ thời gian
def _fold(s):
    s = unicodedata.normalize("NFD", (s or "").lower()).replace("đ", "d")
    return "".join(c for c in s if unicodedata.category(c) != "Mn" and (c.isalnum() or c in "°%"))


def motion_profile(analysis, trim, dur):
    """[(t_shot, energy)] trên cửa sổ đã trim, đổi sang thời gian output của shot."""
    if not analysis or not trim:
        return []
    e = analysis.get("energy") or []
    f0, f1 = int(round(trim["in"] * FPS)), int(round(trim["out"] * FPS))
    f1 = min(f1, len(e))
    if f1 - f0 < 2:
        return []
    return [((k - f0) / (f1 - f0) * dur, float(e[k])) for k in range(f0, f1)]


def impacts(profile, after=0.0):
    """Đỉnh chuyển động nổi bật (va chạm) theo thời gian shot."""
    if len(profile) < 5:
        return []
    v = np.array([p[1] for p in profile])
    med = float(np.median(v)) + 1e-6
    out = []
    for k in range(2, len(v) - 2):
        if v[k] >= v[k - 2:k + 3].max() and v[k] > 1.8 * med and profile[k][0] >= after:
            if not out or profile[k][0] - out[-1] > 0.25:
                out.append(profile[k][0])
    return out


def resolve_sync(spec, shot_idx, seg, vo, profile):
    """'vo_word:nghìn | motion_peak' → thời điểm (giây trong shot) hoặc None."""
    if not spec:
        return None, None
    t0 = seg["start_f"] / FPS
    for part in [p.strip() for p in str(spec).split("|") if p.strip()]:
        if part.startswith("vo_word:") and vo:
            want = _fold(part.split(":", 1)[1])
            lines = [ln for ln in vo["lines"] if shot_idx in ln["shots"]] or \
                [ln for ln in vo["lines"] if ln["shots"][0] <= shot_idx]
            for ln in lines[-1:] + lines[:-1]:
                for w in ln["words"]:
                    if want and want in _fold(w["w"]) and t0 - 0.05 <= w["start"] < t0 + seg["dur"]:
                        # phản ứng hình ảnh đặt 0–3 frame TRƯỚC từ khoá (quy tắc timing theo giọng)
                        return max(0.0, w["start"] - t0 - react_lead()), part
        elif part in ("motion_peak", "impact") and profile:
            if part == "motion_peak":
                k = int(np.argmax([p[1] for p in profile]))
                return profile[k][0], part
            imp = impacts(profile, 0.1)
            if imp:
                return imp[0], part
        elif part.startswith("t:"):
            return float(part[2:]), part
    return None, None


# ------------------------------------------------------------------ sự kiện
class Event:
    def __init__(self, idx, fx, shot, seg, style, t_in, t_out, sync_used, impacts_abs, stage):
        self.idx = idx
        self.fx = fx
        self.shot = shot
        self.sid = shot["id"]
        self.seg = seg
        self.style = fx.get("style_override") or style
        self.st = textstyle.load_style(self.style)
        self.t_in, self.t_out = t_in, t_out
        self.sync_used = sync_used
        self.impacts = impacts_abs
        self.stage = stage
        self.b = set(fx["behavior"])
        self.role = fx["role"]
        self.layer = fx["layer"]
        maxw = (stage["w"] * W if stage else W * 0.78) if self.role != "tag" else W * 0.62
        size = fx.get("size") or (self.st["size"] * (0.5 if self.role == "tag" else 1.0))
        self.size = textstyle.fit_size(self._display(1.0), self.style, maxw, self.role, size)
        self.offset = None
        self.rel = False
        self.last_c = None
        self.blast_at = None
        if "blast_away" in self.b:
            later = [t for t in impacts_abs if t > t_in + 0.4]
            self.blast_at = fx.get("blast_at_abs") or (later[0] if later else t_out - 0.45)
        self.t_end = (self.blast_at + 0.6) if self.blast_at else t_out
        self.qa = {"overlap": [], "occluded": [], "frames": [], "crops": [], "bboxes": []}
        self.qa_times = self._qa_times()

    # -- nội dung chữ
    def _display(self, k):
        txt = self.fx["text"]
        if "count_up" not in self.b:
            return txt
        m = NUM_RE.search(txt)
        if not m:
            return txt
        raw = m.group(1).rstrip(".,")
        target = lang.parse_number(raw)
        start = float(self.fx.get("from") or 0)
        v = start + (target - start) * k
        s = lang.fmt_number(round(v), 0) if float(target).is_integer() else lang.fmt_number(v, 1)
        return txt[:m.start()] + s + txt[m.start() + len(raw):]

    def text_at(self, tau):
        return self._display(ease_out(clamp(tau / 0.75)))

    def _qa_times(self):
        D = self.t_out - self.t_in
        settle = min(self.t_in + max(0.35, D * 0.4), self.t_out - 0.05)
        mid = self.t_in + D * 0.6
        end = (self.blast_at + 0.2) if self.blast_at else self.t_out - 2.0 / FPS
        # OCR: 5 mẫu SAU khi chữ đã vào khung (intro + count_up xong ~0.8s) và trước khi nổ văng; đạt nếu 1 mẫu khớp
        lo = self.t_in + min(0.8, D * 0.45)
        hi = (self.blast_at - 0.06) if self.blast_at else self.t_out - 2.0 / FPS
        hi = max(hi, lo)
        ocr = [lo + (hi - lo) * k / 4 for k in range(5)]
        return {"frames": [settle, mid, end], "ocr": ocr}

    # -- neo
    def anchor_kind(self):
        m = ANCHOR_RE.match(self.fx["anchor"])
        return (m.group(1), m.group(2)) if m and m.group(1) else (self.fx["anchor"], None)

    def anchor_point(self, trackers, lag=0):
        kind, oid = self.anchor_kind()
        if kind == "world_xy":
            return None
        if kind == "character_hand":
            tr = trackers.get("character")
            if tr is None or tr.center is None:
                return None
            target = self.stage_center() or (W * 0.8, H * 0.25)
            return tr.extreme_toward(target)
        tr = trackers.get(oid)
        if tr is None or tr.center is None:
            return None
        if lag and len(tr.history) > lag:
            return tr.history[-1 - lag]
        b = tr.box_full()
        cx, cy = tr.center_full()
        if kind == "above":
            return cx, b[1]
        if kind == "below":
            return cx, b[1] + b[3]
        if kind == "left":
            return b[0], cy
        if kind == "right":
            return b[0] + b[2], cy
        return cx, cy

    def stage_center(self):
        if self.fx.get("pos"):
            return self.fx["pos"][0] * W, self.fx["pos"][1] * H
        if self.stage:
            return self.stage["x"] * W, self.stage["y"] * H
        return None

    def place(self, A, art, trackers, subj, fgs):
        """Chọn vị trí lần đầu: ưu tiên text_stage; với lớp front, tránh đè chủ thể và tiền cảnh."""
        bw, bh = art.box[2] - art.box[0], art.box[3] - art.box[1]
        kind, oid = self.anchor_kind()
        T = self.stage_center()
        if T is None:
            if self.role == "tag":
                T = (0.3 * W, 0.14 * H)
            elif A is None:
                T = (0.5 * W, 0.22 * H)
            else:
                tr = trackers.get(oid) if oid else trackers.get("character")
                b = tr.box_full() if tr else None
                if kind == "below" and b:
                    T = (A[0], A[1] + bh / 2 + 30)
                elif kind in ("left", "right") and b:
                    T = (A[0] + (-1 if kind == "left" else 1) * (bw / 2 + 30), A[1])
                else:
                    T = (A[0], (b[1] if b else A[1]) - bh / 2 - 34)
        best, cost_best = T, None
        if self.layer == "front" and self.role != "tag":
            for dy in range(-520, 521, 40):
                for dx in range(-360, 361, 40):
                    c = (T[0] + dx, T[1] + dy)
                    c2 = _clamp_safe(c, bw, bh)
                    ov_s = _rect_overlap(subj, c2, bw, bh)
                    ov_f = _rect_overlap(fgs, c2, bw, bh)
                    # đè chủ thể ≫ đè vật sáng khác (biển chữ, đạo cụ) ≫ đi xa vị trí mong muốn
                    cost = 1e4 * ov_s + 4e3 * ov_f + math.hypot(dx, dy) + 3 * math.hypot(c2[0] - c[0], c2[1] - c[1])
                    if cost_best is None or cost < cost_best:
                        best, cost_best = c2, cost
        else:
            best = _clamp_safe(T, bw, bh)
        self.rel = A is not None and kind != "world_xy"
        self.offset = (best[0] - A[0], best[1] - A[1]) if self.rel else best

    # -- dựng sprite của frame
    def parts(self, t, trackers, subj, fgs, frame_no):
        tau = t - self.t_in
        D = self.t_out - self.t_in
        f = tau * FPS
        art = textstyle.render(self.text_at(tau), self.style, self.size, self.role)
        lag = 5 if "follow_path" in self.b else 0
        A = self.anchor_point(trackers, lag)
        if self.offset is None:
            self.place(A, art, trackers, subj, fgs)
        if self.rel and A is not None:      # neo vào vật: đi theo vật
            C = (A[0] + self.offset[0], A[1] + self.offset[1])
        elif self.rel:                       # mất dấu vật: giữ vị trí lần cuối
            C = self.last_c or self.offset
        else:                                # world_xy / chưa bắt được vật lúc đặt: vị trí cố định
            C = self.offset
        self.last_c = C
        bw, bh = art.box[2] - art.box[0], art.box[3] - art.box[1]
        C = _clamp_safe(C, bw, bh)
        img = art.img
        intro = self._intro_kind()
        img = self._apply_intro(img, art, intro, f)
        sx = sy = 1.0
        rot = 0.0
        dx = dy = 0.0
        alpha = 1.0
        # pop_from: bay ra từ điểm neo, scale theo back (vượt rồi về)
        if "pop_from" in self.b and f < 10:
            k = M.back(f / 8)
            src = A or (C[0], C[1] + 60)
            C = (src[0] + (C[0] - src[0]) * min(1.0, k), src[1] + (C[1] - src[1]) * min(1.0, k))
            sx = sy = max(0.2, 0.25 + 0.75 * k)
        if "slam" in self.b:  # lấy đà (anticip) → rơi đập (back) → 2 frame nén → settle bằng spring
            if f < SLAM_LAND:
                dy = -240 * (1 - M.anticip(f / SLAM_LAND))
                sy, sx = 1.08, 0.94
            elif f < SLAM_LAND + 2:
                sy, sx = 0.72, 1.24
            else:
                k = M.spring((f - SLAM_LAND - 2) / FPS, 3.2, 7.0)
                sy, sx = 0.72 + 0.28 * k, 1.24 - 0.24 * k
        if intro == "pop" and not self.b & set(INTRO_BEHAVIORS):
            s = 0.6 + 0.4 * M.back(f / 7)
            sx *= s
            sy *= s
        if self.role == "sfx" and not self.b & {"slam", "pop_from"}:
            s = 0.3 + 0.7 * M.back(f / 7, 2.4)
            sx *= s
            sy *= s
        if "settle" in self.b:  # lắc tắt dần sau khi vào khung
            w = 1 - M.spring(f / FPS, 2.6, 4.5)
            rot += 6 * w
            sx *= 1 + 0.05 * w
            sy *= 1 - 0.05 * w
        # rung theo va chạm: kick 7 frame (lib.motion.kick_at — cùng kiểu rung với camera ảo)
        hits = list(self.impacts) + ([self.t_in + SLAM_LAND / FPS] if "slam" in self.b else [])
        if "shake_on_impact" in self.b or "slam" in self.b:
            s = M.kick_at(t * FPS, [{"f": th * FPS, "a": 0.2} for th in hits])
            dx += s * 90
            dy += s * 55
            rot += s * 20
        # biến dạng
        if "heat_wobble" in self.b:
            img = _heat(img, tau, self.st)
        if "frost" in self.b:
            img = _frost(img, art, tau, self.st, textstyle.seed(self.sid, self.idx))
            dx += 1.5 * math.sin(tau * 55)
        if "melt" in self.b:
            img = _melt(img, art, tau, D, textstyle.seed(self.sid, self.idx))
        bp = float((self.st.get("boil") or {}).get("px", 0))
        every = int((self.st.get("boil") or {}).get("every", 2))
        if bp > 0:
            img = textstyle.boil(img, textstyle.seed(self.sid, self.idx, frame_no // max(every, 1)), bp)
        if "follow_path" in self.b and A is not None:
            tr = trackers.get(self.anchor_kind()[1])
            if tr and len(tr.history) > 3:
                (x1, y1), (x2, y2) = tr.history[-4], tr.history[-1]
                rot += clamp(math.degrees(math.atan2(y2 - y1, x2 - x1 + 1e-6)) * 0.15, -10, 10) if abs(x2 - x1) + abs(
                    y2 - y1) > 3 else 0.0
        # văng khi nổ
        if self.blast_at and t >= self.blast_at:
            return self._blast_parts(art, C, t - self.blast_at), None
        out = img
        if abs(sx - 1) > 1e-3 or abs(sy - 1) > 1e-3:
            out = out.resize((max(1, int(out.width * sx)), max(1, int(out.height * sy))), Image.BICUBIC)
        if abs(rot) > 0.05:
            out = out.rotate(rot, resample=Image.BICUBIC, expand=True)
        if alpha < 0.999:
            out.putalpha(out.getchannel("A").point(lambda v: int(v * alpha)))
        bcx = (art.box[0] + art.box[2]) / 2 * sx + (out.width - img.width * sx) / 2
        bcy = (art.box[1] + art.box[3]) / 2 * sy + (out.height - img.height * sy) / 2
        x = int(C[0] + dx - bcx)
        y = int(C[1] + dy - bcy)
        bbox = (int(C[0] + dx - bw * sx / 2), int(C[1] + dy - bh * sy / 2), int(C[0] + dx + bw * sx / 2),
                int(C[1] + dy + bh * sy / 2))
        leader = None
        if self.st.get("leader_line") and A is not None and self.anchor_kind()[0] != "world_xy":
            leader = (bbox, A, self.st["leader_line"], clamp(f / 8))
        return [(out, x, y)], (bbox, leader)

    def _intro_kind(self):
        if "write_on" in self.b:
            return "write_on"
        if self.b & {"pop_from", "slam"}:
            return "none"
        return self.st.get("intro", "pop")

    def _apply_intro(self, img, art, kind, f):
        n = int(self.st.get("intro_frames", 8))
        if kind in ("pop", "none") or f >= n * 1.6 + 2:
            return img
        if kind == "flicker":
            pattern = [0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1]
            on = pattern[int(f)] if int(f) < len(pattern) else 1
            if not on:
                return Image.new("RGBA", img.size, (0, 0, 0, 0))
            return img
        letters = art.letters
        if not letters:
            return img
        arr = np.asarray(img).copy()
        h, w = arr.shape[:2]
        mask = np.zeros((h, w), np.float32)
        if kind in ("write_on", "type", "brush"):
            span = n * (1.6 if kind == "write_on" else 1.0)
            prog = clamp(f / max(span, 1))
            if kind == "brush":
                x0, x1 = art.box[0] - 30, art.box[2] + 30
                rows = np.random.default_rng(textstyle.seed(self.sid, self.idx)).normal(0, 18, (h, 1))
                rows = cv2.GaussianBlur(rows.astype(np.float32), (0, 0), 3)
                fr = x0 + (x1 - x0) * prog + rows
                mask = (np.arange(w)[None, :] < fr).astype(np.float32)
            else:
                k_float = prog * len(letters)
                for k, (im, lx, _ly) in enumerate(letters):
                    lx0, lx1 = lx + 10, lx + im.width - 10
                    if kind == "type":
                        if k < int(k_float) + (1 if prog >= 1 else 0):
                            mask[:, max(0, lx0 - 6):max(0, lx1 + 6)] = 1
                    else:  # viết dần từng chữ: quét chéo trong ô chữ
                        p = clamp(k_float - k)
                        if p <= 0:
                            continue
                        yy, xx = np.mgrid[0:h, max(0, lx0):max(0, lx1)]
                        diag = (xx - lx0) / max(lx1 - lx0, 1) * 0.7 + (yy / h) * 0.3
                        mask[:, max(0, lx0):max(0, lx1)] = np.maximum(mask[:, max(0, lx0):max(0, lx1)],
                                                                         (diag <= p * 1.05).astype(np.float32))
                if prog >= 1:
                    mask[:] = 1
            # glow/bóng ngoài phạm vi chữ: hiện theo tiến độ
            mask = cv2.GaussianBlur(mask, (0, 0), 2.0)
            arr[..., 3] = (arr[..., 3] * np.clip(mask, 0, 1)).astype(np.uint8)
            out = Image.fromarray(arr, "RGBA")
            if kind == "type" and prog < 1 and int(f) % 8 < 5:  # con trỏ gõ phím
                k = min(len(letters) - 1, int(k_float))
                im, lx, ly = letters[k]
                d = ImageDraw.Draw(out)
                cx = lx + im.width - 6
                d.rectangle([cx, art.box[1], cx + max(6, self.size // 14), art.box[3]], fill=(*art.fill, 255))
            return out
        if kind == "drop_letters":
            base = Image.new("RGBA", img.size, (0, 0, 0, 0))
            for k, (im, lx, ly) in enumerate(letters):
                ff = f - 2 * k
                if ff < 0:
                    continue
                dy = _bounce(ff)
                base.alpha_composite(im, (max(0, lx), int(ly + dy)))
            return textstyle.decorate(base, art)
        return img

    def _blast_parts(self, art, C, dt):
        parts = []
        cx = (art.box[0] + art.box[2]) / 2
        cy = (art.box[1] + art.box[3]) / 2
        a = clamp(1 - dt / 0.55)
        if a <= 0:
            return parts
        for k, (im, lx, ly) in enumerate(art.letters):
            r = np.random.default_rng(textstyle.seed(self.sid, self.idx, k))
            lcx = lx + im.width / 2
            vx = (lcx - cx) * 3.2 + r.uniform(-260, 260)
            vy = -r.uniform(420, 820)
            px = C[0] + (lcx - cx) + vx * dt
            py = C[1] + (ly + im.height / 2 - cy) + vy * dt + 1300 * dt * dt
            rot = r.uniform(-720, 720) * dt
            sp = im.rotate(rot, resample=Image.BICUBIC, expand=True)
            if a < 0.999:
                sp.putalpha(sp.getchannel("A").point(lambda v, a=a: int(v * a)))
            parts.append((sp, int(px - sp.width / 2), int(py - sp.height / 2)))
        return parts


# ------------------------------------------------------------------ biến dạng / trang trí
def _heat(img, tau, st):
    out = textstyle.remap(img, lambda xx, yy: 5.0 * np.sin(2 * np.pi * (yy / 58.0 - tau * 1.7)),
                          lambda xx, yy: 2.5 * np.sin(2 * np.pi * (xx / 95.0 + tau * 1.1)))
    glow = Image.new("RGBA", out.size, (*color(st.get("heat_color", "#FF2D2D")), 0))
    a = out.getchannel("A")
    pulse = 0.55 + 0.25 * math.sin(tau * 9)
    from PIL import ImageFilter
    glow.putalpha(a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * pulse)))
    base = Image.new("RGBA", out.size, (0, 0, 0, 0))
    base.alpha_composite(glow)
    base.alpha_composite(out)
    return base


def _frost(img, art, tau, st, seed):
    arr = np.asarray(img)
    a = arr[..., 3]
    rim = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    rim = cv2.GaussianBlur(rim, (0, 0), 2)
    layer = np.zeros_like(arr)
    layer[..., :3] = color(st.get("frost_color", "#9FC0FF"))
    layer[..., 3] = (rim * 0.85).astype(np.uint8)
    base = Image.fromarray(layer, "RGBA")
    base.alpha_composite(img)
    d = ImageDraw.Draw(base)
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = art.box
    n = int(clamp(tau / 0.6) * 7)
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        pts = [(x, y)]
        for _ in range(4):
            x += rng.uniform(-28, 28)
            y += rng.uniform(-22, 22)
            pts.append((x, y))
        d.line(pts, fill=(255, 255, 255, 220), width=3)
    # chỉ giữ vết nứt trong phạm vi chữ
    out = np.asarray(base).copy()
    keep = cv2.dilate(a, np.ones((5, 5), np.uint8)) | (rim > 30).astype(np.uint8) * 255
    out[..., 3] = np.minimum(out[..., 3], np.maximum(keep, rim))
    return Image.fromarray(out, "RGBA")


def _melt(img, art, tau, D, seed):
    start = 0.3 * D
    if tau < start:
        return img
    m = clamp((tau - start) / max(D - start, 0.1)) ** 1.4
    pad = 170
    big = Image.new("RGBA", (img.width, img.height + pad), (0, 0, 0, 0))
    big.alpha_composite(img)
    rng = np.random.default_rng(seed)
    w = img.width
    col = cv2.resize(rng.random((1, 9)).astype(np.float32), (w, 1), interpolation=cv2.INTER_CUBIC)[0]
    drip = m * (30 + 150 * col ** 2)
    top, bot = art.box[1], art.box[3]

    def fy(xx, yy):
        rel = np.clip((yy - top) / max(bot - top, 1), 0, 1.6)
        return -drip[np.clip(xx.astype(int), 0, w - 1)] * rel ** 1.5

    out = textstyle.remap(big, lambda xx, yy: np.zeros_like(xx), fy)
    return out


def _bounce(f):
    """Rơi từ trên xuống rồi nảy (đơn vị pixel, f = frame)."""
    if f < 6:
        return -260 * (1 - f / 6) ** 2
    t = (f - 6) / 30
    return -60 * abs(math.sin(t * math.pi * 3)) * math.exp(-t * 4)


# ------------------------------------------------------------------ hình học
def _clamp_safe(c, bw, bh):
    sz = channel()["safe_zone"]
    x, y = c
    right = sz["right_icons_x"] if y + bh / 2 > sz["right_icons_from_y"] else W - sz["left"]
    x = clamp(x, sz["left"] + bw / 2, right - bw / 2) if bw < right - sz["left"] else W / 2
    y = clamp(y, sz["top"] + bh / 2, H - sz["bottom"] - bh / 2)
    return x, y


def _rect_overlap(mask_small, c, bw, bh):
    if mask_small is None:
        return 0.0
    x0, y0 = int((c[0] - bw / 2) / track.SX), int((c[1] - bh / 2) / track.SY)
    x1, y1 = int((c[0] + bw / 2) / track.SX) + 1, int((c[1] + bh / 2) / track.SY) + 1
    x0, y0 = max(0, x0), max(0, y0)
    sub = mask_small[y0:y1, x0:x1]
    return float(sub.mean()) if sub.size else 0.0


# ------------------------------------------------------------------ lớp chữ cho render
def build_events(sb, tl, vo, analyses, trims, style):
    segs = {s["sid"]: s for s in tl["segments"]}
    ev = []
    for idx, shot in enumerate(sb["shots"]):
        seg = segs.get(shot["id"])
        if not seg:
            continue
        prof = motion_profile((analyses or {}).get(shot["id"]), (trims or {}).get(shot["id"]), seg["dur"])
        t0 = seg["start_f"] / FPS
        imps = [t0 + t for t in impacts(prof, 0.1)]
        for fx in shot_fx(shot):
            if fx["tier"] != 1:
                continue
            ts, used = resolve_sync(fx.get("sync"), idx, seg, vo, prof)
            t_in = ts if ts is not None else float(fx["t_in"]) * seg["scale"]
            t_in = clamp(t_in, 0.0, max(0.0, seg["dur"] - 0.5))
            t_out = float(fx["t_out"]) * seg["scale"] if fx.get("t_out") else seg["dur"]
            t_out = clamp(t_out, t_in + 0.5, seg["dur"])
            ev.append(Event(len(ev), fx, shot, seg, style, t0 + t_in, t0 + t_out, used, imps, shot.get("text_stage")))
    return ev


def sfx_events(events):
    out = []
    for e in events:
        if "slam" in e.b:
            out.append((e.t_in + SLAM_LAND / FPS, "hit"))
        elif e.role == "sfx":
            out.append((e.t_in, "hit"))
        elif "pop_from" in e.b or e.st.get("intro") == "pop":
            out.append((e.t_in, "pop"))
        if "count_up" in e.b:
            out.append((e.t_in + 0.1, "tick"))
        if e.blast_at:
            out.append((e.blast_at, "whoosh"))
    return out


def timing_report(events):
    return [{"kind": e.role, "text": e.fx["text"], "start": round(e.t_in, 3), "end": round(e.t_end, 3), "shot": e.sid,
             "anchor": e.fx["anchor"], "layer": e.layer, "behavior": sorted(e.b), "sync": e.sync_used} for e in events]


class Layer:
    """Vẽ chữ Tầng 1 vào từng frame (gọi trong vòng render)."""

    def __init__(self, sb, events):
        self.sb = sb
        self.by_shot = {}
        for e in events:
            self.by_shot.setdefault(e.sid, []).append(e)
        self.events = events
        self.cur = None
        self.trackers = {}

    def begin(self, seg, shot):
        self.cur = seg["sid"]
        objs = shot_objects(self.sb, shot) if shot else {}
        self.trackers = {oid: track.ObjectTracker(oid, sel) for oid, sel in objs.items()}

    def draw(self, img, clean, seg, shot, frame_no, t):
        if seg["sid"] != self.cur:
            self.begin(seg, shot)
        evs = self.by_shot.get(seg["sid"])
        if not evs:
            return img
        rgb_s = track.small(clean)
        gray_s = cv2.cvtColor(rgb_s, cv2.COLOR_RGB2GRAY)
        for tr in self.trackers.values():
            tr.update(rgb_s, gray_s)
        active = [e for e in evs if e.t_in - 1e-6 <= t < e.t_end]
        if not active:
            return img
        subj = None
        masks = [tr.mask for tr in self.trackers.values() if tr.mask is not None]
        if masks:
            subj = cv2.dilate(np.maximum.reduce(masks), np.ones((3, 3), np.uint8)).astype(np.float32)
        fgs = (track.color_mask(rgb_s, "bright")).astype(np.float32)
        fg_full = None
        drawn = []
        for layer_name in ("behind", "front"):
            for e in [e for e in active if e.layer == layer_name]:
                parts, extra = e.parts(t, self.trackers, subj, fgs, frame_no)
                if layer_name == "behind" and parts:
                    if fg_full is None:
                        fg_full = track.fg_soft(clean)
                    for sp, x, y in parts:
                        _paste_occluded(img, sp, x, y, fg_full)
                else:
                    for sp, x, y in parts:
                        img.paste(sp, (x, y), sp)
                if extra and extra[1]:
                    _leader(img, *extra[1])
                drawn.append((e, parts, extra[0] if extra else None))
        # QA: tỉ lệ đè chủ thể / bị che
        for e, parts, bbox in drawn:
            if not parts:
                continue
            tm = _text_mask_small(parts)
            n = tm.sum()
            if n < 3:
                continue
            if e.layer == "front":
                e.qa["overlap"].append(float((tm * (subj if subj is not None else 0)).sum() / n))
            else:
                e.qa["occluded"].append(float((tm * fgs).sum() / n))
            for tq in e.qa_times["frames"]:
                if abs(t - tq) < 0.5 / FPS and len(e.qa["frames"]) < 3:
                    e.qa["frames"].append((t, img.resize((360, 640)), bbox))
            for tq in e.qa_times["ocr"]:
                if abs(t - tq) < 0.5 / FPS and bbox:
                    x0, y0, x1, y1 = bbox
                    pad = 26
                    crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)))
                    e.qa["crops"].append((t, crop))
        return img


def _paste_occluded(img, sp, x, y, fg):
    """Dán chữ ở lớp SAU: chỉ hiện ở chỗ nền đen, vật đi qua sẽ che chữ."""
    w, h = sp.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = sp.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    a = np.asarray(sub.getchannel("A"), np.float32) / 255.0
    a *= 1.0 - fg[y0:y1, x0:x1]
    mask = Image.fromarray((a * 255).astype(np.uint8), "L")
    img.paste(sub.convert("RGB"), (x0, y0), mask)


def _leader(img, bbox, A, spec, k):
    """Đường dẫn chú thích (blueprint) từ chữ tới vật."""
    if k <= 0:
        return
    x0, y0, x1, y1 = bbox
    cx = clamp(A[0], x0, x1)
    sy = y1 + 8 if A[1] > y1 else y0 - 8
    ex, ey = cx + (A[0] - cx) * k, sy + (A[1] - sy) * k
    d = ImageDraw.Draw(img)
    col = color(spec.get("color", "#A9C4FF"))
    d.line([(cx, sy), (ex, ey)], fill=col, width=int(spec.get("width", 4)))
    if k >= 1:
        r = int(spec.get("node", 8))
        d.ellipse([A[0] - r, A[1] - r, A[0] + r, A[1] + r], outline=col, width=3)


def _text_mask_small(parts):
    m = np.zeros((track.SH, track.SW), np.float32)
    for sp, x, y in parts:
        a = np.asarray(sp.getchannel("A"), np.float32) / 255.0
        sw, sh = max(1, int(sp.width / track.SX)), max(1, int(sp.height / track.SY))
        a = cv2.resize(a, (sw, sh), interpolation=cv2.INTER_AREA)
        xs, ys = int(x / track.SX), int(y / track.SY)
        x0, y0 = max(0, xs), max(0, ys)
        x1, y1 = min(track.SW, xs + sw), min(track.SH, ys + sh)
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = np.maximum(m[y0:y1, x0:x1], a[y0 - ys:y1 - ys, x0 - xs:x1 - xs])
    return (m > 0.5).astype(np.float32)
