"""Nền dùng chung: đường dẫn, cấu hình, ffmpeg, font, màu, easing.

Mọi hằng số đọc từ config/*.json và brand/*.json — không hard-code ở module khác.
"""
import glob
import json
import math
import os
import re
import shutil
import subprocess
import unicodedata
from functools import lru_cache, cache

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config")
BRAND_DIR = os.path.join(ROOT, "brand")
PROMPTS_DIR = os.path.join(ROOT, "prompts")
ASSETS_DIR = os.path.join(ROOT, "assets")
FONT_DIR = os.path.join(ASSETS_DIR, "fonts")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
PROJECTS = os.path.join(ROOT, "projects")

VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".m4v")
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")


class StudioError(Exception):
    """Lỗi có thông điệp tiếng Việt cho người dùng (không in traceback)."""


# ------------------------------------------------------------------ cấu hình
def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise StudioError(f"Thiếu file {os.path.relpath(path, ROOT)}")
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as ex:
            raise StudioError(f"{os.path.relpath(path, ROOT)} không phải JSON hợp lệ: {ex}") from ex


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def replace_retry(src, dst, tries=40, wait=0.25):
    """os.replace có thử lại: trên Windows file đích đang được đọc (vd UI đang phát final.mp4) bị khoá tạm thời."""
    import time  # noqa: PLC0415
    for k in range(tries):
        try:
            os.replace(src, dst)
            return dst
        except PermissionError as e:
            if k == tries - 1:
                raise StudioError(f"Không ghi đè được {dst} — file đang mở ở chương trình khác "
                                  "(đóng trình phát rồi chạy lại).") from e
            time.sleep(wait)
    return dst


def save_text(path, text):
    """Ghi text UTF-8/LF nguyên tử (tạm → đổi tên)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def valid_media(path, min_bytes=1024):
    """File media dùng được: tồn tại, không quá nhỏ (vd 48 byte sau khi bị ngắt), ffprobe đọc ra thời lượng > 0."""
    if not os.path.exists(path) or os.path.getsize(path) < min_bytes:
        return False
    if not path.lower().endswith((".mp4", ".mov", ".m4a", ".wav", ".mp3")):
        return True
    try:
        return probe(path)["duration"] > 0
    except Exception:  # noqa: BLE001
        return False


@cache
def channel():
    return load_json(os.path.join(CONFIG_DIR, "channel.json"))


def env(name):
    """Biến môi trường, hoặc dòng NAME=... trong file .env ở gốc repo (đã gitignore). Không có → None."""
    v = os.environ.get(name)
    if v:
        return v.strip()
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                k, _, val = line.strip().partition("=")
                if k.strip() == name and val.strip():
                    return val.strip().strip('"').strip("'")
    return None


@cache
def brand():
    return load_json(os.path.join(BRAND_DIR, "style.json"))


@cache
def flow_models():
    return load_json(os.path.join(CONFIG_DIR, "flow-models.json"))


@cache
def block(name):
    """Đọc một block prompt cố định trong prompts/blocks/<name>.txt."""
    with open(os.path.join(PROMPTS_DIR, "blocks", name + ".txt"), encoding="utf-8") as f:
        return " ".join(f.read().split())


def fmt():
    f = channel()["format"]
    return f["width"], f["height"], f["fps"]


W, H, FPS = 1080, 1920, 30


def _init_format():
    global W, H, FPS
    try:
        W, H, FPS = fmt()
    except StudioError:
        pass


_init_format()


# ------------------------------------------------------------------ màu
def hex2rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def color(token_or_hex):
    """'accent' → (24, 73, 247); '#ff0000' → (255, 0, 0)."""
    if isinstance(token_or_hex, (tuple, list)):
        return tuple(token_or_hex[:3])
    s = str(token_or_hex)
    if s.startswith("#"):
        return hex2rgb(s)
    return hex2rgb(brand()["colors"][s])


def rgba(token_or_hex, a=1.0):
    return (*color(token_or_hex), int(255 * clamp(a)))


# ------------------------------------------------------------------ ffmpeg
@cache
def ffbin(name="ffmpeg"):
    """Tìm ffmpeg/ffprobe: biến môi trường FFMPEG_DIR → PATH → thư mục winget/choco/scoop phổ biến."""
    exe = name + (".exe" if os.name == "nt" else "")
    env = os.environ.get("FFMPEG_DIR")
    if env and os.path.exists(os.path.join(env, exe)):
        return os.path.join(env, exe)
    found = shutil.which(name)
    if found:
        return found
    pats = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        pats += [os.path.join(la, "Microsoft", "WinGet", "Links", exe),
                 os.path.join(la, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "*", "bin", exe)]
    pats += [r"C:\ffmpeg\bin\\" + exe, r"C:\ProgramData\chocolatey\bin\\" + exe,
             os.path.expanduser(r"~\scoop\shims\\" + exe), "/opt/homebrew/bin/" + name, "/usr/local/bin/" + name]
    for p in pats:
        hits = sorted(glob.glob(p))
        if hits:
            return hits[-1]
    raise StudioError(f"Không tìm thấy {name}. Cài: Windows `winget install Gyan.FFmpeg` · macOS `brew install ffmpeg` "
                      f"(hoặc đặt biến FFMPEG_DIR trỏ tới thư mục chứa {exe}).")


def timeout_for(kind, default):
    """Giây tối đa cho một tiến trình con (config/channel.json → timeouts) — AUD-204: không treo vô hạn."""
    try:
        return float((channel().get("timeouts") or {}).get(kind, default))
    except Exception:  # noqa: BLE001
        return float(default)


def run(cmd, what="ffmpeg", capture=True, timeout=None):
    """Chạy lệnh; cmd[0] là 'ffmpeg'/'ffprobe' sẽ được thay bằng đường dẫn thật. Quá `timeout` giây → lỗi rõ ràng."""
    cmd = list(cmd)
    if cmd[0] in ("ffmpeg", "ffprobe"):
        cmd[0] = ffbin(cmd[0])
    t = timeout if timeout is not None else timeout_for("ffprobe" if "ffprobe" in os.path.basename(cmd[0]) else "ffmpeg",
                                                        120 if "ffprobe" in os.path.basename(cmd[0]) else 3600)
    try:
        r = subprocess.run(cmd, capture_output=capture, timeout=t)
    except subprocess.TimeoutExpired as e:
        raise StudioError(f"{what} chạy quá {t:.0f}s — dừng (timeouts trong config/channel.json).") from e
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", "replace")[-1500:]
        raise StudioError(f"Lỗi {what}:\n{err}")
    return r


def probe(path):
    """ffprobe → dict {width, height, fps, duration, audio_streams, video_codec}."""
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path], "ffprobe")
    data = json.loads(r.stdout.decode("utf-8", "replace"))
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    num, _, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    return {
        "width": int(v.get("width", 0)), "height": int(v.get("height", 0)), "fps": round(fps, 3),
        "duration": float(data.get("format", {}).get("duration", 0) or 0),
        "audio_streams": sum(1 for s in data.get("streams", []) if s.get("codec_type") == "audio"),
        "video_codec": v.get("codec_name", ""),
        "nb_frames": int(v.get("nb_frames", 0) or 0),
    }


# ------------------------------------------------------------------ font
@lru_cache(maxsize=128)
def font(size, weight="black"):
    """Font brand có đủ dấu tiếng Việt, theo chuỗi dự phòng trong brand/style.json."""
    chain = brand().get("fonts", {}).get(weight) or brand()["fonts"]["black"]
    for item in chain:
        fname, _, var = item.partition(":")
        path = os.path.normpath(os.path.join(FONT_DIR, fname))
        if not os.path.exists(path):
            continue
        f = ImageFont.truetype(path, int(size))
        if var:
            try:
                f.set_variation_by_name(var)
            except Exception:  # noqa: BLE001 — font không có trục biến thể
                pass
        return f
    return ImageFont.load_default(size)


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, x):
    return a + (b - a) * x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def db2amp(db):
    return 10 ** (db / 20.0)


# ------------------------------------------------------------------ chữ
def slugify(s, n=48):
    s = unicodedata.normalize("NFKD", s.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    if len(s) > n:  # cắt ở ranh giới từ
        s = s[: n + 1].rsplit("-", 1)[0]
    return s.strip("-") or "video"


def words(text):
    return re.findall(r"[\wÀ-ỹ%°.,]+", text or "")


def syllables(text):
    return len(re.findall(r"[\wÀ-ỹ]+", text or ""))


UNIT_SYL = {"km": 3, "kcal": 4, "cal": 2, "kg": 3, "g": 1, "m": 1, "h": 1, "%": 2, "°c": 2, "x": 1, "vs": 2,
            "ml": 3, "l": 1, "s": 1, "bpm": 3}


def num_syllables(n):
    """Số âm tiết khi đọc số nguyên bằng tiếng Việt (xấp xỉ): 42 → 3, 2700 → 4, 50000 → 3."""
    n = int(n)
    if n <= 10:
        return 1
    if n < 20:
        return 2
    if n < 100:
        return 2 if n % 10 == 0 else 3
    if n < 1000:
        r = n % 100
        return 2 + (0 if r == 0 else 2 if r < 10 else num_syllables(r))
    for base, word in ((10 ** 9, 1), (10 ** 6, 1), (1000, 1)):
        if n >= base:
            r = n % base
            return num_syllables(n // base) + word + (0 if r == 0 else num_syllables(r) + (2 if r < 100 else 0))
    return 1


def spoken_syllables(text):
    """Ước lượng âm tiết khi ĐỌC (số → chữ, đơn vị, từ mượn) — dùng để ước thời lượng lời đọc."""
    total = 0
    for tok in re.findall(r"[0-9][0-9.,]*|[A-Za-zÀ-ỹ°%]+", (text or "").lower()):
        if tok[0].isdigit():
            digits = re.sub(r"[.,]\d{3}", lambda m: m.group(0)[1:], tok).split(",")[0].replace(".", "")
            total += num_syllables(digits) if digits.isdigit() else 1
        elif tok in UNIT_SYL:
            total += UNIT_SYL[tok]
        elif tok.isascii() and len(tok) >= 5:
            total += max(1, len(re.findall(r"[aeiouy]+", tok)))
        else:
            total += 1
    return total


GLYPH_SUB = {"→": "-", "←": "-", "↑": "^", "×": "x", "…": "...", "—": "-", "–": "-", "“": '"', "”": '"'}


def glyph_safe(text, fnt):
    """Thay ký tự font không có (vd '→' trong Be Vietnam Pro) để không bị hổng chữ."""
    out = []
    for ch in text or "":
        if ch.isspace() or ch.isalnum():
            out.append(ch)
            continue
        bbox = fnt.getmask(ch).getbbox()
        out.append(ch if bbox else GLYPH_SUB.get(ch, ""))
    return "".join(out)


def wrap(text, fnt, max_w):
    out, cur = [], ""
    for w_ in (text or "").split():
        test = (cur + " " + w_).strip()
        if fnt.getlength(test) <= max_w or not cur:
            cur = test
        else:
            out.append(cur)
            cur = w_
    if cur:
        out.append(cur)
    return out


def find_file(folder, stems, exts):
    """Tìm <folder>/<stem><ext> không phân biệt hoa thường phần mở rộng."""
    if not os.path.isdir(folder):
        return None
    names = {n.lower(): n for n in os.listdir(folder)}
    for st in stems:
        for e in exts:
            hit = names.get((st + e).lower())
            if hit:
                return os.path.join(folder, hit)
    return None


def ceil_to(values, x):
    """Giá trị nhỏ nhất trong values ≥ x; nếu không có thì giá trị lớn nhất."""
    vals = sorted(values)
    for v in vals:
        if v >= x - 1e-9:
            return v
    return vals[-1] if vals else math.ceil(x)
