"""Scene: đọc board.json (do vidlib/boardplan.py sinh) → render từng frame BGR. KHÔNG có mốc thời gian nào trong mã:
mọi thời điểm/vị trí nằm trong board.json; mã chỉ chứa máy vẽ + thời lượng hoạt ảnh chuẩn (anim) đọc từ board.json.

board.json (rút gọn):
  width/height/fps/frames · surface (token style) · world {w, h} · anim {drop_sec, stamp_sec, …}
  camera  [{t, cx, cy, zoom, rot, ease}]
  items   [{id, kind: media|paper|number|thesis|counter|image, x, y, rot, t_in, z, …}]
  marks   [{kind: tag|circle|string|stamp|highlight, t0, …}]   (toạ độ world)
  fx      [{kind: shake|flash|rgb|dim, t, dur, …}] · overlays [{kind: title_glitch, t0, t1, title, sub}]
  inserts [{id, f0, n, spec, iris_in, iris_out}]  (phim câm; mặt nạ iris trên nền bảng)
  returns {t, dur}   (tất cả nhãn quay lại cho NETWORK_REVEAL)
"""
import math
import os
import re
from collections import OrderedDict

import cv2
import numpy as np

import lib.motion as M

from . import camera, draw, sprites, surface, vintage
from . import color as col
from . import fonts

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def ss(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def fmt_like(target, v):
    """Định dạng số v theo mẫu `target` ('1,000°C', '0.3 s', '×1000')."""
    m = NUM_RE.search(target)
    if not m:
        return target
    num = m.group(0)
    dec = len(num.split(".")[1]) if "." in num else 0
    s = f"{v:,.{dec}f}" if "," in num else f"{v:.{dec}f}"
    return target[: m.start()] + s + target[m.end():]


def num_of(target):
    m = NUM_RE.search(target or "")
    return float(m.group(0).replace(",", "")) if m else None


class LRU(OrderedDict):
    def __init__(self, n):
        super().__init__()
        self.n = n

    def get_or(self, key, fn):
        if key in self:
            self.move_to_end(key)
            return self[key]
        v = fn()
        self[key] = v
        if len(self) > self.n:
            self.popitem(last=False)
        return v


class Scene:
    def __init__(self, board, root=None):
        self.b = board
        self.root = root or fonts.ROOT
        self.W, self.H, self.fps = int(board["width"]), int(board["height"]), int(board["fps"])
        self.tok = board.get("surface") or {}
        self.anim = {"drop_sec": 0.45, "stamp_sec": 0.2, "tag_cps": 22, "tag_fade": 0.4, "return_sec": 0.5,
                     "thesis_cps_old": 18, "thesis_cps_new": 14, "strike_sec": 0.28, **(board.get("anim") or {})}
        self.twos = bool(self.tok.get("twos"))
        self.ww, self.wh = board["world"]["w"], board["world"]["h"]
        self.bg = surface.build_bg(self.ww, self.wh, self.tok, seed=int(board.get("seed", 1)))
        self.post = surface.Post(self.W, self.H, self.tok)
        self.keys = board.get("camera") or []
        self.items = sorted(board.get("items") or [], key=lambda it: (it.get("z", 0), it.get("t_in", 0)))
        self.marks = board.get("marks") or []
        self.fx = board.get("fx") or []
        self.overlays = board.get("overlays") or []
        self.returns = board.get("returns")
        self.sprite_cache = LRU(160)
        self.frame_cache = LRU(12)
        self._build()
        self.inserts = []
        for ins in board.get("inserts") or []:
            v = vintage.Insert(ins["spec"], self.W, self.H, self.fps, int(ins["n"]),
                               ins.get("tokens") or self.tok)
            self.inserts.append((ins, v))

    # ------------------------------------------------------------------ build
    def _path(self, p):
        return p if os.path.isabs(p) else os.path.join(self.root, p)

    def _build(self):
        tok = self.tok
        for it in self.items:
            k = it["kind"]
            seed = sum(map(ord, it["id"]))  # ổn định giữa các lần chạy (hash() của Python bị ngẫu nhiên hoá)
            if k == "media":
                spr, rect = sprites.media_card(it["photo"][0], it["photo"][1], tok, it.get("caption", ""), seed)
                it["_spr"], it["_rect"] = spr, rect
            elif k == "paper":
                spr, lay, size = sprites.paper(it["lines"], it["w"], tok, seed, kind=it.get("paper_kind", "paper"))
                it["_spr"], it["_lay"] = spr, lay
            elif k == "image":
                spr, size = sprites.image_card(self._path(it["path"]), it["w"], tok, seed, gray=bool(it.get("gray")))
                it["_spr"] = spr
            elif k in ("number", "thesis", "counter"):
                rules = []
                if k == "number":
                    w, h = it["w"], it["h"]
                    y = h * 0.78
                    rules = [(y, w * 0.12, w * 0.40), (y, w * 0.60, w * 0.88)]
                it["_spr"] = sprites.card(it["w"], it["h"], tok, seed, rules)

    def _sprite(self, key, fn):
        return self.sprite_cache.get_or(key, fn)

    # ------------------------------------------------------------------ media
    def media_frame(self, it, fi):
        segs = it["src"]["segments"]
        seg = segs[0]
        j = 0
        for s in segs:
            if fi >= s["f0"]:
                seg, j = s, fi - s["f0"]
        j = max(0, min(int(seg["n"]) - 1, j))
        if fi < segs[0]["f0"]:
            seg, j = segs[0], 0
        key = (seg["dir"], j)

        def load():
            p = os.path.join(self._path(seg["dir"]), f"f{j:04d}.jpg")
            if not os.path.exists(p):
                cand = sorted(f for f in os.listdir(self._path(seg["dir"])) if f.endswith(".jpg")) \
                    if os.path.isdir(self._path(seg["dir"])) else []
                if not cand:
                    img = np.zeros((self.H, self.W, 3), np.uint8)
                    cv2.putText(img, f"{it['id']} (no frames)", (60, self.H // 2), cv2.FONT_HERSHEY_SIMPLEX, 2,
                                (90, 90, 90), 3)
                    return img
                best = min(cand, key=lambda f: abs(int(f[1:5]) - j))
                p = os.path.join(self._path(seg["dir"]), best)
            return cv2.imread(p, cv2.IMREAD_COLOR)
        return self.frame_cache.get_or(key, load)

    # ------------------------------------------------------------------ helpers
    def tq(self, t):
        return math.floor(t * 12) / 12 if self.twos else t

    def appear(self, it, t):
        """(scale, dy, alpha) cho hoạt ảnh thả thẻ: trượt xuống, nảy nhẹ (back-out), hiện dần."""
        if it.get("reveal") == "none":
            return 1.0, 0.0, 1.0
        u = (t - it["t_in"]) / self.anim["drop_sec"]
        if u >= 1:
            return 1.0, 0.0, 1.0
        sc = 1.12 - 0.12 * M.back(u)
        dy = -60 * (1 - M.ease_out(u))
        return sc, dy, ss(u * 1.6)

    def life(self, m, t):
        """Độ hiện của nhãn: gõ từ t0, mờ ở t_fade, quay lại ở returns.t (NETWORK_REVEAL)."""
        a = 1.0
        if m.get("t_fade") is not None:
            a = 1 - ss((t - m["t_fade"]) / self.anim["tag_fade"])
        if self.returns and t >= self.returns["t"] and m.get("t0", 0) < self.returns["t"]:
            a = max(a, ss((t - self.returns["t"]) / self.returns.get("dur", self.anim["return_sec"])))
        if m.get("t_out") is not None:
            a = min(a, 1 - ss((t - m["t_out"]) / 0.3))
        return a

    def camera_at(self, t):
        C = list(camera.at(self.keys, t))
        for f in self.fx:
            if f["kind"] == "shake" and f["t"] <= t < f["t"] + f["dur"]:
                k = (1 - (t - f["t"]) / f["dur"]) * f.get("amp", 14)
                C[0] += k * math.sin(t * 90) / C[2]
                C[1] += k * math.cos(t * 77) / C[2]
        return tuple(C)

    # ------------------------------------------------------------------ items
    def draw_item(self, frame, it, t, fi, C):
        sc, dy, al = self.appear(it, t)
        if it.get("t_out") is not None:
            al *= 1 - ss((t - it["t_out"]) / 0.3)
        if al <= 0.003:
            return False
        c = (it["x"], it["y"] + dy)
        rot = it.get("rot", 0.0)
        draw.blit(frame, it["_spr"], c, rot, C, sc, al)
        k = it["kind"]
        covers = False
        if k == "media":
            img = self.media_frame(it, fi)
            if al < 0.999:
                img = (img.astype(np.float32) * al).astype(np.uint8)
            covers = draw.photo(frame, img, c, rot, sc, it["_rect"], C, col.bgr(self.tok.get("card", "#d6d6d0")))
        elif k == "number":
            self.draw_number(frame, it, t, c, rot, sc, al, C)
        elif k == "thesis":
            self.draw_thesis(frame, it, t, c, rot, sc, al, C)
        elif k == "counter":
            self.draw_counter(frame, it, t, c, rot, sc, al, C)
        return covers

    def _txt(self, frame, s, role, size, fill, c, rot, sc, al, C, off, anchor="center"):
        if not s:
            return
        spr = self._sprite(("txt", s, role, round(size, 2), fill, anchor),
                           lambda: sprites.text(s, role, size, fill, anchor=anchor))
        draw.blit(frame, spr, c, rot, C, sc, al, offset=off)

    def draw_number(self, frame, it, t, c, rot, sc, al, C):
        h = it["h"]
        target = it["text"]
        v1 = num_of(target)
        v0 = it.get("from")
        u = (t - it["count_t0"]) / max(it.get("count_dur", 0.6), 1e-3) if it.get("count_t0") is not None else 1.0
        u = max(0.0, min(1.0, u))
        s = target if v1 is None or v0 is None or u >= 1 else fmt_like(target, v0 + (v1 - v0) * M.ease_out(u))
        ink = self.tok.get("text_light", "#ecebe4")
        if it.get("caption"):
            self._txt(frame, it["caption"], "mono", it.get("caption_size", 34), self.tok.get("text_dim", "#9a9993"), c, rot,
                      sc, al, C, (0, -h * 0.30))
        self._txt(frame, s, "serif", it.get("size", 150), ink, c, rot, sc, al, C, (0, h * 0.06))
        if it.get("sub"):
            self._txt(frame, it["sub"], "mono", it.get("sub_size", 26), self.tok.get("text_dim", "#9a9993"), c, rot, sc,
                      al, C, (0, h * 0.30 + 6))

    def draw_thesis(self, frame, it, t, c, rot, sc, al, C):
        w, h = it["w"], it["h"]
        t = self.tq(t)
        old, new = it["old"], it["new"]
        so, sn = it.get("old_size", 40), it.get("new_size", 74)
        cps = it.get("old_cps") or self.anim["thesis_cps_old"]
        n1 = len(old) if it.get("t_old") is None else min(len(old), max(0, int((t - it["t_old"]) * cps)))
        y_old, y_new = -h * 0.20, h * 0.14
        x_old = -fonts.width(old, "mono", so) / 2
        light = self.tok.get("text_light", "#ecebe4")
        self._txt(frame, old[:n1], "mono", so, self.tok.get("text_dim", "#b9b8b1"), c, rot, sc, al, C, (x_old, y_old),
                  anchor="left")
        red = col.bgr(self.tok.get("accent", "#d0312d"))
        if it.get("t_strike") is not None and t >= it["t_strike"]:
            u = M.ease_out((t - it["t_strike"]) / self.anim["strike_sec"])
            wo = fonts.width(old, "mono", so)
            a = draw.local_to_screen((x_old - 8, y_old + 2), c, rot, sc, C, self.W, self.H)
            b = draw.local_to_screen((x_old - 8 + (wo + 16) * u, y_old - 2), c, rot, sc, C, self.W, self.H)
            draw.polyline(frame, [a, b], red, max(3, 6 * C[2] * sc), al)
        if it.get("t_new") is not None and t >= it["t_new"]:
            n2 = min(len(new), int((t - it["t_new"]) * self.anim["thesis_cps_new"]) + 1)
            size = sn
            while fonts.width(new + ".", "serif", size) > w * 0.86 and size > 20:
                size *= 0.95
            wn = fonts.width(new + ".", "serif", size)
            x_new = -wn / 2
            self._txt(frame, new[:n2], "serif", size, light, c, rot, sc, al, C, (x_new, y_new), anchor="left")
            if n2 >= len(new) and (it.get("t_dot") is None or t >= it["t_dot"]):
                self._txt(frame, ".", "serif", size, self.tok.get("accent", "#d0312d"), c, rot, sc, al, C,
                          (x_new + fonts.width(new, "serif", size), y_new), anchor="left")

    def draw_counter(self, frame, it, t, c, rot, sc, al, C):
        h = it["h"]
        v0, v1 = float(it.get("from", 0)), float(it.get("to", 0))
        t0, du = it.get("t0", it["t_in"]), it.get("dur", 0.8)
        u = max(0.0, min(1.0, (t - t0) / max(du, 1e-3)))
        v = v0 + (v1 - v0) * M.ease_out(u)
        jit = float(it.get("jitter", 0))
        if jit and u >= 1:
            v += jit * math.sin(math.floor(t * 6) * 2.1)
        dec = int(it.get("decimals", 1))
        s = f"{v:.{dec}f}{it.get('unit', '')}"
        if s.startswith("-0") and abs(v) < 0.5 * 10 ** -dec:
            s = s[1:]
        self._txt(frame, it.get("label", ""), "mono", it.get("label_size", 30), self.tok.get("text_dim", "#9a9993"), c, rot,
                  sc, al, C, (0, -h * 0.30))
        self._txt(frame, s, "mono", it.get("size", 120), self.tok.get("text_light", "#ecebe4"), c, rot, sc, al, C,
                  (0, h * 0.08))

    # ------------------------------------------------------------------ marks
    def draw_marks(self, frame, t, C):
        red = col.bgr(self.tok.get("accent", "#d0312d"))
        t2 = self.tq(t)
        z = C[2]
        for m in self.marks:
            k = m["kind"]
            if t < m["t0"]:
                continue
            if k == "circle":
                a = self.life(m, t)
                frac = max(0.0, min(1.0, (t2 - m["t0"]) / m["dur"]))
                pts = draw.wobble_ellipse_pts(m["c"], m["rx"], m["ry"], m.get("rot", 0), frac, m.get("seed", 0))
                draw.polyline(frame, draw.to_px(pts, C, self.W, self.H), red, max(3, m.get("width", 5) * z), a)
            elif k == "string":
                a = self.life(m, t)
                u = M.ease_out((t2 - m["t0"]) / m["dur"])
                pts = draw.string_pts(m["a"], m["b"], u, m.get("sag", 30))
                px = draw.to_px(pts, C, self.W, self.H)
                draw.polyline(frame, px, red, max(2, m.get("width", 4) * z), a)
                for p in (px[0], px[-1]):
                    draw.dot(frame, p, max(4, 7 * z), red, a)
            elif k == "highlight":
                a = self.life(m, t) * m.get("alpha", 0.5)
                u = M.ease_out((t2 - m["t0"]) / m["dur"])
                A, B = m["a"], m["b"]
                pts = [(A[0] + (B[0] - A[0]) * s / 12, A[1] + (B[1] - A[1]) * s / 12 + math.sin(s * 1.3) * 2)
                       for s in range(int(12 * u) + 1)]
                if len(pts) >= 2:
                    draw.polyline(frame, draw.to_px(pts, C, self.W, self.H), red, max(4, m.get("h", 30) * z), a)
            elif k == "tag":
                self.draw_tag(frame, m, t, C, red)
            elif k == "stamp":
                u = (t - m["t0"]) / self.anim["stamp_sec"]
                scl = 1.6 - 0.6 * M.back(u, 2.2)
                spr = self._sprite(("stamp", m["text"], m["size"]),
                                   lambda m=m: sprites.stamp(m["text"], m["size"], self.tok, seed=len(m["text"])))
                draw.blit(frame, spr, m["c"], m.get("rot", -12), C, scl, ss(u * 3) * self.life(m, t))

    def draw_tag(self, frame, m, t, C, red):
        a = self.life(m, t)
        if a <= 0.01:
            return
        txt = m["text"]
        n = min(len(txt), int((self.tq(t) - m["t0"]) * (m.get("cps") or self.anim["tag_cps"])) + 1)
        cursor = n < len(txt) or ((t - m["t0"]) < 1.6 and int(t * 2.5) % 2 == 0)
        spr, (w, h) = self._sprite(("tag", txt, n, cursor, m["size"]),
                                   lambda: sprites.tag(txt[:n], txt, m["size"], self.tok, cursor))
        p = m["pos"]
        if m.get("anchor"):
            an = camera.to_screen(m["anchor"], C, self.W, self.H)
            end = (p[0] + (w if m.get("side") == "left" else 0), p[1])
            q = camera.to_screen(end, C, self.W, self.H)
            draw.polyline(frame, [an, q], red, max(2, 3 * C[2]), a)
            draw.dot(frame, an, max(4, 6 * C[2]), red, a)
        draw.blit(frame, spr, p, m.get("rot", 0), C, 1.0, a, offset=(0, 0))

    # ------------------------------------------------------------------ overlays
    def draw_overlays(self, frame, t):
        for o in self.overlays:
            if o["kind"] == "title_glitch" and o["t0"] <= t <= o["t1"] + 1e-6:
                return self.title_glitch(frame, o, t)
        return frame

    def title_glitch(self, frame, o, t):
        a = ss((t - o["t0"]) / 0.35)
        out = frame.astype(np.float32) * (1 - 0.82 * a)
        out = out.astype(np.uint8)
        W = self.W
        red = self.tok.get("accent", "#d0312d")
        lines = o.get("title_lines") or [o.get("title", "")]
        size = o.get("size", 112)
        y = self.H * o.get("y", 0.40) - len(lines) * size * 0.6
        for s in lines:
            spr = self._sprite(("tt", s, size), lambda s=s: sprites.text(s, "serif", size, red, Dd=1.0))
            draw.blit(out, spr, (W / 2, y), 0, (W / 2, self.H / 2, 1.0, 0.0), 1.0, a)
            y += size * 1.15
        if o.get("sub"):
            spr = self._sprite(("ts", o["sub"]), lambda: sprites.text(o["sub"], "mono", o.get("sub_size", 36),
                                                                      self.tok.get("text_light", "#ecebe4"), Dd=1.0))
            draw.blit(out, spr, (W / 2, y + size * 0.15), 0, (W / 2, self.H / 2, 1.0, 0.0), 1.0, a)
        g0 = o["t0"] + o.get("glitch_at", 0.0)
        if g0 <= t < g0 + o.get("glitch_sec", 0.45):
            r = np.random.default_rng(int(t * self.fps))
            y0, y1 = int(self.H * 0.25), int(self.H * 0.6)
            for _ in range(7):
                yy = int(r.integers(y0, y1))
                hh = int(r.integers(8, 34))
                out[yy:yy + hh] = np.roll(out[yy:yy + hh], int(r.integers(-70, 70)), axis=1)
            out = draw.rgb_split(out, int(r.integers(4, 12)))
        fade = o.get("fade_out", 0.35)
        if t > o["t1"] - fade:
            k = max(0.0, (o["t1"] - t) / fade)
            out = (out.astype(np.float32) * k).astype(np.uint8)
        return out

    def apply_fx(self, frame, t):
        for f in self.fx:
            if not (f["t"] <= t < f["t"] + f["dur"]):
                continue
            k = 1 - (t - f["t"]) / f["dur"]
            if f["kind"] == "flash":
                frame = np.clip(frame.astype(np.float32) + f.get("gain", 160) * k, 0, 255).astype(np.uint8)
            elif f["kind"] == "rgb":
                frame = draw.rgb_split(frame, int(round(f.get("px", 10) * k)))
            elif f["kind"] == "dim":
                frame = (frame.astype(np.float32) * (1 - f.get("amount", 0.5))).astype(np.uint8)
        return frame

    # ------------------------------------------------------------------ frame
    def board_frame(self, fi):
        t = fi / self.fps
        C = self.camera_at(t)
        frame = np.empty((self.H, self.W, 3), np.uint8)
        vis = [it for it in self.items if t >= it["t_in"] - 1e-6 and (it.get("t_gone") is None or t < it["t_gone"])]
        start = 0
        for i in range(len(vis) - 1, -1, -1):  # thẻ clip phủ kín màn hình → không cần vẽ những gì nằm dưới nó
            it = vis[i]
            if it["kind"] == "media" and self.appear(it, t)[2] >= 0.999 and self._covers(it, C):
                start = i
                break
        if start == 0:
            surface.draw_bg(frame, self.bg, C, self.tok)
            surface.draw_grid(frame, C, self.tok, self.ww, self.wh)
        else:
            frame[:] = 0
        for it in vis[start:]:
            self.draw_item(frame, it, t, fi, C)
        self.draw_marks(frame, t, C)
        frame = self.draw_overlays(frame, t)
        frame = self.apply_fx(frame, t)
        return frame

    def _covers(self, it, C):
        x0, y0, x1, y1 = it["_rect"]
        pts = [draw.local_to_screen(p, (it["x"], it["y"]), it.get("rot", 0), 1.0, C, self.W, self.H)
               for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        return draw._covers(np.array(pts), self.W, self.H)

    def frame(self, fi):
        """Frame hoàn chỉnh (BGR uint8): bảng + đoạn chèn phim câm (iris) + hậu kỳ."""
        t = fi / self.fps
        for ins, v in self.inserts:
            f0, n = int(ins["f0"]), int(ins["n"])
            if f0 <= fi < f0 + n:
                j = fi - f0
                lt = j / self.fps
                kin, kout = ins.get("iris_in", 0.3), ins.get("iris_out", 0.35)
                k = 1.0
                if lt < kin:
                    k = M.smooth(lt / kin)
                if (n - j) / self.fps < kout:
                    k = min(k, M.smooth((n - j - 1) / self.fps / kout))
                film = v.frame(j)
                if k >= 0.999:
                    return film
                if ins.get("iris_bg") == "black":  # đường `cuts`: iris trên nền đen, mở sẵn một phần (không đen kịt)
                    km = float(ins.get("iris_min", 0.4))
                    return vintage.iris(film, np.zeros_like(film), km + (1 - km) * k)
                board = self.post.apply(self.board_frame(fi), fi)
                board = (board.astype(np.float32) * 0.55).astype(np.uint8)
                return vintage.iris(film, board, k)
        out = self.post.apply(self.board_frame(fi), fi)
        if t < self.b.get("fade_in", 0):
            out = (out.astype(np.float32) * (t / self.b["fade_in"])).astype(np.uint8)
        return out
