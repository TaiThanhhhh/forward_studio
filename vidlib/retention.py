"""Vòng 23 — kiểm "giữ chân người xem" cho Shorts/Reels/TikTok (chủ kênh không đọc QA → cổng tự chặn).

Ba nhóm, mỗi nhóm là một dòng QA (tiền tố nằm trong `qa.blocking` → đỏ chặn xuất bản):

1. **hook** (shot đầu): ≤ 16 từ, có khoảng trống tò mò (câu hỏi / đảo ngược "not…/isn't/actually/but" / con số cụ thể /
   "why/how/what happens"), không mở đầu chậm ("In this video", "Today we", "Hey guys", "Welcome", "Let's talk").
2. **kịch bản giữ chân**: không câu độn ("basically", "let's dive in", "without further ado", "it's important to note"…),
   không xin tương tác trong lời đọc ("like and subscribe", "smash that"…) — vừa phạt giữ chân vừa là rủi ro spam;
   câu ≤ 24 từ; có ít nhất một câu nối lại (re-hook) ở giữa video ("but", "here's the", "the weird part", "turns out",
   câu hỏi…); câu cuối là cú chốt ngắn (≤ 16 từ) hoặc nối về ý mở đầu (xem lại vòng lặp); thời lượng 20–75 s.
3. **diễn viên**: video có ≥ 4 shot người tả thực phải dùng ≥ 2 góc nhìn (nghiêng/chính diện/sau lưng); người chính
   không trùng y hệt (loài + trang phục) với video ngay trước — tránh "cùng một người đổi màu" giữa các ngày.

Trung thực: hook phải đúng với nội dung (không câu kéo sai sự thật) — phần đó do sổ dữ kiện (`facts.py`) và `policy.py`
(số trong tiêu đề phải được nói) đảm nhận; ở đây chỉ đo cấu trúc giữ chân.
"""
import os
import re

from .common import PROJECTS, load_json

SLOW_OPENERS = ("in this video", "today we", "today i", "hey guys", "hi guys", "welcome", "let's talk", "lets talk",
                "have you ever wondered", "so, ", "so today", "in today's")
CURIOSITY = re.compile(r"\?|\b(not|isn't|isnt|aren't|don't|doesn't|never|actually|but|instead|wrong|myth|why|how|what "
                       r"happens|secret|weird|surprising|really|probably|only|just|more than|less than|\w+er than|faster|"
                       r"slower|makes you|can make|kills?|wrecks?|destroys?|shrinks?|crush(es)?|lies|lying|steals?|"
                       r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|"
                       r"hundred|thousand|million|billion|percent)\b|\d", re.I)
FILLER = ("basically", "let's dive in", "lets dive in", "without further ado", "it's important to note", "as we all know",
          "in conclusion", "needless to say", "at the end of the day", "fun fact:")
ENGAGE_BAIT = ("like and subscribe", "smash that", "hit the like", "hit subscribe", "subscribe for more",
               "comment below", "follow for more", "don't forget to like", "share this video")
REHOOK = re.compile(r"\?|\b(but|here's the|heres the|the weird part|the twist|turns out|wait|plot twist|the catch|"
                    r"so why|that's why|here's why|the real|surprisingly|yet)\b", re.I)
STOP = set("the a an of to in on and or is are was were it its you your for with that this as at by be from".split())


def _vo(shot):
    return (shot.get("vo") or "").strip()


def _words(s):
    return re.findall(r"[\w']+", s or "")


def english(sb):
    """Kiểm giữ chân viết cho kênh tiếng Anh — dự án tiếng Việt cũ (không render lại) không áp dụng."""
    lg = str(sb.get("language") or "").lower()
    if lg and not lg.startswith("en"):
        return False
    txt = " ".join(_vo(s) for s in sb.get("shots") or [])
    letters = [ch for ch in txt if ch.isalpha()]
    return not letters or sum(ord(ch) > 127 for ch in letters) / len(letters) < 0.03


def hook_check(sb):
    shots = [s for s in (sb.get("shots") or []) if _vo(s)]
    if not shots:
        return ("không có lời đọc", None)
    first = _vo(shots[0])
    low = first.lower()
    n = len(_words(first))
    probs = []
    if any(low.startswith(o) for o in SLOW_OPENERS):
        probs.append("mở đầu chậm")
    if n > 16:
        probs.append(f"{n} từ (> 16)")
    if not CURIOSITY.search(first):
        probs.append("không có khoảng trống tò mò (câu hỏi/đảo ngược/con số)")
    return (("; ".join(probs) + f" — “{first[:70]}”") if probs else f"đạt — “{first[:60]}”", not probs)


def script_check(sb, duration=None):
    shots = [s for s in (sb.get("shots") or []) if _vo(s)]
    if not shots:
        return ("không có lời đọc", None)
    vos = [_vo(s) for s in shots]
    full = " ".join(vos).lower()
    probs = []
    fill = [f for f in FILLER if f in full]
    if fill:
        probs.append("câu độn: " + ", ".join(fill[:3]))
    bait = [b for b in ENGAGE_BAIT if b in full]
    if bait:
        probs.append("xin tương tác trong lời đọc: " + ", ".join(bait[:2]))
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", " ".join(vos)) if x.strip()]
    long_s = [x for x in sents if len(_words(x)) > 24]
    if long_s:
        probs.append(f"{len(long_s)} câu > 24 từ (“{long_s[0][:40]}…”)")
    mid = vos[2:-1] if len(vos) > 4 else vos[1:-1]
    if len(vos) >= 5 and not any(REHOOK.search(v) for v in mid):
        probs.append("không có câu nối lại (re-hook) ở giữa video")
    last = vos[-1]
    first_kw = {w.lower() for w in _words(vos[0]) if w.lower() not in STOP and len(w) > 3}
    last_kw = {w.lower() for w in _words(last) if w.lower() not in STOP and len(w) > 3}
    if len(_words(last)) > 16 and not (first_kw & last_kw):
        probs.append("câu kết dài và không nối về ý mở đầu")
    if duration is not None and not 20 <= float(duration) <= 75:
        probs.append(f"thời lượng {float(duration):.0f}s ngoài 20–75s")
    return ("; ".join(probs) if probs else f"đạt ({len(sents)} câu)", not probs)


# ------------------------------------------------------------------ diễn viên
def _humans(sb):
    """[(sid, loài, góc, trang phục)] cho mọi diễn viên rig người tả thực trong shot code."""
    from engines.html import rig2d  # noqa: PLC0415
    table = rig2d.table()
    out = []
    for s in sb.get("shots") or []:
        p = ((s.get("code") or {}).get("params") or {})
        for a in p.get("actors") or []:
            r = rig2d.parse(a.get("icon")) if isinstance(a.get("icon"), str) else None
            if not r or table.get(r["species"]) != "human":
                continue
            views = {a.get("view") or r.get("view") or "side"} | {k["view"] for k in a.get("keys") or [] if k.get("view")}
            out.append((s.get("id"), r["species"], views, a.get("outfit") or ""))
    return out


def main_cast(sb):
    """Người xuất hiện nhiều shot nhất: 'loài/trang phục' (None nếu video không có người)."""
    cnt = {}
    for _sid, sp, _v, outfit in _humans(sb):
        cnt[f"{sp}/{outfit}"] = cnt.get(f"{sp}/{outfit}", 0) + 1
    return max(cnt, key=cnt.get) if cnt else None


def _previous(slug):
    from . import motionplan  # noqa: PLC0415
    me = motionplan.birth(slug) if slug else None
    best = None
    for s in os.listdir(PROJECTS) if os.path.isdir(PROJECTS) else []:
        if s == slug or s.startswith(("_", ".", "cmp-")):
            continue
        b = motionplan.birth(s)
        if b is None or (me is not None and b >= me):
            continue
        if best is None or b > best[0]:
            best = (b, s)
    return best[1] if best else None


def cast_check(sb, slug=None):
    hs = _humans(sb)
    if not hs:
        return ("không có người tả thực", True)
    shots = {}
    for sid, _sp, views, _o in hs:
        shots.setdefault(sid, set()).update(views)
    all_views = set().union(*shots.values())
    probs = []
    if len(shots) >= 4 and len(all_views) < 2:
        probs.append(f"{len(shots)} shot người đều một góc ({', '.join(sorted(all_views))}) — thêm góc chính diện/sau lưng")
    prev = _previous(slug) if slug else None
    if prev:
        psb = load_json(os.path.join(PROJECTS, prev, "storyboard.json"), {}) or {}
        mine, theirs = main_cast(sb), main_cast(psb)
        if mine and mine == theirs:
            probs.append(f"người chính trùng video trước ({prev}): {mine}")
    return ("; ".join(probs) if probs else f"đạt — {len(shots)} shot người, góc {', '.join(sorted(all_views))}", not probs)


def checks(sb, slug=None, duration=None):
    """Dòng QA cho pipeline (nhãn bắt đầu bằng tiền tố chặn trong qa.blocking)."""
    if not english(sb):
        return {"hook 2 giây đầu (khoảng trống tò mò)": ("không áp dụng (kịch bản không phải tiếng Anh)", True)}
    return {"hook 2 giây đầu (khoảng trống tò mò)": hook_check(sb),
            "kịch bản giữ chân (độn/xin tương tác/re-hook/kết)": script_check(sb, duration),
            "diễn viên đa dạng (góc nhìn, không lặp người chính)": cast_check(sb, slug)}


def lint(sb, slug=None):
    """Cho linter trước khi render (tiếng Việt, cùng nội dung với QA): [{level, where, msg}]."""
    out = []
    for label, (val, ok) in checks(sb, slug).items():
        if ok is False:
            out.append({"level": "error", "where": "retention", "msg": f"{label}: {val}"})
    return out
