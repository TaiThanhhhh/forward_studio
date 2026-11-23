"""QA cho engine board (vòng 6): bảng lệch frame dấu đỏ/nhãn ↔ từ khoá, glyph (không ô vuông), màu BGR (đỏ vẫn là
đỏ), đứng hình (camera + hoạt ảnh), OCR từng chữ do engine vẽ — cắt đúng vùng chữ trong frame thật.

Chạy được TRƯỚC render đầy đủ (frame lấy từ Scene — look-check) và SAU render (frame giải mã từ out/final.mp4).
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image

from engines.board import camera as bcam
from engines.board import color as bcol
from engines.board import fonts as bfonts
from engines.board import sprites

from .common import FPS, ffbin


# ------------------------------------------------------------------ lệch frame
def mark_rows(board):
    """Mỗi vòng tròn / nhãn / dấu: frame từ khoá, frame dấu bắt đầu hiện, lệch (phải 0–3 frame TRƯỚC từ khoá)."""
    rows = []
    for m in board["qa"]["marks"]:
        rows.append({**m, "ok": 0 <= m["lead_f"] <= 3})
    return rows


def glyph_rows(board):
    return [{"where": t["where"], "text": t["text"], "role": t["role"], "missing": t["missing"], "ok": not t["missing"]}
            for t in board["qa"]["texts"]]


# ------------------------------------------------------------------ đứng hình
def _cam(board, t):
    C = list(bcam.at(board["camera"], t))
    for f in board.get("fx") or []:
        if f["kind"] == "shake" and f["t"] <= t < f["t"] + f["dur"]:
            k = (1 - (t - f["t"]) / f["dur"]) * f.get("amp", 14)
            C[0] += k * math.sin(t * 90) / C[2]
            C[1] += k * math.cos(t * 77) / C[2]
    return tuple(C)


def activity(board, f):
    """Có thứ gì đang chuyển động ngoài camera ở frame f (clip đang chạy, dấu đang vẽ, chữ đang gõ, phim câm…)?"""
    t = f / FPS
    for ins in board.get("inserts") or []:
        if ins["f0"] <= f < ins["f0"] + ins["n"]:
            return "phim câm (twos)"
    for m in board["marks"]:
        if m["kind"] == "tag" and m["t0"] <= t <= m["t0"] + len(m["text"]) / board["anim"].get("tag_cps", 22) + 0.1:
            return "gõ nhãn"
        if m["kind"] in ("circle", "highlight", "string") and m["t0"] <= t <= m["t0"] + m.get("dur", 0.3):
            return "vẽ dấu"
        if m["kind"] == "stamp" and m["t0"] <= t <= m["t0"] + 0.25:
            return "đóng dấu"
    for o in board.get("overlays") or []:
        if o["t0"] <= t <= o["t1"] and (t - o["t0"] < 0.8 or o["t1"] - t < o.get("fade_out", 0.35)):
            return "tiêu đề"
    return None


def stills(board, thr_px=0.35):
    """Đoạn dài nhất camera gần như đứng (dịch < thr_px px/frame ở mọi góc màn hình). Trả về (giây, từ, tới)."""
    W, H = board["width"], board["height"]
    best, cur, start = 0, 0, 0
    run_start = 0
    prev = _cam(board, 0.0)
    for f in range(1, int(board["frames"])):
        C = _cam(board, f / FPS)
        px = bcam.motion_px(prev, C, W, H)
        prev = C
        if px < thr_px and not activity(board, f):
            if cur == 0:
                start = f
            cur += 1
            if cur > best:
                best, run_start = cur, start
        else:
            cur = 0
    return best / FPS, run_start / FPS, (run_start + best) / FPS


def camera_px_stats(board):
    W, H = board["width"], board["height"]
    vals = []
    prev = _cam(board, 0.0)
    for f in range(1, int(board["frames"])):
        C = _cam(board, f / FPS)
        vals.append(bcam.motion_px(prev, C, W, H))
        prev = C
    v = np.array(vals)
    return {"min_px": round(float(v.min()), 3), "median_px": round(float(np.median(v)), 3),
            "max_px": round(float(v.max()), 1)}


# ------------------------------------------------------------------ màu (BGR ↔ RGB)
def color_rows(board, get_frame):
    """Lấy mẫu pixel đúng trên nét vòng tròn / dây đỏ / tiêu đề cuối trong frame thật → kênh R phải trội.
    Nếu đảo BGR, đỏ #d0312d sẽ thành xanh lam (B trội)."""
    acc = bcol.rgb(board["surface"].get("accent", "#d0312d"))
    W, H = board["width"], board["height"]
    rows = []
    picks = [m for m in board["marks"] if m["kind"] in ("circle", "string")][:3]
    for m in picks:
        t = m["t0"] + m.get("dur", 0.3) + 0.15
        f = int(math.ceil(t * FPS))
        C = _cam(board, f / FPS)
        if m["kind"] == "circle":
            from engines.board.draw import wobble_ellipse_pts  # noqa: PLC0415
            pts = wobble_ellipse_pts(m["c"], m["rx"], m["ry"], m.get("rot", 0), 1.0, m.get("seed", 0))
        else:
            from engines.board.draw import string_pts  # noqa: PLC0415
            pts = string_pts(m["a"], m["b"], 1.0, m.get("sag", 30))
        rgb = bcol.to_rgb(get_frame(f))
        samp = []
        for p in pts:
            x, y = bcam.to_screen(p, C, W, H)
            xi, yi = int(round(x)), int(round(y))
            if 2 <= xi < W - 2 and 2 <= yi < H - 2:
                samp.append(rgb[yi - 1:yi + 2, xi - 1:xi + 2].reshape(-1, 3).max(0))
        if not samp:
            continue
        s = np.array(samp, np.float32)
        red = (s[:, 0] > s[:, 2] + 40) & (s[:, 0] > s[:, 1] + 40)
        blue = (s[:, 2] > s[:, 0] + 40)
        rows.append({"where": f"{m['kind']} {m.get('item', '')} · frame {f}", "expect_rgb": acc,
                     "median_rgb": tuple(int(v) for v in np.median(s, 0)), "red_share": round(float(red.mean()), 2),
                     "blue_share": round(float(blue.mean()), 2), "ok": bool(red.mean() >= 0.5 and blue.mean() < 0.1)})
    return rows


# ------------------------------------------------------------------ OCR
def _item(board, iid):
    return next((it for it in board["items"] if it["id"] == iid), None)


def _poly(center, rot, box):
    r = math.radians(rot)
    x0, y0, x1, y1 = box
    out = []
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        out.append((center[0] + x * math.cos(r) - y * math.sin(r), center[1] + x * math.sin(r) + y * math.cos(r)))
    return out


def _txt_box(text, role, size, off, anchor="center"):
    w = bfonts.width(text, role, size)
    asc, desc = bfonts.metrics(role, size)
    h = asc + desc
    x0 = off[0] if anchor == "left" else off[0] - w / 2
    return (x0, off[1] - h / 2, x0 + w, off[1] + h / 2)


def text_targets(board):
    """[(nơi, chuỗi, role, màu chữ hex, frame, đa giác world | ('screen', box))] cho mọi chữ engine board vẽ."""
    tok = board["surface"]
    light, dim = tok.get("text_light", "#ecebe4"), tok.get("text_dim", "#a3a29b")
    out = []
    cps = board["anim"].get("tag_cps", 22)
    for it in board["items"]:
        c, rot = (it["x"], it["y"]), it.get("rot", 0)
        if it["kind"] == "number":
            f = math.ceil((it.get("count_t0", it["t_in"]) + it.get("count_dur", 0.6) + 0.35) * FPS)
            h = it["h"]
            out.append((f"{it['id']} thẻ số", it["text"], "serif", light, f,
                        _poly(c, rot, _txt_box(it["text"], "serif", it.get("size", 150), (0, h * 0.06)))))
            if it.get("caption"):
                out.append((f"{it['id']} thẻ số (nhãn)", it["caption"], "mono", dim, f,
                            _poly(c, rot, _txt_box(it["caption"], "mono", it.get("caption_size", 34), (0, -h * 0.30)))))
        elif it["kind"] == "thesis":
            h, w = it["h"], it["w"]
            so = it.get("old_size", 40)
            t_old_done = it.get("t_old", it["t_in"]) + len(it["old"]) / (it.get("old_cps") or 18) + 0.08
            f = math.ceil(min(t_old_done, (it.get("t_strike") or 1e9) - 0.05) * FPS)
            out.append((f"{it['id']} luận điểm (cũ)", it["old"], "mono", dim, f,
                        _poly(c, rot, _txt_box(it["old"], "mono", so, (-bfonts.width(it["old"], "mono", so) / 2, -h * 0.2),
                                               "left"))))
            if it.get("t_dot"):
                sn = it.get("new_size", 74)
                wn = bfonts.width(it["new"] + ".", "serif", sn)
                out.append((f"{it['id']} luận điểm (mới)", it["new"], "serif", light, math.ceil((it["t_dot"] + 0.3) * FPS),
                            _poly(c, rot, _txt_box(it["new"], "serif", sn, (-wn / 2, h * 0.14), "left"))))
        elif it["kind"] == "paper":
            lay, hh = sprites.paper_layout(it["lines"], it["w"], tok)
            hh = it["h"]
            first = min([m["t0"] for m in board["marks"] if m.get("item") == it["id"]] or [it["t_in"] + 1.2])
            f = math.ceil(max(it["t_in"] + 0.6, first - 0.06) * FPS)
            ink = tok.get("ink", "#1b1b1b") if it.get("paper_kind", "paper") == "paper" else light
            for ln in lay:
                box = (ln["x"] - it["w"] / 2, ln["top"] - hh / 2, ln["boxes"][-1][1] - it["w"] / 2,
                       ln["top"] + ln["h"] - hh / 2)
                out.append((f"{it['id']} trang giấy", ln["text"], ln["role"], ink, f, _poly(c, rot, box)))
        elif it["kind"] == "counter":
            f = math.ceil((it.get("t0", it["t_in"]) + 0.9) * FPS)
            if it.get("label"):
                out.append((f"{it['id']} đồng hồ (nhãn)", it["label"], "mono", dim, f,
                            _poly(c, rot, _txt_box(it["label"], "mono", it.get("label_size", 30), (0, -it["h"] * 0.30)))))
    for m in board["marks"]:
        if m["kind"] == "tag":
            tw, th = sprites.tag_size(m["text"], m["size"])
            done = m["t0"] + len(m["text"]) / (m.get("cps") or cps)
            f = math.ceil(min(done + 0.25, m.get("t_end", 1e9) - 2 / FPS) * FPS)  # lúc đọc được, trước khi camera rời đi
            pad = 0.45 * m["size"]
            out.append((f"{m.get('item', '')} nhãn", m["text"], "mono", tok.get("tape_text", "#ecebe4"), f,
                        _poly(m["pos"], m.get("rot", 0), (pad * 0.5, -th / 2 + 2, tw - pad * 0.5, th / 2 - 2)),
                        m.get("rot", 0), -2))
        elif m["kind"] == "stamp":
            sw, sh = sprites.stamp_size(m["text"], m["size"])
            f = math.ceil(min(m["t0"] + 0.6, m.get("t_end", 1e9) - 2 / FPS) * FPS)
            out.append((f"{m.get('item', '')} con dấu", m["text"], "serif", tok.get("accent", "#d0312d"), f,
                        _poly(m["c"], m.get("rot", -12), (-sw / 2, -sh / 2, sw / 2, sh / 2)), m.get("rot", -12), -4))
    W, H = board["width"], board["height"]
    for o in board.get("overlays") or []:
        size = o.get("size", 112)
        lines = o.get("title_lines") or []
        y = H * o.get("y", 0.40) - len(lines) * size * 0.6
        f = math.ceil(min(o["t0"] + 0.9, o["t1"] - o.get("fade_out", 0.35) - 0.1) * FPS)
        for s in lines:
            w = bfonts.width(s, "serif", size)
            out.append(("tiêu đề cuối", s, "serif", tok.get("accent", "#d0312d"), f,
                        ("screen", (W / 2 - w / 2 - 10, y - size * 0.7, W / 2 + w / 2 + 10, y + size * 0.7))))
            y += size * 1.15
        if o.get("sub"):
            sz = o.get("sub_size", 36)
            w = bfonts.width(o["sub"], "mono", sz)
            yy = y + size * 0.15
            out.append(("tiêu đề cuối (phụ)", o["sub"], "mono", tok.get("text_light", "#ecebe4"), f,
                        ("screen", (W / 2 - w / 2 - 10, yy - sz, W / 2 + w / 2 + 10, yy + sz))))
    for ins in board.get("inserts") or []:  # intertitle: cả khung chữ
        panels = ins["spec"].get("panels") or []
        total = ins["n"] / FPS
        want = sum(float(p.get("dur", 1.0)) for p in panels) or 1.0
        t = 0.0
        for p in panels:
            d = float(p.get("dur", 1.0)) * total / want
            if p.get("kind") == "intertitle":
                f = ins["f0"] + int((t + d * 0.45) * FPS)
                txt = "\n".join(([p["kicker"]] if p.get("kicker") else []) + list(p.get("lines") or []))
                out.append((f"{ins['id']} intertitle", txt, "serif", tok.get("film_ink", "#d9d9d4"), f,
                            ("screen", (W * 0.09, H * 0.3, W * 0.91, H * 0.7))))
            t += d
    return out


def _crop(frame_rgb, poly, C, W, H, rot=None, pad=14):
    """Cắt vùng chữ. rot (độ, world) → xoay ngược để chữ nằm ngang trước khi OCR (con dấu nghiêng, thẻ nghiêng)."""
    if isinstance(poly, tuple) and poly and poly[0] == "screen":
        x0, y0, x1, y1 = poly[1]
    else:
        pts = [bcam.to_screen(p, C, W, H) for p in poly]
        if rot is not None:
            ang = rot - C[3]
            cx, cy = sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4
            w, h = math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])
            R = int(max(w, h) / 2 + 40)
            big = np.zeros((2 * R, 2 * R, 3), np.uint8)
            bx0, by0 = int(cx) - R, int(cy) - R
            sx0, sy0, sx1, sy1 = max(0, bx0), max(0, by0), min(W, bx0 + 2 * R), min(H, by0 + 2 * R)
            if sx1 <= sx0 or sy1 <= sy0:
                return None, (0, 0, 0, 0)
            big[sy0 - by0:sy1 - by0, sx0 - bx0:sx1 - bx0] = frame_rgb[sy0:sy1, sx0:sx1]
            im = Image.fromarray(big).rotate(ang, resample=Image.BICUBIC, center=(cx - bx0, cy - by0))
            c0, c1 = (cx - bx0, cy - by0)
            box = (int(c0 - w / 2 - pad), int(c1 - h / 2 - pad), int(c0 + w / 2 + pad), int(c1 + h / 2 + pad))
            return im.crop(box), (int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))
        x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
        x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
    x0, y0 = max(0, int(x0 - pad)), max(0, int(y0 - pad))
    x1, y1 = min(W, int(x1 + pad)), min(H, int(y1 + pad))
    if x1 - x0 < 8 or y1 - y0 < 8:
        return None, (x0, y0, x1, y1)
    return Image.fromarray(frame_rgb[y0:y1, x0:x1]), (x0, y0, x1, y1)


def _chroma_prep(crop, fill):
    """Chữ màu (đỏ accent) trên nền rối: chiếu mỗi pixel lên hướng màu của chữ → Otsu → đen trên trắng. Bền với
    yuv420 (kênh màu bị nhoè khi nén) hơn cách so khoảng cách màu."""
    import cv2  # noqa: PLC0415
    a = np.asarray(crop.convert("RGB")).astype(np.float32)
    f = np.array(fill, np.float32)
    fc = f - f.mean()
    score = ((a - a.mean(-1, keepdims=True)) * fc).sum(-1) / (np.linalg.norm(fc) + 1e-6)
    _, m = cv2.threshold(np.clip(score * 2, 0, 255).astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = 255 - cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    h, w = m.shape
    m = cv2.resize(m, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    return Image.fromarray(cv2.copyMakeBorder(m, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255))


def ocr_rows(board, get_frame, out_dir):
    """OCR từng chữ: (1) sprite sạch cùng font (chứng minh font vẽ đúng chuỗi), (2) vùng chữ cắt từ frame thật."""
    from . import ocr  # noqa: PLC0415
    from .qareport import _similar, _similar_in  # noqa: PLC0415
    os.makedirs(out_dir, exist_ok=True)
    W, H = board["width"], board["height"]
    avail = ocr.available()
    rows = []
    cache = {}
    for k, tgt in enumerate(text_targets(board)):
        where, text, role, fill, f, poly = tgt[:6]
        rot, pad = (tgt[6], tgt[7]) if len(tgt) > 6 else (None, 14)
        f = max(0, min(int(board["frames"]) - 1, int(f)))
        if f not in cache:
            cache[f] = bcol.to_rgb(get_frame(f))
        C = _cam(board, f / FPS)
        crop, box = _crop(cache[f], poly, C, W, H, rot, pad)
        lines = [ln for ln in text.split("\n") if ocr.norm(ln)]
        miss = bfonts.missing(text.replace("\n", " "), role)
        clean_s, frame_s, found = 0.0, 0.0, ""
        if crop is not None:
            crop.save(os.path.join(out_dir, f"{k:02d}_{where.split()[0]}_{f:05d}.png"))
        if avail:
            spr = sprites.text(text.replace("\n", " "), role, 64, "#ffffff", Dd=1.0)
            a = spr.arr
            clean = Image.fromarray(np.dstack([a[..., 2], a[..., 1], a[..., 0]]))
            got, _ = ocr.read(clean, fill=(255, 255, 255))
            clean_s = 1.0 if ocr.matches(got, text.replace("\n", " ")) else _similar(got, text.replace("\n", " "))
            if crop is not None:
                rgb = bcol.rgb(fill)
                for psm in ((6, 11) if len(lines) > 1 else (7, 6)):
                    if len(lines) > 1:
                        got = " ".join(w["text"] for w in ocr._run(ocr.prepare(crop, None), psm, ocr.langmod.ocr_lang()))
                        s = min(1.0 if ocr.norm(ln) in ocr.norm(got) else _similar_in(got, ln) for ln in lines)
                    else:
                        got, _ = ocr.read(crop, fill=rgb, psm=psm)
                        s = 1.0 if ocr.matches(got, text) else max(_similar(got, text), _similar_in(got, text))
                    if s >= frame_s:
                        frame_s, found = s, got or found
                    if s >= 1.0:
                        break
                sat = max(rgb) - min(rgb) > 80
                if frame_s < 1.0 and sat and len(lines) == 1:
                    for psm in (6, 13):
                        got = " ".join(w["text"] for w in ocr._run(_chroma_prep(crop, rgb), psm, ocr.langmod.ocr_lang()))
                        s = 1.0 if ocr.matches(got, text) else max(_similar(got, text), _similar_in(got, text))
                        if s >= frame_s:
                            frame_s, found = s, got or found
                        if s >= 1.0:
                            break
        n = len(ocr.norm(text))
        legible = frame_s >= 0.7 or (0 < n <= 5 and frame_s >= (n - 1) / n - 1e-6)
        rows.append({"where": where, "expected": text.replace("\n", " / "), "frame": f, "found": (found or "")[:60],
                     "glyph_ok": not miss, "missing": miss, "ocr_clean": round(clean_s, 3), "ocr_frame": round(frame_s, 3),
                     "exact": frame_s >= 0.999, "ok": not miss and legible, "box": box})
    return {"available": avail, "total": len(rows), "ok": sum(r["ok"] for r in rows),
            "exact": sum(r["exact"] for r in rows), "glyph_ok": sum(r["glyph_ok"] for r in rows), "rows": rows}


# ------------------------------------------------------------------ nguồn frame
class VideoFrames:
    """Frame giải mã từ video cuối (BGR) — đọc một lượt cho cả danh sách frame cần."""

    def __init__(self, path, frames, W, H):
        self.cache = {}
        want = sorted(set(int(f) for f in frames))
        if not want:
            return
        expr = "+".join(f"eq(n\\,{f})" for f in want)
        # ffmpeg 7+ bỏ -vsync → -fps_mode passthrough (mỗi frame được chọn ra đúng một frame)
        cmd = [ffbin("ffmpeg"), "-v", "error", "-i", path, "-vf", f"select={expr}", "-fps_mode", "passthrough",
               "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            raise RuntimeError("Không trích được frame từ video cuối: " + r.stderr.decode("utf-8", "replace")[-400:])
        size = W * H * 3
        buf = r.stdout
        for k, f in enumerate(want):
            if (k + 1) * size <= len(buf):
                self.cache[f] = np.frombuffer(buf[k * size:(k + 1) * size], np.uint8).reshape(H, W, 3)

    def __call__(self, f):
        if int(f) not in self.cache:  # không âm thầm trả frame đen (QA sẽ báo sai)
            raise KeyError(f"frame {f} không có trong video cuối")
        return self.cache[int(f)]


def frames_needed(board):
    fs = [t[4] for t in text_targets(board)]
    for m in board["marks"]:
        if m["kind"] in ("circle", "string"):
            fs.append(int(math.ceil((m["t0"] + m.get("dur", 0.3) + 0.15) * FPS)))
    return [max(0, min(int(board["frames"]) - 1, int(f))) for f in fs]


def run(board, get_frame, out_dir):
    """Toàn bộ QA board → dict (ghi vào work/board_qa.json, đưa vào report)."""
    sec, a, b = stills(board)
    return {"marks": mark_rows(board), "reads": board["qa"].get("reads", []), "glyphs": glyph_rows(board),
            "color": color_rows(board, get_frame),
            "still": {"longest_sec": round(sec, 3), "from": round(a, 2), "to": round(b, 2), **camera_px_stats(board)},
            "ocr": ocr_rows(board, get_frame, out_dir)}


def summary_checks(q):
    """Các dòng cho bảng 'Kiểm tra' của report."""
    m = q["marks"]
    lead = [r["lead_f"] for r in m]
    g = q["glyphs"]
    c = q["color"]
    o = q["ocr"]
    rd = q.get("reads") or []
    out = {
        "nhãn / con dấu còn ≥ 0.6s để đọc trước khi camera rời": (
            ", ".join(f"{r['what']} {r['read_sec']:.2f}s" for r in rd) or "—", all(r["read_sec"] >= 0.6 for r in rd)),
        "dấu đỏ/nhãn bắt đầu 0–3 frame TRƯỚC từ khoá": (f"{sum(r['ok'] for r in m)}/{len(m)} · lệch {min(lead, default=0)}…"
                                                       f"{max(lead, default=0)} frame", all(r["ok"] for r in m)),
        "không ô vuông (đủ glyph mọi chữ board)": (f"{sum(r['ok'] for r in g)}/{len(g)}", all(r["ok"] for r in g)),
        "màu không đảo BGR (đỏ accent đo trên frame)": (", ".join(f"R{r['median_rgb']}" for r in c) or "—",
                                                       bool(c) and all(r["ok"] for r in c)),
        "camera không đứng ≥ 0.4s (board)": (f"dài nhất {q['still']['longest_sec']:.2f}s · camera ≥ {q['still']['min_px']} "
                                             f"px/frame", q["still"]["longest_sec"] < 0.4),
    }
    if o["available"]:
        out["OCR chữ board (cắt từ frame)"] = (f"{o['ok']}/{o['total']} đọc được · {o['exact']}/{o['total']} khớp 100%",
                                               o["ok"] == o["total"])
    return out
