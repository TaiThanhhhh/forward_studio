"""Gemini Multimodal Video QA Reviewer (`python studio.py review <slug>` — Vòng 17).

Gửi trực tiếp `out/final.mp4` lên Gemini API (google-genai Interactions API + Files API, mặc định `gemini-4-hydrogen`)
để AI xem video thật như khán giả YouTube Shorts / TikTok và đánh giá 4 tiêu chí sống còn:
  1. Độ dễ hiểu tổng thể (clarity_score 0..10)
  2. Hiệu quả 3 giây đầu khi tắt tiếng (muted_hook_score 0..10)
  3. Độ khớp thực tế của hình ảnh/vật thể so với lời đọc (visual_realism_score 0..10 — bắt lỗi icon trừu tượng khó hiểu)
  4. Nhịp chuyển cảnh & thời gian đọc (pacing_score 0..10)

Xuất: `qa/ai_review.json` + `qa/ai_review.md`. Tự xoá file tạm trên Gemini Files API sau khi chấm xong.
"""
import json
import os
import tempfile
import time

from . import director_skill
from . import storyboard as sbm
from .common import StudioError, env, run, save_json, save_text

DEFAULT_MODEL = "gemini-4-hydrogen"
FALLBACK_MODELS = (
    "gemini-4-hydrogen",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)
PROXY_THRESHOLD_BYTES = 15 * 1024 * 1024

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["READY", "NEEDS_POLISH", "REDO"],
            "description": "Overall publish readiness verdict.",
        },
        "clarity_score": {"type": "integer", "minimum": 0, "maximum": 10},
        "muted_hook_score": {"type": "integer", "minimum": 0, "maximum": 10},
        "visual_realism_score": {"type": "integer", "minimum": 0, "maximum": 10},
        "pacing_score": {"type": "integer", "minimum": 0, "maximum": 10},
        "poster_frame_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
            "description": "Poster Freeze-Frame Test: if paused on key moments, do frames look print-ready?",
        },
        "anti_slop_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Detected AI-slop flaws (wiggle/flicker, slow zoom, karaoke text, generic icons, mobile clip).",
        },
        "summary": {"type": "string", "description": "Concise 2-sentence Vietnamese critique for the creator."},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "at": {"type": "string", "description": "Timestamp MM:SS (e.g. 00:08)"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "problem": {"type": "string", "description": "Specific visual, pacing, or logic issue (Vietnamese)"},
                    "fix": {"type": "string", "description": "Concrete actionable fix (Vietnamese)"},
                },
                "required": ["at", "severity", "problem", "fix"],
            },
        },
    },
    "required": [
        "verdict",
        "clarity_score",
        "muted_hook_score",
        "visual_realism_score",
        "pacing_score",
        "poster_frame_score",
        "anti_slop_flags",
        "summary",
        "issues",
    ],
}


def build_prompt(sb=None):
    sb = sb or {}
    title = sb.get("title") or sb.get("topic") or "Short-form explainer video"
    fmt = sb.get("format_family_resolved") or sb.get("format_family") or "short"
    skill_txt = director_skill.load_text()
    skill_sec = f"\nChannel Director Craft Rules (`brand/DIRECTOR_SKILL.md`):\n{skill_txt}\n\n" if skill_txt else "\n"
    return (
        f"You are a ruthless senior creative director for viral YouTube Shorts & TikTok 2D/3D explainer channels "
        f"(Kurzgesagt, TED-Ed, The Infographics Show, Veritasium, Fern). Watch this rendered vertical video carefully.\n"
        f"Title: {title}\n"
        f"Intended format family: {fmt}\n"
        f"{skill_sec}"
        "Evaluate the video strictly from a real viewer's perspective across 5 criteria (0–10 each):\n"
        "1. clarity_score: Can an average viewer follow the single core logic effortlessly on the first watch?\n"
        "2. muted_hook_score: In the first 3 seconds with sound OFF, is the visual hook & on-screen text instantly clear?\n"
        "3. visual_realism_score: Do the on-screen objects LITERALLY match what is being explained? Penalize heavily if "
        "abstract/confusing clipart icons (stars/atoms/palettes) replace real objects, characters, code, or text.\n"
        "4. pacing_score: Does the viewer have enough time to read text and absorb each visual beat without whiplash?\n"
        "5. poster_frame_score (Poster Freeze-Frame Test): If paused on key frames, does the layout look clean, balanced, "
        "and aligned enough to print as a poster (zero overlap, zero clipped text, clear focal point, mobile safe zone)?\n\n"
        "Also populate `anti_slop_flags` (empty list if clean) for any of the 5 AI-slop flaws spotted: "
        "gratuitous wiggle/flicker, monotonous slow zoom, karaoke text wall on stage, generic abstract icons, or mobile "
        "safe-zone clipping.\n\n"
        "Set verdict to:\n"
        "- READY if all scores >= 8 and there are zero high-severity issues.\n"
        "- NEEDS_POLISH if fixable with targeted tweaks.\n"
        "- REDO if visuals are confusing, abstract, too fast, or logic feels broken.\n\n"
        "Write `summary`, `anti_slop_flags`, and every item in `issues` (with exact MM:SS timestamps) in concise, practical "
        "Vietnamese with proper Vietnamese diacritics (tiếng Việt có dấu chuẩn, UTF-8)."
    )


def _file_state(fobj):
    st = getattr(fobj, "state", None)
    if st is None:
        return "ACTIVE"
    name = getattr(st, "name", None)
    return str(name or st).upper().split(".")[-1]


def _wait_active(client, uploaded, timeout_sec=180, poll_sec=2.0):
    cur = uploaded
    t0 = time.time()
    while _file_state(cur) == "PROCESSING":
        if time.time() - t0 > timeout_sec:
            raise StudioError(f"Gemini xử lý video quá {timeout_sec}s — thử lại sau.")
        time.sleep(poll_sec)
        cur = client.files.get(name=cur.name)
    state = _file_state(cur)
    if state != "ACTIVE":
        raise StudioError(f"Gemini Files API lỗi trạng thái '{state}' khi xử lý video.")
    return cur


def format_markdown(data, title="", model=""):
    v = data.get("verdict", "NEEDS_POLISH")
    badge = {"READY": "SẴN SÀNG ĐĂNG", "NEEDS_POLISH": "CẦN CHỈNH NHẸ", "REDO": "NÊN LÀM LẠI"}.get(v, v)
    L = [
        f"# Gemini Video QA — {title or 'Video'}",
        "",
        f"- Kết luận: **{v} ({badge})** · Model: `{model or DEFAULT_MODEL}`",
        "",
        "| Tiêu chí | Điểm (/10) |",
        "|---|---:|",
        f"| Độ dễ hiểu tổng thể (`clarity`) | **{data.get('clarity_score', 0)}** |",
        f"| 3 giây đầu khi tắt tiếng (`muted_hook`) | **{data.get('muted_hook_score', 0)}** |",
        f"| Hình ảnh khớp thực tế (`visual_realism`) | **{data.get('visual_realism_score', 0)}** |",
        f"| Nhịp chuyển cảnh & đọc chữ (`pacing`) | **{data.get('pacing_score', 0)}** |",
        f"| Kiểm tra khung hình Poster (`poster_frame`) | **{data.get('poster_frame_score', 0)}** |",
        "",
        "## Nhận xét tổng quan",
        "",
        data.get("summary") or "—",
        "",
    ]
    slop = data.get("anti_slop_flags") or []
    if slop:
        L += ["## Cờ lỗi AI-Slop phát hiện", ""] + [f"- {s}" for s in slop] + [""]
    issues = data.get("issues") or []
    if issues:
        L += ["## Điểm cần sửa theo mốc thời gian", "", "| Mốc | Mức | Vấn đề | Cách sửa |", "|---|---|---|---|"]
        for it in issues:
            L.append(
                f"| `{it.get('at', '00:00')}` | {str(it.get('severity', 'medium')).upper()} "
                f"| {it.get('problem', '')} | {it.get('fix', '')} |"
            )
    else:
        L += ["## Điểm cần sửa", "", "Không phát hiện lỗi hình ảnh/logic nghiêm trọng."]
    return "\n".join(L) + "\n"


def _prepare_upload(vid, log=print):
    """Nếu video > 15 MB, nén bản xem nhanh 480p (~3 MB) để tải lên Gemini nhanh gấp 10 lần mà vẫn đủ đọc chữ."""
    if os.path.getsize(vid) <= PROXY_THRESHOLD_BYTES:
        return vid, False
    fd, tmp = tempfile.mkstemp(prefix="studio_ai_review_", suffix=".mp4")
    os.close(fd)
    try:
        log(f"  · Nén bản xem nhanh 480p từ {os.path.getsize(vid) / 1e6:.1f} MB để tải lên nhanh hơn…")
        run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", vid,
                "-vf", "scale=480:-2",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                tmp,
            ],
            "ffmpeg (ai_review proxy)",
        )
        return tmp, True
    except Exception:  # noqa: BLE001
        if os.path.exists(tmp):
            os.remove(tmp)
        return vid, False


def _is_transient_err(ex):
    msg = str(ex).lower()
    return any(
        k in msg
        for k in ("503", "service_unavailable", "high demand", "429", "too_many_requests", "resource_exhausted", "timed out")
    )


def _model_candidates(model=None):
    if model:
        return [model]
    pref = os.environ.get("GEMINI_VIDEO_MODEL") or DEFAULT_MODEL
    out = [pref]
    for m in FALLBACK_MODELS:
        if m not in out:
            out.append(m)
    return out


def review_video(proj, video_path=None, model=None, log=print):
    """Upload `out/final.mp4` lên Gemini API, chấm điểm đa phương thức và ghi `qa/ai_review.{json,md}`."""
    api_key = env("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise StudioError(
            "Chưa có GEMINI_API_KEY trong .env.\n"
            "  → Lấy API key tại https://aistudio.google.com/apikey (dùng đúng Gmail gói Google AI Pro để nhận $10/tháng)\n"
            "  → Thêm dòng GEMINI_API_KEY=... vào file .env ở gốc repo rồi chạy lại."
        )
    vid = video_path or os.path.join(proj, "out", "final.mp4")
    if not os.path.exists(vid):
        raise StudioError(f"Chưa có video để chấm: {vid}")
    try:
        from google import genai  # noqa: PLC0415
    except ImportError as ex:
        raise StudioError("Chưa cài SDK google-genai. Chạy: pip install -U google-genai") from ex

    sb = sbm.load(proj) or {}
    candidates = _model_candidates(model)
    try:
        client = genai.Client(api_key=api_key, http_options={"retry_options": {"attempts": 1}})
    except TypeError:
        client = genai.Client(api_key=api_key)
    up_path, is_tmp = _prepare_upload(vid, log=log)
    log(
        f"▶ review · tải {os.path.basename(up_path)} "
        f"({os.path.getsize(up_path) / 1e6:.1f} MB) lên Gemini ({candidates[0]})…"
    )
    uploaded = None
    used_model = candidates[0]
    interaction = None
    last_err = None
    try:
        uploaded = client.files.upload(file=up_path)
        ready = _wait_active(client, uploaded)
        prompt = build_prompt(sb)
        mime = getattr(ready, "mime_type", None) or "video/mp4"
        for idx, cand in enumerate(candidates):
            used_model = cand
            try:
                if idx > 0:
                    log(f"  · Model trước đang quá tải → chuyển tự động sang `{cand}`…")
                interaction = client.interactions.create(
                    model=cand,
                    input=[
                        {"type": "text", "text": prompt},
                        {"type": "video", "uri": ready.uri, "mime_type": mime},
                    ],
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": REVIEW_SCHEMA,
                    },
                )
                break
            except Exception as ex:  # noqa: BLE001
                last_err = ex
                if idx + 1 < len(candidates) and _is_transient_err(ex):
                    continue
                raise StudioError(
                    f"Gemini API lỗi với `{cand}`: {ex}\n"
                    "  → Nếu gặp 503 (quá tải Free Tier), thử lại sau 1 phút hoặc liên kết Billing Google AI Pro "
                    "($10/tháng credit) trong Google AI Studio."
                ) from ex
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:  # noqa: BLE001
                pass
        if is_tmp and os.path.exists(up_path):
            try:
                os.remove(up_path)
            except Exception:  # noqa: BLE001
                pass

    raw_text = getattr(interaction, "output_text", None) or ""
    if not raw_text:
        raise StudioError(f"Gemini không trả về kết quả chấm video ({last_err or 'empty output'}).")
    data = json.loads(raw_text)
    data["model"] = used_model
    data["video"] = os.path.relpath(vid, proj).replace("\\", "/")

    qa_dir = os.path.join(proj, "qa")
    os.makedirs(qa_dir, exist_ok=True)
    jp = os.path.join(qa_dir, "ai_review.json")
    mp = os.path.join(qa_dir, "ai_review.md")
    save_json(jp, data)
    save_text(mp, format_markdown(data, title=sb.get("title") or os.path.basename(proj), model=used_model))

    log(
        f"✔ Gemini QA ({used_model}): {data['verdict']} · Dễ hiểu {data['clarity_score']}/10 · "
        f"Tắt tiếng {data['muted_hook_score']}/10 · Khớp thực tế {data['visual_realism_score']}/10 · "
        f"Nhịp {data['pacing_score']}/10 · Poster {data.get('poster_frame_score', '-')}/10"
    )
    log(f"  · {data.get('summary', '')}")
    for it in data.get("issues") or []:
        log(f"  · [{str(it.get('severity', '')).upper()}] {it.get('at')}: {it.get('problem')} → {it.get('fix')}")
    log(f"  · Báo cáo: {mp}")
    return data
