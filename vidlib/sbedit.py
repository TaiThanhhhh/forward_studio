"""Sửa storyboard.json / ideas.json CÓ KIỂM — để người làm (và UI) không bao giờ phải mở file JSON bằng tay.

  python studio.py sb check   <slug> [<file|->]                 kiểm (không ghi); không đưa file → storyboard.json hiện có
  python studio.py sb import  <slug> <file|-> [--note "…"]      dán storyboard (JSON thô hoặc cả câu trả lời của AI)
  python studio.py sb patch   <slug> [--shot C03] --set code.params.to=157 [--set …] [--unset đường] [--json <file|->]
  python studio.py sb history <slug>                             các bản đã lưu (mới nhất trước)
  python studio.py sb restore <slug> <id>                        khôi phục một bản (bản hiện tại được lưu lại → làm lại được)
  python studio.py sb preview <slug> <C03> [--u 0.5]             dựng MỘT frame của shot code → work/preview/<C03>.jpg
  python studio.py ideas import <lô> <file|->                    dán 10 ý tưởng (ideas/<lô>/ideas.json)

Luật: sai → KHÔNG ghi, in lỗi có đường dẫn trường (shots[2].code.params.to) + số dòng trong JSON dán vào. Sửa một
storyboard đang lỗi: được ghi nếu KHÔNG thêm lỗi mới (bớt lỗi dần được). Mỗi lần ghi giữ bản cũ ở
work/sb_history/ (hoàn tác = restore). Ghi qua common.save_json. Dòng cuối luôn là `::sbedit {json}` (UI đọc).
Kiểm = normalize + validate (vidlib/storyboard) + style/code_only như stage storyboard + compile + linter (như stage
page) — cùng điều kiện làm pipeline dừng ở storyboard_invalid / lint_failed (exit 3).
"""
import argparse
import copy
import json
import os
import re
import sys
import time
import uuid

from . import storyboard as sbm
from .common import FPS, PROJECTS, ROOT, StudioError, load_json, save_json

HISTORY_KEEP = 40
MAX_TEXT = 4 * 1024 * 1024
LOCKED = ("id",)                      # sửa id shot làm gãy seed_from/refs/clip → không cho patch


class SbError(StudioError):
    def __init__(self, msg, report=None):
        super().__init__(msg)
        self.report = report or {"ok": False, "errors": [{"msg": msg, "path": "", "line": None}], "warnings": []}


# ------------------------------------------------------------------ đọc JSON dán vào (kể cả câu trả lời của AI)
def _line_at(text, i):
    return text.count("\n", 0, max(0, i)) + 1


def extract_json(text):
    """(object, start_index, notes). Chấp nhận JSON thô, khối ```json … ```, hoặc câu trả lời có chữ trước/sau.
    Lỗi cú pháp → SbError có số dòng/cột trong văn bản GỐC."""
    if not isinstance(text, str) or not text.strip():
        raise SbError("Chưa có nội dung — dán JSON (hoặc cả câu trả lời của AI) vào ô.")
    if len(text) > MAX_TEXT:
        raise SbError(f"Nội dung quá lớn ({len(text) // 1024} KB > {MAX_TEXT // 1024} KB).")
    notes = []
    a = text.find("{")
    b = text.rfind("}")
    if a < 0 or b < a:
        raise SbError("Không thấy JSON (cần một object bắt đầu bằng '{').")
    if text[:a].strip() or text[b + 1:].strip():
        notes.append("Đã bỏ phần chữ/``` ngoài JSON.")
    body = text[a:b + 1]
    try:
        return json.loads(body), a, notes
    except json.JSONDecodeError as e:
        line = _line_at(text, a + e.pos)
        g = a + e.pos                                    # vị trí trong văn bản gốc
        col = g - (text.rfind("\n", 0, g) + 1) + 1
        hint = _json_hint(body, e)
        msg = f"JSON sai cú pháp ở dòng {line}, cột {col}: {e.msg}." + (f" {hint}" if hint else "")
        raise SbError(msg, {"ok": False, "errors": [{"msg": msg, "path": "", "line": line, "kind": "syntax"}],
                            "warnings": []}) from e


def _json_hint(body, e):
    before = body[:e.pos].rstrip()
    if e.msg.startswith("Expecting property name") and before.endswith(","):
        return "Có dấu phẩy thừa trước '}' hoặc ']'."
    if e.msg.startswith("Expecting ',' delimiter"):
        return "Thiếu dấu phẩy giữa hai phần tử (hoặc thiếu dấu \" đóng chuỗi)."
    if "Invalid control character" in e.msg:
        return "Chuỗi có xuống dòng thật — thay bằng \\n."
    if e.msg.startswith("Expecting value") and re.search(r"[‘’“”]", body[max(0, e.pos - 2):e.pos + 2]):
        return "Dấu nháy cong (“ ”) — JSON cần nháy thẳng \"."
    return ""


def locate(text, start=0):
    """{đường dẫn: số dòng} cho mọi giá trị trong JSON (đường dẫn kiểu shots[2].code.params.to). Không ném lỗi."""
    out = {}
    n = len(text)
    nl = [i for i, c in enumerate(text) if c == "\n"]

    def line(i):
        import bisect  # noqa: PLC0415
        return bisect.bisect_left(nl, i) + 1

    def ws(i):
        while i < n and text[i] in " \t\r\n":
            i += 1
        return i

    def string(i):
        j = i + 1
        while j < n and text[j] != '"':
            j += 2 if text[j] == "\\" else 1
        return j + 1

    def value(i, path):
        i = ws(i)
        if i >= n:
            return i
        out.setdefault(path, line(i))
        c = text[i]
        if c == "{":
            i = ws(i + 1)
            while i < n and text[i] != "}":
                if text[i] != '"':
                    return n
                j = string(i)
                key = text[i + 1:j - 1]
                i = ws(j)
                if i >= n or text[i] != ":":
                    return n
                i = value(i + 1, f"{path}.{key}" if path else key)
                i = ws(i)
                if i < n and text[i] == ",":
                    i = ws(i + 1)
            return i + 1
        if c == "[":
            i = ws(i + 1)
            k = 0
            while i < n and text[i] != "]":
                i = value(i, f"{path}[{k}]")
                k += 1
                i = ws(i)
                if i < n and text[i] == ",":
                    i = ws(i + 1)
            return i + 1
        if c == '"':
            return string(i)
        while i < n and text[i] not in ",]}\r\n\t ":
            i += 1
        return i

    try:
        value(start, "")
    except (IndexError, RecursionError):
        pass
    return out


# ------------------------------------------------------------------ kiểm
FIELD_HINTS = (   # (trường trong shot, regex trên câu báo lỗi) — để trỏ lỗi về đúng ô/dòng
    ("beat_recipe", r"beat_recipe"), ("transition_in", r"transition_in"), ("mode", r"\bmode '"),
    ("code.params", r"thiếu params|layout|params|icon|actor|camera|depth|groups|events|meter|split|body\.|physics|prop|"
                    r"set '|keys|verb|svg:|lottie|rive"),
    ("code.scene", r"không có cảnh|cảnh/beat|beat html '\w+' không có|shot code cần|code\.engine"),
    ("beat", r"\bbeat '"), ("start_frame.desc", r"start_frame"), ("action", r"thiếu action|\baction\b"),
    ("target_sec", r"target_sec"), ("onscreen", r"onscreen|chữ '"), ("refs", r"ref '"),
    ("text_fx", r"text_fx|behavior|anchor|layer"), ("vo", r"\bvo\b|lời đọc|từ/giây|words?"), ("id", r"id phải"),
)


def _shot_field(msg):
    for field, rx in FIELD_HINTS:
        if re.search(rx, msg, re.I):
            return field
    return None


def _entry(msg, sb, where=None, lines=None, level="error"):
    """Câu báo lỗi → {msg, shot, path, field, line}."""
    ids = [s.get("id") for s in (sb.get("shots") or []) if isinstance(s, dict)]
    shot = where if where in ids else None
    m = re.match(r"^(C\d{2,3}|OUTRO)\s*:\s*(.*)$", msg, re.S)
    if m and not shot:
        shot, msg = m.group(1), m.group(2)
    elif m:
        msg = m.group(2)
    path, field = "", None
    if shot in ids:
        k = ids.index(shot)
        field = _shot_field(msg)
        path = f"shots[{k}]" + (f".{field}" if field else "")
    elif where and where not in ("model",):
        path = where
    else:
        for top in ("topic", "shots", "assembly", "style", "voice", "flow", "thumbnail", "outro", "publish"):
            if re.search(rf"\b{top}\b", msg):
                path = top
                break
    line = None
    if lines:
        p = path
        while p and line is None:
            line = lines.get(p)
            up = re.sub(r"(\.[^.\[\]]+|\[\d+\])$", "", p)
            p = up if up != p else ""                    # khoá gốc (không còn '.'/'[i]') → dừng
    return {"msg": msg.strip(), "shot": shot, "path": path, "field": field, "line": line, "level": level}


def _structure(data):
    """Lỗi cấu trúc trước khi normalize (normalize sẽ ném lỗi khó hiểu với kiểu sai)."""
    if not isinstance(data, dict):
        return ["storyboard phải là một object JSON { … } (không phải danh sách)."]
    errs = []
    shots = data.get("shots")
    if shots is None:
        errs.append("Thiếu trường 'shots' (danh sách các shot).")
    elif not isinstance(shots, list):
        errs.append("'shots' phải là danh sách [ … ].")
    else:
        for i, s in enumerate(shots):
            if not isinstance(s, dict):
                errs.append(f"shots[{i}] phải là object {{ id, beat, vo, … }}.")
                continue
            for key, typ, label in (("code", dict, "object {scene, params}"), ("start_frame", (dict, str), "object"),
                                    ("trim", dict, "object"), ("override", dict, "object"), ("board", dict, "object")):
                if s.get(key) is not None and not isinstance(s[key], typ):
                    errs.append(f"shots[{i}].{key} phải là {label}.")
            c = s.get("code")
            if isinstance(c, dict) and c.get("params") is not None and not isinstance(c["params"], dict):
                errs.append(f"shots[{i}].code.params phải là object {{ … }}.")
    for key in ("thumbnail", "outro", "publish", "format", "flow"):
        if data.get(key) is not None and not isinstance(data[key], dict):
            errs.append(f"'{key}' phải là object.")
    return errs


def _plan(proj):
    return load_json(os.path.join(proj, "plan.json"), {}) if proj and os.path.exists(os.path.join(proj, "plan.json")) else {}


def check(proj, data, text=None, start=0):
    """Báo cáo kiểm một storyboard (không ghi gì). proj có thể None (chỉ kiểm schema + style)."""
    from . import compiler, linter, styles  # noqa: PLC0415
    lines = locate(text, start) if text else {}
    slug = os.path.basename(proj) if proj else ""
    rep = {"ok": False, "errors": [], "warnings": [], "summary": {}}
    se = _structure(data)
    if se:
        for m in se:
            mm = re.match(r"^(shots\[\d+\][\w.]*)", m) or re.match(r"^'(\w+)'", m)
            path = mm.group(1) if mm else ""
            rep["errors"].append({"msg": m, "path": path, "line": lines.get(path), "shot": None, "field": None,
                                  "level": "error"})
        return rep
    raw = data
    try:
        sb = sbm.normalize(raw)
    except Exception as e:  # noqa: BLE001 — kiểu dữ liệu lạ: báo một lỗi dễ hiểu, không sập
        rep["errors"] = [{"msg": f"Không chuẩn hoá được storyboard: {e}", "path": "", "line": None, "shot": None,
                          "field": None, "level": "error"}]
        return rep
    sb["slug"] = slug
    plan = _plan(proj)
    if sb.get("style") == "auto" and not sb.get("style_resolved") and plan.get("style") in styles.available():
        sb["style_resolved"] = plan["style"]
    errs, warns = sbm.validate(sb)
    try:
        style, note = styles.resolve(sb, slug)
    except Exception as e:  # noqa: BLE001
        style, note = None, None
        errs.append(f"style: {e}")
    if style and style not in styles.available():
        errs.append(f"style '{style}' không có trong styles/ (có: {', '.join(styles.available())}).")
    elif style and styles.info(style)["code_only"]:
        non = [s["id"] for s in sb["shots"] if not s.get("code")]
        if non:
            errs.append(f"style '{style}' dựng TOÀN BỘ bằng code — các shot sau chưa có 'code': {', '.join(non)}.")
    if note:
        warns.append(note)
    rep["errors"] = [_entry(m, raw, None, lines) for m in errs]
    rep["warnings"] = [_entry(m, raw, None, lines, "warn") for m in warns]
    if not errs and style:
        sb["style_resolved"] = style
        try:
            clips = os.path.join(proj, "clips") if proj else ""
            have = {os.path.splitext(f)[0].upper() for f in os.listdir(clips)} if clips and os.path.isdir(clips) else set()
            csb = compiler.compile_all(sb, auto_code_ids=[s["id"] for s in sb["shots"] if s["id"] not in have])
            for i in linter.lint(csb):
                lvl = "error" if i["level"] == "error" else "warn"
                (rep["errors"] if lvl == "error" else rep["warnings"]).append(
                    _entry(f"{i['msg']}", raw, i.get("where"), lines, lvl) | {"lint": True})
        except Exception as e:  # noqa: BLE001 — linter/compile của WP khác đang dở: không chặn, chỉ cảnh báo
            rep["warnings"].append({"msg": f"Không chạy được linter: {e}", "path": "", "line": None, "level": "warn"})
    shots = sb.get("shots") or []
    words = sum(len(re.findall(r"[A-Za-z0-9'’-]+", re.sub(r"\[[^\]]*\]", "", s.get("vo") or ""))) for s in shots)
    from . import codeshot  # noqa: PLC0415
    mix = {}
    for s in shots:
        e = "board" if (s.get("code") or {}).get("engine") == "board" else (
            (codeshot.engine_of(s, style) or "three") if (s.get("code") or {}).get("scene") else "flow")
        mix[e] = mix.get(e, 0) + 1
    rep["summary"] = {"title": sb.get("title") or sb.get("topic"), "shots": len(shots), "words": words,
                      "sec": round(sum(float(s.get("target_sec") or 0) for s in shots), 1), "style": style, "mix": mix}
    rep["ok"] = not rep["errors"]
    return rep


# ------------------------------------------------------------------ lịch sử + ghi
def _hist_dir(proj):
    return os.path.join(proj, "work", "sb_history")


def history(proj):
    d = _hist_dir(proj)
    out = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d), reverse=True):
            if f.endswith(".json"):
                m = load_json(os.path.join(d, f), {}) or {}
                out.append({"id": f[:-5], "note": m.get("note", ""), "time": m.get("time"),
                            "shots": len((m.get("storyboard") or {}).get("shots") or [])})
    return out


def _backup(proj, note):
    """Lưu storyboard hiện tại (nếu có) vào lịch sử. Trả về id bản lưu hoặc None."""
    cur = sbm.load(proj)
    if cur is None:
        return None
    bid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    save_json(os.path.join(_hist_dir(proj), bid + ".json"),
              {"note": note, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "storyboard": cur})
    files = sorted(f for f in os.listdir(_hist_dir(proj)) if f.endswith(".json"))
    for f in files[:-HISTORY_KEEP]:
        try:
            os.remove(os.path.join(_hist_dir(proj), f))
        except OSError:
            pass
    return bid


def _err_keys(rep):
    return {(e.get("shot"), e.get("msg")) for e in rep.get("errors") or []}


def write(proj, data, note, text=None, start=0):
    """Kiểm rồi ghi. Không có bản cũ → phải sạch lỗi. Có bản cũ → không được THÊM lỗi mới. Trả về report + backup."""
    rep = check(proj, data, text, start)
    if not rep["ok"]:
        cur = sbm.load(proj)
        new = _err_keys(rep) - (_err_keys(check(proj, cur)) if isinstance(cur, dict) else set())
        if cur is None or new:
            rep["rejected"] = True
            rep["new_errors"] = len(new) if cur is not None else len(rep["errors"])
            raise SbError(f"Không ghi: {rep['new_errors']} lỗi" + (" mới" if cur is not None else "")
                          + " — sửa rồi lưu lại.", rep)
    data = copy.deepcopy(data)
    data["slug"] = os.path.basename(proj)
    rep["backup"] = _backup(proj, note)
    sbm.save(proj, data)
    rep["saved"] = True
    return rep


def import_text(proj, text, note="dán storyboard"):
    data, start, notes = extract_json(text)
    if not isinstance(data, dict):
        raise SbError("Storyboard phải là object JSON { … }.")
    if "ideas" in data and "shots" not in data:
        raise SbError("Đây là ideas.json (10 ý tưởng), không phải storyboard — dán ở trang Ý tưởng.")
    rep = write(proj, data, note, text, start)
    rep["notes"] = notes
    return rep


# ------------------------------------------------------------------ patch theo đường dẫn
def _tokens(path):
    toks = re.findall(r"[^.\[\]]+", str(path or ""))
    if not toks:
        raise SbError(f"Đường dẫn trường rỗng: '{path}'.")
    return toks


def _walk(obj, toks, create):
    for k, t in enumerate(toks[:-1]):
        nxt_is_idx = toks[k + 1].isdigit()
        if isinstance(obj, list):
            if not t.isdigit() or int(t) > len(obj):
                raise SbError(f"Chỉ số '{t}' ngoài danh sách (dài {len(obj)}).")
            i = int(t)
            if i == len(obj):
                if not create:
                    raise SbError(f"Không có phần tử {i}.")
                obj.append({})
            obj = obj[i]
            continue
        if not isinstance(obj, dict):
            raise SbError(f"'{t}': cha không phải object.")
        if t not in obj or obj[t] is None:
            if not create:
                raise SbError(f"Không có trường '{t}'.")
            obj[t] = [] if nxt_is_idx else {}
        obj = obj[t]
    return obj


def set_path(obj, path, value):
    toks = _tokens(path)
    parent = _walk(obj, toks, True)
    last = toks[-1]
    if isinstance(parent, list):
        if not last.isdigit() or int(last) > len(parent):
            raise SbError(f"Chỉ số '{last}' ngoài danh sách (dài {len(parent)}).")
        if int(last) == len(parent):
            parent.append(value)
        else:
            parent[int(last)] = value
    elif isinstance(parent, dict):
        parent[last] = value
    else:
        raise SbError(f"'{path}': cha không phải object/danh sách.")


def unset_path(obj, path):
    toks = _tokens(path)
    try:
        parent = _walk(obj, toks, False)
    except SbError:
        return False
    last = toks[-1]
    if isinstance(parent, list) and last.isdigit() and int(last) < len(parent):
        parent.pop(int(last))
        return True
    if isinstance(parent, dict) and last in parent:
        parent.pop(last)
        return True
    return False


def parse_value(s):
    """--set k=v: v là JSON nếu đọc được (157, true, [1,2], {"a":1}, "chữ"), không thì là chuỗi."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s


def patch(proj, sid=None, sets=None, unsets=None, note=None):
    """sets: {đường: giá trị} (đường tính trong shot sid, hoặc từ gốc storyboard khi sid None)."""
    cur = sbm.load(proj)
    if cur is None:
        raise SbError("Dự án chưa có storyboard.json — dán storyboard trước.")
    data = copy.deepcopy(cur)
    target = data
    if sid:
        sid = sid.upper()
        target = next((s for s in data.get("shots") or [] if isinstance(s, dict) and s.get("id") == sid), None)
        if target is None:
            raise SbError(f"Không có shot {sid} (có: {', '.join(s.get('id', '?') for s in data.get('shots') or [])}).")
    sets, unsets = dict(sets or {}), list(unsets or [])
    if not sets and not unsets:
        raise SbError("Không có gì để sửa (--set đường=giá trị hoặc --unset đường).")
    for p in list(sets) + unsets:
        if _tokens(p)[0] in LOCKED and sid:
            raise SbError(f"Không sửa '{p}' (id shot) — đổi thứ tự bằng `studio.py shots`.")
        if not sid and _tokens(p)[0] == "slug":
            raise SbError("Không sửa 'slug'.")
    for p, v in sets.items():
        set_path(target, p, v)
    for p in unsets:
        unset_path(target, p)
    what = ", ".join([f"{p}={json.dumps(v, ensure_ascii=False)[:40]}" for p, v in sets.items()] + [f"−{p}" for p in unsets])
    rep = write(proj, data, note or f"sửa {sid + ' · ' if sid else ''}{what}"[:200])
    rep["changed"] = {"shot": sid, "set": list(sets), "unset": unsets}
    return rep


def restore(proj, bid):
    if not re.fullmatch(r"[\w-]{6,40}", str(bid or "")):
        raise SbError("Id bản lưu không hợp lệ.")
    p = os.path.join(_hist_dir(proj), f"{bid}.json")
    if not os.path.exists(p):
        raise SbError(f"Không có bản lưu {bid}.")
    old = (load_json(p, {}) or {}).get("storyboard")
    if not isinstance(old, dict):
        raise SbError(f"Bản lưu {bid} hỏng.")
    rep = check(proj, old)
    rep["backup"] = _backup(proj, f"trước khi khôi phục {bid}")
    sbm.save(proj, old)
    rep["saved"] = True
    rep["restored"] = bid
    return rep


# ------------------------------------------------------------------ xem trước 1 frame
def preview_path(proj, sid):
    return os.path.join(proj, "work", "preview", f"{sid}.jpg")


def preview(proj, sid, u=0.5, log=print):
    """Dựng MỘT frame của shot code (three/html/manim) từ storyboard hiện tại → work/preview/<sid>.jpg.
    Không đụng work/code/<sid>/ (frame render thật giữ nguyên). Bố cục html chọn như lúc render (assign_layouts)."""
    import shutil  # noqa: PLC0415

    from engines import adapter  # noqa: PLC0415

    from . import codeshot, styles  # noqa: PLC0415
    raw = sbm.load(proj)
    if raw is None:
        raise SbError("Chưa có storyboard.json.")
    sb = sbm.normalize(raw)
    sb["slug"] = os.path.basename(proj)
    plan = _plan(proj)
    if sb.get("style") == "auto" and not sb.get("style_resolved") and plan.get("style") in styles.available():
        sb["style_resolved"] = plan["style"]
    style = sb.get("style_resolved") or styles.resolve(sb, sb["slug"])[0]
    shot = sbm.shot(sb, sid.upper())
    if not shot:
        raise SbError(f"Không có shot {sid}.")
    if not codeshot.is_3d(shot):
        raise SbError(f"{shot['id']} không phải shot code (three/html/manim) — shot Flow xem ảnh khung ở Generate; shot "
                      "board xem bằng Render lại.")
    codeshot.assign_layouts(sb, style)
    tl = load_json(os.path.join(proj, "work", "timeline.json"), {}) if os.path.exists(
        os.path.join(proj, "work", "timeline.json")) else {}
    seg = next((x for x in tl.get("segments") or [] if x.get("sid") == shot["id"]), None)
    n = int(seg["n"]) if seg and seg.get("n") else max(2, round(float(shot.get("target_sec") or 2) * FPS))
    f = max(0, min(n - 1, round(float(u) * (n - 1))))
    spec = codeshot.spec_for(proj, sb, shot, n, style)
    spec.work = os.path.join(proj, "work", "preview", shot["id"])
    shutil.rmtree(os.path.join(spec.work, "frames"), ignore_errors=True)
    eng = adapter.get(spec.engine)
    job = eng.job(spec)
    fdir = os.path.join(spec.work, "frames")
    t0 = time.time()
    eng.render(job, fdir, [f], log=lambda m: None, workers=1)
    src = os.path.join(fdir, f"f{f:04d}.jpg")
    if not os.path.exists(src):
        raise SbError(f"Engine {spec.engine} không xuất được frame {f}.")
    dst = preview_path(proj, shot["id"])
    shutil.copyfile(src, dst + ".tmp")
    os.replace(dst + ".tmp", dst)
    return {"ok": True, "shot": shot["id"], "engine": spec.engine, "scene": spec.scene, "frame": f, "frames": n,
            "u": round(f / max(1, n - 1), 3), "file": os.path.relpath(dst, proj).replace("\\", "/"),
            "sec": round(time.time() - t0, 2), "style": style}


# ------------------------------------------------------------------ ideas.json
def ideas_check(data):
    from . import ideas  # noqa: PLC0415
    if not isinstance(data, dict):
        return {"ok": False, "errors": [{"msg": "ideas.json phải là object {theme, ideas: [ … ]}.", "path": ""}],
                "warnings": []}
    if "shots" in data and "ideas" not in data:
        return {"ok": False, "errors": [{"msg": "Đây là storyboard, không phải ideas.json — dán ở trang Script của dự án.",
                                         "path": ""}], "warnings": []}
    errs = []
    for m in ideas.validate(data):
        mm = re.match(r"^#(\d+): (.*)$", m)
        errs.append({"msg": mm.group(2) if mm else m, "idea": int(mm.group(1)) if mm else None,
                     "path": f"ideas[{int(mm.group(1)) - 1}]" if mm else "ideas"})
    return {"ok": not errs, "errors": errs, "warnings": [], "summary": {"ideas": len(data.get("ideas") or []),
                                                                       "theme": data.get("theme")}}


def ideas_dir(batch):
    from . import ideas  # noqa: PLC0415
    if not re.fullmatch(r"[A-Za-z0-9_][\w.-]{0,120}", str(batch or "")) or ".." in batch:
        raise SbError("Tên lô ý tưởng không hợp lệ.")
    d = os.path.join(ideas.IDEAS_DIR, batch)
    if not os.path.isdir(d):
        raise SbError(f"Không có lô ý tưởng '{batch}' (tạo bằng: studio.py ideas \"<chủ đề>\").")
    return d


def ideas_import(batch, text):
    d = ideas_dir(batch)
    data, start, notes = extract_json(text)
    rep = ideas_check(data)
    lines = locate(text, start)
    for e in rep["errors"]:
        e["line"] = lines.get(e.get("path") or "")
    if not rep["ok"]:
        raise SbError(f"Không ghi: {len(rep['errors'])} lỗi trong ideas.json.", rep)
    jp = os.path.join(d, "ideas.json")
    if os.path.exists(jp):
        bid = time.strftime("%Y%m%d-%H%M%S")
        save_json(os.path.join(d, "history", f"ideas-{bid}.json"), load_json(jp, {}))
        rep["backup"] = bid
    old = load_json(jp, {}) if os.path.exists(jp) else {}
    data.setdefault("theme", old.get("theme") or batch)
    save_json(jp, data)
    rep.update({"saved": True, "notes": notes})
    return rep


# ------------------------------------------------------------------ CLI
def _read_src(src):
    if src in (None, "-"):
        raw = sys.stdin.buffer.read()
    else:
        with open(src, "rb") as fh:
            raw = fh.read()
    return raw.decode("utf-8-sig", errors="replace")


def _proj(slug):
    p = os.path.join(PROJECTS, slug)
    if not re.fullmatch(r"[A-Za-z0-9_][\w.-]{0,120}", slug or "") or ".." in slug or not os.path.isdir(p):
        raise SbError(f"Không có dự án '{slug}'.")
    return p


def _emit(rep, log=print):
    for e in rep.get("errors") or []:
        where = " · ".join(x for x in (e.get("path"), f"dòng {e['line']}" if e.get("line") else "") if x)
        log(f"  ✖ {e['msg']}" + (f"  [{where}]" if where else ""))
    for w in rep.get("warnings") or []:
        log(f"  ⚠ {w['msg']}" + (f"  [{w['path']}]" if w.get("path") else ""))
    log("::sbedit " + json.dumps(rep, ensure_ascii=False, separators=(",", ":")))


def cli(argv, log=print):
    ap = argparse.ArgumentParser(prog="studio.py sb", description="Sửa storyboard.json có kiểm (không mở file tay)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("slug")
    c.add_argument("src", nargs="?")
    i = sub.add_parser("import")
    i.add_argument("slug")
    i.add_argument("src")
    i.add_argument("--note", default="dán storyboard")
    p = sub.add_parser("patch")
    p.add_argument("slug")
    p.add_argument("--shot")
    p.add_argument("--set", action="append", default=[], metavar="ĐƯỜNG=GIÁ_TRỊ")
    p.add_argument("--unset", action="append", default=[], metavar="ĐƯỜNG")
    p.add_argument("--json", metavar="FILE|-", help='{"set": {đường: giá trị}, "unset": [đường]} (UI dùng, qua stdin)')
    p.add_argument("--note")
    h = sub.add_parser("history")
    h.add_argument("slug")
    r = sub.add_parser("restore")
    r.add_argument("slug")
    r.add_argument("id")
    v = sub.add_parser("preview")
    v.add_argument("slug")
    v.add_argument("shot")
    v.add_argument("--u", type=float, default=0.5)
    a = ap.parse_args(argv)
    try:
        proj = _proj(a.slug)
        if a.cmd == "check":
            if a.src:
                text = _read_src(a.src)
                data, start, notes = extract_json(text)
                rep = check(proj, data, text, start)
                rep["notes"] = notes
            else:
                cur = sbm.load(proj)
                if cur is None:
                    raise SbError("Dự án chưa có storyboard.json.")
                with open(sbm.path_of(proj), encoding="utf-8") as fh:
                    text = fh.read()
                rep = check(proj, cur, text)
            log(("✔ storyboard hợp lệ" if rep["ok"] else f"✖ {len(rep['errors'])} lỗi") +
                f" · {rep['summary'].get('shots', 0)} shot" if rep.get("summary") else "")
            _emit(rep, log)
            return 0 if rep["ok"] else 3
        if a.cmd == "import":
            rep = import_text(proj, _read_src(a.src), a.note)
            log(f"✔ đã ghi storyboard.json · {rep['summary'].get('shots', 0)} shot"
                + (f" · bản cũ: {rep['backup']}" if rep.get("backup") else "")
                + ("" if rep["ok"] else f" · còn {len(rep['errors'])} lỗi cũ"))
            _emit(rep, log)
            return 0
        if a.cmd == "patch":
            sets, unsets = {}, list(a.unset)
            for kv in a.set:
                k, eq, val = kv.partition("=")
                if not eq:
                    raise SbError(f"--set cần dạng đường=giá_trị (nhận '{kv}').")
                sets[k.strip()] = parse_value(val)
            if a.json:
                body = json.loads(_read_src(a.json) or "{}")
                if not isinstance(body, dict):
                    raise SbError("--json cần object {set, unset}.")
                sets.update(body.get("set") or {})
                unsets += list(body.get("unset") or [])
                a.shot = a.shot or body.get("shot")
            rep = patch(proj, a.shot, sets, unsets, a.note)
            log(f"✔ đã sửa {(a.shot or 'storyboard').upper()} · {len(sets)} trường đặt, {len(unsets)} trường bỏ"
                + (f" · bản cũ: {rep['backup']}" if rep.get("backup") else ""))
            _emit(rep, log)
            return 0
        if a.cmd == "history":
            hs = history(proj)
            for x in hs:
                log(f"  {x['id']}  {x['time']}  {x['shots']} shot  {x['note']}")
            log("::sbedit " + json.dumps({"ok": True, "history": hs}, ensure_ascii=False))
            return 0
        if a.cmd == "restore":
            rep = restore(proj, a.id)
            log(f"✔ đã khôi phục {a.id} · bản trước đó lưu thành {rep['backup']}")
            _emit(rep, log)
            return 0
        if a.cmd == "preview":
            log(f"▶ preview · {a.shot.upper()} · u={a.u}")
            res = preview(proj, a.shot, a.u)
            log(f"✔ {res['file']} · frame {res['frame']}/{res['frames'] - 1} · {res['engine']}:{res['scene']}"
                f" · {res['sec']}s")
            log("::sbedit " + json.dumps(res, ensure_ascii=False))
            return 0
    except SbError as e:
        log(f"✖ {e}")
        _emit({**e.report, "ok": False}, log)
        return 3
    return 1


def ideas_cli(argv, log=print):
    """python studio.py ideas import <lô> <file|->"""
    ap = argparse.ArgumentParser(prog="studio.py ideas import")
    ap.add_argument("batch")
    ap.add_argument("src")
    a = ap.parse_args(argv)
    try:
        rep = ideas_import(a.batch, _read_src(a.src))
        log(f"✔ đã ghi ideas/{a.batch}/ideas.json · {rep['summary']['ideas']} ý tưởng — chọn: "
            f"python studio.py ideas {a.batch} --pick <số>")
        _emit(rep, log)
        return 0
    except SbError as e:
        log(f"✖ {e}")
        _emit({**e.report, "ok": False}, log)
        return 3


__all__ = ["check", "cli", "extract_json", "history", "ideas_check", "ideas_cli", "ideas_import", "import_text",
           "locate", "patch", "preview", "restore", "ROOT"]
