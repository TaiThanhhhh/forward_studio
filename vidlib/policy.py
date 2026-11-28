"""Rủi ro chính sách YouTube (vòng 22) — kiểm trước khi đăng, chạy ở cổng QA và `studio.py policy`.

Căn cứ (đọc ngày 27/11/2026, chi tiết + nguồn ở docs/YOUTUBE_RISK.md):
- YPP "inauthentic content" (đổi tên 15/07/2025, làm rõ 16/07/2026): KHÔNG kiếm tiền với nội dung "generic or
  repetitive" (trông như làm từ template, "minimal variation across numerous videos"), "unsatisfying or off-putting"
  (video na ná nhau tới mức hoán đổi được) và "AI personas" tự xưng chuyên gia cho lời khuyên sức khoẻ/tài chính/pháp lý.
  Template được phép nếu phần lớn nội dung khác nhau và có giá trị giáo dục.
- Spam & deceptive practices: tiêu đề/thumbnail/mô tả hứa thứ video không có = metadata gây hiểu lầm; câu kéo tương tác
  (sub4sub, "comment YES"), bình luận lặp hàng loạt.
- Altered/synthetic content: chỉ bắt buộc khai với nội dung TRÔNG NHƯ THẬT; hoạt hình rõ ràng không cần khai.
- Made for Kids: hoạt hình + nhân vật dễ bị gắn nhãn "dành cho trẻ em" → tắt bình luận, giảm đề xuất. Upload luôn gửi
  `selfDeclaredMadeForKids: false` (vidlib/ytupload.py) và chữ khán giả thấy không nhắm tới trẻ em.
- Thông tin y tế sai: không khuyên thay thế điều trị, không hứa chữa khỏi; nội dung sức khoẻ ghi rõ là giáo dục.

Kiểm (mỗi mục → {level: error|warn|info, code, msg}):
- `repeat`: khung hình lặp giữa các video gần đây (khoá khung = beat + bố cục + bộ đạo cụ; `scene` so tập đạo cụ).
- `inner`: một khuôn khung dùng quá nhiều lần trong cùng video.
- `persona`: lời khuyên mệnh lệnh / liều lượng / tự xưng chuyên gia trong video sức khoẻ; mô tả thiếu dòng "không phải
  lời khuyên y tế".
- `promise`: số trong tiêu đề/thumbnail không có trong lời đọc/sổ dữ kiện.
- `shock`: từ giật gân trong tiêu đề/hook/thumbnail (nhắc, không chặn — quảng cáo hạn chế + "off-putting").
- `spam`: quá nhiều hashtag, mô tả/bình luận ghim chép từ video khác, câu kéo tương tác.
- `kids`: chữ khán giả thấy nhắm tới trẻ em.
"""
import os
import re

from .common import PROJECTS, channel, load_json

TEMPLATE_BEATS = {"title", "counter", "compare", "fact", "meter", "dossier", "xray_cutaway", "hero_stat", "callout",
                  "drop", "process", "timeline", "graph", "scale", "split", "units", "zoomin", "outro"}
SHOCK = re.compile(r"\b(kill(s|ed|ing)?|deadly|death|die(s|d)?|dying|destroy(s|ed)?|crush(es|ed)?|explode(s|d)?|"
                   r"toxic|poison(s|ed)?|horrif\w*|terrifying|disgusting|shocking|insane)\b", re.I)
ADVICE = re.compile(r"\b(you (should|must|need to|have to)|always (take|eat|drink)|never (eat|drink|take|run)|"
                    r"take \d+\s*(mg|g|grams?|milligrams?|pills?)|stop (eating|taking|drinking)|cure[sd]?\b|"
                    r"guarantee[sd]?|instead of (seeing|asking) a doctor|skip (the|your) doctor)", re.I)
PERSONA = re.compile(r"\b(as an? (doctor|physician|nurse|dietitian|nutritionist|coach|trainer|physio\w*|expert)|"
                     r"i'?m an? (doctor|physician|nurse|dietitian|nutritionist|coach|trainer|expert))\b", re.I)
BAIT = re.compile(r"\b(sub(scribe)? ?4 ?sub|like (and|&) subscribe (for|to see)|comment ['\"]?(yes|1|me)['\"]? if|"
                  r"type ['\"]?\w+['\"]? in the comments|tag \d+ friends|share (this )?with \d+)\b", re.I)
KIDS = re.compile(r"\b(for kids|kids'? (video|show|cartoon)|children'?s|for children|toddlers?|preschool|nursery)\b", re.I)
NUM = re.compile(r"\d+(?:[.,]\d+)?")
HEALTH_UNIVERSES = {"A", "B"}
HEALTH_WORDS = re.compile(r"\b(muscle|heart|blood|brain|sleep|caffeine|sore|injur\w*|body|run(ning|ner)?|marathon|"
                          r"lift(ing)?|workout|diet|calorie|hormone|glycogen|lactic|endorphin|disc|spine)\b", re.I)


def cfg():
    d = {"recent": 10, "repeat_warn": 0.25, "repeat_error": 0.4, "scene_sim": 0.6, "inner_max": 2,
         "hashtags_max": 15, "copy_sim": 0.8,
         "health_disclaimer": "Educational content, not medical advice."}
    d.update({k: v for k, v in (channel().get("policy") or {}).items() if not k.startswith("_")})
    return d


# ---------- khoá khung hình ----------
def _icons_of(params):
    """Tập đạo cụ một shot dùng (icon + rig loài:hành động) — đi sâu vào actors/left/right/events/evidence…"""
    out = set()

    def walk(x, key=""):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, k)
        elif isinstance(x, list):
            for v in x:
                walk(v, key)
        elif isinstance(x, str) and key == "organs":
            out.add(f"org:{x}")
        elif isinstance(x, str) and key in ("icon", "visual_icon", "shell_icon", "core_icon", "lottie", "rive", "type"):
            s = x.strip().lower()
            if s.startswith("rig:"):
                p = s.split(":")
                s = ":".join(p[:3])
            out.add(s)
    walk(params or {})
    bd = (params or {}).get("backdrop")                     # vòng 22: bối cảnh là một phần của khung
    if bd:
        out.add("bd:" + str(bd.get("kind") if isinstance(bd, dict) else bd))
    return out


def frame_key(shot):
    """(loại, khoá, tập đạo cụ). Shot Flow/không code → None (clip Flow luôn mới)."""
    code = shot.get("code") or {}
    if (shot.get("mode") or shot.get("mode_resolved")) != "code" or not code:
        return None
    scene = str(code.get("scene") or "")
    p = code.get("params") or {}
    icons = _icons_of(p)
    eng = str(code.get("engine") or "")
    if scene in TEMPLATE_BEATS:
        variant = str(p.get("layout") or p.get("kind") or "")
        return ("template", f"{eng or 'html'}:{scene}:{variant}", icons)
    return ("scene", f"{eng or 'code'}:{scene}", icons)


def _jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def same_frame(a, b, sim=None):
    """Hai shot cho ra 'cùng một khung' (chỉ khác chữ/màu)?"""
    if not a or not b or a[1] != b[1]:
        return False
    if a[0] == "template":
        return not a[2] or not b[2] or _jacc(a[2], b[2]) >= 0.5
    sim = cfg()["scene_sim"] if sim is None else sim
    return bool(a[2]) and _jacc(a[2], b[2]) >= sim


# ---------- lịch sử kênh ----------
def _birth(slug):
    from . import motionplan  # noqa: PLC0415
    return motionplan.birth(slug)


def history(slug=None, n=None):
    """[(slug, storyboard)] của N video sinh TRƯỚC slug (mới nhất trước)."""
    from . import motionplan  # noqa: PLC0415
    n = int(n or cfg()["recent"])
    me = _birth(slug) if slug else None
    rows = []
    for s in motionplan.projects():
        if s == slug:
            continue
        b = _birth(s)
        if b is None or (me is not None and b >= me):
            continue
        sb = load_json(os.path.join(PROJECTS, s, "storyboard.json"), None)
        if sb and sb.get("shots"):
            rows.append((b, s, sb))
    rows.sort(key=lambda r: -r[0])
    return [(s, sb) for _, s, sb in rows[:n]]


def repetition(sb, slug=None, hist=None):
    """Shot nào cho ra khung đã thấy ở video gần đây → {rows, ratio, n}."""
    hist = history(slug) if hist is None else hist
    past = [(s, [frame_key(x) for x in (o.get("shots") or [])]) for s, o in hist]
    rows, n = [], 0
    for sh in sb.get("shots") or []:
        k = frame_key(sh)
        if not k:
            continue
        n += 1
        seen = [s for s, keys in past if any(same_frame(k, q) for q in keys if q)]
        if seen:
            rows.append({"sid": sh.get("id"), "key": k[1], "icons": sorted(k[2])[:6], "seen_in": seen[:4]})
    return {"rows": rows, "n": n, "ratio": round(len(rows) / max(1, n), 3)}


def inner_repeats(sb):
    keys = {}
    for sh in sb.get("shots") or []:
        k = frame_key(sh)
        if k and k[0] == "template":
            keys.setdefault(k[1], []).append(sh.get("id"))
    return {k: v for k, v in keys.items() if len(v) > cfg()["inner_max"]}


# ---------- văn bản ----------
def _pub(sb):
    return sb.get("publish") or {}


def _titles(sb):
    pub = _pub(sb)
    yt = pub.get("youtube_shorts") or {}
    return [t for t in (yt.get("titles") or pub.get("titles") or [sb.get("title")]) if t]


def _thumb_texts(sb):
    return [str(v.get("text") or "") for v in ((sb.get("thumbnail") or {}).get("variants") or []) if v.get("text")]


def _vo(sb):
    return " ".join(str(s.get("vo") or "") for s in sb.get("shots") or [])


def _desc(sb):
    pub = _pub(sb)
    return str((pub.get("youtube_shorts") or {}).get("description") or pub.get("description") or "")


def is_health(sb):
    if str(sb.get("universe") or "").upper() in HEALTH_UNIVERSES:
        return True
    return len(HEALTH_WORDS.findall(" ".join([sb.get("topic") or "", sb.get("title") or "", _vo(sb)]))) >= 4


def _nums(text):
    out = set()
    for m in NUM.findall(str(text)):
        v = m.replace(",", "")
        try:
            out.add(float(v))
        except ValueError:
            pass
    return out


_UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                      "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
_SCALE = {"hundred": 100, "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}


def word_numbers(text):
    """Số đọc bằng chữ trong lời đọc: 'forty percent' → 40, 'one point five' → 1.5, 'twenty-four' → 24."""
    out = set()
    for chunk in re.split(r"[,.;:!?—()]+(?:\s|$)", str(text).lower().replace("-", " ")):
        out |= _word_numbers(re.findall(r"[a-z]+", chunk))
    return out


def _word_numbers(toks):
    out, i = set(), 0
    while i < len(toks):
        if toks[i] == "point" and i + 1 < len(toks) and toks[i + 1] in _UNITS and _UNITS[toks[i + 1]] < 10:
            k, dec = i + 1, ""
            while k < len(toks) and toks[k] in _UNITS and _UNITS[toks[k]] < 10:
                dec += str(_UNITS[toks[k]])
                k += 1
            out.add(float("0." + dec))
            i = k
            continue
        if toks[i] not in _UNITS and toks[i] not in _TENS and toks[i] != "a":
            i += 1
            continue
        total, cur, j, got = 0.0, 0.0, i, False
        while j < len(toks):
            w = toks[j]
            if w in _UNITS:
                cur += _UNITS[w]
            elif w in _TENS:
                cur += _TENS[w]
            elif w == "a" and j + 1 < len(toks) and toks[j + 1] in _SCALE:
                cur += 1
            elif w in _SCALE and (cur or got):
                if _SCALE[w] == 100:
                    cur *= 100
                else:
                    total += cur * _SCALE[w]
                    cur = 0
            elif w == "and" and got:
                pass
            else:
                break
            got = True
            j += 1
        if got:
            val = total + cur
            if j + 1 < len(toks) and toks[j] == "point" and toks[j + 1] in _UNITS:
                k, dec = j + 1, ""
                while k < len(toks) and toks[k] in _UNITS and _UNITS[toks[k]] < 10 and not (
                        k + 1 < len(toks) and toks[k + 1] in _SCALE):
                    dec += str(_UNITS[toks[k]])
                    k += 1
                if dec:
                    val = float(f"{int(val)}.{dec}")
                j = k
            if val or toks[i] == "zero":
                out.add(float(val))
        i = max(j, i + 1)
    return out


def _spoken_nums(sb):
    have = set(word_numbers(_vo(sb))) | _nums(_vo(sb))
    for c in sb.get("claims") or []:
        if isinstance(c, dict):
            have |= _nums(c.get("text", "")) | _nums(c.get("value", "")) | word_numbers(c.get("text", ""))
    for sh in sb.get("shots") or []:
        have |= _nums(str((sh.get("code") or {}).get("params") or ""))
    return have


def _words(t):
    return set(re.findall(r"[a-z0-9']+", str(t).lower()))


def lint(sb, slug=None, hist=None):
    c = cfg()
    out = []
    hist = history(slug) if hist is None else hist
    rep = repetition(sb, slug, hist)
    if rep["rows"]:
        lvl = "error" if rep["ratio"] >= c["repeat_error"] else "warn" if rep["ratio"] >= c["repeat_warn"] else "info"
        ex = "; ".join(f"{r['sid']} {r['key']} (đã có ở {', '.join(r['seen_in'][:2])})" for r in rep["rows"][:4])
        out.append({"level": lvl, "code": "repeat",
                    "msg": f"{len(rep['rows'])}/{rep['n']} shot lặp khung của video gần đây "
                           f"({int(rep['ratio'] * 100)}%): {ex}"})
    for k, ids in inner_repeats(sb).items():
        out.append({"level": "warn", "code": "inner",
                    "msg": f"khung {k} dùng {len(ids)} lần trong video ({', '.join(ids)})"})
    vo = _vo(sb)
    if is_health(sb):
        for m in sorted({m.group(0) for m in ADVICE.finditer(vo)})[:3]:
            out.append({"level": "warn", "code": "persona",
                        "msg": f"lời khuyên mệnh lệnh/liều lượng trong VO: “{m}” — kể như "
                        "thông tin có nguồn (“studies found…”), không ra lệnh"})
        disc = str(c.get("health_disclaimer") or "")
        if disc and disc.lower()[:20] not in (_desc(sb) + " " + str(_pub(sb).get("disclaimer") or "")).lower():
            out.append({"level": "info", "code": "persona", "msg": f"mô tả sẽ tự thêm dòng “{disc}” (video sức khoẻ)"})
    for m in PERSONA.finditer(vo + " " + _desc(sb)):
        out.append({"level": "error", "code": "persona", "msg": f"giọng AI tự xưng chuyên gia: “{m.group(0)}”"})
    have = _spoken_nums(sb)
    for t in _titles(sb) + _thumb_texts(sb):
        miss = [x for x in _nums(t) if x not in have and not any(abs(x - h) < 1e-9 for h in have)]
        if miss:
            out.append({"level": "warn", "code": "promise",
                        "msg": f"“{t}”: số {', '.join(f'{x:g}' for x in miss)} không có trong lời đọc/sổ dữ kiện"})
    for t in _titles(sb)[:1] + [sb.get("hook") or ""] + _thumb_texts(sb):
        m = SHOCK.search(str(t))
        if m:
            out.append({"level": "warn", "code": "shock",
                        "msg": f"từ giật gân “{m.group(0)}” trong “{t}” — quảng cáo hạn chế, "
                        "dễ bị xếp 'off-putting'; dùng từ trung tính nếu không cần"})
    pub = _pub(sb)
    yt = pub.get("youtube_shorts") or {}
    tags = list(yt.get("hashtags") or pub.get("hashtags") or [])
    if len(tags) > c["hashtags_max"]:
        out.append({"level": "error", "code": "spam",
                    "msg": f"{len(tags)} hashtag (> {c['hashtags_max']} — YouTube bỏ qua/coi là spam)"})
    texts = " ".join([_desc(sb), str(yt.get("pinned_comment") or ""), str((pub.get("tiktok") or {}).get("caption") or "")])
    for m in BAIT.finditer(texts):
        out.append({"level": "error", "code": "spam", "msg": f"câu kéo tương tác: “{m.group(0)}”"})
    me_d, me_p = _words(_desc(sb)), str(yt.get("pinned_comment") or "").strip().lower()
    for s, o in hist:
        od = _words(_desc(o))
        if me_d and od and _jacc(me_d, od) >= c["copy_sim"]:
            out.append({"level": "warn", "code": "spam", "msg": f"mô tả gần như chép từ {s}"})
        op = str(((o.get("publish") or {}).get("youtube_shorts") or {}).get("pinned_comment") or "").strip().lower()
        if me_p and me_p == op:
            out.append({"level": "warn", "code": "spam", "msg": f"bình luận ghim trùng {s}"})
    aud = " ".join(_titles(sb) + _thumb_texts(sb) + [_desc(sb), vo])
    for m in KIDS.finditer(aud):
        out.append({"level": "warn", "code": "kids",
                    "msg": f"“{m.group(0)}” — dễ bị xếp Made for Kids (tắt bình luận, giảm đề xuất)"})
    return out


def disclaimer_for(sb):
    """Dòng thêm vào cuối mô tả (video sức khoẻ) — rỗng nếu không cần."""
    d = str(cfg().get("health_disclaimer") or "")
    return d if d and is_health(sb) and d.lower()[:20] not in _desc(sb).lower() else ""


def checks(sb, slug=None):
    """Dòng QA: (nhãn → (chi tiết, đạt?)). Nhãn 'khung lặp giữa các video' nằm trong qa.blocking."""
    iss = lint(sb, slug)
    rep = [i for i in iss if i["code"] == "repeat"]
    bad_rep = [i for i in rep if i["level"] == "error"]
    rows = {"khung lặp giữa các video (YouTube: nội dung khuôn mẫu)":
            ((rep[0]["msg"] if rep else "đạt"), not bad_rep)}
    other = [i for i in iss if i["code"] != "repeat" and i["level"] in ("warn", "error")]
    rows["rủi ro YouTube (persona sức khoẻ, metadata, giật gân, spam, Made for Kids)"] = (
        ("; ".join(i["msg"] for i in other[:3]) + (f" (+{len(other) - 3})" if len(other) > 3 else "")) or "đạt",
        not other)
    return rows, iss


def report_md(sb, iss, slug=""):
    L = [f"# Rủi ro chính sách YouTube — {sb.get('title') or slug}", "",
         "Căn cứ + nguồn: docs/YOUTUBE_RISK.md. Mức: error = sửa trước khi đăng · warn = nên sửa · "
         "info = tool tự xử lý.", ""]
    if not iss:
        L.append("Không thấy rủi ro.")
    for i in iss:
        L.append(f"- **{i['level']}** `{i['code']}` — {i['msg']}")
    rep = repetition(sb, slug)
    if rep["rows"]:
        L += ["", "## Shot lặp khung", "", "| Shot | Khung | Đạo cụ | Đã có ở |", "|---|---|---|---|"]
        for r in rep["rows"]:
            L.append(f"| {r['sid']} | `{r['key']}` | {', '.join(r['icons'])} | {', '.join(r['seen_in'])} |")
    return "\n".join(L) + "\n"
