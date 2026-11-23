"""lib/motion/verbs — ĐỘNG TỪ CHUYỂN ĐỘNG (vòng 10): bản Python, cùng API/cùng kết quả với phần verb của motion.js.

    verb(name, t, args)      → delta {x,y,z,sx,sy,sz,rot,alpha,glow,blur,reveal}
    play(items, f, N, fps)   → chạy danh sách `do: [{u|t|f, verb, dur?, args?, stagger?}]`, gộp thành một delta
    stagger(pattern, i, n)   → độ trễ (giây) của phần tử i trong n phần tử (cascade, center_out, wave…)
    compose(*deltas)         → x/y/z/rot/glow/blur cộng, sx/sy/sz/alpha/reveal nhân
    VERBS                    → từ vựng {tên: {g, dur, args}} (brief + validate đọc từ đây); VERB_DOC = mô tả tiếng Anh

t = GIÂY kể từ lúc verb bắt đầu (âm = chưa bắt đầu). Đơn vị: x/y/z theo "cỡ vật" (1 = một lần chiều cao vật), y HƯỚNG
LÊN, z hướng về camera; rot độ, dương = ngược chiều kim đồng hồ. Nhóm: in (trước t=0 ẩn) · accent (nhấn, về nguyên dạng)
· out (xong thì ẩn) · idle (nghỉ/chuyển động phụ, lặp tới khi hết args.dur). Ngẫu nhiên chỉ qua hash01(seed) → tất định.
tests/test_motion_depth.py chạy bản JS bằng node và so từng giá trị với bản này.
"""
import math

from . import back, back_in, bounce_out, clamp, ease_in, ease_out, expo_out, lerp, sine, smooth, steps

KEYS_ADD = ("x", "y", "z", "rot", "glow", "blur")
KEYS_MUL = ("sx", "sy", "sz", "alpha", "reveal")
GROUPS = ("in", "accent", "out", "idle")


def identity():
    return {"x": 0.0, "y": 0.0, "z": 0.0, "sx": 1.0, "sy": 1.0, "sz": 1.0, "rot": 0.0, "alpha": 1.0, "glow": 0.0,
            "blur": 0.0, "reveal": 1.0}


M32 = 0xFFFFFFFF


def _imul(a, b):
    return ((a & M32) * (b & M32)) & M32


def seed_of(s):
    """Hạt giống từ số hoặc chuỗi (FNV-1a trên mã UTF-16) — giống seedOf() của motion.js."""
    if isinstance(s, bool):
        s = "true" if s else "false"
    if isinstance(s, (int, float)):
        return int(s) & M32 if math.isfinite(s) else 0
    data = ("" if s is None else str(s)).encode("utf-16-le")
    h = 0x811C9DC5
    for i in range(0, len(data), 2):
        h ^= data[i] | (data[i + 1] << 8)
        h = _imul(h, 0x01000193)
    return h


def hash01(a, b=0):
    """Băm số nguyên 32-bit → [0,1) — giống hash01() của motion.js (không random)."""
    x = _imul(int(a), 0x9E3779B1) ^ _imul((int(b) + 0x7F4A7C15) & M32, 0x85EBCA77)
    x ^= x >> 15
    x = _imul(x, 0x2C1B3C6D)
    x ^= x >> 12
    x = _imul(x, 0x297A2D39)
    x ^= x >> 15
    return x / 4294967296


TAU = math.pi * 2
DIRS = {"left": (-1, 0), "right": (1, 0), "up": (0, 1), "top": (0, 1), "down": (0, -1), "bottom": (0, -1)}


def _bell(x, c, w):
    return 0.5 + 0.5 * math.cos(math.pi * (x - c) / w) if abs(x - c) < w else 0.0


def _dirv(d, default):
    if isinstance(d, (list, tuple)):
        return (float(d[0] or 0), float(d[1] or 0))
    return DIRS.get(d) or DIRS[default]


def _out_a(p, a0):
    return 1 - clamp((p - a0) / (1 - a0))


def _sd(a, k):
    return hash01(seed_of(a.get("seed")), k)


def _v(g, dur, **args):
    return {"g": g, "dur": dur, "args": args}


# Bảng từ vựng — PHẢI trùng VERBS của motion.js (test đối chiếu tên, nhóm, dur, args mặc định).
VERBS = {
    # vào (in)
    "pop": _v("in", 0.35, over=2.2),
    "drop_bounce": _v("in", 0.8, h=3),
    "slide_overshoot": _v("in", 0.5, **{"from": "left", "dist": 4}),
    "unfold": _v("in", 0.6, axis="y"),
    "draw_on": _v("in", 0.9),
    "iris": _v("in", 0.5),
    "typewriter": _v("in", 0.8, chars=12),
    "assemble": _v("in", 0.7, seed=1),
    "grow_from": _v("in", 0.6, anchor="bottom"),
    "shatter_in": _v("in", 0.55, seed=1),
    "fade_up": _v("in", 0.5, dist=0.6),
    "spin_in": _v("in", 0.6, turns=1),
    "swing_in": _v("in", 0.9, deg=80),
    "stamp_in": _v("in", 0.4),
    "zoom_in": _v("in", 0.5),
    "flip_in": _v("in", 0.5),
    "emerge": _v("in", 0.5, dist=1),
    # nhấn (accent)
    "pulse": _v("accent", 0.5, amp=0.15, count=1),
    "shake": _v("accent", 0.4, amp=0.08, freq=18),
    "squash": _v("accent", 0.45, amp=0.3),
    "wobble": _v("accent", 0.7, amp=0.12),
    "jiggle": _v("accent", 0.5, deg=12),
    "heartbeat": _v("accent", None, bpm=72, amp=0.14),
    "flip": _v("accent", 0.5),
    "flash": _v("accent", 0.25),
    "ripple": _v("accent", 0.8, amp=0.08),
    "nod": _v("accent", 0.5, amp=0.08),
    "hop": _v("accent", 0.5, h=0.6),
    "recoil": _v("accent", 0.5, dir="left", dist=0.4),
    "swell": _v("accent", 1.0, amp=0.3),
    "shrink": _v("accent", 1.0, amp=0.3),
    "spin": _v("accent", 0.8, turns=1),
    "glitch": _v("accent", 0.4, seed=1, amp=0.3),
    "stretch": _v("accent", 0.35, amp=0.35, axis="y"),
    "highlight": _v("accent", 0.6),
    # ra (out)
    "fly_off": _v("out", 0.5, dir="right", dist=5),
    "fall_away": _v("out", 0.7, dist=4, seed=1),
    "dissolve": _v("out", 0.6),
    "fold": _v("out", 0.5, axis="y"),
    "shrink_out": _v("out", 0.35),
    "burst_out": _v("out", 0.45, seed=1),
    "sink": _v("out", 0.6, dist=1.2),
    "evaporate": _v("out", 1.0, dist=1),
    "slide_out": _v("out", 0.45, dir="left", dist=4),
    "vanish": _v("out", 0.35),
    "zoom_out": _v("out", 0.5),
    # nghỉ / chuyển động phụ (idle)
    "breathe": _v("idle", None, rate=16, amp=0.03),
    "float": _v("idle", None, amp=0.08, period=2.6, seed=1),
    "sway": _v("idle", None, deg=6, period=2.4, seed=1),
    "follow_through": _v("idle", 1.0, deg=10),
    "orbit": _v("idle", None, r=0.5, period=4, seed=1),
    "drift": _v("idle", None, amp=0.1, seed=1),
    "flicker": _v("idle", None, rate=12, amp=0.3, seed=1),
    "wag": _v("idle", None, freq=2.5, deg=18),
    "shiver": _v("idle", None, amp=0.02),
    "bob": _v("idle", None, spm=120, amp=0.06),
    "spin_loop": _v("idle", None, rpm=10),
    "tick": _v("idle", None, rate=1, step=6),
}
VERB_ALIASES = {"pop_in": "pop", "drop": "drop_bounce", "fade_in": "fade_up", "fade_out": "dissolve", "draw": "draw_on",
                "type": "typewriter", "pop_out": "shrink_out", "shatter_out": "burst_out", "heart": "heartbeat",
                "bounce": "hop", "cadence": "bob", "rotate": "spin_loop", "slide_in": "slide_overshoot",
                "wipe_in": "iris", "settle": "follow_through", "fade": "dissolve"}
# Mô tả một dòng (tiếng Anh, cho brief LLM). Verb nào thiếu mô tả → test đỏ.
VERB_DOC = {
    "pop": "scale up from nothing with an overshoot",
    "drop_bounce": "falls in from `h` sizes above and bounces with squash on each landing",
    "slide_overshoot": "slides in from a side (`from` left|right|up|down), overshoots, leans into the move",
    "unfold": "opens in two folds like paper (`axis` y|x)",
    "draw_on": "line drawing reveals itself stroke by stroke",
    "iris": "circular mask opens from the centre",
    "typewriter": "text appears character by character (`chars`)",
    "assemble": "pieces fly together and lock into place",
    "grow_from": "grows out of its base (`anchor` bottom|top|center) like a plant or a bar",
    "shatter_in": "shards converge from a scattered burst",
    "fade_up": "rises a little while fading in",
    "spin_in": "spins in (`turns`) and settles",
    "swing_in": "swings in on a hinge and damps out (`deg`)",
    "stamp_in": "slams down from big like a rubber stamp, with a shake",
    "zoom_in": "punches in from far behind (depth)",
    "flip_in": "flips over like a card to face the viewer",
    "emerge": "rises out of a slot or the ground, masked",
    "pulse": "swells and relaxes `count` times (`amp`)",
    "shake": "fast left-right shake that dies out (`amp`, `freq` Hz)",
    "squash": "squash-and-stretch on impact, base stays planted",
    "wobble": "jelly wobble after a hit",
    "jiggle": "quick rotational jiggle",
    "heartbeat": "real lub-dub beat at `bpm` beats per minute (data-driven)",
    "flip": "full 360° flip around the vertical axis",
    "flash": "bright glow spike that fades",
    "ripple": "ripple of size + glow, like a drop hitting water",
    "nod": "two small nods (yes)",
    "hop": "small jump with anticipation and landing squash (`h`)",
    "recoil": "knocked back (`dir`) then returns",
    "swell": "inflates by `amp` and stays bigger (state change)",
    "shrink": "deflates by `amp` and stays smaller (state change)",
    "spin": "one full turn (`turns`)",
    "glitch": "digital jitter + dropout flicker",
    "stretch": "stretches along an axis then relaxes (anticipation)",
    "highlight": "soft glow up and back down",
    "fly_off": "winds up, then flies off-screen (`dir`, `dist`)",
    "fall_away": "drops away under gravity, tumbling",
    "dissolve": "fades out while blurring",
    "fold": "folds flat and disappears",
    "shrink_out": "winds up slightly, then shrinks to nothing",
    "burst_out": "bursts outward and vanishes",
    "sink": "sinks into the ground, masked",
    "evaporate": "rises and fades like steam",
    "slide_out": "slides off-screen (`dir`)",
    "vanish": "circular mask closes",
    "zoom_out": "recedes into the distance",
    "breathe": "breathing at `rate` breaths per minute (data-driven)",
    "float": "gentle hover up and down",
    "sway": "pendulum sway (`deg`, `period` s)",
    "follow_through": "damped overlapping wobble AFTER a move stops (tails, ears, antennae)",
    "orbit": "circles a point in depth (`r`, `period` s)",
    "drift": "slow organic drift",
    "flicker": "light/flame flicker at `rate` Hz",
    "wag": "tail-wag rotation at `freq` Hz",
    "shiver": "tiny high-frequency shiver (cold, fear, strain)",
    "bob": "walking/running bob at `spm` steps per minute (data-driven cadence)",
    "spin_loop": "continuous rotation at `rpm` (wheels, fans, planets)",
    "tick": "steps like a clock hand: `step` degrees, `rate` ticks per second",
}
STAGGERS = ("cascade", "reverse", "center_out", "edges_in", "wave", "random", "diagonal")
STAGGER_DOC = {"cascade": "one after another", "reverse": "last first", "center_out": "middle first, then outwards",
               "edges_in": "outer items first, closing in", "wave": "eased wave across the row",
               "random": "seeded random order", "diagonal": "grid sweep from a corner (`cols`)"}


def verb_name(name):
    """Tên verb chuẩn (chấp nhận gạch nối/khoảng trắng/bí danh) hoặc None."""
    n = "_".join(str(name if name is not None else "").strip().lower().replace("-", " ").split())
    return n if n in VERBS else VERB_ALIASES.get(n)


# ---- thân verb: (D, p, t, a) — p tiến độ 0..1 (verb lặp: p = 0), t giây, a = args đã gộp. Sửa D tại chỗ.
def _pop(D, p, t, a):
    k = max(0.0, back(p, a["over"]))
    D["sx"] = D["sy"] = D["sz"] = k
    D["alpha"] = clamp(p * 4)


def _drop_bounce(D, p, t, a):
    e = bounce_out(p)
    q = 0.22 * _bell(p, 0.3636, 0.06) + 0.12 * _bell(p, 0.7273, 0.05) + 0.06 * _bell(p, 0.9091, 0.04)
    D["y"] = a["h"] * (1 - e) - q * 0.5
    D["sy"] = 1 - q
    D["sx"] = D["sz"] = 1 + q * 0.8
    D["alpha"] = clamp(p * 12)


def _slide_overshoot(D, p, t, a):
    e, v = back(p, 1.6), _dirv(a["from"], "left")
    D["x"] = v[0] * a["dist"] * (1 - e)
    D["y"] = v[1] * a["dist"] * (1 - e)
    D["rot"] = v[0] * 10 * math.sin(math.pi * p) * (1 - p)
    D["alpha"] = clamp(p * 5)


def _unfold(D, p, t, a):
    k = 0.5 * smooth(p * 2) if p < 0.5 else 0.5 + 0.5 * back((p - 0.5) * 2, 1.2)
    D["sx" if a["axis"] == "x" else "sy"] = k
    D["reveal"] = clamp(p * 1.25)
    D["alpha"] = clamp(p * 4)


def _draw_on(D, p, t, a):
    D["reveal"] = smooth(p)
    D["alpha"] = clamp(p * 6)
    D["glow"] = 0.35 * math.sin(math.pi * p)


def _iris(D, p, t, a):
    e = ease_out(p)
    D["reveal"] = e
    D["sx"] = D["sy"] = 0.92 + 0.08 * e


def _typewriter(D, p, t, a):
    D["reveal"] = steps(p, max(1, _round(a["chars"])))
    D["alpha"] = 1.0 if p > 0 else 0.0


def _assemble(D, p, t, a):
    e, r = ease_out(p), _sd(a, 7) - 0.5
    D["sx"] = D["sy"] = 1 + 0.25 * (1 - e)
    D["rot"] = 50 * r * (1 - e)
    D["blur"] = (1 - e) * 0.8
    D["alpha"] = clamp(p * 2.5)
    D["reveal"] = e


def _grow_from(D, p, t, a):
    k = max(0.0, back(p, 1.4))
    D["sy"] = k
    D["sx"] = D["sz"] = lerp(0.7, 1, ease_out(p))
    D["y"] = (1 - k) * 0.5 if a["anchor"] == "top" else 0.0 if a["anchor"] == "center" else -(1 - k) * 0.5
    D["alpha"] = clamp(p * 5)


def _shatter_in(D, p, t, a):
    e = ease_out(p)
    D["x"] = (_sd(a, 1) - 0.5) * 0.8 * (1 - e)
    D["y"] = (_sd(a, 2) - 0.5) * 0.8 * (1 - e)
    D["rot"] = (_sd(a, 3) - 0.5) * 90 * (1 - e)
    D["sx"] = D["sy"] = 1 + 0.6 * (1 - e)
    D["blur"] = (1 - p) * (1 - p)
    D["alpha"] = clamp(p * 3)


def _fade_up(D, p, t, a):
    D["y"] = -a["dist"] * (1 - ease_out(p))
    D["alpha"] = smooth(p)
    D["blur"] = 0.6 * (1 - p)


def _spin_in(D, p, t, a):
    D["rot"] = 360 * a["turns"] * (1 - back(p, 1.3))
    D["sx"] = D["sy"] = ease_out(p)
    D["alpha"] = clamp(p * 4)


def _swing_in(D, p, t, a):
    D["rot"] = a["deg"] * math.exp(-5 * p) * math.cos(3 * math.pi * p) * (1 - p)
    D["alpha"] = clamp(p * 6)


def _stamp_in(D, p, t, a):
    i = 0.45
    if p < i:
        D["sx"] = D["sy"] = lerp(2.4, 1, ease_in(p / i))
    else:
        q = (p - i) / (1 - i)
        D["sx"] = D["sy"] = 1 + 0.12 * math.exp(-6 * q) * math.cos(15 * q) * (1 - q)
        D["x"] = 0.05 * math.exp(-8 * q) * math.sin(40 * q) * (1 - q)
        D["glow"] = max(0.0, 1 - q * 4) * 0.9
    D["alpha"] = clamp(p * 5)


def _zoom_in(D, p, t, a):
    e = expo_out(p)
    D["z"] = -3 * (1 - e)
    D["sx"] = D["sy"] = lerp(0.2, 1, e)
    D["blur"] = (1 - p) * 0.8
    D["alpha"] = clamp(p * 4)


def _flip_in(D, p, t, a):
    D["sx"] = math.cos((1 - ease_out(p)) * math.pi / 2)
    D["alpha"] = 1.0 if p > 0 else 0.0


def _emerge(D, p, t, a):
    e = ease_out(p)
    D["y"] = -a["dist"] * (1 - e)
    D["reveal"] = e
    D["alpha"] = clamp(p * 8)


def _pulse(D, p, t, a):
    q = (p * max(1, _round(a["count"]))) % 1
    w = math.sin(math.pi * q)
    D["sx"] = D["sy"] = D["sz"] = 1 + a["amp"] * w
    D["glow"] = 0.5 * w


def _shake(D, p, t, a):
    d = 1 - p
    D["x"] = a["amp"] * math.sin(TAU * a["freq"] * t) * d
    D["rot"] = 3 * math.sin(TAU * a["freq"] * t * 0.7 + 1) * d


def _squash(D, p, t, a):
    k = a["amp"] * math.exp(-7 * p) * math.cos(4 * math.pi * p) * (1 - p)
    D["sy"] = 1 - k
    D["sx"] = D["sz"] = 1 + k * 0.8
    D["y"] = -k * 0.5


def _wobble(D, p, t, a):
    k = a["amp"] * math.exp(-4 * p) * math.sin(6 * math.pi * p)
    D["sx"] = 1 + k
    D["sy"] = 1 - k


def _jiggle(D, p, t, a):
    D["rot"] = a["deg"] * math.exp(-5 * p) * math.sin(8 * math.pi * p)


def _heartbeat(D, p, t, a):
    per = 60 / max(1, a["bpm"])
    ph = (t % per) / per
    e = _bell(ph, 0.08, 0.08) + 0.6 * _bell(ph, 0.34, 0.08)
    D["sx"] = D["sy"] = D["sz"] = 1 + a["amp"] * e
    D["glow"] = 0.6 * e


def _flip(D, p, t, a):
    D["sx"] = math.cos(TAU * smooth(p))


def _flash(D, p, t, a):
    D["glow"] = 1 - p
    D["sx"] = D["sy"] = 1 + 0.06 * (1 - p)


def _ripple(D, p, t, a):
    D["sx"] = D["sy"] = 1 + a["amp"] * math.sin(4 * math.pi * p) * (1 - p)
    D["glow"] = 0.6 * math.sin(math.pi * p)


def _nod(D, p, t, a):
    w = math.sin(4 * math.pi * p) * (1 - p)
    D["y"] = -a["amp"] * w
    D["rot"] = 4 * w


def _hop(D, p, t, a):
    sq = 0.15 * _bell(p, 0.075, 0.075) + 0.18 * _bell(p, 0.9, 0.1)
    x = (p - 0.15) / 0.65
    D["y"] = (a["h"] * 4 * x * (1 - x) if 0.15 < p < 0.8 else 0.0) - sq * 0.5
    D["sy"] = 1 - sq
    D["sx"] = D["sz"] = 1 + sq * 0.8


def _recoil(D, p, t, a):
    k = ease_out(p / 0.2) if p < 0.2 else 1 - smooth((p - 0.2) / 0.8)
    v = _dirv(a["dir"], "left")
    D["x"] = v[0] * a["dist"] * k
    D["y"] = v[1] * a["dist"] * k
    D["rot"] = -v[0] * 8 * k


def _swell(D, p, t, a):
    D["sx"] = D["sy"] = D["sz"] = 1 + a["amp"] * smooth(p)


def _shrink(D, p, t, a):
    D["sx"] = D["sy"] = D["sz"] = 1 - a["amp"] * smooth(p)


def _spin(D, p, t, a):
    D["rot"] = 360 * a["turns"] * smooth(p)


def _glitch(D, p, t, a):
    if p >= 1:
        return
    n = math.floor(t * 24)
    D["x"] = (hash01(seed_of(a.get("seed")), n) - 0.5) * a["amp"] * (1 - p)
    D["alpha"] = 1.0 if hash01(seed_of(a.get("seed")), n + 101) > 0.2 else 0.35


def _stretch(D, p, t, a):
    w = math.sin(math.pi * p)
    if a["axis"] == "x":
        D["sx"], D["sy"] = 1 + a["amp"] * w, 1 - a["amp"] * 0.5 * w
    else:
        D["sy"], D["sx"] = 1 + a["amp"] * w, 1 - a["amp"] * 0.5 * w


def _highlight(D, p, t, a):
    w = math.sin(math.pi * p)
    D["glow"] = w
    D["sx"] = D["sy"] = 1 + 0.04 * w


def _fly_off(D, p, t, a):
    e, v = back_in(p), _dirv(a["dir"], "right")
    D["x"] = v[0] * a["dist"] * e
    D["y"] = v[1] * a["dist"] * e
    D["rot"] = -v[0] * 15 * p
    D["alpha"] = _out_a(p, 0.75)


def _fall_away(D, p, t, a):
    s = 1 if _sd(a, 3) > 0.5 else -1
    D["y"] = -a["dist"] * p * p
    D["rot"] = s * 40 * p * p
    D["alpha"] = _out_a(p, 0.6)


def _dissolve(D, p, t, a):
    D["alpha"] = 1 - smooth(p)
    D["blur"] = p
    D["sx"] = D["sy"] = 1 + 0.08 * p
    D["glow"] = 0.2 * math.sin(math.pi * p)


def _fold(D, p, t, a):
    D["sx" if a["axis"] == "x" else "sy"] = 1 - smooth(p)
    D["reveal"] = 1 - p
    D["alpha"] = _out_a(p, 0.8)


def _shrink_out(D, p, t, a):
    D["sx"] = D["sy"] = D["sz"] = max(0.0, 1 - back_in(p, 2.2))
    D["alpha"] = _out_a(p, 0.85)


def _burst_out(D, p, t, a):
    e = ease_out(p)
    D["sx"] = D["sy"] = 1 + 0.8 * e
    D["blur"] = p
    D["alpha"] = 1 - e
    D["glow"] = 0.8 * (1 - p) * clamp(p * 8)
    D["rot"] = (_sd(a, 5) - 0.5) * 40 * e


def _sink(D, p, t, a):
    e = ease_in(p)
    D["y"] = -a["dist"] * e
    D["reveal"] = 1 - e
    D["alpha"] = _out_a(p, 0.9)


def _evaporate(D, p, t, a):
    D["y"] = a["dist"] * ease_out(p)
    D["alpha"] = 1 - smooth(p)
    D["blur"] = p
    D["sx"] = 1 + 0.3 * p
    D["sy"] = 1 - 0.2 * p


def _slide_out(D, p, t, a):
    e, v = ease_in(p), _dirv(a["dir"], "left")
    D["x"] = v[0] * a["dist"] * e
    D["y"] = v[1] * a["dist"] * e
    D["alpha"] = _out_a(p, 0.8)


def _vanish(D, p, t, a):
    D["reveal"] = 1 - ease_in(p)
    D["sx"] = D["sy"] = 1 - 0.1 * p
    D["alpha"] = _out_a(p, 0.9)


def _zoom_out(D, p, t, a):
    e = ease_in(p)
    D["z"] = -3 * e
    D["sx"] = D["sy"] = lerp(1, 0.2, e)
    D["blur"] = 0.8 * p
    D["alpha"] = _out_a(p, 0.6)


def _breathe(D, p, t, a):
    w = math.sin(TAU * t / (60 / max(1, a["rate"])))
    D["sy"] = 1 + a["amp"] * w
    D["sx"] = D["sz"] = 1 + a["amp"] * 0.5 * w
    D["y"] = a["amp"] * w * 0.5


def _float(D, p, t, a):
    ph = _sd(a, 9) * TAU
    D["y"] = a["amp"] * math.sin(TAU * t / a["period"] + ph)
    D["rot"] = 2 * math.sin(TAU * t / (a["period"] * 1.3) + ph)


def _sway(D, p, t, a):
    D["rot"] = a["deg"] * math.sin(TAU * t / a["period"] + _sd(a, 9) * TAU)


def _follow_through(D, p, t, a):
    e = math.exp(-5 * p)
    D["rot"] = a["deg"] * e * math.sin(6 * math.pi * p)
    D["sx"] = 1 + 0.04 * e * math.sin(6 * math.pi * p + 1) * (1 - p)


def _orbit(D, p, t, a):
    ph = _sd(a, 9) * TAU
    w = TAU * t / a["period"] + ph
    D["x"] = a["r"] * (math.cos(w) - math.cos(ph))
    D["y"] = 0.35 * a["r"] * (math.sin(w) - math.sin(ph))
    D["z"] = a["r"] * (math.sin(w) - math.sin(ph))


def _drift(D, p, t, a):
    ph = _sd(a, 9) * TAU
    D["x"] = a["amp"] * (math.sin(0.9 * t + ph) + 0.5 * math.sin(2.3 * t + 2 * ph) - math.sin(ph)
                         - 0.5 * math.sin(2 * ph)) / 1.5
    D["y"] = a["amp"] * (math.sin(0.7 * t + 3 * ph) + 0.5 * math.sin(1.9 * t + ph) - math.sin(3 * ph)
                         - 0.5 * math.sin(ph)) / 1.5


def _flicker(D, p, t, a):
    r = hash01(seed_of(a.get("seed")), math.floor(t * a["rate"]))
    D["alpha"] = 1 - a["amp"] * 0.5 * r
    D["glow"] = a["amp"] * r


def _wag(D, p, t, a):
    D["rot"] = a["deg"] * math.sin(TAU * a["freq"] * t)


def _shiver(D, p, t, a):
    D["x"] = a["amp"] * (math.sin(TAU * 23 * t) + 0.7 * math.sin(TAU * 31 * t + 1) - 0.7 * math.sin(1))
    D["rot"] = 1.5 * math.sin(TAU * 19 * t)


def _bob(D, p, t, a):
    per = 60 / max(1, a["spm"])
    D["y"] = a["amp"] * abs(math.sin(math.pi * ((t % per) / per)))
    D["rot"] = 2 * math.sin(math.pi * t / per)


def _spin_loop(D, p, t, a):
    D["rot"] = -360 * a["rpm"] / 60 * t


def _tick(D, p, t, a):
    q = (t * a["rate"]) % 1
    D["rot"] = -a["step"] * math.floor(t * a["rate"]) - a["step"] * 0.15 * math.exp(-q * 12) * math.sin(q * 30)


VF = {k: globals()["_" + k] for k in VERBS}


def _round(x):
    return math.floor(x + 0.5)          # như Math.round của JS


def verb(name, t, args=None):
    """Một động từ ở thời điểm t (giây kể từ lúc bắt đầu). Tên lạ → không đổi gì (validate: verb_errors)."""
    D = identity()
    n = verb_name(name)
    if not n:
        return D
    meta = VERBS[n]
    a = {**meta["args"], **(args or {})}
    dur = a.get("dur") if a.get("dur") is not None else meta["dur"]
    try:
        t = float(t or 0)
    except (TypeError, ValueError):
        t = 0.0
    if a.get("sec") is not None:                      # gọi kiểu (tiến độ, {sec}) của beats.js: sec = giây thật
        try:
            t = float(a["sec"] or 0)
        except (TypeError, ValueError):
            t = 0.0
    if t < 0:
        if meta["g"] == "in":
            VF[n](D, 0.0, 0.0, a)
        return D
    if dur is None:                                   # lặp vô hạn
        VF[n](D, 0.0, t, a)
        return D
    if meta["dur"] is None and t >= dur:              # verb lặp có args.dur: hết giờ → dừng
        return D
    VF[n](D, clamp(t / dur) if dur > 0 else 1.0, t, a)
    return D


def compose(*ds):
    """Gộp nhiều delta: x/y/z/rot/glow/blur cộng, sx/sy/sz/alpha/reveal nhân."""
    o = identity()
    flat = []
    for d in ds:
        flat.extend(d if isinstance(d, (list, tuple)) else [d])
    for d in flat:
        if not d:
            continue
        for k in KEYS_ADD:
            o[k] += d.get(k, 0.0)
        for k in KEYS_MUL:
            o[k] *= d.get(k, 1.0)
    return o


def stagger(pattern, i, n, args=None):
    """Độ trễ (giây) của phần tử i trong n phần tử theo một mẫu so le. args: each (s, 0.08), seed, cols."""
    a = args or {}
    each = a.get("each") if a.get("each") is not None else 0.08
    m = (n - 1) / 2
    pat = str(pattern or "cascade").replace("-", "_")
    if pat == "reverse":
        return (n - 1 - i) * each
    if pat == "center_out":
        return abs(i - m) * each
    if pat == "edges_in":
        return (m - abs(i - m)) * each
    if pat == "wave":
        return (n - 1) * each * sine(i / max(1, n - 1))
    if pat in ("random", "seeded_random"):
        return hash01(seed_of(a.get("seed") if a.get("seed") is not None else 1), i) * (n - 1) * each
    if pat == "diagonal":
        c = a.get("cols") or math.ceil(math.sqrt(n))
        return ((i % c) + math.floor(i / c)) * each
    return i * each


def play(items, f, N, fps=30, i=0, n=1):
    """Chạy danh sách `do: [{u | t | f, verb, dur?, args?, stagger?}]` ở frame f của shot N frame → delta đã gộp."""
    ds = []
    for it in items or []:
        if not isinstance(it, dict) or not it.get("verb"):
            continue
        if it.get("t") is not None:
            t0 = float(it["t"])
        elif it.get("f") is not None:
            t0 = it["f"] / fps
        else:
            t0 = float(it.get("u") or 0) * max(0, N - 1) / fps
        if it.get("stagger"):
            t0 += stagger(it["stagger"], i, n, it.get("args") or {})
        args = {**(it.get("args") or {}), **({"dur": it["dur"]} if it.get("dur") is not None else {})}
        ds.append(verb(it["verb"], f / fps - t0, args))
    return compose(ds)


def canvas_delta(d, size):
    """Delta → canvas 2D (y xuống, rot radian theo chiều kim đồng hồ). size = chiều cao vật (px)."""
    return {"dx": d["x"] * size, "dy": -d["y"] * size, "dz": d["z"] * size, "sx": d["sx"], "sy": d["sy"],
            "rot": -d["rot"] * math.pi / 180, "alpha": clamp(d["alpha"]), "glow": max(0.0, d["glow"]),
            "blur": max(0.0, d["blur"]), "reveal": clamp(d["reveal"])}


def three_delta(d, h):
    """Delta → three.js (y lên, rot.z radian ngược chiều kim đồng hồ). h = chiều cao vật (m)."""
    return {"dx": d["x"] * h, "dy": d["y"] * h, "dz": d["z"] * h, "sx": d["sx"], "sy": d["sy"], "sz": d["sz"],
            "rotZ": d["rot"] * math.pi / 180, "alpha": clamp(d["alpha"]), "glow": max(0.0, d["glow"]),
            "blur": max(0.0, d["blur"]), "reveal": clamp(d["reveal"])}


# ---- cho brief / validate
def groups():
    """{nhóm: [verb]} theo thứ tự bảng."""
    out = {g: [] for g in GROUPS}
    for k, v in VERBS.items():
        out[v["g"]].append(k)
    return out


def verb_errors(items, where="do"):
    """Lỗi (tiếng Việt) của một danh sách `do`/keys có verb: tên lạ (gợi ý gần nhất), args lạ, stagger lạ."""
    import difflib  # noqa: PLC0415
    errs = []
    for it in items or []:
        if not isinstance(it, dict) or "verb" not in it:
            continue
        n = verb_name(it.get("verb"))
        if not n:
            near = difflib.get_close_matches(str(it.get("verb")), list(VERBS) + list(VERB_ALIASES), n=3, cutoff=0.5)
            errs.append(f"{where}: verb '{it.get('verb')}' không có" + (f" — gần: {', '.join(near)}" if near else
                                                                        f" (có: {', '.join(VERBS)})") + ".")
            continue
        extra = [k for k in (it.get("args") or {}) if k not in VERBS[n]["args"] and k not in ("dur", "each", "seed",
                                                                                           "cols", "sec")]
        if extra:
            errs.append(f"{where}: verb '{n}' không nhận args {', '.join(extra)} (nhận: "
                        f"{', '.join(VERBS[n]['args']) or '—'}, dur).")
        if it.get("stagger") and str(it["stagger"]).replace("-", "_") not in STAGGERS + ("seeded_random",):
            errs.append(f"{where}: stagger '{it['stagger']}' không có (có: {', '.join(STAGGERS)}).")
    return errs


def help_text():
    """Từ vựng verb cho brief LLM (tiếng Anh), sinh từ VERBS + VERB_DOC — không viết tay tên ở nơi khác."""
    def one(k):
        args = VERBS[k]["args"]
        a = ", ".join(f"{x}={v}" for x, v in args.items() if x != "seed")
        return f"`{k}`" + (f"({a})" if a else "")
    names = {"in": "enter", "accent": "emphasise", "out": "exit", "idle": "idle / secondary"}
    lines = [f"  - {names[g]}: " + " · ".join(one(k) for k in ks) for g, ks in groups().items()]
    return "\n".join(lines)
