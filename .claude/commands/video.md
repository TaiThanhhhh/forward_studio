---
description: Pipeline short thí nghiệm một lệnh (kênh tiếng Anh) — ý tưởng → storyboard → scripts.html → (chờ clip Flow) → look-check → final.mp4 + thumbnail + publish.md + QA
argument-hint: "<ý tưởng>" | <slug> [--style <id>] [--voice <tên>] [--narrative <id>] [--flow|--no-flow] [--dry-run] [--from <stage>] [--only <stage>] [--model "<model Flow>"] [--yes] [--look-ok]
allowed-tools: Bash(python studio.py:*), Bash(py studio.py:*), Read, Write, Edit, WebSearch
---

Bạn đang điều khiển pipeline `python studio.py video`. Trả lời người dùng bằng **tiếng Việt**, ngắn gọn. Nội dung khán
giả thấy/nghe (VO, text_fx, outro, thumbnail, publish) viết **tiếng Anh tự nhiên kiểu người bản xứ**. Làm theo skill
`.claude/skills/black-lab-toon/SKILL.md`.

Tham số người dùng: `$ARGUMENTS`

## Vòng lặp

1. Chạy `python studio.py video $ARGUMENTS` (trên Windows có thể là `py`). Đọc dòng cuối dạng
   `::stage=<stage> project=<thư mục dự án>`.
2. Xử lý theo `stage`:
   - **need_storyboard** — Bạn là biên kịch/đạo diễn. Đọc TOÀN BỘ `<project>/brief.md` và làm đúng brief. Đầu brief có
     **kế hoạch của video** (`<project>/plan.json`, tool chọn theo chủ đề): style hôm nay, là ngày **có Flow** hay **toàn code
     (NO-FLOW DAY)**, giọng đọc, và **dạng kịch bản** (§1 "NARRATIVE SHAPE FOR THIS VIDEO": countdown, timeline,
     myth_fact, versus… — viết đúng khung đó, ghi `"narrative": "<id>"`). Ngày toàn code: MỌI shot là `"mode": "code"` với
     beat của engine (title, drop, counter, compare, graph, process, scale, callout, fact, **scene**…) — 1–3 khoảnh khắc
     hành động dựng bằng `scene` (nhiều vật di chuyển, fx), không chuỗi thẻ một-icon; chọn đạo cụ (`icon`) đúng chủ đề,
     không có thì tự ghép `{"parts": [...]}`. Báo người dùng một dòng: style + giọng + dạng kịch bản đã chọn và lý do (họ
     có thể đổi bằng `--style`/`--voice`/`--narrative`).
     - **Sổ dữ kiện**: kiểm chứng mọi con số/khẳng định bằng WebSearch rồi MỞ trang nguồn (WebFetch) để đối chiếu số.
       Ghi `sources` dạng object `{id, title, publisher, year, url, kind}` (ưu tiên nguồn gốc: cơ quan, tạp chí, viện,
       bộ dữ liệu — không blog/mạng xã hội) và `claims` `{id, text, value, unit, source, status}`; mỗi shot ghi
       `"claims": ["K1"]`. Không chắc → làm tròn + rào đón (`estimate`) hoặc bỏ. Giả định/tranh cãi: VO phải nói rõ.
     - **SEO**: `publish.primary_keyword` = cụm người ta gõ tìm; nằm trong 40 ký tự đầu tiêu đề, câu đầu mô tả và được
       NÓI ở shot 1–2. Không ghi tên kênh/studio khác vào bất cứ chữ nào (linter chặn).
     - **Zoom xuyên bộ phận** khi ý tưởng có khoảnh khắc "đi vào bên trong": shot trước kết bằng camera
       `{"at": "hero.eye", "zoom": 12}` (2D) hoặc `frame.dive` (3D), shot sau `transition_in: "zoom_through"` +
       `through`. Nhân vật dùng `xray`/`organs`/`focus`/`hold`/`talk`/bong bóng để cho thấy cơ chế thật.
     - Viết `<project>/storyboard.json` (JSON hợp lệ, đúng schema trong brief). Chỉ điền **trường ngữ nghĩa**
       (vo, onscreen, subject, camera, action, start_frame.desc, `beat_recipe` + `board`…). KHÔNG viết prompt Flow dài:
       tool tự compile. Luôn điền `beat_recipe` (brief §4b) — style board-* dựng cả video từ đó.
     - Chạy lại bước 1.
   - **storyboard_invalid** hoặc **lint_failed** — đọc lỗi in ra, sửa `storyboard.json` (vd icon không có trong thư viện →
     đổi sang tên gần nghĩa trong danh sách lỗi in ra, hoặc tự ghép `parts`). Chỉ sửa trường do người viết;
     muốn ép một prompt thì dùng `override.video_prompt` / `override.start_prompt` / `override.end_prompt`. Chạy lại.
     Cảnh báo (⚠) về mật độ lời đọc / nhịp: sửa nếu hợp lý.
   - **confirm_map** — cho người dùng xem bảng map clip ↔ shot vừa in và hỏi xác nhận. Đúng → chạy lại với `--yes`.
     Sai → hướng dẫn đổi tên file thành `C01.mp4`… hoặc sửa `clips/_map.json`.
   - **look_check** — ĐỌC ảnh `<project>/qa/look/sheet.jpg` (Read) và tự soi: đạo cụ/chữ bị cắt mép khung dọc, chữ bị
     che/lật gương, chữ đè mặt, nét shot code khác nét Flow (số đo in ở dòng `▶ look`), nhân vật bị cắt. Style board-*
     (`board_spine`): đọc thêm các dòng ✔/✖ in sau `▶ look` (lệch frame dấu↔từ khoá, thời gian đọc nhãn, glyph, màu,
     đứng hình, OCR) và các dòng `⚠ board:`; nhãn không kịp đọc → đổi `sync` sang từ SỚM hơn trong câu. Lỗi → sửa
     storyboard (`beat_recipe`/`board`)/cảnh code rồi chạy lại; đạt → chạy lại với `--look-ok`.
   - **waiting_clips** — DỪNG. Tóm tắt checklist (đường dẫn `scripts.html`, ingredients cần tạo trước, cảnh còn thiếu,
     lệnh chạy lại `/video <slug>`). Không tự thao tác trên Flow.
   - **done** — đọc `<project>/qa/report.md` và báo: `out/final.mp4`, thời lượng, freeze, OCR, loudness, khớp nét code↔Flow,
     điểm cắt ⚠/✗, `qa/report.html`, `publish.md`, `out/captions.srt`, `thumbnails/contact-sheet.png`. Nêu điều nên soi lại.
   - Exit code khác 0 mà không có dòng `::stage=` → báo lỗi nguyên văn, không đoán.
3. Không bao giờ sửa các trường do tool sinh (`*.prompt`, `video_prompt`, `mode_resolved`, `gen_sec`, `image_prompt`,
   `bg_prompt`): chúng bị ghi đè mỗi lần chạy.

## Ý tưởng
- `python studio.py ideas "<chủ đề>"` → `need_ideas`: đọc `ideas/<slug>/brief.md`, kiểm chứng, viết `ideas.json`
  (10 ý tưởng) → chạy lại → `pick_idea`: cho người dùng chọn → `ideas <slug> --pick N` (hoặc `--auto-pick`).

## Style và giọng mỗi video
- Mặc định `auto`: tool chọn style theo chủ đề (nhãn `tags` của style) + cân bằng ngày có Flow / ngày toàn code
  (`config/channel.json → styles.flow_share`), không lặp 3 video gần nhất; giọng không lặp 5 video gần nhất, hợp
  `voice_tags` của style, đổi nam/nữ so với video trước.
- Dạng kịch bản cũng xoay vòng (`python studio.py narratives "<chủ đề>"`), không lặp 3 video gần nhất.
- Người dùng muốn tự chọn: `--style <id>` · `--voice <tên>` (vd Brian, Lily; xem `python studio.py voices`) ·
  `--narrative <id>` ·
  `--flow` (hôm nay làm clip Flow) · `--no-flow` (hôm nay không làm Flow). Xem trước: `python studio.py styles --plan "<ý tưởng>"`.

## Flags hữu ích
- `--dry-run`: chạy trọn pipeline bằng clip/lời đọc/nhạc GIẢ (kiểm tra tool, xem nhịp).
- `--from render` làm lại từ bước render · `--only thumbnail` chỉ làm thumbnail · `--only page` chỉ làm `scripts.html`
  · `--only look` contact sheet trước render · `--look-ok` đã xem sheet, render đầy đủ · `--tts-force` tạo lại giọng.
- `--model "Veo 3.1 Lite"`: đổi model Flow (xem `python studio.py models`); mode/độ dài clip tự tính lại.
