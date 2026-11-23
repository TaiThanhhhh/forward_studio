"""lib/motion — thư viện chuyển động dùng chung (bản Python cho hậu kỳ: text_fx, camera ảo, outro, thumbnail).

Cùng API với lib/motion/motion.js (engine code-shot) — port từ cartoon-short-kit/engine/motion.js.
tests/test_motion_lib.py chạy bản JS bằng node và so từng giá trị với bản này.

    smooth   smootherstep, cho các cú lướt camera 18–45 frame
    ease_out nhanh rồi đáp nhẹ (reveal, whip, giữ quán tính qua điểm cắt)
    back     vượt quá rồi về (pop)
    anticip  lấy đà ngược rồi back (slam)
    spring   lắc tắt dần (settle) — t tính bằng GIÂY
    spline   Catmull-Rom 3D
    cam_from_keys  camera từ keyframe + creep (không bao giờ đứng hình) + kicks (rung 7 frame)
    idle / blink_at / walk / q
    verb / play / stagger / compose / VERBS — động từ chuyển động (vòng 10, lib/motion/verbs.py; cùng API với motion.js)
"""
import math

__all__ = ["clamp", "lerp", "lerp3", "ramp", "smooth", "ease_out", "ease_in", "back", "anticip", "spring", "linear",
           "bounce_out", "elastic", "expo_out", "circ_out", "sine", "back_in", "steps",
           "EASE", "spline", "kick_at", "cam_from_keys", "idle", "blink_at", "walk", "q",
           "VERBS", "VERB_ALIASES", "VERB_DOC", "STAGGERS", "verb", "verb_name", "play", "stagger", "compose",
           "identity", "seed_of", "hash01", "canvas_delta", "three_delta", "verb_errors"]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(a, b, t):
    return [lerp(x, y, t) for x, y in zip(a, b)]


def ramp(f, a, b):
    return clamp((f - a) / (b - a))


def smooth(t):
    t = clamp(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def ease_out(t):
    return 1 - (1 - clamp(t)) ** 3


def ease_in(t):
    return clamp(t) ** 3


def back(t, s=1.7):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def anticip(t, s=0.12):
    t = clamp(t)
    return -s * math.sin(t / 0.25 * math.pi) if t < 0.25 else back((t - 0.25) / 0.75)


def spring(t, freq=3.0, damp=5.0):
    t = max(0.0, t)
    return 1 - math.exp(-damp * t) * math.cos(freq * 2 * math.pi * t)


def linear(t):
    return clamp(t)


# bộ easing chuẩn (đường cong Penner — cùng tên/hình với GSAP, Anime.js, Motion), viết lại không phụ thuộc thư viện
def bounce_out(t):
    t, n, d = clamp(t), 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def elastic(t):
    t = clamp(t)
    if t <= 0 or t >= 1:
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def expo_out(t):
    t = clamp(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def circ_out(t):
    t = clamp(t) - 1
    return math.sqrt(1 - t * t)


def sine(t):
    return -(math.cos(math.pi * clamp(t)) - 1) / 2


def back_in(t, s=1.70158):
    t = clamp(t)
    return (s + 1) * t * t * t - s * t * t


def steps(t, n=5):
    t = clamp(t)
    return 1.0 if t >= 1 else math.floor(t * n) / n


EASE = {"smooth": smooth, "easeOut": ease_out, "easeIn": ease_in, "back": back, "anticip": anticip,
        "spring": spring, "linear": linear, "bounceOut": bounce_out, "elastic": elastic, "expoOut": expo_out,
        "circOut": circ_out, "sine": sine, "backIn": back_in, "steps": steps}


def spline(pts, u):
    n = len(pts) - 1
    x = clamp(u) * n
    i = min(n - 1, int(math.floor(x)))
    t = x - i
    p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n, i + 2)]
    return [0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t * t * t) for k in range(len(p1))]


def kick_at(f, kicks=()):
    """Rung "lật" 7 frame: s ∈ [-a, a], đổi dấu mỗi frame và tắt dần. kicks = [{"f", "a"}]."""
    s = 0.0
    for k in kicks:
        d = f - k["f"]
        if 0 <= d < 7:
            s += (-1 if int(d) % 2 else 1) * k["a"] * (1 - d / 7)
    return s


def cam_from_keys(keys, f, creep=0.0012, kicks=()):
    """keys = [{"f", "pos", "look", "fov", "roll"?, "ease"?, "path"?}] → {"pos", "look", "fov", "roll"}."""
    K = keys
    if f <= K[0]["f"]:
        c = dict(K[0])
    elif f >= K[-1]["f"]:
        c = dict(K[-1])
    else:
        i = next(j for j in range(len(K) - 1) if K[j]["f"] <= f <= K[j + 1]["f"])
        a, b = K[i], K[i + 1]
        t = EASE[b.get("ease") or "smooth"]((f - a["f"]) / (b["f"] - a["f"]))
        pos = spline([a["pos"], *b["path"], b["pos"]], t) if b.get("path") else lerp3(a["pos"], b["pos"], t)
        c = {"pos": pos, "look": lerp3(a["look"], b["look"], t), "fov": lerp(a["fov"], b["fov"], t),
             "roll": lerp(a.get("roll") or 0, b.get("roll") or 0, t)}
    c = {"pos": list(c["pos"]), "look": list(c["look"]), "fov": c["fov"], "roll": c.get("roll") or 0}
    c["fov"] *= 1 - creep * max(0, f - K[0]["f"]) * 0.15
    s = kick_at(f, kicks)
    if s:
        c["look"] = [c["look"][0], c["look"][1] + s * 3, c["look"][2] + s * 2]
        c["roll"] += s * 20
    return c


def idle(f, seed=1):
    return {"bob": 0.006 * math.sin((f + seed * 11) * 0.11), "tilt": 1.2 * math.sin((f + seed * 7) * 0.05),
            "headTilt": 1.5 * math.sin((f + seed * 5) * 0.037 + 1)}


def blink_at(f, seed):
    per = 38 + (seed * 17) % 31
    ph = (f + seed * 13) % per
    return 0.5 if ph < 2 else 1 if ph < 4 else 0


def walk(f, f0, speed=1.1, stride=0.8):
    t = max(0, f - f0) / 30
    return {"dist": t * speed, "phase": (t * speed / (2 * stride)) % 1}


def q(x, n=2):
    return math.floor(x * 10 ** n + 0.5) / 10 ** n  # như Math.round của JS


# động từ chuyển động — nạp sau cùng vì verbs.py dùng các easing ở trên
from .verbs import (  # noqa: E402
    STAGGERS, VERB_ALIASES, VERB_DOC, VERBS, canvas_delta, compose, hash01, identity, play, seed_of, stagger,
    three_delta, verb, verb_errors, verb_name)
