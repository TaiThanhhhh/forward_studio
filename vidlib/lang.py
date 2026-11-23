"""Ngôn ngữ của kênh — một chỗ duy nhất (config/channel.json → language / locale / ui_language).

- language  : ngôn ngữ khán giả THẤY và NGHE (VO, text_fx, outro, thumbnail, tiêu đề, .srt). Hiện tại "en".
- locale    : định dạng số ("en-US" → 1,000°C · 2.5 ; "vi-VN" → 1.000°C · 2,5).
- ui_language: ngôn ngữ giao diện cho người làm (scripts.html, log, báo cáo QA) — "vi".

Đổi ngôn ngữ kênh = sửa `language` (và `locale`) trong config/channel.json; chuỗi khán giả thấy lấy từ
channel.json → copy.<language>.
"""
import re
from functools import cache

from .common import channel

LOCALES = {"en-US": {"thousands": ",", "decimal": "."}, "en-GB": {"thousands": ",", "decimal": "."},
           "vi-VN": {"thousands": ".", "decimal": ","}}
DEFAULT_LOCALE = {"en": "en-US", "vi": "vi-VN"}
OCR_LANG = {"en": "eng", "vi": "vie+eng"}


_PROJECT = {"language": None}


def set_project_language(code):
    """Ngôn ngữ của DỰ ÁN đang chạy (storyboard.language) — dự án tiếng Việt cũ vẫn xử lý đúng khi kênh đã là en.
    None = theo kênh."""
    _PROJECT["language"] = code or None


def language():
    return _PROJECT["language"] or channel().get("language", "en")


def locale():
    if _PROJECT["language"] and _PROJECT["language"] != channel().get("language"):
        return DEFAULT_LOCALE.get(_PROJECT["language"], "en-US")
    return channel().get("locale") or DEFAULT_LOCALE.get(language(), "en-US")


VI_CHARS = set("ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹáàãéèíìóòõúùýĂÂĐÊÔƠƯ")


def detect(texts):
    """Đoán ngôn ngữ của lời đọc (dự án cũ không có trường language): có dấu tiếng Việt → vi."""
    s = " ".join(t or "" for t in texts)
    return "vi" if sum(c in VI_CHARS for c in s) >= 3 else None


def ocr_lang():
    return OCR_LANG.get(language(), "eng")


def copy(key, **kw):
    """Chuỗi khán giả thấy (CTA outro, tag…): channel.json → copy.<language>.<key>."""
    table = channel().get("copy", {}).get(language()) or {}
    s = table.get(key, key)
    return s.format(**kw) if kw else s


# ------------------------------------------------------------------ số
def fmt_number(x, decimals=None, loc=None):
    """1000 → '1,000' (en-US) / '1.000' (vi-VN); 2.5 → '2.5' / '2,5'."""
    sep = LOCALES.get(loc or locale(), LOCALES["en-US"])
    x = float(x)
    if decimals is None:
        decimals = 0 if abs(x - round(x)) < 1e-9 else (1 if abs(x * 10 - round(x * 10)) < 1e-9 else 2)
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "\0").replace(".", sep["decimal"]).replace("\0", sep["thousands"])


def parse_number(s, loc=None):
    """'1,000' / '1.000' / '2.5' / '2,5' → float theo locale (để count_up đọc đúng)."""
    sep = LOCALES.get(loc or locale(), LOCALES["en-US"])
    s = s.strip().replace(sep["thousands"], "").replace(sep["decimal"], ".")
    return float(s)


NUM_IN_TEXT = re.compile(r"\d[\d,.]*\d|\d")

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_SCALES = [(10 ** 12, "trillion"), (10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")]


def int_words(n):
    """Số nguyên → chữ tiếng Anh (Mỹ, không 'and'): 1000 → 'one thousand', 525 → 'five hundred twenty-five'."""
    n = int(n)
    if n < 0:
        return "minus " + int_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return _ONES[n // 100] + " hundred" + (" " + int_words(n % 100) if n % 100 else "")
    for base, name in _SCALES:
        if n >= base:
            return int_words(n // base) + " " + name + (" " + int_words(n % base) if n % base else "")
    return str(n)


def number_words(s):
    """'1,000' → 'one thousand' · '2.5' → 'two point five' · '0.03' → 'zero point zero three' (en)."""
    v = s.replace(",", "") if locale().startswith("en") else s.replace(".", "").replace(",", ".")
    if "." in v:
        whole, frac = v.split(".", 1)
        return int_words(int(whole or 0)) + " point " + " ".join(_ONES[int(c)] for c in frac if c.isdigit())
    return int_words(int(v))


UNITS = [  # (mẫu sau số, đọc số ít, đọc số nhiều) — thứ tự quan trọng (dài trước)
    (r"°\s?C\b", "degree Celsius", "degrees Celsius"), (r"°\s?F\b", "degree Fahrenheit", "degrees Fahrenheit"),
    (r"°", "degree", "degrees"), (r"%", "percent", "percent"), (r"\s?km/h\b", "kilometer per hour", "kilometers per hour"),
    (r"\s?mph\b", "mile per hour", "miles per hour"), (r"\s?kg\b", "kilogram", "kilograms"),
    (r"\s?km\b", "kilometer", "kilometers"), (r"\s?cm\b", "centimeter", "centimeters"),
    (r"\s?mm\b", "millimeter", "millimeters"), (r"\s?ml\b", "milliliter", "milliliters"),
    (r"\s?kcal\b", "kilocalorie", "kilocalories"), (r"\s?bpm\b", "beat per minute", "beats per minute"),
    (r"\s?ms\b", "millisecond", "milliseconds"), (r"\s?g\b", "gram", "grams"), (r"\s?m\b", "meter", "meters"),
    (r"\s?s\b", "second", "seconds"), (r"\s?L\b", "liter", "liters"), (r"×|x\b", "times", "times"),
]
_UNIT_RE = [(re.compile(r"^" + p), one, many) for p, one, many in UNITS]


def spoken(text):
    """Chuẩn hoá để ĐỌC/đếm âm tiết: số + ký hiệu → chữ. '1,000°C' → 'one thousand degrees Celsius'.
    (vi: giữ nguyên — tiếng Việt đếm âm tiết theo common.spoken_syllables.)"""
    if not language().startswith("en") or not text:
        return text or ""
    out, i = [], 0
    for m in NUM_IN_TEXT.finditer(text):
        if m.start() < i:
            continue
        out.append(text[i:m.start()])
        num = m.group(0).rstrip(".,")
        end = m.start() + len(num)
        words = number_words(num)
        rest = text[end:]
        for rx, one, many in _UNIT_RE:
            u = rx.match(rest)
            if u:
                words += " " + (one if num in ("1", "1.0") else many)
                end += u.end()
                break
        if text[m.start() - 1:m.start()] == "-" and (m.start() < 2 or not text[m.start() - 2].isalnum()):
            out[-1] = out[-1][:-1]
            words = "minus " + words
        out.append(words)
        i = end
    out.append(text[i:])
    s = "".join(out)
    return s.replace("&", " and ").replace("→", " to ").replace("×", " times ")


# ------------------------------------------------------------------ âm tiết (tiếng Anh)
def en_syllables(word):
    """Đếm âm tiết một từ tiếng Anh (heuristic của cartoon-short-kit/tools/timing.py, sửa: số đã đổi thành chữ)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    v = re.findall(r"[aeiouy]+", w)
    n = len(v)
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee", "ye")):
        n -= 1
    if w.endswith("ed") and n > 1 and not w.endswith(("ted", "ded")):
        n -= 1
    return max(1, n)


def word_list(text):
    """Từ khi đọc (đã chuẩn hoá số) — dùng cho mật độ lời và căn thời gian."""
    return [w for w in re.split(r"[\s\-–—]+", spoken(text)) if re.search(r"[A-Za-z0-9]", w)]


def syllables_spoken(text):
    if language().startswith("en"):
        return sum(en_syllables(w) for w in word_list(text))
    from .common import spoken_syllables  # noqa: PLC0415 — tiếng Việt: một âm tiết mỗi chữ
    return spoken_syllables(text)


def word_count(text):
    return len(word_list(text))


@cache
def pace():
    """Nhịp đọc mục tiêu: channel.json → script.words_per_sec (kit: ~3.7 từ/giây)."""
    return float(channel().get("script", {}).get("words_per_sec", 3.7))
