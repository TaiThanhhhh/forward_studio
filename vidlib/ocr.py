"""OCR (Tesseract) để kiểm chữ: text_fx, chữ trong cảnh của shot code, Tầng 2 (AI vẽ) và toàn bộ video.
Ngôn ngữ OCR theo kênh (lang.ocr_lang(): en → "eng").

Tesseract: PATH → biến TESSERACT → C:\\Program Files\\Tesseract-OCR. Dữ liệu ngôn ngữ: assets/tessdata (vie + eng bản
"best"), tải bằng `python studio.py setup-ocr` nếu thiếu.
"""
import glob
import os
import shutil
import subprocess
import tempfile
import unicodedata
from functools import cache

import cv2
import numpy as np
from PIL import Image

from . import lang as langmod
from .common import ASSETS_DIR, StudioError

TESSDATA = os.path.join(ASSETS_DIR, "tessdata")
URLS = {"vie": "https://github.com/tesseract-ocr/tessdata_best/raw/main/vie.traineddata",
        "eng": "https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata"}


@cache
def tesseract():
    for c in (os.environ.get("TESSERACT"), shutil.which("tesseract"),
              r"C:\Program Files\Tesseract-OCR\tesseract.exe", "/opt/homebrew/bin/tesseract", "/usr/bin/tesseract"):
        if c and os.path.exists(c):
            return c
    hits = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"))
    return hits[0] if hits else None


def available():
    return bool(tesseract()) and all(os.path.exists(os.path.join(TESSDATA, f"{x}.traineddata"))
                                     for x in langmod.ocr_lang().split("+"))


def setup():
    """Tải dữ liệu tiếng Việt/Anh cho Tesseract vào assets/tessdata."""
    import urllib.request
    os.makedirs(TESSDATA, exist_ok=True)
    for lang, url in URLS.items():
        p = os.path.join(TESSDATA, f"{lang}.traineddata")
        if not os.path.exists(p):
            urllib.request.urlretrieve(url, p)
    if not tesseract():
        raise StudioError("Chưa cài Tesseract: Windows `winget install UB-Mannheim.TesseractOCR` · macOS `brew install "
                          "tesseract`.")
    return TESSDATA


def norm(s):
    """Chuẩn hoá để so khớp: NFC, in hoa, bỏ khoảng trắng & dấu câu (giữ chữ có dấu, số, °, %)."""
    s = unicodedata.normalize("NFC", s or "").upper()
    s = s.replace("º", "°").replace("˚", "°").replace("’", "'")
    return "".join(c for c in s if c.isalnum() or c in "°%")


def _run(img, psm, lang):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "i.png")
        img.save(p)
        # bật TSV bằng biến (thư mục tessdata riêng không có file cấu hình "tsv")
        cmd = [tesseract(), p, "stdout", "--psm", str(psm), "-l", lang, "--tessdata-dir", TESSDATA,
               "-c", "tessedit_create_tsv=1"]
        r = subprocess.run(cmd, capture_output=True)
    rows = r.stdout.decode("utf-8", "replace").splitlines()[1:]
    words = []
    for ln in rows:
        c = ln.split("\t")
        if len(c) >= 12 and c[11].strip() and float(c[10]) >= 0:
            words.append({"text": c[11], "conf": float(c[10]), "box": tuple(int(v) for v in c[6:10])})
    return words


def prepare(crop, fill=None, tol=95):
    """Ảnh cho OCR: chữ đen trên nền trắng, phóng to. Có màu chữ → tách theo màu (bền với texture/bóng/nền)."""
    a = np.asarray(crop.convert("RGB")).astype(np.int16)
    if fill is not None:
        d = np.sqrt(((a - np.array(fill)) ** 2).sum(-1))
        m = (d < tol).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    else:
        g = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        _, m = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if m.mean() > 127:  # chữ tối trên nền sáng
            m = 255 - m
    m = 255 - m
    h, w = m.shape
    k = 3 if h < 140 else (2 if max(h, w) < 1200 else 1)  # chữ nhỏ (tag) phóng 3×
    m = cv2.resize(m, (w * k, h * k), interpolation=cv2.INTER_CUBIC)
    m = cv2.copyMakeBorder(m, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)
    return Image.fromarray(m)


def read(crop, fill=None, psm=7, lang=None):
    """→ (chuỗi đọc được, độ tin trung bình)."""
    if not available():
        return None, 0.0
    lang = lang or langmod.ocr_lang()
    best = ("", 0.0)
    for f, t in ((fill, 95), (fill, 140), (None, 0)) if fill is not None else ((None, 0),):
        words = _run(prepare(crop, f, t), psm, lang)
        txt = " ".join(w["text"] for w in words)
        conf = float(np.mean([w["conf"] for w in words])) if words else 0.0
        if norm(txt) and conf > best[1]:
            best = (txt, conf)
    return best


def matches(found, expected):
    return bool(found) and norm(found) == norm(expected)


def missing_glyphs(text, font_path, variation=None):
    """Ký tự KHÔNG có glyph trong font (sẽ hiện ô .notdef/bị glyph_safe bỏ) — nguồn sai chính tả thật duy nhất khi chuỗi
    do code vẽ. So ảnh của từng ký tự với ảnh .notdef (một ký tự chắc chắn không có trong font)."""
    from PIL import ImageDraw, ImageFont  # noqa: PLC0415
    f = ImageFont.truetype(font_path, 96)
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:  # noqa: BLE001
            pass

    def ink(ch):
        im = Image.new("L", (220, 220), 0)
        ImageDraw.Draw(im).text((40, 40), ch, font=f, fill=255)
        return np.asarray(im)
    notdef = ink("󰀀")
    out = []
    for ch in sorted(set(text)):
        if ch.isspace():
            continue
        a = ink(ch)
        if not a.any() or np.array_equal(a, notdef):
            out.append(ch)
    return out
