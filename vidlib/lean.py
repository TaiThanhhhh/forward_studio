"""Vòng 23 — đầu ra gọn (`channel.json → output.lean`, mặc định bật).

Chủ kênh chỉ dùng: video, caption theo từng nền tảng, bìa 16:9, tag. Sau khi QA KHÔNG đỏ, mỗi dự án chỉ còn:

    out/final.mp4        video 9:16 (đăng chung cho YouTube Shorts / TikTok / Reels — cùng một file)
    out/cover-16x9.jpg   bìa 16:9 (1280×720)
    out/captions.srt     phụ đề
    out/post.md          tiêu đề / mô tả / tag / hashtag / bình luận ghim / caption theo nền tảng + nguồn + cài đặt đăng

Giữ để làm lại được mà không tốn tiền: storyboard.json, plan.json, idea.txt, script.md, audio/vo.* (lời đọc), file
nhỏ trong work/ (state, timeline, qa.json…). Xoá: khung hình render, stems, mix, video trung gian, version cũ, gói nền
tảng trùng lặp (3 bản MP4 giống nhau), ảnh bìa các tỉ lệ khác, ảnh/báo cáo QA, scripts.html, publish.md.
Cổng QA đỏ → không gọi pack: giữ nguyên mọi thứ để sửa.
"""
import glob
import os
import shutil

from .common import channel, load_json, save_text

SMALL = 1_000_000                       # file trong work/ nhỏ hơn mức này được giữ (state, timeline, qa.json…)
KEEP_ROOT = {"storyboard.json", "plan.json", "idea.txt", "script.md", "ideas.json", "out", "audio", "work",
             "clips", "refs", "frames"}          # clip/ảnh Flow là đồ trả tiền/người dùng đưa → không bao giờ xoá
KEEP_OUT = {"final.mp4", "cover-16x9.jpg", "captions.srt", "post.md", "manifest.json", "rights.json"}


def enabled():
    return bool((channel().get("output") or {}).get("lean", True))


def _size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)


def _rm(p):
    n = _size(p)
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.exists(p):
        os.remove(p)
    return n


def cover(proj):
    """Bìa 16:9: biến thể thumbnail đầu tiên (T1 = khung hook) → out/cover-16x9.jpg."""
    from PIL import Image  # noqa: PLC0415
    out = os.path.join(proj, "out", "cover-16x9.jpg")
    cands = sorted(glob.glob(os.path.join(proj, "thumbnails", "*_youtube.png")))
    if not cands:
        return out if os.path.exists(out) else None
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.open(cands[0]).convert("RGB").save(out, quality=92, optimize=True)
    return out


def post_md(proj, sb, verdict=None):
    """Nội dung copy-dán theo nền tảng — không bảng kiểm, không checklist (chủ kênh không đọc QA)."""
    from . import facts, qareport, seo  # noqa: PLC0415
    p = qareport.platform_seo(sb)
    yt, tt, ig = p["youtube_shorts"], p["tiktok"], p["instagram_reels"]
    desc = (yt.get("description") or "").strip()
    block = facts.description_block(sb)
    if block and "source" not in desc.lower():
        desc = (desc + "\n\n" + block).strip()
    alt = seo.altered_content(sb)
    title = (yt.get("titles") or [sb.get("title") or sb.get("topic") or ""])[0]
    L = [f"# {title}", "",
         "Video `final.mp4` (dùng chung cho mọi nền tảng 9:16) · bìa `cover-16x9.jpg` · phụ đề `captions.srt`"
         + (f" · QA tự động: **{verdict}**" if verdict else ""), "",
         "## YouTube Shorts", "", "**Tiêu đề (chọn 1):**"]
    L += [f"{i + 1}. {t}" for i, t in enumerate(yt.get("titles") or [])]
    L += ["", "**Mô tả:**", "", "```", desc, "", " ".join(f"#{h}" for h in yt.get("hashtags") or []), "```", ""]
    if yt.get("tags"):
        L += ["**Tag (YouTube Studio):**", "", "```", ", ".join(yt["tags"]), "```", ""]
    if yt.get("pinned_comment"):
        L += [f"**Bình luận ghim:** {yt['pinned_comment']}", ""]
    L += [f"**Cài đặt:** Made for kids = **No** · Altered or synthetic content = "
          f"**{'No' if alt is False else 'Yes' if alt else 'tự quyết'}** · Category {seo.category_id(sb)}", ""]
    tags_tt = " ".join(f"#{h}" for h in tt.get("hashtags") or [])
    L += ["## TikTok", "", "```", (tt.get("caption") or "").strip() + " " + tags_tt, "```", ""]
    if tt.get("comment_hook"):
        L += [f"**Bình luận mồi:** {tt['comment_hook']}", ""]
    L += ["## Instagram / Facebook Reels", "", "```",
          (ig.get("caption") or "").strip() + "\n\n" + " ".join(f"#{h}" for h in ig.get("hashtags") or []), "```", ""]
    src = facts.sources_lines(sb)
    if src:
        L += ["## Nguồn", ""] + [f"- {x}" for x in src] + [""]
    return "\n".join(L)


def prune(proj, log=print):
    """Xoá mọi thứ không dùng để đăng / làm lại. Trả số byte đã giải phóng."""
    freed = 0
    work = os.path.join(proj, "work")
    if os.path.isdir(work):
        for e in os.listdir(work):
            p = os.path.join(work, e)
            if os.path.isdir(p) or os.path.getsize(p) >= SMALL:
                freed += _rm(p)
    out = os.path.join(proj, "out")
    if os.path.isdir(out):
        for e in os.listdir(out):
            if e not in KEEP_OUT:
                freed += _rm(os.path.join(out, e))
    for e in os.listdir(proj):
        if e not in KEEP_ROOT:
            freed += _rm(os.path.join(proj, e))
    aud = os.path.join(proj, "audio")
    for f in glob.glob(os.path.join(aud, "vo.prev-*")):     # lời đọc cũ (đã thay)
        freed += _rm(f)
    log(f"  · đầu ra gọn: giải phóng {freed / 1e6:.0f} MB")
    return freed


def pack(proj, sb, verdict=None, log=print):
    """Bìa + post.md rồi dọn. Gọi SAU khi qua cổng QA."""
    c = cover(proj)
    save_text(os.path.join(proj, "out", "post.md"), post_md(proj, sb, verdict))
    freed = prune(proj, log=log)
    return {"cover": c, "post": os.path.join(proj, "out", "post.md"), "freed": freed}


def pack_existing(proj, log=print):
    """Cho dự án đã render xong trước vòng 23: đọc verdict từ work/qa.json; QA đỏ → không đụng."""
    q = load_json(os.path.join(proj, "work", "qa.json"), {}) or {}
    v = q.get("verdict")
    if v == "red" or not os.path.exists(os.path.join(proj, "out", "final.mp4")):
        log(f"  · bỏ qua {os.path.basename(proj)} (QA {v or 'chưa có'} / chưa có final.mp4)")
        return None
    sb = load_json(os.path.join(proj, "storyboard.json"), {})
    word = {"green": "XANH", "yellow": "VÀNG"}.get(v, v)
    return pack(proj, sb, word, log=log)
