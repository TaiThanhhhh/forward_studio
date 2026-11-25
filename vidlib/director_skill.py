"""Cẩm nang nghề sống (`brand/DIRECTOR_SKILL.md`) — nạp vào brief/QA và tự tích luỹ qua `studio.py learn`."""
from datetime import date
import os

from .common import BRAND_DIR, StudioError, save_text

SKILL_PATH = os.path.join(BRAND_DIR, "DIRECTOR_SKILL.md")
LEARNED_HEADER = "## 4. Bài học thực chiến đã tích luỹ (tự cập nhật bằng `studio.py learn`)"
VALID_CATEGORIES = ("visual", "pacing", "script", "2d", "audio", "qa")


def load_text(path=None):
    """Đọc toàn bộ nội dung `brand/DIRECTOR_SKILL.md` (trả về chuỗi rỗng nếu chưa tồn tại)."""
    p = path or SKILL_PATH
    if not os.path.isfile(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read().strip()


def brief_block(path=None):
    """Khối tóm tắt cẩm nang nghề để nhúng vào `prompts/storyboard_brief.md`."""
    txt = load_text(path)
    if not txt:
        return ""
    return (
        "### CHANNEL DIRECTOR SKILL (Living Craft Rules — `brand/DIRECTOR_SKILL.md`)\n"
        "Follow every principle, anti-slop rule, and learned lesson below strictly:\n\n"
        + txt
    )


def list_lessons(path=None):
    """Trích danh sách các dòng bài học trong mục `## 4.`."""
    txt = load_text(path)
    if not txt:
        return []
    out = []
    in_sec = False
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("## 4."):
            in_sec = True
            continue
        if in_sec and s.startswith("## "):
            break
        if in_sec and s.startswith("- "):
            out.append(s[2:].strip())
    return out


def add_lesson(lesson, category="visual", path=None):
    """Thêm 1 bài học mới vào `brand/DIRECTOR_SKILL.md` (tránh trùng lặp nguyên văn)."""
    clean = " ".join(str(lesson or "").split()).strip()
    if not clean:
        raise StudioError("Nội dung bài học không được để trống.")
    cat = str(category or "visual").strip().lower()
    if cat not in VALID_CATEGORIES:
        raise StudioError(f"Nhóm '{cat}' không hợp lệ (chọn: {', '.join(VALID_CATEGORIES)}).")

    p = path or SKILL_PATH
    existing = load_text(p)
    entry = f"- [{cat} · {date.today().isoformat()}] {clean}"
    if clean.lower() in existing.lower():
        return p, entry, False

    if not existing:
        content = f"# DIRECTOR SKILL\n\n{LEARNED_HEADER}\n{entry}\n"
    elif "## 4." in existing:
        content = existing.rstrip() + "\n" + entry + "\n"
    else:
        content = existing.rstrip() + f"\n\n{LEARNED_HEADER}\n{entry}\n"
    save_text(p, content)
    return p, entry, True
