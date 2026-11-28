"""SEO đa nền tảng chuẩn hiện đại (vòng 21) — chạy ở bước `prompts` (linter) và khi ghi publish.md / upload YouTube.

Nguyên tắc (đã kiểm trong tài liệu nền tảng; chi tiết + nguồn ở docs/ROUND21_REPORT.md):
- Shorts được tìm qua tiêu đề, mô tả, hashtag VÀ lời nói (YouTube tạo transcript) → từ khoá chính
  (`publish.primary_keyword`) phải nằm trong ~40 ký tự đầu của tiêu đề, câu đầu mô tả và lời đọc 1–2 shot đầu.
- 3 hashtag đầu của mô tả hiện ngay trên tiêu đề → 2–4 hashtag tập trung, không nhồi.
- Link trong mô tả/bình luận Shorts KHÔNG bấm được → ghi tên nguồn (Sources: NASA (2023); …), không phụ thuộc link.
- Tag YouTube Studio ≤ 500 ký tự, trọng số thấp — chỉ cho lỗi chính tả/biến thể từ khoá.
- KHÔNG gắn tên kênh/thương hiệu khác vào metadata (spam/metadata gây hiểu lầm) — `seo.brand_blocklist` (lỗi chặn).
- `status.containsSyntheticMedia` (YouTube Data API): video toàn hoạt hình code → false; có clip AI trông như thật →
  chủ kênh quyết (`publish.youtube_shorts.altered_content`), tool nhắc khi chưa quyết.
"""
import re

from .common import channel

STOP = {"a", "an", "the", "of", "in", "on", "to", "for", "and", "or", "is", "are", "was", "be", "it", "its", "your", "you",
        "why", "how", "what", "when", "who", "does", "do", "did", "can", "this", "that", "with", "from", "by", "at", "as",
        "if", "into", "out", "up", "my", "we", "our", "they", "their", "than", "then", "so", "just", "really", "actually",
        "happens", "happen", "explained", "shorts"}
WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def _cfg():
    return channel().get("seo") or {}


def words(text):
    return [w for w in WORD.findall(str(text or "").lower()) if w not in STOP and len(w) > 1]


def _stem(w):
    for suf in ("ing", "ies", "es", "s", "ed"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def covers(keyword, text, need=0.7):
    """Văn bản chứa ≥ need phần từ nội dung của từ khoá (so gốc từ: brain/brains, sleep/sleeping)."""
    kw = {_stem(w) for w in words(keyword)}
    if not kw:
        return True
    have = {_stem(w) for w in words(text)}
    return len(kw & have) / len(kw) >= need


def _pub(sb):
    return (sb or {}).get("publish") or {}


def primary_keyword(sb):
    """publish.primary_keyword → tag YouTube đầu tiên → tiêu đề đầu (bỏ hư từ)."""
    pub = _pub(sb)
    kw = str(pub.get("primary_keyword") or "").strip()
    if kw:
        return kw, True
    yt = pub.get("youtube_shorts") or {}
    tags = [t for t in (yt.get("tags") or []) if str(t).strip()]
    if tags:
        return str(tags[0]).strip(), False
    titles = yt.get("titles") or pub.get("titles") or [sb.get("title") or sb.get("topic") or ""]
    return " ".join(words(titles[0])[:3]), False


# ------------------------------------------------------------------ brand safety
def _audience_texts(sb):
    """[(nơi, chữ)] — mọi chữ khán giả thấy/nghe."""
    pub, out = _pub(sb), []
    for k in ("title", "caption"):
        if sb.get(k):
            out.append((k, sb[k]))
    out += [("hashtags", h) for h in sb.get("hashtags") or []]
    for k in ("titles", "hashtags"):
        out += [(f"publish.{k}", t) for t in pub.get(k) or []]
    if pub.get("description"):
        out.append(("publish.description", pub["description"]))
    for plat, keys in (("youtube_shorts", ("titles", "description", "hashtags", "tags", "pinned_comment")),
                       ("tiktok", ("caption", "hashtags", "search_query", "comment_hook")),
                       ("instagram_reels", ("caption", "hashtags"))):
        blk = pub.get(plat) or {}
        for k in keys:
            v = blk.get(k)
            for t in (v if isinstance(v, list) else [v] if v else []):
                out.append((f"publish.{plat}.{k}", t))
    for lg, blk in (pub.get("localizations") or {}).items():
        for k in ("title", "description"):
            if isinstance(blk, dict) and blk.get(k):
                out.append((f"publish.localizations.{lg}.{k}", blk[k]))
    for v in (sb.get("thumbnail") or {}).get("variants") or []:
        if isinstance(v, dict) and v.get("text"):
            out.append((f"thumbnail {v.get('id', '')}", v["text"]))
    if (sb.get("outro") or {}).get("teaser"):
        out.append(("outro.teaser", sb["outro"]["teaser"]))
    for s in sb.get("shots") or []:
        if not isinstance(s, dict):
            continue
        sid = s.get("id", "?")
        if s.get("vo"):
            out.append((f"{sid} vo", s["vo"]))
        for fx in (s.get("text_fx") or []) + (s.get("onscreen") or []):
            if isinstance(fx, dict) and fx.get("text"):
                out.append((f"{sid} chữ", fx["text"]))
        p = (s.get("code") or {}).get("params") or {}
        for k in ("kicker", "title", "text", "label", "headline"):
            if isinstance(p.get(k), str):
                out.append((f"{sid} chữ cảnh", p[k]))
        for lab in p.get("labels") or []:
            if isinstance(lab, dict) and lab.get("text"):
                out.append((f"{sid} nhãn", lab["text"]))
    return out


def _prompt_texts(sb):
    out = []
    for v in (sb.get("thumbnail") or {}).get("variants") or []:
        if isinstance(v, dict) and v.get("scene"):
            out.append((f"thumbnail {v.get('id', '')} scene", v["scene"]))
    for s in sb.get("shots") or []:
        if not isinstance(s, dict):
            continue
        sf = s.get("start_frame") or {}
        if isinstance(sf, dict) and sf.get("desc"):
            out.append((f"{s.get('id')} start_frame", sf["desc"]))
        for a in s.get("action") or []:
            if isinstance(a, dict) and a.get("do"):
                out.append((f"{s.get('id')} action", a["do"]))
    return out


def _brand_re():
    names = [n for n in _cfg().get("brand_blocklist") or [] if n.strip()]
    if not names:
        return None
    return re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(n.lower()) for n in names) + r")(?![a-z0-9])", re.I)


def brand_hits(sb):
    """([(nơi, tên)] chữ khán giả thấy, [(nơi, tên)] prompt hình) chứa tên kênh/thương hiệu tham chiếu."""
    rx = _brand_re()
    if rx is None:
        return [], []

    def scan(items):
        return [(w, m.group(1)) for w, t in items for m in [rx.search(str(t))] if m]
    return scan(_audience_texts(sb)), scan(_prompt_texts(sb))


# ------------------------------------------------------------------ YouTube metadata
def category_id(sb):
    """Category YouTube: publish.youtube_shorts.category (tên hoặc số) → suy theo chủ đề (27 Education / 28 Sci&Tech)."""
    cats = _cfg().get("category") or {"education": 27, "science_tech": 28}
    want = (_pub(sb).get("youtube_shorts") or {}).get("category")
    if isinstance(want, int) or (isinstance(want, str) and want.isdigit()):
        return str(int(want))
    if isinstance(want, str) and want in cats:
        return str(cats[want])
    yt = _pub(sb).get("youtube_shorts") or {}
    tags = [str(t) for t in (_pub(sb).get("hashtags") or []) + (yt.get("hashtags") or []) + (yt.get("tags") or [])]
    tags.append(str(_pub(sb).get("primary_keyword") or ""))
    text = " ".join([str(sb.get("topic") or ""), str(sb.get("title") or "")] + tags)
    edu = set(_cfg().get("education_tags") or [])
    return str(cats.get("education", 27) if set(words(text)) & edu else cats.get("science_tech", 28))


def altered_content(sb):
    """True/False cho `status.containsSyntheticMedia`; None = chưa quyết (có clip Flow mà chủ kênh chưa ghi)."""
    want = (_pub(sb).get("youtube_shorts") or {}).get("altered_content")
    if isinstance(want, bool):
        return want
    shots = [s for s in sb.get("shots") or [] if isinstance(s, dict)]
    if shots and all(s.get("code") or s.get("mode") == "code" for s in shots):
        return False                                   # toàn hoạt hình dựng bằng code: không phải cảnh thật
    return None


def localizations(sb):
    """{lang: {title, description}} hợp lệ từ publish.localizations (tiêu đề ≤ 100 ký tự)."""
    out = {}
    for lg, blk in (_pub(sb).get("localizations") or {}).items():
        if isinstance(blk, dict) and blk.get("title") and re.fullmatch(r"[a-z]{2}(-[A-Z]{2})?", str(lg)):
            out[lg] = {"title": str(blk["title"])[:100], "description": str(blk.get("description") or "")[:5000]}
    return out


# ------------------------------------------------------------------ lint + điểm
def checks(sb):
    """[(nhãn, đạt?, gợi ý)] — bảng SEO cho publish.md / QA."""
    pub = _pub(sb)
    yt = pub.get("youtube_shorts") or {}
    titles = [str(t) for t in (yt.get("titles") or pub.get("titles") or []) if str(t).strip()]
    title = titles[0] if titles else str(sb.get("title") or "")
    desc = str(yt.get("description") or pub.get("description") or "")
    first_sent = re.split(r"(?<=[.!?])\s", desc.strip(), maxsplit=1)[0] if desc.strip() else ""
    kw, explicit = primary_keyword(sb)
    lim = int(_cfg().get("title_keyword_chars", 40))
    early_vo = " ".join(str(s.get("vo") or "") for s in (sb.get("shots") or [])[:2] if isinstance(s, dict))
    tags = [str(t) for t in yt.get("tags") or []]
    tag_chars = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)
    hashtags = yt.get("hashtags") or pub.get("hashtags") or []
    caps = [w for w in re.findall(r"\b[A-Z]{3,}\b", title) if w not in {"DNA", "NASA", "USA", "CPU", "GPU", "API", "WHO"}]
    aud, _ = brand_hits(sb)
    has_claims = bool(sb.get("claims"))
    return [
        ("có từ khoá chính (publish.primary_keyword)", explicit,
         f"đang suy ra: \"{kw}\" — ghi rõ cụm người ta thật sự gõ tìm"),
        (f"từ khoá trong {lim} ký tự đầu tiêu đề", covers(kw, title[:lim]), f"đưa \"{kw}\" lên đầu tiêu đề: {title!r}"),
        ("từ khoá trong câu đầu mô tả", covers(kw, first_sent), "câu đầu mô tả nên chứa đúng từ khoá"),
        ("từ khoá được NÓI ở 1–2 shot đầu", covers(kw, early_vo, 0.5),
         "YouTube đọc transcript — nói từ khoá trong ~3 giây đầu"),
        ("tiêu đề 30–60 ký tự", 30 <= len(title) <= 60, f"hiện {len(title)} ký tự"),
        ("tiêu đề không IN HOA/!!! kiểu giật tít", len(caps) <= 1 and "!!" not in title, f"bớt: {caps}"),
        ("2–4 hashtag tập trung", 2 <= len(hashtags) <= 4, f"hiện {len(hashtags)}"),
        ("tag ≤ 500 ký tự", tag_chars <= int(_cfg().get("tags_max_chars", 500)), f"hiện {tag_chars}"),
        ("không tên kênh/thương hiệu khác", not aud, "; ".join(f"{w}: {n}" for w, n in aud[:4])),
        ("mô tả có nguồn", (not has_claims) or "source" in desc.lower(),
         "tool tự thêm dòng 'Sources: …' khi upload — vẫn nên viết vào mô tả"),
    ]


def score(sb):
    rows = checks(sb)
    return round(100 * sum(1 for _, ok, _ in rows if ok) / max(1, len(rows))), rows


def lint(sb):
    """Issue {level, where, msg} cho linter.lint: tên kênh khác trong chữ khán giả thấy = LỖI (chặn); còn lại cảnh báo."""
    out = []
    aud, prm = brand_hits(sb)
    for where, name in aud:
        out.append({"level": "error", "where": f"seo {where}",
                    "msg": f"có tên kênh/thương hiệu khác \"{name}\" trong chữ khán giả thấy — xoá (rủi ro chính sách spam/"
                           "metadata gây hiểu lầm; mô tả phong cách bằng từ thể loại: 'flat vector science animation')."})
    for where, name in prm:
        out.append({"level": "warn", "where": f"seo {where}",
                    "msg": f"prompt hình nhắc \"{name}\" — tả thể loại thay vì bắt chước một kênh cụ thể."})
    if not _pub(sb):
        return out
    for label, ok, hint in checks(sb):
        if not ok and label != "không tên kênh/thương hiệu khác":
            out.append({"level": "info" if label.startswith("có từ khoá chính") else "warn", "where": "seo",
                        "msg": f"{label}: {hint}"})
    return out
