"""Auto-upload YouTube Shorts ở chế độ Draft/Private qua YouTube Data API v3.

Tự động lấy file video đã tối ưu (`out/deliver/youtube_shorts/<slug>.mp4`), metadata SEO YouTube Shorts
từ `storyboard.json` (Title ≤ 60 ký tự, Description + 3 hashtags, Studio Tags, Category 28 Science & Technology,
Language `en`), đính kèm phụ đề `captions.srt` (`captions.insert`) và tuỳ chọn đăng Pinned/Seed Comment
(`commentThreads.insert`).

Mặc định luôn tải lên ở chế độ `private` để an toàn với dự án Google Cloud chưa qua Compliance Audit
(và cho phép chủ kênh kiểm tra lại 5 giây trên YouTube Studio trước khi bấm Public / Lên lịch).
"""
from datetime import datetime, timezone
import os

from . import qareport, storyboard
from .common import CONFIG_DIR, StudioError, env, save_json

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
DEFAULT_CLIENT_SECRET = os.path.join(CONFIG_DIR, "yt_client_secret.json")
DEFAULT_TOKEN = os.path.join(CONFIG_DIR, "yt_token.json")
DEFAULT_CATEGORY_ID = "28"  # Science & Technology
PRIVACY_CHOICES = ("private", "unlisted", "public")
MAX_TITLE_CHARS = 100
MAX_DESC_CHARS = 5000
MAX_TAGS_TOTAL_CHARS = 480


def find_video(proj, sb=None):
    """Tìm file video ưu tiên để đăng YouTube Shorts: `<slug>.mp4` → `video.mp4` → `out/final.mp4`."""
    slug = (sb or {}).get("slug") or os.path.basename(os.path.abspath(proj))
    yt_dir = os.path.join(proj, "out", "deliver", "youtube_shorts")
    candidates = [
        os.path.join(yt_dir, f"{slug}.mp4"),
        os.path.join(yt_dir, "video.mp4"),
    ]
    if os.path.isdir(yt_dir):
        for name in sorted(os.listdir(yt_dir)):
            if name.lower().endswith(".mp4"):
                full = os.path.join(yt_dir, name)
                if full not in candidates:
                    candidates.append(full)
    candidates.append(os.path.join(proj, "out", "final.mp4"))
    for path in candidates:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    raise StudioError(
        f"Không tìm thấy video để tải lên YouTube trong {proj} "
        "(chạy `python studio.py video <slug>` trước)."
    )


def find_srt(proj):
    """Tìm file phụ đề `captions.srt` (ưu tiên bản trong gói youtube_shorts)."""
    for path in (
        os.path.join(proj, "out", "deliver", "youtube_shorts", "captions.srt"),
        os.path.join(proj, "out", "captions.srt"),
    ):
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


def _trim_tags(raw_tags, max_total=MAX_TAGS_TOTAL_CHARS):
    """Cắt danh sách YouTube Studio Tags để tổng độ dài an toàn dưới giới hạn 500 ký tự của API."""
    kept = []
    used = 0
    seen = set()
    for t in raw_tags or []:
        s = str(t).strip().lstrip("#")
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        cost = len(s) + (2 if " " in s else 0) + (1 if kept else 0)
        if used + cost > max_total:
            break
        seen.add(key)
        kept.append(s)
        used += cost
    return kept


def build_payload(sb, title_idx=0, privacy="private", category_id=None, made_for_kids=False):
    """Xây payload `videos.insert` (snippet + status [+ localizations]) từ `qareport.platform_seo(sb)['youtube_shorts']`.
    Vòng 21: category theo chủ đề (vidlib/seo.py), `status.containsSyntheticMedia` theo nhãn nội dung tổng hợp,
    dòng "Sources: …" từ sổ dữ kiện, tiêu đề/mô tả đa ngôn ngữ (`publish.localizations`)."""
    from . import facts, seo as seomod  # noqa: PLC0415
    if privacy not in PRIVACY_CHOICES:
        raise StudioError(f"Chế độ privacy không hợp lệ '{privacy}' (chọn: {', '.join(PRIVACY_CHOICES)}).")
    seo = qareport.platform_seo(sb)["youtube_shorts"]
    titles = [str(t).strip() for t in (seo.get("titles") or []) if str(t).strip()]
    if not titles:
        fallback = str(sb.get("title") or sb.get("topic") or "Untitled Short").strip()
        titles = [fallback]
    if title_idx < 0 or title_idx >= len(titles):
        raise StudioError(f"--title-idx phải từ 1 đến {len(titles)} (hiện chọn {title_idx + 1}).")
    title = titles[title_idx][:MAX_TITLE_CHARS].strip()

    desc_base = (seo.get("description") or "").strip()
    hashtags = [str(h).strip().lstrip("#") for h in (seo.get("hashtags") or []) if str(h).strip()]
    tag_line = " ".join(f"#{h}" for h in hashtags)
    if tag_line and tag_line.lower() not in desc_base.lower():
        description = f"{desc_base}\n\n{tag_line}".strip() if desc_base else tag_line
    else:
        description = desc_base
    src_line = facts.description_block(sb)
    if src_line and "source" not in description.lower():
        description = f"{description}\n\n{src_line}".strip()
    from . import policy  # noqa: PLC0415 — vòng 22: video sức khoẻ ghi rõ là nội dung giáo dục (AI persona / y tế)
    disc = policy.disclaimer_for(sb)
    if disc and disc.lower() not in description.lower():
        description = f"{description}\n{disc}".strip()
    description = description[:MAX_DESC_CHARS]

    tags = _trim_tags(seo.get("tags") or [])
    lang_raw = str(sb.get("language") or "en").strip().lower()
    lang = lang_raw.split("-")[0] if lang_raw else "en"

    snippet = {
        "title": title,
        "description": description,
        "categoryId": str(category_id or seomod.category_id(sb) or DEFAULT_CATEGORY_ID),
        "defaultLanguage": lang,
        "defaultAudioLanguage": lang,
    }
    if tags:
        snippet["tags"] = tags

    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": bool(made_for_kids),
    }
    synthetic = seomod.altered_content(sb)
    if synthetic is not None:
        status["containsSyntheticMedia"] = bool(synthetic)
    body = {"snippet": snippet, "status": status}
    loc = seomod.localizations(sb)
    if loc:
        body["localizations"] = loc
    return {
        "body": body,
        "synthetic_undecided": synthetic is None,
        "pinned_comment": (seo.get("pinned_comment") or "").strip(),
        "language": lang,
        "titles": titles,
    }


def _load_youtube_libs():
    """Import lười các thư viện Google API để không ảnh hưởng pipeline chính khi chưa cài."""
    try:
        from google.auth.transport.requests import Request  # noqa: PLC0415
        from google.oauth2.credentials import Credentials  # noqa: PLC0415
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: PLC0415
        from googleapiclient.discovery import build  # noqa: PLC0415
        from googleapiclient.http import MediaFileUpload  # noqa: PLC0415
    except ImportError as ex:
        raise StudioError(
            "Chưa cài thư viện YouTube Data API. Chạy:\n"
            "  pip install google-api-python-client google-auth-oauthlib\n"
            "Xem hướng dẫn chi tiết: docs/YOUTUBE_UPLOAD_SETUP.md"
        ) from ex
    return build, MediaFileUpload, Credentials, Request, InstalledAppFlow


def _media_upload(path, mimetype, resumable=False, chunksize=-1):
    """Tạo đối tượng MediaFileUpload (tách riêng để dễ mock trong unit test)."""
    _, media_cls, _, _, _ = _load_youtube_libs()
    if resumable:
        return media_cls(path, chunksize=chunksize, resumable=True, mimetype=mimetype)
    return media_cls(path, mimetype=mimetype)


def _authorize(client_secret=None, token_path=None, log=print):
    """Xác thực OAuth2 Desktop và trả về client YouTube Data API v3."""
    build, _, creds_cls, req_cls, flow_cls = _load_youtube_libs()
    secret_path = client_secret or env("YOUTUBE_CLIENT_SECRET") or DEFAULT_CLIENT_SECRET
    tok_path = token_path or env("YOUTUBE_TOKEN_PATH") or DEFAULT_TOKEN

    creds = None
    if os.path.isfile(tok_path):
        creds = creds_cls.from_authorized_user_file(tok_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log("  · Đang làm mới OAuth token YouTube…")
            creds.refresh(req_cls())
        else:
            if not os.path.isfile(secret_path):
                raise StudioError(
                    f"Thiếu file OAuth client secret: {secret_path}\n"
                    "Tải file OAuth Desktop Client từ Google Cloud Console, lưu thành "
                    "config/yt_client_secret.json (xem docs/YOUTUBE_UPLOAD_SETUP.md)."
                )
            log("  · Mở trình duyệt để đăng nhập Google / cấp quyền YouTube (chỉ 1 lần đầu)…")
            flow = flow_cls.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(os.path.abspath(tok_path)), exist_ok=True)
        with open(tok_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload(
    proj,
    title_idx=0,
    privacy="private",
    upload_srt=True,
    post_comment=False,
    dry_run=False,
    client_secret=None,
    token_path=None,
    category_id=None,
    service=None,
    log=print,
):
    """Tải video dự án lên YouTube Shorts ở chế độ Draft/Private kèm metadata SEO + captions.srt."""
    sb = storyboard.load(proj)
    vid = find_video(proj, sb)
    srt = find_srt(proj) if upload_srt else None
    payload = build_payload(sb, title_idx=title_idx, privacy=privacy, category_id=category_id)
    body = payload["body"]
    sn = body["snippet"]
    size_mb = os.path.getsize(vid) / (1024 * 1024)

    if dry_run:
        log("▶ YouTube Upload [DRY-RUN — chưa gọi API]")
        log(f"  · Video   : {vid} ({size_mb:.2f} MB)")
        log(f"  · Captions: {srt or '(không có)'}")
        log(
            f"  · Privacy : {body['status']['privacyStatus']} · "
            f"Category: {sn['categoryId']} · Lang: {sn['defaultLanguage']}"
        )
        st = body["status"]
        log("  · Nội dung tổng hợp (containsSyntheticMedia): "
            + ("CHƯA QUYẾT — có clip Flow: ghi publish.youtube_shorts.altered_content" if payload.get("synthetic_undecided")
               else str(st.get("containsSyntheticMedia"))))
        if body.get("localizations"):
            log(f"  · Localizations: {', '.join(body['localizations'])}")
        log(f"  · Title   : {sn['title']} ({len(sn['title'])} chars)")
        log(f"  · Tags    : {', '.join(sn.get('tags') or []) or '(trống)'}")
        log("  · Description:")
        for line in sn["description"].splitlines():
            log(f"      {line}")
        if payload["pinned_comment"]:
            flag = "SẼ ĐĂNG" if post_comment else "tắt (thêm --comment để đăng tự động)"
            log(f"  · Comment ({flag}): {payload['pinned_comment']}")
        return {
            "dry_run": True,
            "video": vid,
            "srt": srt,
            **payload,
        }

    yt = service or _authorize(client_secret=client_secret, token_path=token_path, log=log)
    log(f"▶ Đang tải lên YouTube ({privacy}): {os.path.basename(vid)} ({size_mb:.2f} MB)…")
    media = _media_upload(vid, "video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    req = yt.videos().insert(
        part="snippet,status" + (",localizations" if body.get("localizations") else ""),
        body=body,
        media_body=media,
        notifySubscribers=True,
    )
    resp = None
    while resp is None:
        status_obj, resp = req.next_chunk()
        if status_obj:
            log(f"  · Tiến độ: {int(status_obj.progress() * 100)}%")

    video_id = resp["id"]
    warnings = []
    captions_uploaded = False
    if srt:
        try:
            cap_name = "English" if payload["language"] == "en" else payload["language"]
            cap_body = {
                "snippet": {
                    "videoId": video_id,
                    "language": payload["language"],
                    "name": cap_name,
                    "isDraft": False,
                }
            }
            yt.captions().insert(
                part="snippet",
                body=cap_body,
                media_body=_media_upload(srt, "application/octet-stream"),
            ).execute()
            captions_uploaded = True
            log(f"  ✔ Đã đính kèm phụ đề CC: {os.path.basename(srt)}")
        except Exception as ex:  # noqa: BLE001
            msg = f"Không tải được captions.srt (video đã tải lên thành công): {ex}"
            warnings.append(msg)
            log(f"  ⚠ {msg}")

    comment_posted = False
    if post_comment and payload["pinned_comment"]:
        try:
            yt.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": payload["pinned_comment"]}},
                    }
                },
            ).execute()
            comment_posted = True
            log("  ✔ Đã đăng Seed Comment (vào YouTube Studio để bấm Pin).")
        except Exception as ex:  # noqa: BLE001
            msg = f"Không đăng được comment (video private có thể chưa mở bình luận): {ex}"
            warnings.append(msg)
            log(f"  ⚠ {msg}")

    result = {
        "video_id": video_id,
        "watch_url": f"https://youtube.com/shorts/{video_id}",
        "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
        "privacy": privacy,
        "title": sn["title"],
        "video_file": os.path.relpath(vid, proj).replace("\\", "/"),
        "captions_uploaded": captions_uploaded,
        "comment_posted": comment_posted,
        "warnings": warnings,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(os.path.join(proj, "out", "youtube_upload.json"), result)
    log(f"✔ Tải lên thành công! ID: {video_id}")
    log(f"  · Mở YouTube Studio để duyệt & bật Public/Lên lịch: {result['studio_url']}")
    return result
