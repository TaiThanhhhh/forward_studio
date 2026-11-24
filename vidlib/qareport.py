"""QA mở rộng (vòng 5): .srt, freeze/black/qa_sheet (gộp từ finish.sh của cartoon-short-kit), khớp nhìn code↔Flow,
OCR chữ (text_fx + chữ trong cảnh của shot code), publish.md, qa/report.md + qa/report.html (giao diện tiếng Việt)."""
import html
import os
import re

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from . import textstyle
from .common import FPS, channel, probe, run


# ------------------------------------------------------------------ phụ đề .srt (tiếng Anh, cho CC của nền tảng)
def _ts(t):
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(vo, path, max_words=7, max_chars=42):
    """Cụm ≤ max_words từ / ≤ max_chars ký tự, ngắt ở dấu câu — từ mốc từng từ của lời đọc."""
    cues = []
    for ln in vo["lines"]:
        cur = []
        for w in ln["words"]:
            txt = " ".join(x["w"] for x in cur + [w])
            if cur and (len(cur) >= max_words or len(txt) > max_chars):
                cues.append(cur)
                cur = []
            cur.append(w)
            if w["w"].endswith((".", "!", "?", ",", ";", ":")) and len(cur) >= 3:
                cues.append(cur)
                cur = []
        if cur:
            cues.append(cur)
    out = []
    for k, c in enumerate(cues):
        end = c[-1]["end"] if k + 1 == len(cues) else min(c[-1]["end"] + 0.25, cues[k + 1][0]["start"])
        out.append(f"{k + 1}\n{_ts(c[0]['start'])} --> {_ts(end)}\n{' '.join(x['w'] for x in c)}\n")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    return path


# ------------------------------------------------------------------ freeze / black / sheet
def hold_spans(sb, tl):
    hold = {s["id"] for s in sb["shots"] if s.get("hold")}
    return [(g["start_f"] / FPS, (g["start_f"] + g["n"]) / FPS) for g in tl["segments"] if g["sid"] in hold]


def freeze_black(path, holds=(), black_pic_th=None):
    """ffmpeg freezedetect + blackdetect. Freeze ≥ qa.freeze_max_sec là lỗi, trừ khi nằm trong shot hold:true."""
    q = channel().get("qa", {})
    d, n, bd = q.get("freeze_max_sec", 0.4), q.get("freeze_noise", 0.0005), q.get("black_min_sec", 0.05)
    # pic_th: tỉ lệ điểm ảnh tối để coi là "frame đen" (ffmpeg mặc định 0.98). Style nét mảnh trên nền đen (sơ đồ, nét vẽ tay)
    # hợp lệ có < 2% điểm sáng → style đặt qa_black_pic_th cao hơn; frame thật sự trống vẫn bị bắt.
    pic = black_pic_th or q.get("black_pic_th", 0.98)
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-vf", f"freezedetect=n={n}:d={d},blackdetect=d={bd}:pic_th={pic}", "-an",
             "-f", "null", "-"], "ffmpeg (freeze/black)")
    txt = r.stderr.decode("utf-8", "replace")
    fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", txt)]
    fe = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", txt)]
    dur = probe(path)["duration"]
    freezes = [(a, fe[k] if k < len(fe) else dur) for k, a in enumerate(fs)]
    blacks = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", txt)]
    bad = [f for f in freezes if not any(h0 - 0.05 <= f[0] and f[1] <= h1 + 0.05 for h0, h1 in holds)]
    return {"freezes": freezes, "freezes_bad": bad, "blacks": blacks, "threshold_sec": d, "noise": n}


def qa_sheet(path, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", "fps=2,scale=180:-1,tile=10x5", "-frames:v", "1", out],
        "ffmpeg (qa_sheet)")
    return out


# ------------------------------------------------------------------ khớp nhìn code ↔ Flow
def line_weight(img):
    """Độ dày nét mực (px ở khung 1080×1920): trung vị các đoạn tối kẹp giữa hai vùng sáng trên các hàng quét."""
    a = np.asarray(img.convert("L").resize((1080, 1920)), np.int16)
    runs = []
    for y in range(200, 1720, 6):
        row = a[y]
        cls = np.where(row > 200, 2, np.where(row < 50, 0, 1))
        i = 0
        while i < len(row):
            j = i
            while j < len(row) and cls[j] == cls[i]:
                j += 1
            if cls[i] == 0 and i > 0 and j < len(row) and cls[i - 1] == 2 and cls[j] == 2 and j - i < 25:
                runs.append(j - i)
            i = j
    return (float(np.median(runs)) if len(runs) >= 5 else None), len(runs)


def palette_stats(img):
    a = np.asarray(img.convert("RGB").resize((270, 480))).reshape(-1, 3).astype(np.int16)
    mx, mn = a.max(1), a.min(1)
    fg = mx > 60
    blue = (a[:, 2] > 150) & (a[:, 2] > a[:, 0] * 1.6) & (a[:, 2] > a[:, 1] * 1.3)
    neutral = fg & (mx - mn < 30)
    return {"bg_black": round(float((~fg).mean()), 3), "neutral_of_fg": round(float(neutral.sum() / max(fg.sum(), 1)), 3),
            "accent_blue_of_fg": round(float(blue.sum() / max(fg.sum(), 1)), 3),
            "fg_luma_median": round(float(np.median(a[fg].mean(1))) if fg.any() else 0.0, 1)}


def look_metrics(proj, sb, tl, items):
    """So shot code với shot Flow: độ dày nét + palette, đo trên chính các still của contact sheet."""
    rows = []
    for label, im, sid, kind in items:
        lw, n = line_weight(im)
        rows.append({"label": label, "sid": sid, "kind": kind, "line_px": lw, "line_samples": n, **palette_stats(im)})

    def agg(kinds):
        rs = [r for r in rows if r["kind"] in kinds]
        lws = [r["line_px"] for r in rs if r["line_px"]]
        if not rs:
            return None
        return {"n": len(rs), "line_px": round(float(np.median(lws)), 1) if lws else None,
                "neutral_of_fg": round(float(np.median([r["neutral_of_fg"] for r in rs])), 3),
                "bg_black": round(float(np.median([r["bg_black"] for r in rs])), 3),
                "accent_blue_of_fg": round(float(np.median([r["accent_blue_of_fg"] for r in rs])), 3)}
    return {"rows": rows, "flow": agg({"clip", "image"}), "code": agg({"code3d", "outro_code"})}


def look_summary(m):
    f, c = m.get("flow"), m.get("code")
    if not f or not c:
        return "chỉ có một loại nguồn"
    return (f"nét Flow {f['line_px']}px vs code {c['line_px']}px · nền đen {f['bg_black']:.0%} vs {c['bg_black']:.0%} · "
            f"trung tính {f['neutral_of_fg']:.0%} vs {c['neutral_of_fg']:.0%}")


# ------------------------------------------------------------------ OCR


def ocr_report(events, proj, code_jobs, code_texts, out_dir):
    """Kiểm chữ 2 lớp cho MỌI chữ khán giả thấy (text_fx + chữ trong cảnh của shot code):
    1. Tất định — chuỗi hiển thị là chuỗi trong storyboard (code vẽ, không AI) và FONT CÓ ĐỦ GLYPH cho từng ký tự
       (thiếu glyph là cách duy nhất chữ bị sai/mất ký tự) → điều kiện "đúng chính tả 100%".
    2. OCR (Tesseract) — chứng minh chữ ĐỌC ĐƯỢC: sprite sạch / texture phẳng / ảnh cắt trong frame giống ≥ 70%.
       (OCR hay nhầm font display đặc: g→9, °C→°G — nên không dùng OCR làm thước đo chính tả duy nhất.)
    Ghi 3 frame / hiệu ứng vào qa/text_fx/."""
    from . import codeshot, ocr  # noqa: PLC0415
    from .common import FONT_DIR  # noqa: PLC0415
    rows = []
    all_overlaps = []
    all_boxes = []
    os.makedirs(out_dir, exist_ok=True)
    avail = ocr.available()

    def row(where, want, miss, sims, found, overlap=0.0, layer="front"):
        s = max(sims) if sims else 0.0
        n = len(ocr.norm(want))  # chuỗi ngắn (≤ 5 ký tự): cho phép đúng 1 ký tự OCR đọc nhầm (vd C→G ở font đặc)
        legible = s >= 0.7 or (0 < n <= 5 and s >= (n - 1) / n - 1e-6)
        glyph = "đủ glyph" if not miss else "THIẾU glyph " + " ".join(miss)
        rows.append({"where": where, "expected": want.replace(chr(10), " / "), "found": f"{glyph} · OCR giống {s:.0%} · "
                     f"{(found or '').replace(chr(10), ' ')[:40]}", "ok": not miss and legible,
                     "overlap_subject": overlap, "layer": layer, "glyph_ok": not miss, "ocr_sim": round(s, 3)})

    for e in events:
        for k, (_t, im, bbox) in enumerate(e.qa.get("frames", [])[:3]):
            fr = im.copy()
            if bbox:
                ImageDraw.Draw(fr).rectangle([v / 3 for v in bbox], outline=(255, 210, 0), width=2)
            fr.save(os.path.join(out_dir, f"{e.sid}_{e.idx:02d}_{k}.png"))
        want = e.text_at(10.0)
        miss = ocr.missing_glyphs(want, os.path.join(FONT_DIR, e.st["font"]), e.st.get("variation"))
        sims, found = [], ""
        if avail:
            art = textstyle.render(want, e.style, e.size, e.role)
            clean = Image.new("RGB", art.img.size, (0, 0, 0))
            clean.paste(art.img, (0, 0), art.img)
            for img, fill in [(clean, art.fill), (clean, None)] + [(c, art.fill) for _, c in e.qa.get("crops", [])]:
                got, _ = ocr.read(img, fill=fill)
                s = 1.0 if ocr.matches(got, want) else _similar(got, want)
                sims.append(s)
                if s >= max(sims):
                    found = got or found
                if s >= 1.0:
                    break
        ov = e.qa.get("overlap") or [0]
        row(f"{e.sid} text_fx", want, miss, sims, found, round(float(max(ov)), 3), e.layer)
    for sid, job in (code_jobs or {}).items():
        if not (code_texts or {}).get(sid):
            continue
        jd = json_load(job)
        n = int(jd.get("frames", 1))
        font = os.path.join(FONT_DIR, os.path.basename(jd["fonts"][0]["url"])) if jd.get("fonts") else None
        best = {}
        qa_frames = jd.get("qa_frames") or sorted({n // 2, n - 1})   # cú máy liền: frame camera đứng yên
        audit_fn = getattr(codeshot, "text_audit", None)
        if callable(audit_fn):
            audit = audit_fn(job, qa_frames)
            crops_list = audit.get("crops") or []
            for ov in audit.get("overlaps") or []:
                all_overlaps.append({"sid": sid, **ov})
            for bx in audit.get("boxes") or []:
                all_boxes.append({"sid": sid, **bx})
        else:
            crops_list = codeshot.text_crops(job, qa_frames)
        for f, want, crop, tex in crops_list:  # engine báo khung bao từng chữ
            crop.save(os.path.join(out_dir, f"{sid}_scene_{f:04d}_{len(best):02d}.png"))
            lines = [ln for ln in want.split(chr(10)) if ocr.norm(ln)]
            miss = ocr.missing_glyphs(want.replace(chr(10), " "), font) if font else []
            sims, found = [], ""
            if avail:
                imgs = ([tex, ImageOps.invert(tex)] if tex is not None else []) + [_plate_text(crop)]
                for img in imgs:
                    for psm in (6, 7, 11):
                        got = " ".join(w["text"] for w in ocr._run(img, psm, ocr.langmod.ocr_lang()))
                        s = min(1.0 if ocr.norm(ln) in ocr.norm(got) else _similar_in(got, ln) for ln in lines) if lines else 0
                        sims.append(s)
                        if s >= max(sims):
                            found = got or found
                        if s >= 1.0:
                            break
                    if sims and max(sims) >= 1.0:
                        break
            s = max(sims) if sims else 0.0
            if want not in best or s > best[want][0]:
                best[want] = (s, f, miss, sims, found)
        for want, (_s, f, miss, sims, found) in best.items():
            row(f"{sid} chữ trong cảnh (code, frame {f})", want, miss, sims, found, layer="diegetic")
    return {"available": avail, "total": len(rows), "ok": sum(r["ok"] for r in rows), "rows": rows,
            "overlaps": all_overlaps, "boxes": all_boxes}


def _box_overlap_ratio(a, b):
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    if iw <= 0.0 or ih <= 0.0:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return (iw * ih) / max(1.0, min(area_a, area_b))


def studio_checks(sb, ocr_rep=None, captions_on=True, overlap_th=0.05):
    """3 cổng QC Studio Vòng 12:
    1. không chồng chữ (text overlap) — ĐỎ chặn xuất bản nếu cặp chữ giao > 5%.
    2. phụ đề tách vùng hình (caption clearance) — kiểm chữ không lấn vào Zone C (y > 1280) khi captions bật.
    3. mật độ thị giác (less is more) — báo cáo tỉ lệ shot vượt ngân sách vật thể/chữ."""
    from . import linter  # noqa: PLC0415
    oc = ocr_rep or {}
    overlaps = [o for o in (oc.get("overlaps") or []) if float(o.get("ratio", 0)) > overlap_th]
    # Kiểm chéo thêm từ boxes[] phòng trường hợp engine (vd 3D overlay2d) không tự xuất overlapPairs()
    by_sf = {}
    for bx in oc.get("boxes") or []:
        by_sf.setdefault((bx.get("sid", "?"), bx.get("frame", 0)), []).append(bx)
    seen = {(o.get("sid", "?"), o.get("frame", 0), o.get("a", ""), o.get("b", "")) for o in overlaps}
    for (sid, fr), items in by_sf.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                r = _box_overlap_ratio(items[i]["box"], items[j]["box"])
                if r > overlap_th:
                    a_txt, b_txt = str(items[i].get("text", "")), str(items[j].get("text", ""))
                    if (sid, fr, a_txt, b_txt) not in seen and (sid, fr, b_txt, a_txt) not in seen:
                        overlaps.append({"sid": sid, "frame": fr, "a": a_txt, "b": b_txt, "ratio": round(r, 3)})
                        seen.add((sid, fr, a_txt, b_txt))

    checks = {}
    if overlaps:
        sample = "; ".join(
            f"{o.get('sid', '?')}@f{o.get('frame', 0)}: '{o.get('a', '')[:18]}' ∩ '{o.get('b', '')[:18]}' "
            f"({float(o.get('ratio', 0)):.0%})"
            for o in overlaps[:3]
        )
        checks["không chồng chữ (text overlap)"] = (f"{len(overlaps)} cặp chồng — {sample}", False)
    else:
        checks["không chồng chữ (text overlap)"] = ("0 cặp chồng chữ", True)

    grid = channel().get("layout_grid") or {}
    stage = grid.get("stage") or [390, 1240]
    zone_c_y = float(stage[1]) + 40.0
    if captions_on:
        intrusions = []
        for bx in oc.get("boxes") or []:
            if bx.get("sid") == "OUTRO":
                continue
            box = bx.get("box") or [0, 0, 0, 0]
            if float(box[3]) > zone_c_y:
                intrusions.append(f"{bx.get('sid', '?')}@f{bx.get('frame', 0)} '{str(bx.get('text', ''))[:16]}' "
                                  f"(y1={int(box[3])})")
        if intrusions:
            checks["phụ đề tách vùng hình (caption clearance)"] = (
                f"{len(intrusions)} chữ lấn Zone C (>{int(zone_c_y)}px): " + "; ".join(intrusions[:3]), False,
            )
        else:
            checks["phụ đề tách vùng hình (caption clearance)"] = (f"sạch Zone C (≤ {int(zone_c_y)}px)", True)

    shots = (sb or {}).get("shots") or []
    clutter = linter.lint_clutter(sb or {})
    bad_sids = sorted({i["where"] for i in clutter})
    if bad_sids:
        checks["mật độ thị giác (less is more)"] = (
            f"{len(bad_sids)}/{max(1, len(shots))} shot vượt ngân sách ({', '.join(bad_sids[:4])})", False,
        )
    else:
        checks["mật độ thị giác (less is more)"] = (f"đạt (0/{max(1, len(shots))} shot rối)", True)
    return checks


def _similar(a, b):
    import difflib  # noqa: PLC0415

    from . import ocr  # noqa: PLC0415
    return difflib.SequenceMatcher(None, ocr.norm(a or ""), ocr.norm(b or "")).ratio()


def _similar_in(found, want):
    """Giống nhất giữa `want` và mọi đoạn cùng độ dài trong `found` (chữ cần tìm nằm lẫn trong chữ khác)."""
    from . import ocr  # noqa: PLC0415
    f, w = ocr.norm(found or ""), ocr.norm(want or "")
    if not f or not w:
        return 0.0
    if len(f) <= len(w):
        return _similar(f, w)
    return max(_similar(f[i:i + len(w)], w) for i in range(len(f) - len(w) + 1))


def _plate_text(crop):
    """Chữ tối trên tấm biển sáng (biển trong cảnh 3D): lấy vùng sáng lớn nhất làm tấm biển (bao lồi), chữ = điểm tối
    bên trong → ảnh đen-trên-trắng sạch cho OCR (nền đen quanh biển không còn làm hỏng ngưỡng)."""
    import cv2  # noqa: PLC0415
    g = np.asarray(crop.convert("L"))
    light = (g > 150).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(light, 8)
    if n <= 1:
        return crop
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[k, cv2.CC_STAT_AREA] < 0.15 * g.size:
        return crop
    ys, xs = np.nonzero(lab == k)
    hull = cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32))
    plate = np.zeros_like(light)
    cv2.fillConvexPoly(plate, hull, 1)
    plate = cv2.erode(plate, np.ones((5, 5), np.uint8))
    text = (plate > 0) & (g < 120)
    out = np.where(text, 0, 255).astype(np.uint8)
    h, w = out.shape
    out = cv2.resize(out, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    out = cv2.copyMakeBorder(out, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)
    return Image.fromarray(out)


def json_load(p):
    import json  # noqa: PLC0415
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ publish.md
def write_publish(sb, path):
    pub = sb.get("publish") or {}
    titles = pub.get("titles") or [sb.get("title") or sb.get("topic", "")]
    desc = (pub.get("description") or "").strip()
    tags = [t.lstrip("#") for t in (pub.get("hashtags") or sb.get("hashtags") or channel().get("hashtags", []))]
    warns = []
    for t in titles:
        if len(t) > 60:
            warns.append(f"publish: tiêu đề dài {len(t)} ký tự (> 60): {t}")
    if len(titles) < 3:
        warns.append(f"publish: cần 3 phương án tiêu đề (có {len(titles)}).")
    n_sent = len([s for s in re.split(r"[.!?]+", desc) if s.strip()])
    if desc and n_sent != 2:
        warns.append(f"publish: mô tả nên đúng 2 câu (có {n_sent}).")
    if not 5 <= len(tags) <= 8:
        warns.append(f"publish: hashtag nên 5–8 (có {len(tags)}).")
    L = ["# Publish", "", "## Titles (≤ 60 chars)"]
    L += [f"{k + 1}. {t}  _({len(t)} chars)_" for k, t in enumerate(titles)]
    L += ["", "## Description", "", desc or "_(chưa có — thêm publish.description vào storyboard.json)_", "",
          "## Hashtags", "", " ".join(f"#{t}" for t in tags), ""]
    if pub.get("search_notes"):
        L += ["## Search notes", "", pub["search_notes"], ""]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    return path, warns


# ------------------------------------------------------------------ báo cáo
def _ok(v):
    return "✓" if v else "✗"


def board_md(ctx):
    """Phần engine board (vòng 6): lệch frame, thời gian đọc, glyph, màu, đứng hình, OCR, tốc độ render."""
    q = ctx.get("board_qa")
    if not q:
        return []
    L = ["## Engine board — dấu đỏ / nhãn ↔ từ khoá (phải bắt đầu 0–3 frame TRƯỚC từ)",
         "| Shot | Dấu | Từ khoá | Frame từ | Frame dấu | Sớm (frame) | Đạt |", "|---|---|---|---|---|---|---|"]
    for r in q["marks"]:
        L.append(f"| {r['sid']} | {r['what']} | {r['word']} | {r['word_f']} | {r['onset_f']} | {r['lead_f']} | {_ok(r['ok'])} |")
    L += ["", "| Nhãn / con dấu | Shot | Còn đọc được (s) |", "|---|---|---|"]
    L += [f"| {r['what']} | {r['sid']} | {r['read_sec']:.2f} |" for r in q.get("reads", [])]
    L += ["", f"- Glyph: {sum(r['ok'] for r in q['glyphs'])}/{len(q['glyphs'])} chuỗi đủ glyph (FreeMono Bold / Caladea "
          f"Bold, dự phòng từng ký tự)",
          "- Màu (đo trên frame, phải là đỏ accent): " + "; ".join(f"{r['where']} → RGB {r['median_rgb']}" for r in q["color"]),
          f"- Camera: đứng dài nhất {q['still']['longest_sec']:.2f}s · dịch tối thiểu {q['still']['min_px']} px/frame · "
          f"trung vị {q['still']['median_px']} px/frame", ""]
    o = q["ocr"]
    L += [f"### OCR chữ board ({o['ok']}/{o['total']} đọc được · {o['exact']}/{o['total']} khớp 100%)",
          "| Ở đâu | Chữ | Frame | OCR đọc | Sprite sạch | Trong frame | Đạt |", "|---|---|---|---|---|---|---|"]
    for r in o["rows"]:
        L.append(f"| {r['where']} | {r['expected']} | {r['frame']} | {r['found'][:40]} | {r['ocr_clean']:.0%} | "
                 f"{r['ocr_frame']:.0%} | {_ok(r['ok'])} |")
    st = ctx.get("board_stats") or {}
    if st:
        L += ["", f"- Render engine board: {st.get('frames')} frame · {st.get('workers')} tiến trình · "
              f"{st.get('sec')} s · {st.get('sec_per_frame')} s/frame (wall)"]
    return L + [""]


def board_html(ctx, e, table, img):
    q = ctx.get("board_qa")
    if not q:
        return ""
    rows = [f"<tr><td>{e(r['sid'])}</td><td>{e(r['what'])}</td><td>{e(str(r['word']))}</td><td>{r['word_f']}</td>"
            f"<td>{r['onset_f']}</td><td>{r['lead_f']}</td><td class={'ok' if r['ok'] else 'bad'}>{_ok(r['ok'])}</td></tr>"
            for r in q["marks"]]
    o = q["ocr"]
    orow = [f"<tr><td>{e(r['where'])}</td><td>{e(r['expected'])}</td><td>{r['frame']}</td><td>{e(r['found'][:50])}</td>"
            f"<td>{r['ocr_frame']:.0%}</td><td class={'ok' if r['ok'] else 'bad'}>{_ok(r['ok'])}</td></tr>" for r in o["rows"]]
    crops = "".join(img(f"board/{f}", f, "31%") for f in sorted(os.listdir(os.path.join(os.path.dirname(ctx.get("_qa_dir", "")),
                                                                                         "board"))) if f.endswith(".png")) \
        if ctx.get("_qa_dir") and os.path.isdir(os.path.join(os.path.dirname(ctx["_qa_dir"]), "board")) else ""
    return ("<h2>Engine board — dấu đỏ / nhãn ↔ từ khoá</h2>"
            + table(["Shot", "Dấu", "Từ khoá", "Frame từ", "Frame dấu", "Sớm", "Đạt"], rows)
            + f"<h2>OCR chữ board ({o['ok']}/{o['total']} đọc được · {o['exact']}/{o['total']} khớp 100%)</h2>"
            + table(["Ở đâu", "Chữ", "Frame", "OCR đọc", "Trong frame", "Đạt"], orow) + f"<div>{crops}</div>")


LEVEL_WORD = {"green": "XANH", "yellow": "VÀNG", "red": "ĐỎ"}


def _rows(ctx):
    from . import qagate  # noqa: PLC0415
    return ctx.get("rows") or qagate.classify(ctx.get("checks") or {})


def write_report(path, ctx):
    L = []
    from . import qagate  # noqa: PLC0415
    rows = _rows(ctx)
    verdict = qagate.verdict(rows) if rows else "red"
    ok_all = verdict != "red"
    L.append(f"# QA — {ctx['title']}")
    L.append("")
    if ctx.get("dry_run"):
        L += ["> **DRY-RUN**: clip, lời đọc và nhạc là dữ liệu GIẢ do tool sinh ra để kiểm tra pipeline.", ""]
    L.append(f"- Cổng QA: **{LEVEL_WORD[verdict]}** ({sum(r['level'] == 'red' for r in rows)} đỏ · "
             f"{sum(r['level'] == 'yellow' for r in rows)} vàng) — đỏ chặn publish/deliver · style `{ctx.get('style')}` · thời lượng "
             f"{ctx['duration']:.2f}s · {ctx['n_shots']} shot + outro {ctx['outro_sec']:.1f}s · shot TB {ctx['avg_shot']:.2f}s")
    L.append(f"- Nguồn hình: {ctx['kinds']} · punch-in tự chèn: {ctx['auto_punches']}")
    L.append(f"- Loudness: {ctx.get('loudness', '—')}")
    L += ["", "## Kiểm tra", "| Mức | Kiểm tra | Giá trị |", "|---|---|---|"]
    order = {"red": 0, "yellow": 1, "green": 2}
    for r in sorted(rows, key=lambda r: order[r["level"]]):
        L.append(f"| {LEVEL_WORD[r['level']]} | {r['label']} | {r['value']} |")
    fz = ctx.get("freeze") or {}
    if fz.get("freezes"):
        L += ["", f"Đoạn đứng hình (freezedetect n={fz['noise']}, ≥ {fz['threshold_sec']}s): "
              + ", ".join(f"{a:.2f}–{b:.2f}s{'' if (a, b) in fz['freezes_bad'] else ' (hold)'}" for a, b in fz["freezes"])]
    L.append("")
    lk = ctx.get("look") or {}
    if lk.get("flow") or lk.get("code"):
        L += ["## Khớp nhìn: shot code ↔ shot Flow (qa/look/sheet.jpg)",
              "| Nguồn | Still | Nét mực (px) | Nền đen | Trung tính / tiền cảnh | Xanh accent / tiền cảnh |",
              "|---|---|---|---|---|---|"]
        for k in ("flow", "code"):
            a = lk.get(k)
            if a:
                L.append(f"| {k} | {a['n']} | {a['line_px']} | {a['bg_black']:.0%} | {a['neutral_of_fg']:.0%} | "
                         f"{a['accent_blue_of_fg']:.0%} |")
        L.append("")
    L += board_md(ctx)
    oc = ctx.get("ocr") or {}
    if oc.get("rows"):
        L += [f"## OCR ({oc['ok']}/{oc['total']} đúng)", "| Ở đâu | Chữ cần có | OCR đọc | Đúng | Đè chủ thể |",
              "|---|---|---|---|---|"]
        for r in oc["rows"]:
            L.append(f"| {r['where']} | {r['expected']} | {r['found'][:40]} | {_ok(r['ok'])} | {r['overlap_subject']:.0%} |")
        L.append("")
    L += ["## Ingest (bỏ tiếng Flow)", "| Shot | File gốc | Track tiếng gốc | Sau ingest |", "|---|---|---|---|"]
    for sid, info in sorted(ctx["ingest"].items()):
        L.append(f"| {sid} | {info['src']} | {info['src_audio_streams']} | 0 |")
    L += ["", "## Auto-trim (giây nguồn)", "| Shot | Clip | Đầu tĩnh tới | Đuôi giảm tốc từ | Scene cut | Dùng | Cách |",
          "|---|---|---|---|---|---|---|"]
    for sid, tr in sorted(ctx["trims"].items()):
        L.append(f"| {sid} | {tr['clip_sec']:.2f} | {tr['head_end']:.2f} | {tr['tail_start']:.2f} | "
                 f"{', '.join(f'{c:.2f}' for c in tr['cuts']) or '—'} | {tr['in']:.2f}–{tr['out']:.2f} | {tr['how']} |")
    L += ["", "## Điểm cắt (velocity mismatch: 0 = liền mạch, ≥ 0.6 nên soi)", "| # | Cắt | Lúc | Transition | Mismatch | Ảnh |",
          "|---|---|---|---|---|---|"]
    for r in ctx["cuts"]:
        flag = "" if r["mismatch"] < 0.35 else " ⚠" if r["mismatch"] < 0.6 else " ✗"
        if r["to"] == "OUTRO":
            flag = " (vào outro — không tính)"
        L.append(f"| {r['cut']} | {r['from']}→{r['to']} | {r['at_sec']:.2f}s | {r['transition']} | "
                 f"{r['mismatch']:.2f}{flag} | `qa/cuts/{r['file']}` |")
    L += ["", "## Lời đọc"] + [f"- {n}" for n in ctx.get("vo_notes", [])]
    if ctx.get("vo_lines"):
        L += ["", "| Câu | Bắt đầu | Kết thúc | Shot |", "|---|---|---|---|"]
        for ln in ctx["vo_lines"]:
            L.append(f"| {ln['text'][:60]} | {ln['start']:.2f} | {ln['end']:.2f} | {', '.join(ln['shot_ids'])} |")
    L += ["", "## Chữ text_fx", "| Shot | Chữ | Từ | Đến | Neo | Lớp | Hiệu ứng | Đồng bộ |", "|---|---|---|---|---|---|---|---|"]
    for e in ctx["text_events"]:
        L.append(f"| {e['shot']} | {e['text']} | {e['start']:.2f} | {e['end']:.2f} | {e['anchor']} | {e['layer']} | "
                 f"{', '.join(e['behavior'])} | {e['sync'] or '—'} |")
    mx = ctx["mix"]
    lv = mx.get("levels", {})
    L += ["", "## Âm thanh (stems → mix.py khoá mức theo gated RMS → master gain tuyến tính + limiter true-peak)",
          f"- VO: {'có' if mx['vo'] else 'không'} · nhạc: {mx['music'] or 'không'}"
          + (f" · dừng ở twist {mx['music_stop']:.2f}s" if mx.get("music_stop") else "")
          + f" · {len(mx['sfx'])} SFX · mode `{lv.get('mode')}`",
          f"- Mức đo (so với giọng, gated RMS): nhạc {lv.get('music_db_vs_voice', '—')} dB · SFX "
          f"{lv.get('sfx_db_vs_voice', '—')} dB · đỉnh SFX = {lv.get('sfx_peak_vs_voice_peak', '—')} × đỉnh giọng"
          + (" (đã chặn)" if lv.get("sfx_peak_capped") else ""), ""]
    cs = ctx.get("code_stats") or {}
    if cs:
        L.append("## Render shot code")
        L += [f"- {sid}: {st.get('rendered')} frame · {st.get('sec_per_frame')} s/frame · {st.get('workers')} worker · "
              f"{st.get('gl')}" for sid, st in cs.items()]
        L.append("")
    L.append("## Thumbnail")
    L += [f"- {m['id']} ({m['archetype']}, '{m['text']}'): nền YouTube = {m['bg_youtube']}, nền 9:16 = {m['bg_vertical']}"
          for m in ctx.get("thumbs", [])]
    L += ["- Contact sheet: `thumbnails/contact-sheet.png`", ""]
    if ctx.get("notes"):
        L += ["## Ghi chú"] + [f"- {n}" for n in ctx["notes"]] + [""]
    if ctx.get("issues"):
        L += ["## Linter"] + [f"- [{i['level']}] {i['where']}: {i['msg']}" for i in ctx["issues"]]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return ok_all


_CSS = """:root{--bg:#0d0d10;--card:#17171c;--fg:#e9e9ef;--mut:#9a9aa8;--ok:#3ccf7a;--bad:#ff4d4d;--acc:#3f6bff}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:1180px;margin:auto;padding:16px} h1{font-size:22px} h2{font-size:17px;margin-top:28px;border-bottom:1px solid #2a2a33}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-weight:700;color:#000}
.pass{background:var(--ok)} .fail{background:var(--bad)}
table{border-collapse:collapse;width:100%;background:var(--card)} td,th{padding:6px 8px;border-bottom:1px solid #26262e;text-align:left}
td.ok{color:var(--ok);font-weight:700} td.bad{color:var(--bad);font-weight:700} td.lv-red{color:#ff5a52;font-weight:700} td.lv-yellow{color:#f2b33d;font-weight:700} td.lv-green{color:#3fb950} .mut{color:var(--mut)}
figure{display:inline-block;margin:6px;vertical-align:top;max-width:100%} figcaption{font-size:12px;color:var(--mut)}
img{border-radius:6px;max-width:100%} .tbl{overflow-x:auto}"""


def write_html(path, ctx, proj):
    """qa/report.html — một trang tự chứa (CSS nhúng), ảnh tham chiếu tương đối trong qa/."""
    e = html.escape
    from . import qagate  # noqa: PLC0415
    rows = _rows(ctx)
    verdict = qagate.verdict(rows) if rows else "red"
    ok_all = verdict != "red"
    qa_dir = os.path.dirname(path)
    ctx = {**ctx, "_qa_dir": path}

    def img(rel, cap="", w="100%"):
        if not os.path.exists(os.path.join(qa_dir, rel)):
            return ""
        return (f'<figure style="width:{w}"><a href="{e(rel)}"><img src="{e(rel)}" loading="lazy"></a>'
                f'<figcaption>{e(cap)}</figcaption></figure>')

    def table(head, rows):
        return '<div class="tbl"><table><tr>' + "".join(f"<th>{e(h)}</th>" for h in head) + "</tr>" + "".join(rows) + \
            "</table></div>"

    order = {"red": 0, "yellow": 1, "green": 2}
    checks = [f"<tr><td class=lv-{r['level']}>{LEVEL_WORD[r['level']]}</td><td>{e(r['label'])}</td><td>{e(r['value'])}</td></tr>"
              for r in sorted(rows, key=lambda r: order[r["level"]])]
    lk = ctx.get("look") or {}
    look_rows = [f"<tr><td>{k}</td><td>{a['n']}</td><td>{a['line_px']}</td><td>{a['bg_black']:.0%}</td>"
                 f"<td>{a['neutral_of_fg']:.0%}</td><td>{a['accent_blue_of_fg']:.0%}</td></tr>"
                 for k in ("flow", "code") if (a := lk.get(k))]
    oc = ctx.get("ocr") or {}
    ocr_rows = [f"<tr><td>{e(r['where'])}</td><td>{e(r['expected'])}</td><td>{e(r['found'][:50])}</td>"
                f"<td class={'ok' if r['ok'] else 'bad'}>{_ok(r['ok'])}</td><td>{r['overlap_subject']:.0%}</td></tr>"
                for r in oc.get("rows", [])]
    cuts = "".join(img(f"cuts/{r['file']}", f"{r['from']}→{r['to']} · {r['transition']} · mismatch {r['mismatch']:.2f}",
                       "48%") for r in ctx["cuts"])
    tdir = os.path.join(qa_dir, "text_fx")
    tfx = "".join(img(f"text_fx/{f}", f, "31%") for f in sorted(os.listdir(tdir)) if f.endswith(".png")) \
        if os.path.isdir(tdir) else ""
    fz = ctx.get("freeze") or {}
    mx = ctx["mix"]
    lv = mx.get("levels", {})
    cs = ctx.get("code_stats") or {}
    code_rows = "".join(f"<li>{e(sid)}: {st.get('rendered')} frame · {st.get('sec_per_frame')} s/frame · "
                        f"{st.get('workers')} worker · {e(str(st.get('gl')))}</li>" for sid, st in cs.items())
    fr = ", ".join(f"{a:.2f}–{b:.2f}s" for a, b in fz.get("freezes", [])) or "không có"
    bl = ", ".join(f"{a:.2f}–{b:.2f}s" for a, b in fz.get("blacks", [])) or "không có"
    stop = f" · nhạc dừng ở twist {mx['music_stop']:.2f}s" if mx.get("music_stop") else ""
    parts = [
        f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" '
        f'content="width=device-width,initial-scale=1"><title>QA — {e(ctx["title"])}</title><style>{_CSS}</style></head>'
        f'<body><main>',
        f'<h1>QA — {e(ctx["title"])} <span class="badge {"pass" if ok_all else "fail"}">Cổng QA {LEVEL_WORD[verdict]}'
        f'</span></h1>',
        f'<p class="mut">{"DRY-RUN (dữ liệu giả) · " if ctx.get("dry_run") else ""}style <b>{e(str(ctx.get("style")))}</b>'
        f' · {ctx["duration"]:.2f}s · {ctx["n_shots"]} shot + outro {ctx["outro_sec"]:.1f}s · nguồn {e(str(ctx["kinds"]))}'
        f' · {e(ctx.get("loudness", "—"))}</p>',
        "<h2>Kiểm tra</h2>", table(["Mức", "Kiểm tra", "Giá trị"], checks),
        f'<p class="mut">Freeze (n={fz.get("noise")}, ≥{fz.get("threshold_sec")}s): {e(fr)} · Black: {e(bl)}</p>',
        board_html(ctx, e, table, img),
        "<h2>Contact sheet trước render (look-check)</h2>", img("look/sheet.jpg", "giữa mỗi shot + hai phía mỗi điểm cắt"),
        table(["Nguồn", "Still", "Nét mực px", "Nền đen", "Trung tính", "Xanh accent"], look_rows),
        "<h2>QA sheet video cuối (2 fps)</h2>", img("qa_sheet.jpg"),
        f'<h2>OCR ({oc.get("ok", 0)}/{oc.get("total", 0)} đúng){"" if oc.get("available") else " — chưa cài Tesseract"}</h2>',
        table(["Ở đâu", "Cần có", "OCR đọc", "Đúng", "Đè chủ thể"], ocr_rows),
        "<h2>Chữ text_fx (3 frame / hiệu ứng)</h2>", f"<div>{tfx or '<p class=mut>—</p>'}</div>",
        "<h2>Âm thanh</h2>",
        f"<p>VO {'có' if mx['vo'] else 'không'} · nhạc {e(str(mx['music'] or 'không'))}{stop} · {len(mx['sfx'])} SFX · "
        f"mode {e(str(lv.get('mode')))}<br>Nhạc {lv.get('music_db_vs_voice', '—')} dB · SFX {lv.get('sfx_db_vs_voice', '—')} dB "
        f"so với giọng (gated RMS) · đỉnh SFX {lv.get('sfx_peak_vs_voice_peak', '—')}× đỉnh giọng</p>",
        "<h2>Render shot code</h2>", f"<ul>{code_rows or '<li class=mut>—</li>'}</ul>",
        "<h2>Điểm cắt</h2>", f"<div>{cuts}</div>",
        "<h2>Thumbnail</h2>", img("../thumbnails/contact-sheet.png"),
        "<h2>Ghi chú</h2>", "<ul>" + ("".join(f"<li>{e(n)}</li>" for n in ctx.get("notes", [])) or "<li class=mut>—</li>")
        + "</ul>",
        '<p class="mut">Bản markdown: report.md · đồ thị auto-trim: trim/*.png</p></main></body></html>',
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))
    return path

