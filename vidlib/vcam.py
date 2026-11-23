"""Camera ảo phủ lên clip Flow ở hậu kỳ (lib/motion) — chữa tận gốc lỗi "khựng"/đứng hình.

Mỗi frame của một shot = MỘT phép affine (scale + dịch + roll) trên frame 1080×1920:
- creep: luôn push-in 0.5–1.5%/s → không shot nào đứng yên ≥ 4 frame;
- punch-in: snappy (lib.motion.back) thay cho bước nhảy cứng;
- kick: mỗi SFX hit / payoff một cú rung "lật" 7 frame (roll ±2°, lệch dọc);
- quán tính qua điểm cắt: shot sau bắt đầu trôi theo hướng chuyển động cuối của shot trước rồi easeOut về 0
  (chỉ khi hai hướng khác nhau);
- preset payoff (câu twist): push-in + roll theo config/mix.json → payoff.
Upscale tối đa 112% (config pacing.vcam_max_scale); scale tối thiểu được tính theo roll + độ dịch để KHÔNG lộ mép.
"""
import math

import numpy as np
from PIL import Image

import lib.motion as M

from . import mix as mixlib
from .common import FPS, H, W, channel

HIT_SFX = {"hit", "boom", "impact", "thunk", "crash", "snap", "sting", "sting_low", "thud", "splash"}


def cfg():
    p = channel()["pacing"]
    return {"max_scale": p.get("vcam_max_scale", 1.12), "creep": p.get("vcam_creep_per_sec", [0.005, 0.015]),
            "base": p.get("vcam_base_scale", 1.03), "kick_roll_deg": p.get("vcam_kick_roll_deg", 2.0),
            "kick_px": p.get("vcam_kick_px", 14), "carry_frames": p.get("vcam_carry_frames", 8),
            "carry_max_px": p.get("vcam_carry_max_px", 9.0)}


def min_scale(roll_deg, dx=0.0, dy=0.0):
    """Scale nhỏ nhất để frame xoay roll° và dịch (dx, dy) px vẫn phủ kín khung W×H."""
    a = math.radians(abs(roll_deg))
    sx = (W * math.cos(a) + H * math.sin(a) + 2 * abs(dx)) / W
    sy = (W * math.sin(a) + H * math.cos(a) + 2 * abs(dy)) / H
    return max(1.0, sx, sy)


def apply(img, s, dx=0.0, dy=0.0, roll=0.0):
    """Một lần affine: phóng s quanh tâm, dịch (dx, dy) px, xoay roll độ."""
    if abs(s - 1) < 1e-4 and abs(dx) < 0.05 and abs(dy) < 0.05 and abs(roll) < 0.01:
        return img
    a = math.radians(roll)
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = W / 2, H / 2
    # điểm đích (u, v) ← nguồn: x = cx + (ca*(u-cx-dx) + sa*(v-cy-dy)) / s ; y = cy + (-sa*(u-cx-dx) + ca*(v-cy-dy)) / s
    A, B = ca / s, sa / s
    D, E = -sa / s, ca / s
    C = cx - A * (cx + dx) - B * (cy + dy)
    F = cy - D * (cx + dx) - E * (cy + dy)
    return img.transform((W, H), Image.AFFINE, (A, B, C, D, E, F), resample=Image.BICUBIC, fillcolor=(0, 0, 0))


def _dir(vel):
    vx, vy = vel
    n = math.hypot(vx, vy)
    return (vx / n, vy / n) if n > 1e-6 else None


class ShotCam:
    """Kế hoạch camera của MỘT segment. frame(i) → (scale, dx, dy, roll)."""

    def __init__(self, seg, kicks=(), carry=(0.0, 0.0), payoff=False, creep=None, idx=0):
        c = cfg()
        self.c = c
        self.seg = seg
        self.n = seg["n"]
        lo, hi = c["creep"]
        self.creep = creep if creep is not None else (lo + (hi - lo) * (0.5 + 0.5 * math.sin(idx * 1.7)))
        self.base = seg.get("zoom_base", 1.0) * c["base"]
        self.punches = seg.get("punches") or []
        self.kicks = [{"f": int(round(k * FPS)), "a": c["kick_roll_deg"] / 20.0} for k in kicks]
        self.carry = carry
        self.payoff = payoff
        pc = mixlib.cfg()["payoff"]
        self.p_push, self.p_roll, self.p_frames = pc["push_in"], pc["roll_deg"], pc["push_frames"]

    def punch_level(self, f):
        nf = max(channel()["pacing"]["punch_in_frames"], 1)
        prev, cur, t_last = 1.0, 1.0, None
        for tp, lv in self.punches:
            if f / FPS >= tp:
                prev, cur, t_last = cur, lv, tp
        if t_last is None:
            return 1.0
        k = M.back((f / FPS - t_last) * FPS / (nf + 2), 1.2)
        return prev + (cur - prev) * k

    def frame(self, i):
        if not hasattr(self, "_plan"):
            self._plan = self._solve()
        return self._plan[min(max(i, 0), len(self._plan) - 1)]

    def _solve(self):
        """Tính trước cả shot: dành đủ biên zoom cho roll/kick/quán tính (need_max), phần creep/punch/push được NÉN vào
        khoảng còn lại tới trần 112% → zoom luôn tăng, không bao giờ kẹt ở trần (kẹt = đứng hình)."""
        raw = [self._raw(i) for i in range(max(self.n, 1))]
        cap = self.c["max_scale"]
        k = 1.0
        for _ in range(12):  # roll/dịch quá lớn so với trần → giảm dần cho vừa (giữ ≥ 1% cho creep)
            need_max = max(min_scale(r * k, x * k, y * k) for _, x, y, r in raw)
            if need_max <= cap / 1.01:
                break
            k *= 0.85
        e_max = max(s for s, *_ in raw) - 1.0
        room = cap / need_max - 1.0
        q = min(1.0, room / e_max) if e_max > 0 else 1.0
        return [(need_max * (1 + (s - 1.0) * q), x * k, y * k, r * k) for s, x, y, r in raw]

    def _raw(self, i):
        c = self.c
        s = self.base * (1 + self.creep * i / FPS) * self.punch_level(i)
        dx = dy = roll = 0.0
        k = M.kick_at(i, self.kicks)
        if k:
            roll += k * 20
            dy += k / max(self.kicks[0]["a"], 1e-6) * c["kick_px"] * 0.5
        if self.carry != (0.0, 0.0) and i < c["carry_frames"]:
            # quán tính: vị trí = tích phân vận tốc giảm dần (easeOut) — trôi tiếp hướng cũ rồi dừng êm
            T = c["carry_frames"]
            prog = M.ease_out((i + 1) / T)
            dx += self.carry[0] * T * prog / 3
            dy += self.carry[1] * T * prog / 3
        elif self.carry != (0.0, 0.0):
            dx += self.carry[0] * c["carry_frames"] / 3
            dy += self.carry[1] * c["carry_frames"] / 3
        if self.payoff:
            p = M.smooth(i / max(self.p_frames, 1))
            s *= 1 + self.p_push * p
            roll += self.p_roll * p
        return s, dx, dy, roll


def plan(tl, sb, sfx_events, directions=None):
    """{sid: ShotCam}. directions = {sid: (vel_head(vx,vy), vel_tail(vx,vy))} px/frame từ motion.centroid_velocity."""
    shots = {s["id"]: s for s in sb["shots"]}
    hits = [t for t, name in sfx_events if name in HIT_SFX]
    cams, prev = {}, None
    twist_done = False
    for seg in tl["segments"]:
        if seg["sid"] == "OUTRO":
            continue
        t0 = seg["start_f"] / FPS
        kicks = [t - t0 for t in hits if t0 + 2 / FPS <= t < t0 + seg["dur"]]
        shot = shots.get(seg["sid"], {})
        payoff = shot.get("beat") == "twist" and not twist_done
        twist_done = twist_done or payoff
        carry = (0.0, 0.0)
        if directions and prev and seg["transition"] in ("cut", "match"):
            a = (directions.get(prev) or (None, None))[1]
            b = (directions.get(seg["sid"]) or (None, None))[0]
            da, db = _dir(a) if a else None, _dir(b) if b else None
            if da and (db is None or da[0] * db[0] + da[1] * db[1] < 0.5):
                mx = cfg()["carry_max_px"]
                sc = min(1.0, mx / max(math.hypot(*a), 1e-6))
                carry = (a[0] * sc, a[1] * sc)
        cams[seg["sid"]] = ShotCam(seg, kicks, carry, payoff, idx=seg["index"])
        prev = seg["sid"]
    return cams


def directions_from_clips(trims, ingested, sids):
    """Vận tốc trọng tâm vùng sáng ở 4 frame đầu/cuối của cửa sổ đã trim (px/frame ở khung 1080×1920)."""
    from . import motion  # noqa: PLC0415
    out = {}
    for sid in sids:
        vid = ingested(sid)
        tr = trims.get(sid)
        if not vid or not tr:
            continue
        try:
            fr = motion.read_gray(vid, size=(108, 192))
        except Exception:  # noqa: BLE001
            continue
        i0, i1 = int(round(tr["in"] * FPS)), min(len(fr), int(round(tr["out"] * FPS)))
        if i1 - i0 < 6:
            continue
        out[sid] = (_vel(motion, fr[i0:i0 + 4]), _vel(motion, fr[i1 - 4:i1]))
    return out


def _vel(motion, chunk):
    v = motion.centroid_velocity(np.asarray(chunk, np.float32))
    v = (float(v[0]) * W / 108, float(v[1]) * H / 192)
    return v if math.hypot(*v) > 0.8 else None  # < 0.8 px/frame: coi như đứng yên


