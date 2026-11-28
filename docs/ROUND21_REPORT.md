# Vòng 21 — Báo cáo

Prompt: `docs/ROUND21_PROMPT.md` (Claude Opus 5.5, effort xhigh). Ngày 27/11/2026.

## 1. Kiểm định vòng 19–20 (Gemini)

| # | Kết luận | Đã xử lý |
|---|---|---|
| A1 | **Sai về thương hiệu**: style/look mang tên kênh có thật (`kurzgesagt-black`…, bí danh rig `kurzbird`); tên này lọt vào brief → dự án `how-ai-turns-static-noise-into-video` có YouTube tag **"kurzgesagt tech explainer"** và prompt thumbnail "Split Kurzgesagt 2D visual". | Đổi sang `cosmic-flat-black` / `essay-ink-black` / `bold-infographic-black` (+ bí danh tương thích ngược), bỏ `kurzbird`, thêm brand-safety (`vidlib/seo.py`): tên kênh khác trong chữ khán giả thấy = lỗi chặn + dòng đỏ ở cổng QA. **Dự án cũ trên vẫn còn tag đó — xoá trước khi đăng** (`python studio.py facts how-ai-turns-static-noise-into-video` chỉ ra). |
| A2 | **Thiếu kiểm chứng thật**: brief bảo "verify with a web search" nhưng gọi API Claude không bật công cụ tìm kiếm; `sources` là chuỗi tự do. | Sổ dữ kiện `claims` + `sources` có cấu trúc, lint, chip "Source: …" trên màn, `qa/facts.md`; brief `--ai claude` bật `web_search_20260209` + `web_fetch_20260209` (xử lý `pause_turn`), ghi URL thật vào `work/research.json` để đối chiếu. |
| A3 | Rig `duck`/`owl`/`scientist` chỉ đổi tỉ lệ thân. | Cú: đầu nhìn thẳng, túm lông tai, đĩa mặt, mắt to · Vịt: mỏ dẹt hai nửa (mở khi nói), chân màng · Nhà khoa học: áo blouse, kính. |
| A4 | Chuyển cảnh chỉ phóng tâm khung; nhân vật không có điểm neo bộ phận. | WP-1/2/3 bên dưới. |
| A5 | Phần đúng giữ nguyên: 3 look chạy được (easing `bounce`/`snap` có trong `core.js`), Director Skill + `learn`, Poster QA, Edge TTS tuỳ chọn, headroom `story_hud`. | — |

## 2. Đã làm

- **Rig 2D có bộ phận** (`engines/html/rig2d.js`): 21 điểm neo (`PARTS`, `rigAnchors()`) tính theo đúng dáng từng frame (marker vô hình đi qua cùng phép xoay/nghiêng/lật); `xray` + `organs` (não có nếp, tim đập theo `bpm`, phổi thở, dạ dày, xương); miệng nói (`talk`), mắt nhìn theo (`gaze`/`look_at`), đạo cụ cầm tay (`hold`), vầng sáng bộ phận (`focus`), chống trượt chân (pha bước theo quãng đường).
- **Beat `scene`**: tham chiếu `"id.part"` cho nhãn/mũi tên/fx/camera; camera `at` + `zoom` (0.5–40, vector sắc nét); bong bóng `speech|thought` (+ `side`); nhãn `out`; `keep_labels` (soi kính lúp).
- **`zoom_through`**: html→html = kiểu bay `portal` trong cú máy liền (lỗ tròn đúng vị trí bộ phận rồi nở ra, vẽ lại vector); cặp khác = hậu kỳ `vidlib/partzoom.py` (điểm đích từ `meta.json → anchors_end`).
- **3D**: `frame.dive {of, part: head|eye|brain|top|chest|heart|belly|center|thigh|feet, u, dist, fov}`.
- **Sổ dữ kiện** (`vidlib/facts.py`) + **SEO** (`vidlib/seo.py`) + upload YouTube: category theo chủ đề, `status.containsSyntheticMedia`, `localizations`, dòng nguồn.
- **Sổ quyền trung thực**: `vo_alignment.json` ghi nhà cung cấp giọng thật (`provider`), sổ quyền có `voice:edge-tts` (quyết định thương mại `edge_tts` = unknown).
- Công cụ: `studio.py facts <slug>`, `scripts/parts_sheet.py`, `scripts/portal_check.py`.

## 3. Kiểm chứng

- `python -m unittest discover -s tests -t .` → 394 test OK (6 skip) · `python -m ruff check .` sạch.
- Render thật (Edge headless): `qa/round21/parts_cosmic-flat-black.jpg` (x-ray, cú/vịt/nhà khoa học, bong bóng, camera lao 16× vào mắt), `qa/round21/portal_cosmic-flat-black.jpg` (portal + hậu kỳ), `qa/round21/dive3d_clay.jpg` (3D dive).
- Sản xuất 7 video tuần 28/11–04/12 qua pipeline đầy đủ (xem `projects/WEEK_2026-11-28.md`).

## 4. SEO — căn cứ

- `status.containsSyntheticMedia` là trường boolean ghi được khi `videos.insert` (YouTube Data API v3, tài liệu
  developers.google.com/youtube/v3/docs/videos/insert).
- Link trong mô tả và bình luận Shorts không bấm được (YouTube Help, support.google.com/youtube/answer/13748639).
- Các con số "độ dài tiêu đề / số hashtag" là quy ước của kênh (blog SEO bên thứ ba không thống nhất) — tool cảnh báo,
  không chặn.

## 5. Giới hạn còn lại

- **Giọng tuần này**: ElevenLabs hết quota (172 credit) → dùng Edge Neural TTS dự phòng (endpoint đọc to của trình duyệt,
  không phải API thương mại). Trước khi bật kiếm tiền: nạp ElevenLabs và `--tts-force` từng video.
- Đường hậu kỳ `zoom_through` phóng ảnh raster (tối đa 3.4×) — kém sắc hơn portal vector; nhãn sát điểm đích nên có `out`.
- Neo bộ phận của rig là xấp xỉ theo hình 2D (không phải giải phẫu chính xác) — đủ cho camera/nhãn, không dùng để đo.
- Brief còn tên studio tham chiếu trong khối format/archetype (tham chiếu nghề cho LLM); linter chặn rò ra chữ khán giả.
