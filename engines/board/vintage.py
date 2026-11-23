"""Đoạn chèn phim câm (silent-film-black): vẽ tay 2D, chạy trên twos, nét rung, intertitle viền đôi, iris.

Port máy vẽ của vintage_engine.py (kaz-documentary) nhưng MỌI cảnh là dữ liệu (không còn Sarajevo/T0/69.25 trong mã):

  spec = {"panels": [
     {"kind": "tableau", "dur": 2.2, "title": "DUISBURG · 1756", "full_rate": [[t0, t1]],
      "actors": [{"id", "kind", ...thuộc tính, "keys": [{"t", <thuộc tính>: giá trị}], "t0", "t1"}]},
     {"kind": "intertitle", "dur": 1.2, "lines": ["The drop doesn't boil.", "It dances."], "kicker": "LEIDENFROST · 1756"}]}

Toạ độ actor chuẩn hoá theo khung (x, y ∈ 0..1), độ dài theo chiều rộng khung. Thời gian = giây trong panel.
Actor: figure (người nhìn nghiêng; wig, arm 0 buông → 1 đưa thẳng) · table · fire · spoon (hot 0..1, held_by) · drop
(rơi rồi 'nhảy múa' trên lớp hơi) · steam · ball · glass · label (gõ chữ) · circle (khoanh đỏ) · text · line.
Đỏ CHỈ dùng cho accent có nghĩa (accent: true): vật nóng, nhãn chủ thể, vòng khoanh, chấm góc intertitle.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

import lib.motion as M

from . import color as col
from . import fonts
from .surface import Post

TWOS = 12  # bước vẽ / giây


def _J(tq, k, a=2.0):
    """Nét rung (boiling line): đổi mỗi bước twos."""
    r = np.random.default_rng(int(tq * TWOS) * 97 + k)
    return float(r.uniform(-a, a))


def _prop(actor, name, t, default=None):
    v = actor.get(name, default)
    keys = [k for k in actor.get("keys") or [] if name in k]
    if not keys:
        return v
    if t <= keys[0]["t"]:
        return keys[0][name]
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]:
            u = M.smooth((t - a["t"]) / max(b["t"] - a["t"], 1e-6))
            if isinstance(a[name], (int, float)) and isinstance(b[name], (int, float)):
                return a[name] + (b[name] - a[name]) * u
            return b[name] if u >= 0.5 else a[name]
    return keys[-1][name]


class Insert:
    def __init__(self, spec, W, H, fps, n_frames, tokens):
        self.W, self.H, self.fps, self.n = W, H, fps, n_frames
        self.tok = tokens
        pal = tokens
        self.PAPER = col.rgb(pal.get("bg", "#0b0b0b"))
        self.INK = col.rgb(pal.get("film_ink", "#d9d9d4"))
        self.MID = col.rgb(pal.get("film_mid", "#8c8c88"))
        self.DARK = col.rgb(pal.get("film_dark", "#3a3a38"))
        self.FILL = col.rgb(pal.get("film_fill", "#1e1e1d"))
        self.RED = col.rgb(pal.get("accent", "#d0312d"))
        self.post = Post(W, H, {**tokens, "film": True, "grain": tokens.get("grain", 13),
                                "vignette": tokens.get("vignette", 0.62), "flicker": tokens.get("flicker", 0.07)}, seed=11)
        panels = spec.get("panels") or []
        total = n_frames / fps
        want = sum(float(p.get("dur", 1.0)) for p in panels) or 1.0
        self.panels, t = [], 0.0
        for p in panels:
            d = float(p.get("dur", 1.0)) * total / want
            self.panels.append((t, t + d, p))
            t += d
        self.iris_gap = float(spec.get("iris_between", 0.16))

    # ------------------------------------------------------------------ primitives
    def S(self, v):
        return v * self.W

    def P(self, x, y):
        return (x * self.W, y * self.H)

    def wline(self, d, pts, tq, k, fill, w=5, a=2.0):
        pts = [(x + _J(tq, k + i, a), y + _J(tq, k + i + 50, a)) for i, (x, y) in enumerate(pts)]
        d.line(pts, fill=fill, width=int(w), joint="curve")

    def wpoly(self, d, pts, tq, k, fill, outline=None, w=4):
        pts = [(x + _J(tq, k + i, 1.5), y + _J(tq, k + i + 50, 1.5)) for i, (x, y) in enumerate(pts)]
        d.polygon(pts, fill=fill)
        d.line(pts + [pts[0]], fill=outline or self.INK, width=int(w))

    def _c(self, a):
        return self.RED if a.get("accent") else self.INK

    # ------------------------------------------------------------------ actors
    def figure_hand(self, a, t):
        x, y = _prop(a, "x", t, 0.3), _prop(a, "y", t, 0.85)
        s = self.S(_prop(a, "scale", t, 0.42)) / 240.0
        arm = _prop(a, "arm", t, 0.0)
        face = 1 if a.get("facing", 1) >= 0 else -1
        sx, sy = self.P(x, y)
        shx, shy = sx + face * 30 * s, sy - 200 * s
        ang = arm * math.pi / 2
        L = 120 * s
        return (shx + face * L * math.sin(ang), shy + L * math.cos(ang)), s

    def a_figure(self, d, a, t, tq, k):
        x, y = _prop(a, "x", t, 0.3), _prop(a, "y", t, 0.85)
        s = self.S(_prop(a, "scale", t, 0.42)) / 240.0
        face = 1 if a.get("facing", 1) >= 0 else -1
        lean = _prop(a, "lean", t, 0.0)
        X, Y = self.P(x, y)
        coat = self.MID  # bóng người bạc trên nền gần đen (không tối lẫn vào nền)
        lx = lambda v: X + face * v * s  # noqa: E731
        for leg in (-14, 14):
            self.wline(d, [(lx(leg), Y - 60 * s), (lx(leg + lean * 10), Y)], tq, k + leg, self.INK, 16 * s)
        body = [(lx(-38), Y - 50 * s), (lx(40), Y - 50 * s), (lx(34 + lean * 20), Y - 215 * s), (lx(-30 + lean * 20),
                                                                                                  Y - 215 * s)]
        self.wpoly(d, body, tq, k + 3, coat, self.INK, 4 * s + 1)
        hx, hy = lx(4 + lean * 26), Y - 252 * s
        r = 30 * s
        if a.get("wig", False):  # paruka bột: các lọn xoăn sau gáy
            for ox, oy in ((-26, -6), (-30, 16), (-24, 36), (-12, -26)):
                cx, cy = hx + face * ox * s, hy + oy * s
                d.ellipse([cx - 16 * s, cy - 14 * s, cx + 16 * s, cy + 14 * s], fill=self.INK, outline=self.MID,
                          width=max(1, int(2 * s)))
        d.ellipse([hx - r + _J(tq, k + 7), hy - r, hx + r + _J(tq, k + 7), hy + r], fill=self.INK, outline=self.INK,
                  width=max(2, int(4 * s)))
        d.ellipse([hx + face * 12 * s - 3 * s, hy - 6 * s, hx + face * 12 * s + 3 * s, hy], fill=self.PAPER)  # mắt
        d.line([(hx + face * r, hy + 2 * s), (hx + face * (r + 8 * s), hy + 8 * s)], fill=self.INK, width=max(2, int(3 * s)))
        (hx2, hy2), _ = self.figure_hand(a, t)
        shx, shy = X + face * 30 * s, Y - 200 * s
        self.wline(d, [(shx, shy), (hx2, hy2)], tq, k + 9, self.INK, 14 * s)
        d.ellipse([hx2 - 8 * s, hy2 - 8 * s, hx2 + 8 * s, hy2 + 8 * s], fill=self.INK)

    def a_table(self, d, a, t, tq, k):
        x, y, w = a.get("x", 0.5), a.get("y", 0.7), a.get("w", 0.8)
        X0, X1, Y = (x - w / 2) * self.W, (x + w / 2) * self.W, y * self.H
        th = self.S(0.025)
        self.wpoly(d, [(X0, Y), (X1, Y), (X1, Y + th), (X0, Y + th)], tq, k, self.DARK, self.INK, 4)
        for lx in (X0 + th, X1 - th):
            self.wline(d, [(lx, Y + th), (lx, Y + self.S(a.get("leg", 0.3)))], tq, k + int(lx), self.INK, 10)

    def a_fire(self, d, a, t, tq, k):
        X, Y = self.P(a.get("x", 0.6), a.get("y", 0.7))
        w = self.S(a.get("w", 0.16))
        self.wpoly(d, [(X - w / 2, Y), (X + w / 2, Y), (X + w * 0.38, Y - w * 0.35), (X - w * 0.38, Y - w * 0.35)], tq, k,
                   self.DARK, self.INK, 4)
        for j in range(5):
            fx = X - w * 0.3 + j * w * 0.15
            hgt = w * (0.45 + 0.25 * math.sin(tq * 9 + j * 1.7))
            pts = [(fx - w * 0.06, Y - w * 0.35), (fx + _J(tq, k + j, 6), Y - w * 0.35 - hgt), (fx + w * 0.06, Y - w * 0.35)]
            d.polygon(pts, fill=self.MID if j % 2 else self.INK)

    def a_spoon(self, d, a, t, tq, k, actors):
        hot = _prop(a, "hot", t, 1.0)
        held = a.get("held_by")
        if held and held in actors:
            (hx, hy), s = self.figure_hand(actors[held], t)
            ang = math.radians(a.get("angle", 8))
            L = self.S(a.get("len", 0.22))
            bx, by = hx + L * math.cos(ang), hy + L * math.sin(ang)
        else:
            bx, by = self.P(_prop(a, "x", t, 0.6), _prop(a, "y", t, 0.55))
            ang = math.radians(a.get("angle", 8))
            L = self.S(a.get("len", 0.22))
            hx, hy = bx - L * math.cos(ang), by - L * math.sin(ang)
        self.wline(d, [(hx, hy), (bx - self.S(0.03), by)], tq, k, self.INK, 9)
        rx, ry = self.S(0.055), self.S(0.022)
        glow = col.mix(self.DARK, self.RED, max(0.0, min(1.0, hot)))
        d.ellipse([bx - rx, by - ry, bx + rx, by + ry], fill=glow, outline=self.INK, width=4)
        a["_bowl"] = (bx, by - ry)

    def a_drop(self, d, a, t, tq, k, actors):
        t0, t1 = a.get("t0", 0.3), a.get("t1", 0.8)
        tgt = a.get("on")
        if tgt and tgt in actors and "_bowl" in actors[tgt]:
            ex, ey = actors[tgt]["_bowl"]
        else:
            ex, ey = self.P(*a.get("end", [0.6, 0.55]))
        sx, sy = (ex, self.H * a.get("from_y", 0.25))
        r = self.S(a.get("r", 0.022))
        if t < t0:
            return
        if t < t1:
            u = M.ease_in((t - t0) / (t1 - t0))
            x, y = sx, sy + (ey - r - sy) * u
            d.ellipse([x - r * 0.8, y - r * 1.25, x + r * 0.8, y + r], fill=self.MID, outline=self.INK, width=3)
            return
        lt = tq - t1
        hop = abs(math.sin(lt * 7.5)) * self.S(0.018)
        dx = math.sin(lt * 3.1) * self.S(0.022)
        x, y = ex + dx, ey - r - hop - self.S(0.006)
        for j in range(3):  # lớp hơi dưới giọt
            yy = ey - self.S(0.004) - j * 3
            d.line([(x - r + j * 4 + _J(tq, k + j, 2), yy), (x + r - j * 4 + _J(tq, k + j + 9, 2), yy)], fill=self.MID,
                   width=2)
        d.ellipse([x - r, y - r * 0.9, x + r, y + r * 0.9], fill=self.MID, outline=self.INK, width=3)
        d.ellipse([x - r * 0.45, y - r * 0.55, x - r * 0.05, y - r * 0.2], fill=self.INK)
        a["_pos"] = (x, y)

    def a_steam(self, d, a, t, tq, k):
        X, Y = self.P(a.get("x", 0.6), a.get("y", 0.5))
        t0 = a.get("t0", 0.0)
        if t < t0:
            return
        for j in range(4):
            lt = (tq - t0 + j * 0.25) % 1.0
            yy = Y - lt * self.S(0.16)
            xx = X + math.sin(lt * 6 + j) * self.S(0.02) + (j - 1.5) * self.S(0.02)
            rr = self.S(0.012 + lt * 0.02)
            d.ellipse([xx - rr, yy - rr, xx + rr, yy + rr], outline=self.MID, width=2)

    def a_ball(self, d, a, t, tq, k):
        X, Y = self.P(_prop(a, "x", t, 0.5), _prop(a, "y", t, 0.5))
        r = self.S(_prop(a, "r", t, 0.05))
        hot = _prop(a, "hot", t, 0.0)
        d.ellipse([X - r, Y - r, X + r, Y + r], fill=col.mix(self.DARK, self.RED, hot), outline=self.INK, width=4)

    def a_glass(self, d, a, t, tq, k):
        X, Y = self.P(a.get("x", 0.5), a.get("y", 0.7))
        w, h = self.S(a.get("w", 0.3)), self.S(a.get("h", 0.42))
        lvl = _prop(a, "water", t, 0.6)
        d.rectangle([X - w / 2 + 4, Y - h * lvl, X + w / 2 - 4, Y], fill=self.FILL)
        self.wline(d, [(X - w / 2, Y - h), (X - w / 2 * 0.9, Y), (X + w / 2 * 0.9, Y), (X + w / 2, Y - h)], tq, k,
                   self.INK, 6)

    def a_label(self, d, a, t, tq, k):
        t0 = a.get("t0", 0.0)
        if t < t0:
            return
        txt = a.get("text", "")
        n = min(len(txt), int((t - t0) * a.get("cps", 26)) + 1)
        size = self.S(a.get("size", 0.042))
        X, Y = self.P(a.get("x", 0.1), a.get("y", 0.3))
        fonts.draw(d, (X, Y), txt[:n], a.get("role", "mono"), size, self._c(a))
        if a.get("leader"):
            lx, ly = self.P(*a["leader"])
            d.line([(X + size * 0.4, Y + size * 1.15), (lx, ly)], fill=self._c(a), width=4)

    def a_circle(self, d, a, t, tq, k, actors):
        t0, du = a.get("t0", 0.0), a.get("dur", 0.3)
        if t < t0:
            return
        frac = max(0.0, min(1.0, (t - t0) / du))
        tgt = a.get("on")
        if tgt and tgt in actors and "_pos" in actors[tgt]:
            cx, cy = actors[tgt]["_pos"]
        else:
            cx, cy = self.P(a.get("x", 0.5), a.get("y", 0.5))
        rx, ry = self.S(a.get("rx", 0.1)), self.S(a.get("ry", 0.06))
        pts = []
        for i in range(int(60 * frac) + 2):
            th = -1.6 + 2 * math.pi * 1.05 * i / 60
            pts.append((cx + rx * math.cos(th) + _J(tq, i, 2), cy + ry * math.sin(th) + _J(tq, i + 9, 2)))
        d.line(pts, fill=self._c({"accent": a.get("accent", True)}), width=7, joint="curve")

    def a_text(self, d, a, t, tq, k):
        size = self.S(a.get("size", 0.06))
        txt = a.get("text", "")
        tw = fonts.width(txt, a.get("role", "serif"), size)
        X, Y = self.P(a.get("x", 0.5), a.get("y", 0.1))
        fonts.draw(d, (X - tw / 2, Y), txt, a.get("role", "serif"), size, self._c(a))

    def a_line(self, d, a, t, tq, k):
        pts = [self.P(*p) for p in a.get("pts", [])]
        if len(pts) >= 2:
            self.wline(d, pts, tq, k, self._c(a), a.get("w", 5))

    # ------------------------------------------------------------------ panels
    def tableau(self, p, t, tq):
        im = Image.new("RGB", (self.W, self.H), self.PAPER)
        d = ImageDraw.Draw(im)
        for y in range(0, self.H, int(self.H / 32)):  # vân giấy mờ
            d.line([(0, y), (self.W, y)], fill=col.mix(self.PAPER, self.DARK, 0.18), width=1)
        if p.get("title"):
            size = self.S(0.06)
            tw = fonts.width(p["title"], "serif", size)
            fonts.draw(d, ((self.W - tw) / 2, self.H * 0.11), p["title"], "serif", size, self.INK)
        actors = {a.get("id", f"_{i}"): dict(a) for i, a in enumerate(p.get("actors") or [])}
        order = sorted(actors.values(), key=lambda a: a.get("z", 0))
        for i, a in enumerate(order):
            if t < a.get("show", -1e9) or t > a.get("hide", 1e9):
                continue
            kind = a.get("kind")
            fn = getattr(self, f"a_{kind}", None)
            if fn is None:
                continue
            if kind in ("spoon", "drop", "circle"):
                fn(d, a, t, tq, 1000 + i * 37, actors)
            else:
                fn(d, a, t, tq, 1000 + i * 37)
        return im

    def intertitle(self, p, t, tq):
        W, H = self.W, self.H
        im = Image.new("RGB", (W, H), col.mix(self.PAPER, (0, 0, 0), 0.4))
        d = ImageDraw.Draw(im)
        m1, m2 = W * 0.07, W * 0.09
        top, bot = H * 0.3, H * 0.7
        d.rectangle([m1, top, W - m1, bot], outline=self.INK, width=4)
        d.rectangle([m2, top + (m2 - m1), W - m2, bot - (m2 - m1)], outline=self.INK, width=1)
        for (x, y) in ((m2, top + m2 - m1), (W - m2, top + m2 - m1), (m2, bot - m2 + m1), (W - m2, bot - m2 + m1)):
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=self.RED)
        lines = p.get("lines") or []
        y = H * 0.5 - (len(lines) * W * 0.085) / 2 + W * 0.02
        if p.get("kicker"):
            ks = self.S(0.034)
            kw = fonts.width(p["kicker"], "mono", ks)
            fonts.draw(d, ((W - kw) / 2, top + W * 0.07), p["kicker"], "mono", ks, self.INK)
            d.line([(W / 2 - W * 0.12, top + W * 0.07 + ks * 1.5), (W / 2 + W * 0.12, top + W * 0.07 + ks * 1.5)],
                   fill=self.RED, width=4)
        for i, s in enumerate(lines):
            size = self.S(0.072 if i == 0 else 0.062)
            while fonts.width(s, "serif", size) > W - 2 * m2 - 40 and size > 20:
                size *= 0.95
            tw = fonts.width(s, "serif", size)
            fonts.draw(d, ((W - tw) / 2, y), s, "serif", size, self.INK)
            y += size * 1.35
        return im

    # ------------------------------------------------------------------ frame
    def panel_img(self, p, lt):
        full = any(f0 <= lt <= f1 for f0, f1 in p.get("full_rate") or [])
        tq = lt if full else math.floor(lt * TWOS) / TWOS
        img = self.intertitle(p, lt, tq) if p.get("kind") == "intertitle" else self.tableau(p, lt, tq)
        return col.from_rgb(np.asarray(img))

    def frame(self, j):
        """Frame j (0..n-1) của đoạn chèn → BGR uint8 (đã xử lý phim). Giữa hai panel: iris khép dần trên panel cũ để
        lộ panel mới ở ngoài vòng tròn (không có frame đen chết)."""
        t = j / self.fps
        for i, (a0, a1, p) in enumerate(self.panels):
            last = i == len(self.panels) - 1
            if a0 <= t < a1 or (last and t >= a0):
                arr = self.panel_img(p, t - a0)
                g = self.iris_gap
                if not last and a1 - t < g:
                    nxt = self.panel_img(self.panels[i + 1][2], 0.0)
                    arr = iris(arr, nxt, M.smooth((a1 - t) / g))
                return self.post.apply(arr, j)
        return np.zeros((self.H, self.W, 3), np.uint8)


def iris(fg, bg, k, feather=6):
    """Vòng iris cổ điển: k=0 đóng (toàn bg), k=1 mở hết (toàn fg)."""
    H, W = fg.shape[:2]
    if k >= 0.999:
        return fg
    if k <= 0.001:
        return bg
    R = math.hypot(W / 2, H / 2) * k
    yy, xx = np.ogrid[:H, :W]
    d = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2)
    m = np.clip((R - d) / feather + 0.5, 0, 1)[..., None].astype(np.float32)
    return (fg.astype(np.float32) * m + bg.astype(np.float32) * (1 - m)).astype(np.uint8)
