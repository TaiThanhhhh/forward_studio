# AUDIT — hiện trạng tool trước khi nâng cấp (13/11/2026)

## 1. Stack & môi trường

| Hạng mục | Hiện trạng |
|---|---|
| Ngôn ngữ | Python (Pillow + numpy) + ffmpeg qua `subprocess`. Không dùng Remotion/HTML render. |
| Entry | `studio.py` (menu số + 8 subcommand), `scripts/0–5_*.command` (bash, chỉ chạy trên macOS) |
| Thư viện | `vidlib/` 11 module, ~2.300 dòng |
| AI lập kế hoạch | `planner.py` sinh `ai_prompt.txt` → người dùng dán vào app Claude/Gemini → dán JSON trả về vào `plan.json` (hoặc `--ai gemini/claude` có API key) |
| Máy hiện tại | Windows 11, Python 3.13 hệ thống (có Pillow 11, numpy 2.2). `.venv/` là venv **macOS** (`/opt/homebrew/...`) nên không chạy được trên Windows. **ffmpeg chưa cài**, đã cài trong lúc audit (`winget install Gyan.FFmpeg` 9.0.2). Shell cũ chưa nhận PATH mới nên tool phải tự dò ffmpeg. |
| Git | Chưa có repo. Đã `git init`, commit baseline `b3715a5`, làm việc trên branch `feat/one-command-pipeline`. |
| Claude Code | **Không có** `CLAUDE.md`, `.claude/commands/`, `.claude/skills/`. |
| Dự án mẫu | `HUONG_DAN.md` nhắc `projects/mau_xoc_hong_khi_chay`, nhưng thư mục `projects/` đang rỗng. |
| Tên trang | Prompt brief nhắc `scripts.html`; tool thực tế sinh **`prompts.html`**. |

## 2. Pipeline hiện tại

```
python studio.py new "chủ đề" [--vo] [--look] [--ai]
   └─ planner.build() ──► projects/<slug>/ai_prompt.txt  (brief cho LLM, ~140 dòng tiếng Việt)
                         projects/<slug>/plan.json       (rỗng → người dùng tự dán JSON từ app AI)
python studio.py prompts <slug>
   └─ plan.load + plan.check (lỗi/cảnh báo)
   └─ page.build ──► prompts.html  (thẻ theo CLIP: 1 ảnh start, 2 ảnh end, 3 video frames, 3b video text, negative)
   └─ page.export_text ──► prompts.txt
[Người dùng: Flow → images/C1_start.png, clips/C1.mp4, audio/vo.mp3]
python studio.py status <slug>     liệt kê file đã có
python studio.py preview <slug>    contact sheet out/preview.jpg
python studio.py build <slug>
   └─ edit.voice_track: tách câu VO theo khoảng lặng ≥120 ms → co/giãn shot cho khớp câu
   └─ edit.render_shot (mỗi shot): ffmpeg đọc clip (-ss in, setpts speed, scale/crop 1080×1920)
        → apply_fx (punch_in/zoom_out_reveal/slow_zoom/shake/freeze) → apply_transition
        → draw_label (1 nhãn/shot) → pipe x264 → out/.work/shotNN.mp4
   └─ concat → mix_audio (SFX tổng hợp + tiếng Flow tuỳ audio_source + VO) → out/<slug>.mp4, caption.txt
python studio.py cover <slug>     images/cover.png (hoặc frame giây 1 của video) + chữ hook → cover_9x16/16x9.jpg
```

**Mô hình dữ liệu:** `plan.json` gồm `clips[]` (lần tạo Flow, mỗi clip ~8 s, 2–4 nhịp hành động) và `shots[]` (dòng thời gian dựng: cắt nhiều shot từ một clip bằng `in`/`dur`). `channel.json` chứa style DNA, 6 "look" (Clean Vector, Grain Print, Blueprint, Glass Layers, Paper Cut, Bold Minimal), negative prompt, màu nhãn teal/amber.

## 3. Đối chiếu 9 vấn đề người dùng nêu

| # | Vấn đề | Nguyên nhân trong code |
|---|---|---|
| 1 | Prompt tách rời, không rõ Frames hay Ingredients | `page.build` in **cả** prompt Frames và Text-to-Video cho mọi clip, kèm một ô Negative riêng. Không có logic chọn mode. Ingredients chỉ được nhắc chung chung là "thêm style_refs vào Ingredients mỗi lần". Không biết ảnh nào làm start, ảnh nào làm end, cũng không có khái niệm `seed_from`. |
| 2 | Chạy nhiều lệnh lẻ | 8 subcommand + 6 script `.command` theo số. Không có trạng thái, không tự biết đang ở bước nào. |
| 3 | Thumbnail nhạt | `cover.py` chỉ dán chữ hook lên ảnh bìa hoặc frame giây 1 (thường là khoảnh khắc nhạt), cộng một lớp gradient tối. Không có archetype, không có khoảng trống tò mò, không có contact sheet. |
| 4 | Prompt chưa tối ưu | Prompt ghép từ ~15 trường tự do. Style DNA dài + "look" + motion language "smooth ease-in-out, settles" **cố ý tạo chuyển động chậm và có đoạn lắng ở cuối**, ngược với yêu cầu snappy. Prompt có thể dài tới 260 từ. Nền gradient slate/teal, không phải đen. |
| 5 | Chưa có outro | Không có code outro. Chỉ có mẹo "khung cuối giống khung đầu" ở mức prompt. |
| 6 | Cắt còn khựng | Shot lấy `in`/`dur` cố định do LLM đoán trước khi có clip, nên không biết đâu là đầu tĩnh, đâu là đuôi giảm tốc. Prompt lại yêu cầu "overshoots slightly and settles", tức là Flow được dặn tạo đúng đoạn khựng. Không phát hiện scene cut, không có QA điểm cắt. |
| 7 | Clip Flow có tiếng lạ | Prompt **xin** Flow tạo SFX/ambient (`flow_sfx`, `flow_ambient`). `channel.json` đang đặt `"audio_source": "both"`, nên tiếng Flow bị trộn thẳng vào bản cuối. `ClipReader` có `-an` nhưng `mix_audio` lại decode tiếng clip. |
| 8 | Chưa có kinetic text | Mỗi shot chỉ có tối đa 1 nhãn pill tĩnh (scale 0.85→1). Không có caption theo VO, không highlight từ đang nói. Font Inter (có hỗ trợ tiếng Việt) nhưng không có preset. |
| 9 | Nhịp chậm, animation nhạt | Clip 8 s, shot 0.8–3.5 s, nhưng hiệu ứng thưa ("không dồn hiệu ứng"). Không có quy tắc "≤ 1,2 s phải có thay đổi". Motion language trong prompt là ease-in-out mềm. VO không cắt lặng, không tăng tốc. |

## 4. Trùng lặp & hard-code

**Trùng lặp**
- `DEFAULT`/`LOOKS` trong `vidlib/channel.py` lặp gần nguyên văn với `channel.json`.
- `_hex()` được định nghĩa 2 lần (`edit.py`, `anims.py`).
- Bảng màu có 3 nơi: `common.THEME` (RGB), `channel.json → labels` (hex), CSS trong `page.py` (hex).
- Danh sách FX/TRANSITIONS: định nghĩa trong `plan.py`, được nhúng lại vào brief của `planner.py` và phần giải thích của `HUONG_DAN.md`.
- Hướng dẫn chọn model Flow bị viết tay ở **2 chỗ**: `HUONG_DAN.md` và chuỗi HTML trong `page.py` ("Omni Flash 1.2… Veo 3.1 Fast/Quality bị gỡ 5/12/2026").
- Logic tìm file (`find`, `VIDEO_EXT`, `IMAGE_EXT`) nằm trong `edit.py` nhưng `studio.py` và `cover.py` cũng import để dùng.

**Hard-code**
- `clip_seconds` là một số duy nhất cho mọi model, không có bảng capability.
- Kích thước 1080×1920, FPS 30 nằm trong `common.py`. Vị trí nhãn y=300/900/1540 nằm trong `edit.draw_label`.
- Đường dẫn script `.command` (mac-only, gọi lệnh `open`).
- `UNIVERSES` (A–E) cố định trong code.
- Tên model AI mặc định nằm trong `planner.py`.

**Code sẽ thành code chết sau nâng cấp:** hệ "look" (6 look + `style_refs/`), Text-to-Video prompt, `audio_source=flow/both`, `images.py` (Ken Burns cho ảnh tĩnh, vẫn hữu ích làm fallback khi chưa có clip, nên sẽ giữ ý tưởng), `plan.py`/`planner.py`/`page.py`/`cover.py`/`edit.py` (thay bằng module mới).

**Giữ lại vì đang chạy tốt:** thư viện SFX tổng hợp (`sfx.py`, không lo bản quyền), các mẫu đồ hoạ code (`anims.py`: counter/bars/flow…), hiệu ứng whip/flash/glitch/punch-in (`edit.py`), cách tách câu VO theo khoảng lặng, linter phát hiện chữ/phủ định/tham chiếu chéo trong prompt, nút copy có fallback `execCommand`, checkbox lưu localStorage có try/catch.

## 5. Brand (từ `assets/brand/avatar.png` + `refs/`)

Đo trực tiếp trên ảnh avatar 1024×1024:
- Nền: `#110F10` (gần đen, phẳng, không texture).
- Nét: trắng `#FFFFFF` tuyệt đối, dày ≈ 40 px/1024 (≈ 3,9% cạnh), đầu nét **vuông**, góc vuông. Hình bậc thang đi lên phải: tiến về phía trước, hợp với tên kênh "forward.".
- Accent: xanh điện `#1849F7` (median của vùng chấm tròn). Chấm tròn có đường kính bằng độ dày nét và tách khỏi nét bằng một khe đen. Đây là motif "điểm bắt đầu".
- Độ tương phản: xanh `#1849F7` trên nền đen chỉ đạt **3,3:1**, quá thấp nếu dùng làm màu chữ. Trắng trên nền xanh đạt **6,3:1**. Kết luận: từ đang nói sẽ là **chữ trắng trên viên pill xanh brand** (giống chấm tròn của avatar), không phải chữ xanh trên nền đen.

`refs/` gồm 6 ảnh chụp một carousel Instagram về "motion skills" (Motion skill, Motion Design/easing, Manim/3Blue1Brown, JS animation, Huashu Art Motion) và danh sách 10 style (Pixel Art … Minimal Line …). Phần liên quan tới brand:
- Manim/3Blue1Brown: nét trắng mảnh trên nền đen tuyệt đối, một khối màu duy nhất, mọi thứ tối giản.
- Bài easing: "timing, easing and choreography". Mọi chuyển động có anticipation/overshoot, có đồ thị cubic-bezier.
- Người que đen tròn đầu chỉ tay, gạch chân màu xanh (gần với xanh brand).

Chi tiết đầy đủ nằm ở `brand/style-bible.md`.

## 6. Skills

- Stack là Python + ffmpeg, **không** dùng Remotion. Vì vậy **không cài** `remotion-dev/skills`.
- Không render bằng HTML/CSS. Skill frontend-design không có trong phiên này và cũng không cần.
- Repo chưa có skill nào. Sẽ thêm `.claude/commands/video.md` (slash command `/video`).

## 7. Google Flow

Đã kiểm chứng bằng web search. Kết quả nằm ở `config/flow-models.json` (có nguồn + ngày) và mục "Flow" trong `docs/PLAN.md`.
