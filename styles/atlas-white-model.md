# White Model · dark stage (`atlas-white-model`)

Biến thể dark-stage của style #17 "White Model" (Sơ đồ có chiều sâu) trong 3D Style Atlas: năng lượng/nước/nhiệt chạy qua một hệ thống. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #17 White Model · nhóm Diagrams with depth · tier 1 · brand_fit `adapted` · hợp kênh 4/5
- **Block Flow (ảnh):** 3D architect's white presentation model on a pure black stage (#000000): architectural white model: card, foam, paper and plaster whites, crisp bevels. Soft side daylight, real occlusion; only the accent emits light. One accent colour (vivid orange) only on the key element. Leave small blank white flag labels at each stop empty (captions are added later).
- **Block Flow (chuyển động):** Static model; accent travels through conduits lighting parts in order.
- **Hợp chủ đề (tags):** solar, energy, power, grid, heating, insulation, house
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f8f6f0
- `a` #ff6a00
- `b` #b9bec4
- `c` #eef3f8
- sân khấu đen + accent vivid orange

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#eef3f8`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** long lens, shallow focus, single crane from the source up to the full path
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
- thumbnail: một vật chủ đạo kiểu 3d architect's white presentation model nổi giữa nền đen, accent vivid orange trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D architect's white presentation model — Architectural white model: card, foam, paper and plaster whites, crisp bevels; soft side daylight, real occlusion; only the accent emits light
- video_motion: static model; accent travels through conduits lighting parts in order

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#17` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #17 White Model · Diagrams with depth · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `clay` của engine three.js, block Flow ngắn tự viết
