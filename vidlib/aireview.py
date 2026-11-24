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
import time

from . import storyboard as sbm
from .common import StudioError, env, save_json, save_text

DEFAULT_MODEL = "gemini-4-hydrogen"

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
        "summary",
        "issues",
    ],
}


def build_prompt(sb=None):
    sb = sb or {}
    title = sb.get("title") or sb.get("topic") or "Short-form explainer video"
    fmt = sb.get("format_family_resolved") or sb.get("format_family") or "short"
    return (
        f"You are a ruthless senior creative director for viral YouTube Shorts & TikTok science/tech channels "
        f"(like Veritasium, Fern, Johnny Harris, Zack D. Films). Watch this rendered vertical short carefully.\n"
        f"Title: {title}\n"
        f"Intended format family: {fmt}\n\n"
        "Evaluate the video strictly from a real viewer's perspective across 4 criteria (0–10 each):\n"
        "1. clarity_score: Can an average viewer follow the single core logic effortlessly on the first watch?\n"
        "2. muted_hook_score: In the first 3 seconds with sound OFF, is the visual hook & on-screen text instantly clear?\n"
        "3. visual_realism_score: Do the on-screen objects LITERALLY match what is being explained? Penalize heavily if "
        "abstract/confusing clipart icons (stars/atoms/palettes) appear instead of real objects, code, or text.\n"
        "4. pacing_score: Does the viewer have enough time to read text and absorb each visual beat without whiplash?\n\n"
        "Set verdict to:\n"
        "- READY if all scores >= 8 and there are zero high-severity issues.\n"
        "- NEEDS_POLISH if fixable with targeted tweaks.\n"
        "- REDO if visuals are confusing, abstract, too fast, or logic feels broken.\n\n"
        "Write `summary` and every item in `issues` (with exact MM:SS timestamps) in concise, practical Vietnamese."
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
        "",
        "## Nhận xét tổng quan",
        "",
        data.get("summary") or "—",
        "",
    ]
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
    mdl = model or os.environ.get("GEMINI_VIDEO_MODEL", DEFAULT_MODEL)
    client = genai.Client(api_key=api_key)
    log(f"▶ review · tải {os.path.relpath(vid, proj)} ({os.path.getsize(vid) / 1e6:.1f} MB) lên Gemini ({mdl})…")
    uploaded = client.files.upload(file=vid)
    try:
        ready = _wait_active(client, uploaded)
        interaction = client.interactions.create(
            model=mdl,
            input=[
                {"type": "text", "text": build_prompt(sb)},
                {"type": "video", "uri": ready.uri, "mime_type": getattr(ready, "mime_type", None) or "video/mp4"},
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": REVIEW_SCHEMA,
            },
        )
    finally:
        try:
            client.files.delete(name=uploaded.name)
        except Exception:  # noqa: BLE001
            pass

    raw_text = getattr(interaction, "output_text", None) or ""
    if not raw_text:
        raise StudioError("Gemini không trả về kết quả chấm video.")
    data = json.loads(raw_text)
    data["model"] = mdl
    data["video"] = os.path.relpath(vid, proj).replace("\\", "/")

    qa_dir = os.path.join(proj, "qa")
    os.makedirs(qa_dir, exist_ok=True)
    jp = os.path.join(qa_dir, "ai_review.json")
    mp = os.path.join(qa_dir, "ai_review.md")
    save_json(jp, data)
    save_text(mp, format_markdown(data, title=sb.get("title") or os.path.basename(proj), model=mdl))

    log(
        f"✔ Gemini QA: {data['verdict']} · Dễ hiểu {data['clarity_score']}/10 · Tắt tiếng {data['muted_hook_score']}/10 "
        f"· Khớp thực tế {data['visual_realism_score']}/10 · Nhịp {data['pacing_score']}/10"
    )
    log(f"  · {data.get('summary', '')}")
    for it in data.get("issues") or []:
        log(f"  · [{str(it.get('severity', '')).upper()}] {it.get('at')}: {it.get('problem')} → {it.get('fix')}")
    log(f"  · Báo cáo: {mp}")
    return data
