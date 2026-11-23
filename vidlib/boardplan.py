"""storyboard + timeline + mốc từ VO → projects/<slug>/work/board/board.json cho engine board (engines/board/).

Đây là "đạo diễn" của ngữ pháp evidence board (kaz-documentary) dịch sang kênh thí nghiệm. KHÔNG có mốc thời gian
nào viết tay: mọi thời điểm suy ra từ timeline (đã khớp VO) và từ khoá trong lời đọc (`sync: "vo_word:<từ>"`).

beat_recipe (từng shot) → vật trên bảng + camera + dấu đỏ:
  REVEAL_PHOTO   thẻ polaroid chứa clip Flow / cảnh three.js / ảnh → thả xuống nảy nhẹ; `fill` (mặc định true):
                 camera đẩy vào tới khi clip lấp kín khung → chiếu toàn màn hình → kéo ra ở beat sau
  DOC_FOCUS      lướt nhanh tới trang sổ thí nghiệm (board.lines), khoanh đỏ cụm từ (board.circle) đúng lúc đọc
  NUMBER_CARD    thẻ số lớn (board.number "1,000°C"), count-up từ board.from giữa hai đường kẻ
  NAME_TAG       nhãn băng dính đen chữ đánh máy + dây đỏ tới điểm trên vật (board.text, board.at [u, v])
  CONNECT        dây đỏ nối nguyên nhân → kết quả (board.from = id shot, board.to = id shot | "self")
  STAMP          con dấu đỏ đóng mạnh (board.text: CONFIRMED / MYTH / DON'T TRY THIS) — tối đa 2 / video
  HIGHLIGHT_LINE nét cọ đỏ quét qua cụm chữ trên trang giấy (board.phrase)
  THESIS         dòng mono "You'd think…" bị gạch đỏ → câu serif đúng + chấm đỏ (board.old/new) — mặc định cho twist
  NETWORK_REVEAL kéo ra thấy cả bảng, mọi nhãn quay lại — ngay trước outro
  COUNTER        đồng hồ / nhiệt kế số (board.label, from, to, unit, decimals, jitter)
  TITLE_GLITCH   thẻ "Next: …" glitch rồi về đen (outro của board_spine)
  SILENT_FILM    đoạn chèn phim câm (board.film = spec của engines/board/vintage.py), vào/ra bằng iris
`board.marks` (mọi recipe): thêm tag / circle / stamp / string / highlight neo vào vật của beat.
Toạ độ `at` = [u, v] chuẩn hoá trên phần nội dung của vật (ảnh của thẻ clip, mặt thẻ chữ).
"""
import math
import os

from engines.board import fonts as bfonts
from engines.board import sprites

from . import codeshot, lang, textstyle
from . import storyboard as sbm
from .common import FPS, H, ROOT, W, channel, save_json
from .textfx import _fold

DEFAULTS = {
    "media_photo_w": 480, "cell": [780, 1150], "cell_landscape": [1000, 720], "margin": 260,
    "tag_px": 36, "tag_fade_sec": 3.0, "mark_draw_frames": 8, "react_lead_frames": 2,
    "move_sec": [0.38, 0.62], "network_move_sec": 0.9, "drift_zoom_per_sec": 0.035, "fill_overscan": 1.025,
    "frame_frac": [0.84, 0.6], "string_sec": 0.6, "min_read_sec": 0.7, "max_cps": 45, "stamp_px": 0.6, "max_stamps": 2,
    "crf": 17, "workers": 0,
    "size": None, "anim": {"drop_sec": 0.45, "stamp_sec": 0.2, "tag_cps": 22},
}


def cfg():
    c = dict(DEFAULTS)
    c.update(channel().get("board") or {})
    return c


def tokens(style):
    st = textstyle.load_style(style)
    return st.get("board") or textstyle.load_style("board-black")["board"]


def assembly(sb, style):
    """board_spine | cuts — storyboard.assembly ('auto' → theo style)."""
    a = sb.get("assembly") or "auto"
    if a in ("board_spine", "cuts"):
        return a
    return textstyle.load_style(style).get("assembly") or "cuts"


def validate_shot(s):
    errs = []
    r = sbm.recipe_of(s)
    b = s.get("board") or {}
    tag = s.get("id", "?")
    if r == "NUMBER_CARD" and not b.get("number"):
        errs.append(f"{tag}: NUMBER_CARD cần board.number (vd \"1,000°C\").")
    if r == "THESIS" and not (b.get("old") or b.get("new") or b.get("continue")):
        errs.append(f"{tag}: THESIS cần board.old + board.new.")
    if r == "DOC_FOCUS" and not b.get("lines"):
        errs.append(f"{tag}: DOC_FOCUS cần board.lines (các dòng của trang sổ).")
    if r == "SILENT_FILM" and not (b.get("film") or {}).get("panels"):
        errs.append(f"{tag}: SILENT_FILM cần board.film.panels (tableau + intertitle).")
    if b.get("image"):
        try:
            image_path(None, b["image"])
        except FileNotFoundError as ex:
            errs.append(f"{tag}: {ex}")
    if r == "STAMP" and not (b.get("text") or b.get("stamp")):
        errs.append(f"{tag}: STAMP cần board.text (CONFIRMED / MYTH / DON'T TRY THIS).")
    for m in b.get("marks") or []:
        if m.get("kind") not in ("tag", "circle", "stamp", "string", "highlight"):
            errs.append(f"{tag}: board.marks kind '{m.get('kind')}' không hợp lệ (tag|circle|stamp|string|highlight).")
    return errs


def image_path(proj, p):
    """board.image: đường dẫn tương đối dự án, rồi tương đối gốc repo (vd assets/user/leidenfrost.jpg)."""
    for base in ([proj] if proj else []) + [ROOT]:
        q = p if os.path.isabs(p) else os.path.join(base, p)
        if os.path.exists(q):
            return q
    raise FileNotFoundError(f"không thấy ảnh '{p}' (đặt ảnh public domain vào assets/user/ hoặc thư mục dự án)")


def _frames(t):
    return int(math.ceil(t * FPS - 1e-6))


class Plan:
    def __init__(self, proj, sb, tl, vo, style, media, size=None):
        self.c = cfg()
        self.proj, self.sb, self.tl, self.vo, self.style = proj, sb, tl, vo, style
        self.W, self.H = size or tuple(self.c.get("size") or (W, H))
        self.portrait = self.H >= self.W
        self.tok = tokens(style)
        self.media = media or {}
        self.asm = assembly(sb, style)
        self.items, self.marks, self.fx, self.cues, self.keys, self.overlays, self.inserts = [], [], [], [], [], [], []
        self.qa_marks, self.notes = [], []
        self.by_sid = {}
        self.returns = None
        self.lead = max(0, min(3, int(self.c.get("react_lead_frames", channel()["vo"].get("react_lead_default", 2)))))
        sz = channel()["safe_zone"] if self.portrait else {"top": 60, "bottom": 80, "left": 80, "right_icons_x": self.W - 80}
        self.safe = (sz.get("left", 60), sz.get("top", 220), min(self.W - 60, sz.get("right_icons_x", self.W - 60) + 40),
                     self.H - sz.get("bottom", 384))
        pw = float(self.c["media_photo_w"]) if self.portrait else float(self.c["media_photo_w"]) * 16 / 9
        self.photo = (pw, pw * self.H / self.W)
        self.n_stamps = 0
        self.par = 0
        self.reads = []
        self.cur_hold, self.cur_sid = 0.0, ""

    # ------------------------------------------------------------------ helpers
    def shot_idx(self, sid):
        return next(i for i, s in enumerate(self.sb["shots"]) if s["id"] == sid)

    def word_time(self, spec, sid, t0, t1):
        """'vo_word:<từ>' | 't:<giây trong shot>' → (thời điểm tuyệt đối của TỪ, từ) hoặc (None, None)."""
        if not spec:
            return None, None
        for part in [p.strip() for p in str(spec).split("|") if p.strip()]:
            if part.startswith("t:"):
                return t0 + float(part[2:]), None
            if part.startswith("vo_word:") and self.vo:
                want = _fold(part.split(":", 1)[1])
                idx = self.shot_idx(sid)
                lines = [ln for ln in self.vo["lines"] if idx in ln["shots"]] or self.vo["lines"]
                for ln in lines:
                    for w in ln["words"]:
                        if want and want in _fold(w["w"]) and t0 - 0.15 <= w["start"] < t1 + 0.05:
                            return w["start"], w["w"]
        return None, None

    def onset(self, spec, sid, t0, t1, default_after=0.25, what=""):
        """Thời điểm dấu đỏ/nhãn BẮT ĐẦU hiện: lead frame trước từ khoá (0–3 frame), lượng tử theo frame."""
        tw, word = self.word_time(spec, sid, t0, t1)
        if tw is None:
            if spec and str(spec).startswith("vo_word:"):
                self.notes.append(f"{sid}: không tìm thấy từ khoá '{spec}' trong lời đọc của shot — "
                                  f"dùng t0+{default_after}s.")
            f = _frames(t0 + default_after)
            return f / FPS
        wf = _frames(tw)
        f = max(_frames(t0), wf - self.lead)
        if what:
            self.qa_marks.append({"sid": sid, "what": what, "word": word, "word_t": round(tw, 3), "word_f": wf,
                                  "onset_f": f, "lead_f": wf - f})
        return f / FPS

    def cue(self, t, name):
        self.cues.append({"t": round(max(0.0, t), 3), "name": name})

    # ------------------------------------------------------------------ layout
    def plan_slots(self, beats):
        n = sum(1 for b in beats if b["slot"])
        cw, ch = self.c["cell"] if self.portrait else self.c["cell_landscape"]
        a = self.W / self.H
        cols = max(1, min(n, round(math.sqrt(max(1, n) * a * ch / cw)) or 1))
        rows = max(1, math.ceil(n / cols))
        m = self.c["margin"]
        ww, wh = cols * cw + 2 * m, rows * ch + 2 * m
        if ww / wh < a:
            ww = wh * a
        else:
            wh = ww / a
        self.cell, self.cols, self.rows = (cw, ch), cols, rows
        self.world = (round(ww), round(wh))
        self.grid0 = ((ww - cols * cw) / 2, (wh - rows * ch) / 2)
        self.slot_i = 0

    def next_slot(self, seed):
        i = self.slot_i
        self.slot_i += 1
        r, c = divmod(i, self.cols)
        if r % 2:
            c = self.cols - 1 - c
        cw, ch = self.cell
        jx = ((seed * 37) % 61 - 30) * 1.4
        jy = ((seed * 53) % 71 - 35) * 1.4
        rot = ((seed * 29) % 11 - 5) * 0.9
        if abs(rot) < 1.5:
            rot = 2.0 if seed % 2 else -2.0
        return self.grid0[0] + (c + 0.5) * cw + jx, self.grid0[1] + (r + 0.5) * ch + jy, rot

    def content_box(self, it):
        """(x0, y0, x1, y1) cục bộ quanh tâm vật: phần nội dung (ảnh của thẻ clip / mặt thẻ)."""
        if it["kind"] == "media":
            return tuple(it["_rect"])
        return (-it["w"] / 2, -it["h"] / 2, it["w"] / 2, it["h"] / 2)

    def local_to_world(self, it, p):
        r = math.radians(it.get("rot", 0))
        return (it["x"] + p[0] * math.cos(r) - p[1] * math.sin(r), it["y"] + p[0] * math.sin(r) + p[1] * math.cos(r))

    def uv(self, it, at):
        x0, y0, x1, y1 = self.content_box(it)
        return self.local_to_world(it, (x0 + (x1 - x0) * at[0], y0 + (y1 - y0) * at[1]))

    def corners(self, it):
        if it["kind"] == "media":
            cw, ch, _ = sprites.media_geom(*it["photo"], self.tok)
        else:
            cw, ch = it["w"], it["h"]
        return [self.local_to_world(it, (sx * cw / 2, sy * ch / 2)) for sx in (-1, 1) for sy in (-1, 1)]

    # ------------------------------------------------------------------ camera poses
    def fit_pose(self, pts, frac=None, rot=0.0):
        fx, fy = frac or self.c["frame_frac"]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        sx0, sy0, sx1, sy1 = self.safe
        bw, bh = max(bw, 1), max(bh, 1)
        z = min(fx * self.W / bw, fy * self.H / bh, 0.98 * (sx1 - sx0) / bw, 0.98 * (sy1 - sy0) / bh)
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        scx, scy = (sx0 + sx1) / 2, (sy0 + sy1) / 2  # tâm vùng an toàn trên màn hình
        return {"cx": cx - (scx - self.W / 2) / z, "cy": cy - (scy - self.H / 2) / z, "zoom": z, "rot": rot}

    def fill_pose(self, it):
        pw, ph = it["photo"]
        z = max(self.W / pw, self.H / ph) * self.c["fill_overscan"]
        x0, y0, x1, y1 = it["_rect"]
        cx, cy = self.local_to_world(it, ((x0 + x1) / 2, (y0 + y1) / 2))
        return {"cx": cx, "cy": cy, "zoom": z, "rot": it.get("rot", 0.0)}

    def network_pose(self):
        ww, wh = self.world
        return {"cx": ww / 2, "cy": wh / 2, "zoom": min(self.W / ww, self.H / wh) * 0.98, "rot": 0.0}

    def drifted(self, pose, sec, k):
        z = pose["zoom"] * (1 + self.c["drift_zoom_per_sec"] * sec)
        dx = (14 if k % 2 else -14) * sec / max(pose["zoom"], 0.3)
        return {**pose, "zoom": z, "cx": pose["cx"] + dx, "cy": pose["cy"] - 6 * sec / max(pose["zoom"], 0.3),
                "rot": pose["rot"] + (0.25 if k % 2 else -0.25) * sec}

    def pose_at(self, t):
        from engines.board import camera as bcam  # noqa: PLC0415
        cur = bcam.at(self.keys, t)
        return {"cx": cur[0], "cy": cur[1], "zoom": cur[2], "rot": cur[3]}

    def continue_drift(self, t0, t1, rate=1.0):
        """Beat nối tiếp trên CÙNG vật (clip nối liền, luận điểm 2 câu, phim câm): trôi tiếp, không di chuyển mới."""
        last = self.keys[-1]
        if last["t"] > t0 + 1e-6:  # bỏ key trôi cũ vượt quá t0 (sẽ nối dài)
            cur = self.pose_at(t0)
            self.keys.pop()
            self.key(t0, cur, last["ease"])
        cur = self.pose_at(t0)
        self.key(t1, self.drifted(cur, (t1 - t0) * rate, self.par), "linear")

    def key(self, t, pose, ease):
        k = {"t": round(t, 4), "cx": round(pose["cx"], 2), "cy": round(pose["cy"], 2), "zoom": round(pose["zoom"], 5),
             "rot": round(pose["rot"], 3), "ease": ease}
        if self.keys and abs(self.keys[-1]["t"] - k["t"]) < 1e-4:
            self.keys[-1] = k
        else:
            self.keys.append(k)

    def move_to(self, t, pose, t_end, k, md=None, whoosh=True, ease="easeOut"):
        """Cặp key 'di chuyển ngắn' (t → t+md) + 'trôi chậm' (→ t_end). Camera không bao giờ đứng yên."""
        if self.keys:
            from engines.board import camera as bcam  # noqa: PLC0415
            cur = bcam.at(self.keys, t)
            cur_pose = {"cx": cur[0], "cy": cur[1], "zoom": cur[2], "rot": cur[3]}
            self.key(t, cur_pose, self.keys[-1]["ease"] if self.keys[-1]["t"] >= t else "linear")
            dist = math.hypot(pose["cx"] - cur[0], pose["cy"] - cur[1]) * min(pose["zoom"], cur[2]) / self.H \
                + abs(math.log(pose["zoom"] / cur[2])) * 0.6
        else:
            dist = 0.0
        lo, hi = self.c["move_sec"]
        md = md if md is not None else lo + (hi - lo) * min(1.0, dist / 1.2)
        md = min(md, max(0.2, (t_end - t) * 0.6))
        self.par = k
        self.key(t + md, pose, ease)
        self.key(t_end, self.drifted(pose, t_end - t - md, k), "linear")
        if whoosh and dist > 0.15:
            self.cue(t, "whoosh" if dist < 1.2 else "whoosh_soft")
        return md

    # ------------------------------------------------------------------ items
    def add_item(self, it):
        it.setdefault("z", len(self.items))
        self.items.append(it)
        return it

    def image_item(self, b, shot):
        """Ảnh tĩnh người dùng đưa vào (vd chân dung public domain trong assets/user/) → thẻ ảnh trên bảng."""
        from PIL import Image  # noqa: PLC0415
        sid = shot["id"]
        bd = shot["board"]
        path = image_path(self.proj, bd["image"])
        with Image.open(path) as im:
            iw, ih = im.size
        side, bottom = self.tok.get("card_border", [16, 64])
        w = float(bd.get("w", 560 if self.portrait else 700))
        h = (w - 2 * side) * ih / iw + side + bottom
        x, y, rot = self.next_slot(sum(map(ord, sid)))
        it = self.add_item({"id": sid, "kind": "image", "x": round(x, 1), "y": round(y, 1), "rot": rot,
                            "t_in": b["t0"], "w": w, "h": round(h, 2), "gray": bool(bd.get("gray", False)),
                            "path": os.path.relpath(path, ROOT).replace(os.sep, "/")})
        self.by_sid[sid] = it
        return it

    def media_item(self, b, shot, prev):
        sid = shot["id"]
        if shot["board"].get("image"):
            return self.image_item(b, shot)
        src = self.media.get(sid)
        if not src:
            self.notes.append(f"{sid}: chưa có frame của clip/cảnh code — thẻ hiện khung trống.")
            src = {"dir": os.path.relpath(os.path.join(self.proj, "work", "board", "media", sid), ROOT), "n": 1}
        seg = {"dir": src["dir"].replace("\\", "/"), "f0": b["seg"]["start_f"], "n": int(src["n"])}
        cont = prev and prev.get("kind") == "media" and b["continues"]
        if cont:
            prev["src"]["segments"].append(seg)
            self.by_sid[sid] = prev
            return prev
        x, y, rot = self.next_slot(sum(map(ord, sid)))
        it = {"id": sid, "kind": "media", "x": round(x, 1), "y": round(y, 1), "rot": rot, "t_in": b["t0"],
              "photo": [round(self.photo[0], 2), round(self.photo[1], 2)], "caption": shot["board"].get("caption", ""),
              "src": {"segments": [seg]}}
        it["_rect"] = sprites.media_geom(*it["photo"], self.tok)[2]
        self.by_sid[sid] = self.add_item(it)
        return it

    def paper_item(self, b, shot):
        sid = shot["id"]
        bd = shot["board"]
        lines = []
        for k, ln in enumerate(bd.get("lines") or []):
            if isinstance(ln, str):
                ln = {"text": ln, "role": "serif" if k == 0 else "mono", "size": 50 if k == 0 else 38}
            lines.append(ln)
        w = float(bd.get("w", 640 if self.portrait else 760))
        lay, h = sprites.paper_layout(lines, w, self.tok)
        h = max(h, float(self.tok.get("paper_min_h", 160)))
        x, y, rot = self.next_slot(sum(map(ord, sid)))
        it = self.add_item({"id": sid, "kind": "paper", "x": round(x, 1), "y": round(y, 1), "rot": rot, "t_in": b["t0"],
                            "w": w, "h": round(h, 2), "lines": lines, "paper_kind": self.tok.get("paper_kind", "paper")})
        it["_lay"] = lay
        self.by_sid[sid] = it
        return it

    def phrase_box(self, it, phrase):
        """Khung (cục bộ quanh tâm) của cụm từ trên tờ giấy — để khoanh / gạch đúng chữ."""
        want = phrase.lower()
        for ln in it["_lay"]:
            i = ln["text"].lower().find(want)
            if i >= 0:
                bx = ln["boxes"]
                x0, x1 = bx[i][0], bx[i + len(phrase) - 1][1]
                return (x0 - it["w"] / 2, ln["top"] - it["h"] / 2, x1 - it["w"] / 2, ln["top"] + ln["h"] - it["h"] / 2)
        self.notes.append(f"{it['id']}: không thấy cụm '{phrase}' trên trang giấy — bỏ dấu đỏ.")
        return None

    def card_item(self, b, shot, kind, w, h, extra):
        sid = shot["id"]
        x, y, rot = self.next_slot(sum(map(ord, sid)))
        it = self.add_item({"id": sid, "kind": kind, "x": round(x, 1), "y": round(y, 1), "rot": rot * 0.6,
                            "t_in": b["t0"], "w": w, "h": h, **extra})
        self.by_sid[sid] = it
        return it

    # ------------------------------------------------------------------ marks
    def tag_mark(self, it, text, at, t0, pose, fade=None, key=None):
        z = pose["zoom"]
        size = self.c["tag_px"] / z
        tw, th = sprites.tag_size(text, size)
        A = self.uv(it, at)
        from engines.board import camera as bcam  # noqa: PLC0415
        C = (pose["cx"], pose["cy"], z, pose["rot"])
        sa = bcam.to_screen(A, C, self.W, self.H)
        sx0, sy0, sx1, sy1 = self.safe
        dx, dy = self.c.get("tag_offset_px", [96, -150])
        right = sa[0] < (sx0 + sx1) / 2
        qx = sa[0] + dx if right else sa[0] - dx - tw * z
        qy = sa[1] + dy
        qx = max(sx0, min(sx1 - tw * z, qx))
        qy = max(sy0 + th * z / 2, min(sy1 - th * z / 2, qy))
        pos = bcam.to_world((qx, qy), C, self.W, self.H)
        # gõ đủ nhanh để nhãn còn ≥ min_read giây đọc trước khi camera rời vật (từ khoá hay nằm cuối câu)
        t_end = self.cur_hold
        base = self.c["anim"]["tag_cps"]
        avail = t_end - t0 - self.c["min_read_sec"]
        cps = base if avail <= 0 else min(self.c["max_cps"], max(base, len(text) / avail))
        typed = t0 + len(text) / cps
        m = {"kind": "tag", "text": text, "anchor": [round(A[0], 1), round(A[1], 1)],
             "pos": [round(pos[0], 1), round(pos[1], 1)], "size": round(size, 3), "side": "right" if right else "left",
             "t0": round(t0, 4), "rot": pose["rot"], "cps": round(cps, 2), "t_end": round(t_end, 4),
             "t_fade": round(max(t0 + (fade if fade is not None else self.c["tag_fade_sec"]), min(t_end, t0 + 4.0)), 3),
             "item": it["id"]}
        self.marks.append(m)
        self.reads.append({"what": f"nhãn '{text}'", "sid": self.cur_sid, "read_sec": round(t_end - typed, 2)})
        if t_end - typed < self.c["min_read_sec"] - 0.05:
            self.notes.append(f"{self.cur_sid}: nhãn '{text}' chỉ còn {t_end - typed:.2f}s để đọc (đã gõ nhanh nhất "
                              f"{cps:.0f} ký tự/giây) — chọn từ khoá sớm hơn hoặc rút ngắn nhãn.")
        self.cue(t0, f"typing:{min(2.0, round(len(text) / cps, 1))}")
        return m

    def circle_mark(self, c, rx, ry, rot, t0, width, item_id):
        dur = self.c["mark_draw_frames"] / FPS
        self.marks.append({"kind": "circle", "c": [round(c[0], 1), round(c[1], 1)], "rx": round(rx, 1), "ry": round(ry, 1),
                           "rot": rot, "t0": round(t0, 4), "dur": round(dur, 4), "width": width, "seed": len(self.marks),
                           "item": item_id})
        self.cue(t0, f"scratch:{round(max(0.2, dur), 1)}")

    def stamp_mark(self, it, text, at, t0, pose, rot=-12):
        if self.n_stamps >= self.c["max_stamps"]:
            self.notes.append(f"{it['id']}: bỏ con dấu '{text}' — tối đa {self.c['max_stamps']} con dấu / video.")
            return
        self.n_stamps += 1
        z = pose["zoom"]
        w1, _ = sprites.stamp_size(text, 100)
        size = 100 * self.c["stamp_px"] * self.W / z / w1
        c = self.uv(it, at)
        self.marks.append({"kind": "stamp", "text": text, "c": [round(c[0], 1), round(c[1], 1)], "rot": rot + pose["rot"],
                           "size": round(size, 2), "t0": round(t0, 4), "item": it["id"], "t_end": round(self.cur_hold, 4)})
        read = round(self.cur_hold - t0 - self.c["anim"]["stamp_sec"], 2)
        self.reads.append({"what": f"con dấu '{text}'", "sid": self.cur_sid, "read_sec": read})
        if read < self.c["min_read_sec"]:
            self.notes.append(f"{self.cur_sid}: con dấu '{text}' chỉ còn {read:.2f}s để đọc trước khi camera rời — "
                              "chọn từ khoá sớm hơn trong câu (sync).")
        hit = t0 + self.c["anim"]["stamp_sec"] * 0.6
        self.cue(hit, "stamp")
        self.fx += [{"kind": "shake", "t": round(hit, 3), "dur": 0.3, "amp": 12},
                    {"kind": "rgb", "t": round(hit, 3), "dur": 0.2, "px": 10}]

    def string_mark(self, a_it, b_it, t0):
        A = self.uv(a_it, (0.5, 0.42))
        B = self.uv(b_it, (0.5, 0.42))
        dur = self.c["string_sec"]
        self.marks.append({"kind": "string", "a": [round(A[0], 1), round(A[1], 1)], "b": [round(B[0], 1), round(B[1], 1)],
                           "t0": round(t0, 4), "dur": dur, "sag": 40, "width": 4})
        self.cue(t0, "whoosh_soft")
        return t0 + dur

    def generic_marks(self, b, it, pose):
        shot = b["shot"]
        marks = list(shot["board"].get("marks") or [])
        if not marks and self.asm == "board_spine" and shot.get("text_fx"):
            marks = self.fx_as_tags(shot)
        for m in marks:
            k = m.get("kind")
            t0 = self.onset(m.get("sync"), shot["id"], b["t0"], b["t1"], m.get("t", 0.3), f"{k} '{m.get('text', '')}'")
            target = self.by_sid.get(m.get("on"), it) if m.get("on") else it
            if target is None:
                continue
            if k == "tag":
                self.tag_mark(target, m["text"], m.get("at", [0.5, 0.5]), t0, pose)
            elif k == "circle":
                x0, y0, x1, y1 = self.content_box(target)
                c = self.uv(target, m.get("at", [0.5, 0.5]))
                ru, rv = m.get("r", [0.18, 0.1])
                self.circle_mark(c, ru * (x1 - x0), rv * (y1 - y0), target.get("rot", 0), t0, 5, target["id"])
            elif k == "stamp":
                self.stamp_mark(target, m["text"], m.get("at", [0.62, 0.2]), t0, pose, m.get("rot", -12))
            elif k == "string":
                other = self.by_sid.get(m.get("from"))
                if other:
                    self.string_mark(other, target, t0)
            elif k == "highlight" and target["kind"] == "paper":
                self.highlight(target, m.get("phrase", ""), t0)

    @staticmethod
    def fx_as_tags(shot):
        """text_fx (đường cắt) → nhãn băng dính trên bảng (board_spine). Bỏ chữ tượng thanh (role sfx)."""
        out = []
        for fx in shot.get("text_fx") or []:
            if fx.get("role") == "sfx" or int(fx.get("tier") or 1) != 1 or not fx.get("text"):
                continue
            anc = str(fx.get("anchor") or "")
            at = fx.get("pos") or ([0.5, 0.3] if anc.startswith("above") else [0.5, 0.75] if anc.startswith("below")
                                   else [0.5, 0.5])
            out.append({"kind": "tag", "text": str(fx["text"]).upper(), "at": at,
                        "sync": fx.get("sync") or f"t:{float(fx.get('t_in') or 0.2):.2f}"})
        return out

    def highlight(self, it, phrase, t0):
        box = self.phrase_box(it, phrase)
        if not box:
            return
        x0, y0, x1, y1 = box
        ym = (y0 + y1) / 2 + (y1 - y0) * 0.08
        a, b = self.local_to_world(it, (x0 - 8, ym)), self.local_to_world(it, (x1 + 8, ym))
        dur = self.c["mark_draw_frames"] / FPS
        self.marks.append({"kind": "highlight", "a": [round(a[0], 1), round(a[1], 1)], "b": [round(b[0], 1), round(b[1], 1)],
                           "h": round((y1 - y0) * 0.95, 1), "t0": round(t0, 4), "dur": round(dur, 4), "alpha": 0.42})
        self.cue(t0, f"scratch:{round(max(0.2, dur), 1)}")

    # ------------------------------------------------------------------ beats
    def classify(self):
        shots = {s["id"]: s for s in self.sb["shots"]}
        beats, prev = [], None
        for seg in self.tl["segments"]:
            t0, t1 = seg["start_f"] / FPS, (seg["start_f"] + seg["n"]) / FPS
            if seg["sid"] == "OUTRO":
                beats.append({"sid": "OUTRO", "seg": seg, "t0": t0, "t1": t1, "recipe": "TITLE_GLITCH", "slot": False,
                              "shot": None, "continues": False})
                continue
            s = shots[seg["sid"]]
            r = sbm.recipe_of(s)
            media = sbm.has_media(s) and not sbm.board_native(s)
            cont = bool(prev and ((s.get("start_frame") or {}).get("seed_from") == prev["sid"]
                                  or s.get("transition_in") == "match" or s["board"].get("continue"))
                        and prev.get("media") and media)
            thesis_cont = r == "THESIS" and prev and prev["recipe"] == "THESIS" and not s["board"].get("old")
            slot = (media and not cont) or r in ("DOC_FOCUS", "NUMBER_CARD", "COUNTER") or (r == "THESIS"
                                                                                            and not thesis_cont)
            if self.asm == "cuts" and media and not s["board"].get("image"):
                slot = False
            slot = bool(slot)
            b = {"sid": s["id"], "seg": seg, "t0": t0, "t1": t1, "recipe": r, "shot": s, "media": media,
                 "continues": cont or thesis_cont, "slot": slot}
            beats.append(b)
            prev = b
        return beats

    def build(self):
        beats = self.classify()
        self.plan_slots(beats)
        target = None
        k = 0
        for i, b in enumerate(beats):
            r, t0, t1 = b["recipe"], b["t0"], b["t1"]
            shot = b["shot"]
            j = i  # camera ở lại vật này tới hết chuỗi beat nối tiếp (clip nối liền, luận điểm 2 câu)
            while j + 1 < len(beats) and beats[j + 1]["continues"]:
                j += 1
            self.cur_hold, self.cur_sid = beats[j]["t1"], b["sid"]
            if b["sid"] == "OUTRO":
                self.outro(b, i, beats)
                continue
            bd = shot["board"]
            first = not self.keys
            if self.asm == "cuts" and b["media"] and not bd.get("image"):
                continue  # đường `cuts`: clip/cảnh three.js do render.py dựng; board chỉ vẽ shot board thuần
            pose = None
            if b["media"]:
                it = self.media_item(b, shot, target)
                fill = bd.get("fill", r == "REVEAL_PHOTO") and it["kind"] == "media"
                pose = self.fill_pose(it) if fill else self.fit_pose(self.corners(it), rot=it["rot"] * 0.5)
                if r == "CONNECT" and not b["continues"] and not first:
                    it["t_in"] = round(max(0.0, t0 - 0.05), 4)
                    target = self.connect(b, it, k)
                    pose = self.fill_pose(it) if fill else pose
                elif b["continues"]:
                    self.continue_drift(t0, t1)
                    pose = self.pose_at(min(t1, t0 + 0.5))
                elif first:
                    it["reveal"] = "none"
                    it["t_in"] = 0.0
                    start = pose if fill else {**pose, "zoom": pose["zoom"] * 0.88}
                    self.key(0.0, start, "linear")
                    self.move_to(0.0, pose, t1, k, md=0.0 if fill else 0.5, whoosh=False)
                else:
                    it["t_in"] = round(max(0.0, t0 - 0.05), 4)
                    self.move_to(t0, pose, t1, k)
                target = it
                if r == "STAMP":
                    t_s = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.4, f"stamp '{bd.get('text')}'")
                    self.stamp_mark(it, bd.get("text") or bd.get("stamp"), bd.get("at", [0.6, 0.18]), t_s, pose)
                if r == "NAME_TAG":
                    t_s = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.3, f"tag '{bd.get('text')}'")
                    self.tag_mark(it, bd["text"], bd.get("at", [0.5, 0.5]), t_s, pose)
            elif r == "DOC_FOCUS":
                it = self.paper_item(b, shot)
                pose = self.fit_pose(self.corners(it), rot=it["rot"] * 0.7)
                self.begin(b, it, pose, k, first)
                if bd.get("circle"):
                    box = self.phrase_box(it, bd["circle"])
                    if box:
                        t_s = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.5, f"circle '{bd['circle']}'")
                        x0, y0, x1, y1 = box
                        c = self.local_to_world(it, ((x0 + x1) / 2, (y0 + y1) / 2))
                        self.circle_mark(c, (x1 - x0) / 2 + 26, (y1 - y0) / 2 + 22, it["rot"], t_s, 5, it["id"])
                if bd.get("highlight"):
                    t_h = self.onset(bd.get("highlight_sync"), b["sid"], t0, t1, 0.9, f"highlight '{bd['highlight']}'")
                    self.highlight(it, bd["highlight"], t_h)
                target = it
            elif r == "NUMBER_CARD":
                w, h = (680, 460) if self.portrait else (760, 420)
                it = self.card_item(b, shot, "number", w, h, {"text": bd["number"], "from": bd.get("from"),
                                                              "caption": bd.get("caption", ""), "sub": bd.get("sub", ""),
                                                              "size": bd.get("size", 150)})
                pose = self.fit_pose(self.corners(it), rot=it["rot"] * 0.7)
                self.begin(b, it, pose, k, first)
                tc = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.25, f"number '{bd['number']}'")
                it["count_t0"], it["count_dur"] = round(tc, 4), bd.get("count_sec", 0.55)
                self.cue(tc, "tick")
                self.fx.append({"kind": "flash", "t": round(tc, 3), "dur": 0.18, "gain": 60})
                target = it
            elif r == "COUNTER":
                w, h = (600, 400) if self.portrait else (700, 380)
                it = self.card_item(b, shot, "counter", w, h, {"label": bd.get("label", ""), "from": bd.get("from", 0),
                                                               "to": bd.get("to", 0), "unit": bd.get("unit", ""),
                                                               "decimals": bd.get("decimals", 1),
                                                               "jitter": bd.get("jitter", 0), "size": bd.get("size", 118)})
                pose = self.fit_pose(self.corners(it), rot=it["rot"] * 0.7)
                self.begin(b, it, pose, k, first)
                tc = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.25, f"counter '{bd.get('label', '')}'")
                it["t0"], it["dur"] = round(tc, 4), bd.get("count_sec", 0.8)
                self.cue(tc, "tick")
                target = it
            elif r == "THESIS":
                if b["continues"] and target is not None and target.get("kind") == "thesis":
                    it = target
                    pose = self.fit_pose(self.corners(it), rot=it["rot"] * 0.7)
                    self.continue_drift(t0, t1)
                else:
                    w, h = (760, 560) if self.portrait else (1000, 480)
                    old = bd.get("old", "")
                    new = bd.get("new", "")
                    it = self.card_item(b, shot, "thesis", w, h, {
                        "old": old, "new": new,
                        "old_size": round(min(46.0, 0.86 * w * 100 / max(1.0, bfonts.width(old, "mono", 100))), 2),
                        "new_size": round(min(104.0, 0.84 * w * 100 / max(1.0, bfonts.width(new + ".", "serif", 100))), 2)})
                    pose = self.fit_pose(self.corners(it), rot=it["rot"] * 0.7)
                    self.begin(b, it, pose, k, first)
                    it["t_old"] = round(t0 + 0.12, 4)
                    self.cue(t0 + 0.12, f"typing:{round(min(2.0, len(it['old']) / 18), 1)}")
                if bd.get("strike_sync"):
                    ts = self.onset(bd["strike_sync"], b["sid"], t0, t1, 0.8, "thesis strike")
                    it["t_strike"] = round(ts, 4)
                    self.cue(ts, "scratch:0.3")
                    if it.get("t_old") is not None:  # dòng cũ phải gõ XONG trước khi bị gạch
                        avail = max(0.3, ts - 0.2 - it["t_old"])
                        it["old_cps"] = round(max(self.c["anim"].get("thesis_cps_old", 18), len(it["old"]) / avail), 2)
                if bd.get("new_sync"):
                    tn = self.onset(bd["new_sync"], b["sid"], t0, t1, 1.2, f"thesis '{it['new']}'")
                    it["t_new"] = round(tn, 4)
                    self.cue(tn, f"typing:{round(min(2.0, len(it['new']) / 14), 1)}")
                    it["t_dot"] = round(tn + len(it["new"]) / 14 + 0.05, 4)
                    self.cue(it["t_dot"], "thud")
                target = it
            elif r == "NETWORK_REVEAL":
                self.network(t0, t1, k)
            elif r == "SILENT_FILM":
                self.silent(b)
                if self.keys:
                    self.continue_drift(t0, t1)
            elif r == "TITLE_GLITCH":
                self.overlays.append({"kind": "title_glitch", "t0": round(t0, 4), "t1": round(t1, 4),
                                      "title_lines": self.wrap_title(bd.get("title", "")), "sub": bd.get("sub", "")})
            elif r in sbm.MARK_RECIPES:  # dấu đỏ trên một vật đã có (board.on hoặc vật của beat trước)
                it = self.by_sid.get(bd.get("on")) or target
                if it is None:
                    self.notes.append(f"{b['sid']}: {r} không có vật để gắn — bỏ qua.")
                    continue
                pose = self.fit_pose(self.corners(it), rot=it.get("rot", 0) * 0.6) if it["kind"] != "media" or \
                    not bd.get("fill", False) else self.fill_pose(it)
                self.move_to(t0, pose, t1, k)
                if r == "STAMP":
                    t_s = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.4, f"stamp '{bd.get('text')}'")
                    self.stamp_mark(it, bd.get("text"), bd.get("at", [0.6, 0.18]), t_s, pose)
                elif r == "NAME_TAG":
                    t_s = self.onset(bd.get("sync"), b["sid"], t0, t1, 0.3, f"tag '{bd.get('text')}'")
                    self.tag_mark(it, bd["text"], bd.get("at", [0.5, 0.5]), t_s, pose)
                elif r == "HIGHLIGHT_LINE" and it["kind"] == "paper":
                    self.highlight(it, bd.get("phrase", ""), self.onset(bd.get("sync"), b["sid"], t0, t1, 0.3,
                                                                       f"highlight '{bd.get('phrase')}'"))
                elif r == "CONNECT":
                    target = self.connect(b, it, k)
                    continue
                target = it
            if pose is not None and target is not None:
                self.generic_marks(b, target, pose)
            if shot.get("transition_in") == "flash" and i > 0:
                self.fx += [{"kind": "flash", "t": round(t0, 3), "dur": 0.25, "gain": 170},
                            {"kind": "rgb", "t": round(t0, 3), "dur": 0.2, "px": 8}]
                if shot.get("beat") == "payoff":
                    self.fx.append({"kind": "shake", "t": round(t0, 3), "dur": 0.35, "amp": 14})
            for x in shot.get("sfx") or []:
                if isinstance(x, str):
                    self.cue(t0 + 0.02, x)
            k += 1
        self.finish()

    def begin(self, b, it, pose, k, first):
        if first:
            it["reveal"] = "none"
            it["t_in"] = 0.0
            self.key(0.0, {**pose, "zoom": pose["zoom"] * 0.9}, "linear")
            self.move_to(0.0, pose, b["t1"], k, md=0.5, whoosh=False)
        else:
            it["t_in"] = round(max(0.0, b["t0"] - 0.05), 4)
            self.move_to(b["t0"], pose, b["t1"], k)

    def connect(self, b, to_it, k):
        """CONNECT: khung cả hai vật → dây đỏ kéo A→B đúng từ khoá → đẩy vào B (lấp khung nếu là clip)."""
        shot = b["shot"]
        bd = shot["board"]
        src = self.by_sid.get(bd.get("from"))
        t0, t1 = b["t0"], b["t1"]
        if bd.get("to") and bd["to"] != "self":
            to_it = self.by_sid.get(bd["to"], to_it)
        if src is None:
            self.notes.append(f"{shot['id']}: CONNECT không thấy board.from='{bd.get('from')}'.")
            return to_it
        both = self.fit_pose(self.corners(src) + self.corners(to_it), frac=(0.9, 0.7))
        ts = self.onset(bd.get("sync"), shot["id"], t0, t1, 0.5, f"connect {src['id']}→{to_it['id']}")
        t_end = self.string_mark(src, to_it, ts)
        t_push = min(t1 - 0.5, t_end + 0.2)
        if t_push > t0 + 0.6 and to_it["kind"] == "media" and bd.get("fill", True):
            self.move_to(t0, both, t_push, k)
            self.move_to(t_push, self.fill_pose(to_it), t1, k + 1)
        else:
            self.move_to(t0, both, t1, k)
        return to_it

    def network(self, t0, t1, k):
        pose = self.network_pose()
        md = min(self.c["network_move_sec"], max(0.4, (t1 - t0) * 0.7))
        self.move_to(t0, pose, t1, k, md=md, ease="smooth")
        self.returns = {"t": round(t0 + md * 0.35, 4), "dur": 0.5}
        self.qa_network = (t0, t1)

    def silent(self, b):
        shot = b["shot"]
        spec = dict(shot["board"].get("film") or {})
        n = b["seg"]["n"]
        self.inserts.append({"id": shot["id"], "f0": b["seg"]["start_f"], "n": n, "spec": spec,
                             "iris_in": spec.get("iris_in", 0.3), "iris_out": spec.get("iris_out", 0.35),
                             "iris_bg": "board" if self.asm == "board_spine" else "black",
                             "iris_min": 0.0 if self.asm == "board_spine" else 0.4,  # cuts: không có đoạn đen chết
                             "tokens": tokens("silent-film-black")})
        self.cue(b["t0"], f"projector:{round(n / FPS, 1)}")
        for p in spec.get("panels") or []:
            for a in p.get("actors") or []:
                if isinstance(a.get("t0"), str) and a["t0"].startswith("vo_word:"):
                    tw = self.onset(a["t0"], shot["id"], b["t0"], b["t1"], 0.5, f"film {a.get('kind')}")
                    a["t0"] = round(tw - b["t0"] - self._panel_start(spec, p, n), 4)

    @staticmethod
    def _panel_start(spec, panel, n):
        total = n / FPS
        want = sum(float(p.get("dur", 1.0)) for p in spec["panels"]) or 1.0
        t = 0.0
        for p in spec["panels"]:
            if p is panel:
                return t
            t += float(p.get("dur", 1.0)) * total / want
        return 0.0

    def wrap_title(self, s, size=104):
        words, lines, cur = s.split(), [], ""
        maxw = self.W * 0.84
        for w_ in words:
            test = (cur + " " + w_).strip()
            if bfonts.width(test, "serif", size) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w_
        if cur:
            lines.append(cur)
        return lines

    def outro(self, b, i, beats):
        o = self.sb.get("outro", {})
        t0, t1 = b["t0"], b["t1"]
        tstart = t0
        if self.returns is None and self.asm == "board_spine":  # chưa có NETWORK_REVEAL → kéo ra đầu outro
            mid = t0 + (t1 - t0) * 0.4
            self.network(t0, mid, i)
            tstart = mid
        elif self.keys:
            self.continue_drift(t0, t1, -0.6)
        title = f"{lang.copy('next_prefix')} {o.get('teaser') or lang.copy('endscreen_title')}"
        self.overlays.append({"kind": "title_glitch", "t0": round(tstart, 4), "t1": round(t1, 4),
                              "title_lines": self.wrap_title(title), "sub": o.get("follow_text") or lang.copy("follow"),
                              "glitch_at": 0.0, "glitch_sec": 0.45, "fade_out": 0.3, "size": 104, "y": 0.42})
        self.outro_title = title

    def finish(self):
        if self.keys and self.keys[0]["t"] > 0:
            self.keys.insert(0, {**self.keys[0], "t": 0.0})
        total = self.tl["frames"] / FPS
        if self.keys and self.keys[-1]["t"] < total:
            last = self.keys[-1]
            self.key(total, self.drifted({k: last[k] for k in ("cx", "cy", "zoom", "rot")}, total - last["t"], 0), "linear")
        self.keys.sort(key=lambda k: k["t"])
        self.cues.sort(key=lambda c: c["t"])

    # ------------------------------------------------------------------ output
    def to_json(self):
        items = [{k: v for k, v in it.items() if not k.startswith("_")} for it in self.items]
        return {"version": 1, "engine": "board", "style": self.style, "assembly": self.asm, "width": self.W,
                "height": self.H, "fps": FPS, "frames": self.tl["frames"],
                "world": {"w": self.world[0], "h": self.world[1]}, "surface": self.tok,
                "anim": self.c["anim"], "camera": self.keys, "items": items, "marks": self.marks, "fx": self.fx,
                "overlays": self.overlays, "inserts": self.inserts, "returns": self.returns, "cues": self.cues,
                "qa": {"marks": self.qa_marks, "reads": self.reads, "notes": self.notes, "lead_frames": self.lead,
                       "network": getattr(self, "qa_network", None), "texts": self.texts()}}

    def texts(self):
        """Mọi chuỗi khán giả thấy do engine board vẽ (QA: đủ glyph + OCR)."""
        out = []
        for it in self.items:
            if it["kind"] == "paper":
                out += [{"where": f"{it['id']} trang giấy", "text": ln["text"], "role": ln.get("role", "mono")}
                        for ln in it["lines"] if ln.get("text")]
            elif it["kind"] == "number":
                out.append({"where": f"{it['id']} thẻ số", "text": it["text"], "role": "serif"})
                for k in ("caption", "sub"):
                    if it.get(k):
                        out.append({"where": f"{it['id']} thẻ số ({k})", "text": it[k], "role": "mono"})
            elif it["kind"] == "thesis":
                out += [{"where": f"{it['id']} luận điểm (cũ)", "text": it["old"], "role": "mono"},
                        {"where": f"{it['id']} luận điểm (mới)", "text": it["new"] + ".", "role": "serif"}]
            elif it["kind"] == "counter":
                out.append({"where": f"{it['id']} đồng hồ", "text": it.get("label", ""), "role": "mono"})
            elif it["kind"] == "media" and it.get("caption"):
                out.append({"where": f"{it['id']} chú thích thẻ", "text": it["caption"], "role": "mono"})
        for m in self.marks:
            if m["kind"] in ("tag", "stamp"):
                out.append({"where": f"{m.get('item', '')} {m['kind']}", "text": m["text"],
                            "role": "mono" if m["kind"] == "tag" else "serif"})
        for o in self.overlays:
            out += [{"where": "tiêu đề cuối", "text": s, "role": "serif"} for s in o.get("title_lines") or []]
            if o.get("sub"):
                out.append({"where": "tiêu đề cuối (phụ)", "text": o["sub"], "role": "mono"})
        for ins in self.inserts:
            for p in ins["spec"].get("panels") or []:
                for s in p.get("lines") or []:
                    out.append({"where": f"{ins['id']} intertitle", "text": s, "role": "serif"})
                if p.get("kicker"):
                    out.append({"where": f"{ins['id']} intertitle", "text": p["kicker"], "role": "mono"})
                if p.get("title"):
                    out.append({"where": f"{ins['id']} tableau", "text": p["title"], "role": "serif"})
                for a in p.get("actors") or []:
                    if a.get("kind") in ("label", "text") and a.get("text"):
                        out.append({"where": f"{ins['id']} {a['kind']}", "text": a["text"], "role": a.get("role", "mono")})
        for t in out:
            t["missing"] = bfonts.missing(t["text"], t["role"])
        return [t for t in out if t["text"].strip()]


# ---------------------------------------------------------------------- media frames
def media_dir(proj, sid):
    return os.path.join(proj, "work", "board", "media", sid)


def media_sources(proj, sb, tl, trims, ingested, extract=True, log=print):
    """Frame nguồn cho mọi thẻ clip: clip Flow (đã trim, resample đúng n frame) → work/board/media/<sid>/fNNNN.jpg;
    cảnh three.js → work/code/<sid>/frames. Trả về {sid: {dir (tương đối ROOT), n}}."""
    from PIL import Image  # noqa: PLC0415

    from . import render  # noqa: PLC0415
    from .common import load_json  # noqa: PLC0415
    out = {}
    segs = {s["sid"]: s for s in tl["segments"]}
    for s in sb["shots"]:
        sid = s["id"]
        seg = segs.get(sid)
        if not seg or sbm.board_native(s) or (s.get("board") or {}).get("image"):
            continue
        n = seg["n"]
        if codeshot.is_3d(s):
            out[sid] = {"dir": os.path.relpath(codeshot.frames_dir(proj, sid), ROOT), "n": n}
            continue
        d = media_dir(proj, sid)
        out[sid] = {"dir": os.path.relpath(d, ROOT), "n": n}
        if not extract:
            continue
        vid = ingested(sid)
        tr = trims.get(sid) if trims else None
        key = f"{vid and os.path.getmtime(vid):.0f}|{tr and (tr['in'], tr['out'])}|{n}|{s['start_frame'].get('file')}"
        mp = os.path.join(d, "_key.json")
        if load_json(mp, {}).get("key") == key and os.path.exists(os.path.join(d, f"f{n - 1:04d}.jpg")):
            continue
        os.makedirs(d, exist_ok=True)
        src, kind = render.make_source(proj, s, seg, trims or {}, ingested)
        for j in range(n):
            im = src.frame(j)
            if im.size != (W, H):
                im = im.resize((W, H), Image.LANCZOS)
            im.save(os.path.join(d, f"f{j:04d}.jpg"), quality=94)
        src.close()
        save_json(mp, {"key": key, "kind": kind})
        log(f"  · media {sid}: {n} frame ({kind}) → {os.path.relpath(d, proj)}")
    return out


def build(proj, sb, tl, vo, style, media, size=None):
    """Sinh board.json (work/board/board.json). Trả về (đường dẫn, dict)."""
    p = Plan(proj, sb, tl, vo, style, media, size)
    p.build()
    data = p.to_json()
    path = os.path.join(proj, "work", "board", "board.json")
    save_json(path, data)
    return path, data


def native_ids(sb):
    return [s["id"] for s in sb["shots"] if sbm.board_native(s)]
