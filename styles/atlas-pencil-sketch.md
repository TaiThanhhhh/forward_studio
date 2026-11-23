# Pencil Sketch · dark stage (`atlas-pencil-sketch`)

Biến thể dark-stage của style #25 "Pencil Sketch" (Bộ lọc trên 3D) trong 3D Style Atlas: dựng từng bước, cấu trúc. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #25 Pencil Sketch · nhóm Filters over 3D · tier 2 · brand_fit `off-brand` · hợp kênh 2/5 · gần `sketchnote-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D scene drawn as a graphite sketch on a pure black stage (#000000): graphite line work in two weights, red pencil numerals, one red marker wash. Sun top-left expressed only as hatching density. One accent colour (red pencil) only on the key element. Leave blank note spaces beside the parts empty (captions are added later).
- **Block Flow (chuyển động):** Self-drawing: construction lines, outlines, then single and crossed hatching.
- **Hợp chủ đề (tags):** sketch, drawing, construction, house, blueprint-sketch
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f2ede0
- `a` #cf472b
- `b` #33343a
- `c` #e8967a
- sân khấu đen + accent red pencil

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#e8967a`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** slow ~35° arc around the subject, everything in focus
- **cut_rule:** cắt đúng pha va chạm hoặc khoảnh khắc mô hình biến dạng

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên khối 3D nổi hoặc nét trắng dày
- **circle:** vòng sáng 3D bao quanh vật thể
- **label:** biển 3D trong cảnh hoặc chữ nổi viền đậm

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: nhịp plucky tactile, marimba + bass ấm kiểu mô hình sống động · 112 BPM
- persona giọng: người kể chuyện tò mò, giàu năng lượng, nhấn nhá rõ
- thumbnail: một vật chủ đạo kiểu 3d scene drawn as a graphite sketch nổi giữa nền đen, accent red pencil trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D scene drawn as a graphite sketch — Graphite line work in two weights, red pencil numerals, one red marker wash; sun top-left expressed only as hatching density
- video_motion: self-drawing: construction lines, outlines, then single and crossed hatching

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#25` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #25 Pencil Sketch · Filters over 3D · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `toon` của engine three.js, block Flow ngắn tự viết
