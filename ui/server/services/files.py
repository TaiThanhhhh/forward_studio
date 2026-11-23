"""Phục vụ file an toàn: chỉ trong các thư mục gốc cho phép, chặn path traversal, hỗ trợ Range (tua video)."""
import mimetypes
import os

from vidlib.common import PROJECTS, ROOT

# Gốc được phép đọc qua /api/file?root=<key>&path=<tương đối>
ROOTS = {
    "projects": PROJECTS,
    "qa": os.path.join(ROOT, "qa"),
    "styles": os.path.join(ROOT, "styles"),
    "docs": os.path.join(ROOT, "docs"),
    "ideas": os.path.join(ROOT, "ideas"),
    "sfx": os.path.join(ROOT, "assets", "sfx"),
}
WEB_DIR = os.path.join(ROOT, "ui", "web")
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("text/markdown", ".md")


class Forbidden(Exception):
    pass


THUMBS = os.path.join(ROOT, "ui", ".runtime", "thumbs")


def thumbnail(path, w):
    """JPEG rộng w của ảnh `path` (cache theo đường dẫn + mtime + w)."""
    import hashlib  # noqa: PLC0415

    from PIL import Image  # noqa: PLC0415
    key = hashlib.sha1(f"{path}|{os.path.getmtime(path)}|{w}".encode()).hexdigest()[:20]
    out = os.path.join(THUMBS, key + ".jpg")
    if not os.path.exists(out):
        os.makedirs(THUMBS, exist_ok=True)
        im = Image.open(path).convert("RGB")
        im.thumbnail((w, w * 4))
        tmp = out + ".tmp"
        im.save(tmp, "JPEG", quality=82, optimize=True)
        os.replace(tmp, out)
    return out


def safe_join(base, rel):
    """Đường dẫn tuyệt đối của rel trong base; ra ngoài base (../, ổ đĩa khác, symlink) → Forbidden."""
    base = os.path.realpath(base)
    p = os.path.realpath(os.path.join(base, rel.replace("\\", "/").lstrip("/")))
    if os.path.commonpath([base, p]) != base:
        raise Forbidden(rel)
    return p


def resolve(root_key, rel):
    if root_key not in ROOTS:
        raise Forbidden(root_key)
    return safe_join(ROOTS[root_key], rel)


def content_type(path):
    t = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if t.startswith("text/") or t in ("application/json", "text/javascript"):
        t += "; charset=utf-8"
    return t


def parse_range(header, size):
    """'bytes=a-b' → (start, end) bao gồm end; không hợp lệ → None."""
    if not header or not header.startswith("bytes="):
        return None
    spec = header[6:].split(",")[0].strip()
    a, _, b = spec.partition("-")
    try:
        if a == "":
            n = int(b)
            return max(0, size - n), size - 1
        start = int(a)
        end = int(b) if b else size - 1
    except ValueError:
        return None
    if start >= size or start > end:
        return None
    return start, min(end, size - 1)
