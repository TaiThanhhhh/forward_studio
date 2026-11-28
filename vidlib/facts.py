"""Sổ dữ kiện (claims ledger, vòng 21) — mọi con số/khẳng định khán giả thấy hoặc nghe đều truy được về một nguồn.

storyboard.json (tương thích ngược: `sources` kiểu chuỗi cũ vẫn đọc được):
  "sources": [{"id": "S1", "title": "...", "publisher": "NASA", "year": 2023, "url": "https://...",
               "kind": "gov|journal|org|dataset|encyclopedia|news|book|other"}],
  "claims":  [{"id": "K1", "text": "A day on Venus lasts 243 Earth days", "value": 243, "unit": "days",
               "source": "S1" | ["S1", "S2"], "status": "established|estimate|disputed|hypothetical", "quote": "..."}],
  shots[].claims: ["K1"]   ·   shots[].cite: "Source: ..." | false   (chip nguồn trên màn; mặc định tự sinh)

Lint (cảnh báo — chủ kênh quyết): số liệu không có claim · claim thiếu nguồn/URL · nguồn yếu · claim disputed/hypothetical
mà lời đọc không rào đón · từ tuyệt đối/"studies show" không có claim · số trên màn ≠ value của claim · URL không có
trong kết quả tìm kiếm thật (work/research.json) · tỉ lệ vật trong cảnh lệch xa ngoài đời (tắt: `scale_free: true`).
"""
import json
import os
import re
from urllib.parse import urlparse

from .common import channel

STATUSES = ("established", "estimate", "disputed", "hypothetical")
KINDS = ("gov", "journal", "org", "dataset", "encyclopedia", "news", "book", "other")

# Hạng nguồn: A = gốc/sơ cấp (cơ quan nhà nước, tạp chí, viện nghiên cứu, dữ liệu) · B = thứ cấp uy tín · C = đầu mối
# (bách khoa mở — trích tiếp nguồn gốc) · D = yếu (mạng xã hội, blog, trang nội dung tổng hợp).
TIER_A = (".gov", ".mil", ".edu", ".ac.uk", ".ac.jp", ".gov.uk", ".int", "who.int", "nasa.gov", "nih.gov", "cdc.gov",
          "noaa.gov", "esa.int", "nature.com", "science.org", "sciencedirect.com", "springer.com", "wiley.com",
          "cell.com", "thelancet.com", "nejm.org", "bmj.com", "pnas.org", "plos.org", "arxiv.org", "doi.org",
          "pubmed.ncbi", "ncbi.nlm.nih.gov", "jamanetwork.com", "royalsocietypublishing.org", "iea.org",
          "worldbank.org", "oecd.org", "un.org", "ourworldindata.org", "ipcc.ch", "cern.ch", "nobelprize.org")
TIER_B = ("britannica.com", "nationalgeographic.com", "smithsonianmag.com", "si.edu", "scientificamerican.com",
          "newscientist.com", "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "nytimes.com", "theguardian.com",
          "economist.com", "ft.com", "wsj.com", "washingtonpost.com", "npr.org", "pbs.org", "nhm.ac.uk",
          "mayoclinic.org", "clevelandclinic.org", "nhs.uk", "statista.com", "history.com", "space.com",
          "livescience.com", "quantamagazine.org", "arstechnica.com", "ieee.org", "acm.org")
TIER_C = ("wikipedia.org", "wikimedia.org", "wiktionary.org")
TIER_D = ("medium.com", "quora.com", "reddit.com", "youtube.com", "youtu.be", "tiktok.com", "facebook.com",
          "instagram.com", "x.com", "twitter.com", "pinterest.", "blogspot.", "wordpress.com", "substack.com",
          "buzzfeed.com", "boredpanda.com", "ranker.com", "factslides", "thefactsite", "brightside.me",
          "chatgpt.com", "chat.openai.com", "gemini.google.com")
KIND_TIER = {"gov": "A", "journal": "A", "dataset": "A", "org": "B", "book": "B", "news": "B", "encyclopedia": "C",
             "other": "C"}

HEDGE = re.compile(r"\b(if|imagine|could|might|may|would|some|estimated?|estimates?|about|roughly|around|nearly|almost|"
                   r"up to|as (much|many) as|likely|probably|possibly|think|believe|suggests?|disputed|debated?|unclear|"
                   r"nobody knows|no one knows|hypothetical(ly)?|in theory|theoretically|perhaps|maybe|"
                   r"scientists? (think|suspect)|(leading |one )?(idea|theory|hypothes[ie]s)|proposed?|unproven)\b",
                   re.I)
ABSOLUTE = re.compile(r"\b(always|never|100 ?%|one hundred percent|proven|proves|guaranteed|cures?|everyone|nobody|"
                      r"studies show|science says|scientists say|experts say|research shows)\b", re.I)
NUM_WORDS = (r"two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
             r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|"
             r"trillion|percent|dozen|half")
VO_NUM = re.compile(rf"(\d[\d,.]*|\b({NUM_WORDS})\b)", re.I)
DIGIT = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

# Chiều cao điển hình ngoài đời (m) — kiểm tỉ lệ hai vật cùng khung (rig: hộp size bao cả nhân vật)
REAL_SIZE = {
    "rig:adult": 1.7, "rig:scientist": 1.7, "rig:kid": 1.2, "rig:dog": 0.6, "rig:cat": 0.3, "rig:fox": 0.45,
    "rig:wolf": 0.8, "rig:bear": 1.2, "rig:rabbit": 0.3, "rig:mouse": 0.08, "rig:cow": 1.4, "rig:pig": 0.8,
    "rig:horse": 1.6, "rig:sheep": 0.9, "rig:lion": 1.1, "rig:bird": 0.15, "rig:duck": 0.4, "rig:owl": 0.4,
    "rig:fish": 0.3, "rig:frog": 0.1,
    "door": 2.0, "house": 7.0, "building": 30.0, "tree": 8.0, "car": 1.5, "bus": 3.2, "truck": 3.5, "phone": 0.15,
    "smartphone": 0.15, "laptop": 0.3, "cup": 0.1, "coffee": 0.12, "mug": 0.1, "bottle": 0.25, "book": 0.25,
    "chair": 0.9, "bed": 0.6, "apple": 0.08, "burger": 0.1, "pizza": 0.3, "tv": 0.7, "fridge": 1.8, "bicycle": 1.0,
    "bike": 1.0, "rocket": 70.0, "plane": 19.0, "airplane": 19.0,
}
SCALE_TOL = 2.5


def _issue(level, where, msg):
    return {"level": level, "where": where, "msg": msg}


def _cfg():
    return channel().get("facts") or {}


# ------------------------------------------------------------------ chuẩn hoá
def _url_in(text):
    m = re.search(r"https?://\S+", str(text or ""))
    return m.group(0).rstrip(").,;") if m else ""


def domain(url):
    try:
        d = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return d[4:] if d.startswith("www.") else d


def sources(sb):
    """[{id, title, publisher, year, url, kind}] — chuỗi cũ (URL hoặc mô tả) thành object có id S1, S2…"""
    out = []
    for i, s in enumerate((sb or {}).get("sources") or []):
        if isinstance(s, str):
            url = _url_in(s)
            title = re.sub(r"https?://\S+", "", s).strip(" -—:·") or domain(url)
            out.append({"id": f"S{i + 1}", "title": title, "publisher": "", "year": None, "url": url, "kind": ""})
        elif isinstance(s, dict):
            d = dict(s)
            d.setdefault("id", f"S{i + 1}")
            d.setdefault("url", "")
            d.setdefault("title", "")
            d.setdefault("publisher", "")
            d.setdefault("year", None)
            d.setdefault("kind", "")
            out.append(d)
    return out


def claims(sb):
    out = []
    for i, c in enumerate((sb or {}).get("claims") or []):
        if isinstance(c, dict):
            d = dict(c)
            d.setdefault("id", f"K{i + 1}")
            src = d.get("source")
            d["source"] = [src] if isinstance(src, str) else list(src or [])
            d.setdefault("status", "established")
            out.append(d)
    return out


def tier(src):
    """A | B | C | D | ? (không có URL lẫn kind)."""
    d = domain(src.get("url") or "")
    if d:
        if any(x in d for x in TIER_D):
            return "D"
        if any(d.endswith(x) or x in d for x in TIER_A):
            return "A"
        if any(x in d for x in TIER_B):
            return "B"
        if any(x in d for x in TIER_C):
            return "C"
    k = str(src.get("kind") or "").lower()
    return KIND_TIER.get(k, "C" if d else "?")


def short_name(src):
    """'NASA (2023)' — tên ngắn cho chip trên màn/mô tả."""
    name = (src.get("publisher") or "").strip()
    if not name:
        d = domain(src.get("url") or "")
        stem = d.split(".")[-2] if d.count(".") >= 1 else ""
        name = stem.upper() if stem and len(stem) <= 5 else (d or src.get("title") or "")
    if len(name) > 28:
        name = name[:27].rstrip() + "…"
    yr = src.get("year")
    return f"{name} ({yr})" if yr else name


# ------------------------------------------------------------------ số liệu trong shot
_PARAM_NUM_KEYS = {"number", "value", "to", "from", "t", "size", "rate", "values"}
_NUM_BEATS = {"hero_stat", "counter", "compare", "units", "graph", "timeline", "scale", "meter", "split", "dossier"}


def _nums_in(obj, out, depth=0):
    if depth > 5:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _PARAM_NUM_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append(float(v))
            elif k in _PARAM_NUM_KEYS and isinstance(v, str) and DIGIT.search(v):
                out.append(float(DIGIT.search(v).group(0).replace(",", "")))
            elif isinstance(v, (dict, list)):
                _nums_in(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            _nums_in(v, out, depth + 1)


def screen_numbers(shot):
    """Số khán giả THẤY trong shot: chữ text_fx/onscreen có chữ số + tham số số của beat dữ liệu."""
    out = []
    for fx in (shot.get("text_fx") or []) + (shot.get("onscreen") or []):
        for m in DIGIT.finditer(str((fx or {}).get("text", ""))):
            try:
                out.append(float(m.group(0).replace(",", "")))
            except ValueError:
                pass
    code = shot.get("code") or {}
    if code.get("scene") in _NUM_BEATS:
        _nums_in(code.get("params") or {}, out)
    return out


def spoken_numbers(shot):
    return [m.group(0) for m in VO_NUM.finditer(str(shot.get("vo") or ""))]


def _close(a, b):
    if b == 0:
        return abs(a) < 1e-9
    r = abs(a - b) / abs(b)
    return r <= 0.06 or abs(a - b) < 1.0 and abs(b) < 20


# ------------------------------------------------------------------ nghiên cứu đã chạy (URL thật đã thấy)
def research_urls(proj):
    p = os.path.join(proj or "", "work", "research.json")
    if not proj or not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return {u.rstrip("/") for u in data.get("urls") or []}


# ------------------------------------------------------------------ tỉ lệ thực tế
def _real(icon):
    if not isinstance(icon, str):
        return None
    s = icon.strip().lower()
    if s.startswith("rig:"):
        sp = s.split(":")[1] if ":" in s else ""
        from engines.html import rig2d  # noqa: PLC0415 — bí danh rig (puppy → dog…)
        al = dict(rig2d.aliases())
        return REAL_SIZE.get(f"rig:{al.get(sp, sp)}")
    return REAL_SIZE.get(s)


def scale_issues(shot):
    code = shot.get("code") or {}
    p = code.get("params") or {}
    if code.get("scene") != "scene" or p.get("scale_free"):
        return []
    acts = [a for a in p.get("actors") or [] if isinstance(a, dict) and not a.get("scale_free")]
    out = []
    for i, a in enumerate(acts):
        for b in acts[i + 1:]:
            ra, rb = _real(a.get("icon")), _real(b.get("icon"))
            if not ra or not rb or abs((a.get("z") or 0) - (b.get("z") or 0)) > 0.3:
                continue
            sa, sb_ = float(a.get("size", 170)), float(b.get("size", 170))
            want, got = ra / rb, sa / max(1.0, sb_)
            if max(want / got, got / want) > SCALE_TOL:
                out.append(f"{a.get('icon')} ({sa:.0f}px) cạnh {b.get('icon')} ({sb_:.0f}px): ngoài đời tỉ lệ ≈ "
                           f"{want:.2g}× nhưng trong cảnh {got:.2g}× — chỉnh `size` cho đúng thật (hoặc `scale_free: true` "
                           "nếu cố ý phóng đại làm ẩn dụ).")
    return out


# ------------------------------------------------------------------ lint
def lint(sb, proj=None):
    """Danh sách issue {level, where, msg} cho linter.lint (cảnh báo; chủ kênh quyết)."""
    out = []
    srcs, cls = sources(sb), claims(sb)
    sid = {s["id"]: s for s in srcs}
    cid = {c["id"]: c for c in cls}
    seen = research_urls(proj)
    for s in srcs:
        t = tier(s)
        where = f"nguồn {s['id']}"
        if not s.get("url"):
            out.append(_issue("warn", where, f"'{s.get('title') or s.get('publisher')}' thiếu URL — người xem/chủ kênh "
                                             "không "
                                             "kiểm lại được."))
        if t == "D":
            out.append(_issue("warn", where, f"{domain(s.get('url', ''))}: nguồn yếu (mạng xã hội/blog/tổng hợp) — thay "
                                             "bằng "
                                             "nguồn gốc (cơ quan, tạp chí, viện nghiên cứu)."))
        elif t == "C" and domain(s.get("url", "")):
            out.append(_issue("info", where, "bách khoa mở chỉ là đầu mối — trích nguồn gốc mà bài đó dẫn."))
        if seen is not None and s.get("url") and s["url"].rstrip("/") not in seen:
            out.append(_issue("warn", where, f"URL {s['url']} không có trong kết quả tìm kiếm thật (work/research.json) — "
                                             "có thể bị bịa; mở trang kiểm lại."))
    for c in cls:
        where = f"claim {c['id']}"
        if c.get("status") not in STATUSES:
            out.append(_issue("warn", where, f"status '{c.get('status')}' không hợp lệ ({'|'.join(STATUSES)})."))
        if not c["source"]:
            out.append(_issue("warn", where, f"\"{c.get('text', '')[:60]}\" chưa có nguồn (`source`)."))
        for s in c["source"]:
            if s not in sid:
                out.append(_issue("warn", where, f"nguồn '{s}' không có trong `sources`."))
    numeric_shots = []
    for s in sb.get("shots") or []:
        if not isinstance(s, dict):
            continue
        where, refs = s.get("id", "?"), [r for r in (s.get("claims") or []) if isinstance(r, str)]
        for r in refs:
            if r not in cid:
                out.append(_issue("warn", where, f"claim '{r}' không có trong `claims`."))
        vo, scr, spk = str(s.get("vo") or ""), screen_numbers(s), spoken_numbers(s)
        mine = [cid[r] for r in refs if r in cid]
        if (scr or spk) and not mine:
            numeric_shots.append(where)
        for c in mine:
            if c.get("status") in ("disputed", "hypothetical") and vo and not HEDGE.search(vo):
                out.append(_issue("warn", where, f"claim {c['id']} là {c['status']} nhưng lời đọc khẳng định chắc chắn — "
                                                 "thêm "
                                                 "từ rào đón (\"might\", \"scientists think\", \"if\"…)."))
            v = c.get("value")
            if isinstance(v, (int, float)) and scr and not any(_close(x, float(v)) for x in scr):
                out.append(_issue("warn", where, f"số trên màn {sorted(set(scr))[:4]} không khớp claim {c['id']} "
                                                 f"(value {v} {c.get('unit', '')})."))
        if ABSOLUTE.search(vo) and not mine:
            out.append(_issue("warn", where, f"\"{ABSOLUTE.search(vo).group(0)}\" là khẳng định tuyệt đối/viện dẫn chung "
                                             "chung — gắn claim có nguồn hoặc nói mềm lại."))
        for m in scale_issues(s):
            out.append(_issue("warn", where, "tỉ lệ thực tế: " + m))
    if numeric_shots:
        if cls:
            for w in numeric_shots:
                out.append(_issue("warn", w, "có số liệu (lời đọc/trên màn) nhưng chưa gắn claim — thêm "
                                             "`claims: [\"K…\"]`."))
        else:
            out.append(_issue("warn", "facts", f"{len(numeric_shots)} shot có số liệu ({', '.join(numeric_shots[:6])}) "
                                               "nhưng "
                                               "storyboard chưa có sổ dữ kiện `claims` — mỗi con số cần claim + nguồn."))
    return out


# ------------------------------------------------------------------ chip nguồn + publish
def cite_for(sb, shot):
    """Chuỗi chip nguồn của shot ("Source: NASA (2023)") hoặc None."""
    if not _cfg().get("onscreen_cite", True) or not isinstance(shot, dict):
        return None
    c = shot.get("cite")
    if c is False:
        return None
    if isinstance(c, str) and c.strip():
        return c.strip()
    sid = {s["id"]: s for s in sources(sb)}
    cid = {k["id"]: k for k in claims(sb)}
    for r in shot.get("claims") or []:
        k = cid.get(r)
        if not k:
            continue
        names = [short_name(sid[s]) for s in k["source"] if s in sid]
        names = [n for n in names if n]
        if names:
            from . import lang  # noqa: PLC0415
            pre = lang.copy("source_prefix")
            pre = pre if pre and pre != "source_prefix" else "Source"
            lab = " · ".join(dict.fromkeys(names))[:60]
            if k.get("status") == "estimate":
                lab += " · est."
            elif k.get("status") in ("disputed", "hypothetical"):
                lab += f" · {k['status']}"
            return f"{pre}: {lab}"
    return None


def sources_lines(sb, with_url=True):
    out = []
    for s in sources(sb):
        name = short_name(s) or s.get("title") or ""
        title = s.get("title") or ""
        head = f"{title} — {name}" if title and name and title not in name else (title or name)
        out.append(f"{head}{(' — ' + s['url']) if with_url and s.get('url') else ''}")
    return [x for x in out if x.strip()]


def description_block(sb):
    """Dòng nguồn gọn cho mô tả Shorts (link Shorts không bấm được → ghi tên nguồn, đủ để tra)."""
    names = [short_name(s) for s in sources(sb)]
    names = [n for n in dict.fromkeys(names) if n]
    return ("Sources: " + "; ".join(names[:5])) if names else ""


def report_md(sb, issues):
    """qa/facts.md — bảng sổ dữ kiện cho người làm (tiếng Việt)."""
    srcs, cls = sources(sb), claims(sb)
    sid = {s["id"]: s for s in srcs}
    used = {}
    for s in sb.get("shots") or []:
        for r in s.get("claims") or []:
            used.setdefault(r, []).append(s.get("id"))
    L = [f"# Sổ dữ kiện — {sb.get('title') or sb.get('topic', '')}", "",
         f"Nhãn sự thật của ý tưởng: **{sb.get('truth') or '—'}** · {len(cls)} claim · {len(srcs)} nguồn", "",
         "## Claim", "", "| id | khẳng định | giá trị | trạng thái | nguồn | shot |", "|---|---|---|---|---|---|"]
    for c in cls:
        val = f"{c.get('value', '')} {c.get('unit', '')}".strip()
        src = ", ".join(f"{s} ({tier(sid[s])})" if s in sid else f"{s} (?)" for s in c["source"]) or "**thiếu**"
        L.append(f"| {c['id']} | {str(c.get('text', '')).replace('|', '/')} | {val or '—'} | {c.get('status')} | {src} | "
                 f"{', '.join(used.get(c['id'], [])) or '—'} |")
    L += ["", "## Nguồn (hạng A = gốc · B = thứ cấp uy tín · C = đầu mối · D = yếu)", "",
          "| id | hạng | tiêu đề | nơi công bố | năm | URL |", "|---|---|---|---|---|---|"]
    for s in srcs:
        L.append(f"| {s['id']} | {tier(s)} | {str(s.get('title', '')).replace('|', '/')} | {s.get('publisher') or '—'} | "
                 f"{s.get('year') or '—'} | {s.get('url') or '—'} |")
    L += ["", "## Vấn đề", ""]
    L += [f"- {'✖' if i['level'] == 'error' else '⚠' if i['level'] == 'warn' else '·'} [{i['where']}] {i['msg']}"
          for i in issues] or ["- Không có — mọi số liệu đều có claim + nguồn."]
    return "\n".join(L) + "\n"


class CiteChip:
    """Chip nguồn hậu kỳ (mọi engine): giữa đáy sân khấu (Zone B) và dải phụ đề (Zone C), mờ vào/ra theo shot."""

    def __init__(self, sb, w=None, h=None):
        from .common import H, W  # noqa: PLC0415
        self.sb, self.w, self.h, self._cache = sb, w or W, h or H, {}
        grid = channel().get("layout_grid") or {}
        st, cap = (grid.get("stage") or [390, 1240])[1], (grid.get("captions") or [1340, 1460])[0]
        self.cy = int((st + cap) / 2) if cap > st else st + 40

    def _sprite(self, text):
        if text in self._cache:
            return self._cache[text]
        from PIL import Image, ImageDraw  # noqa: PLC0415

        from .common import font  # noqa: PLC0415
        f = font(26, "semibold")
        tw = int(f.getlength(text))
        w, h = tw + 36, 44
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(8, 10, 14, 170), outline=(255, 255, 255, 46), width=1)
        d.text((18, h // 2), text, font=f, fill=(226, 230, 236, 235), anchor="lm")
        self._cache[text] = im
        return im

    def draw(self, img, shot, i, n):
        text = cite_for(self.sb, shot)
        if not text or n <= 0:
            return img
        k = min(1.0, max(0.0, (i - 6) / 8.0)) * min(1.0, max(0.0, (n - 1 - i) / 6.0))
        if k <= 0.01:
            return img
        sp = self._sprite(text)
        if k < 0.999:
            a = sp.getchannel("A").point(lambda v: int(v * k))
            sp = sp.copy()
            sp.putalpha(a)
        out = img.convert("RGBA") if img.mode != "RGBA" else img.copy()
        x = max(16, (self.w - sp.width) // 2)
        out.alpha_composite(sp, (x, int(self.cy - sp.height / 2)))
        return out.convert("RGB")
