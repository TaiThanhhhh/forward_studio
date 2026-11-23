# Floating Screens · dark stage (`atlas-floating-screens`)

Biến thể dark-stage của style #31 "Floating Screens" (Sản phẩm và màn hình) trong 3D Style Atlas: luồng ứng dụng. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #31 Floating Screens · nhóm Products and screens · tier 2 · brand_fit `off-brand` · hợp kênh 1/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D floating interface cards on a pure black stage (#000000): printed card interface faces on thick glass blocks, raised card buttons. Large soft window light, each card shadowing the next. One accent colour (green) only on the key element. Leave blank card faces empty (captions are added later).
- **Block Flow (chuyển động):** Cards hinge in like heavy doors, buttons depress, a cable draws to the next card.
- **Hợp chủ đề (tags):** app, workflow, checkout, interface, online
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f3eee5
- `a` #0f6d4c
- `b` #1f1b16
- `c` #e6dfd2
- sân khấu đen + accent green

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#e6dfd2`

## Luật nhịp

- **fps:** full
- **easing:** mượt, chậm vào chậm ra
- **bounce:** không
- **camera:** constant-speed dolly past the row, panning to the newest card
- **cut_rule:** cắt lúc ánh sáng loé qua cạnh kính

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** tia sáng mảnh
- **circle:** vòng sáng mảnh
- **label:** nhãn chữ mảnh sáng

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: glassy pads, soft bells, airy pulse · 96 BPM
- persona giọng: giọng trầm, rõ, chậm rãi như phim tài liệu khoa học
- thumbnail: một vật chủ đạo kiểu 3d floating interface cards nổi giữa nền đen, accent green trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D floating interface cards — Printed card interface faces on thick glass blocks, raised card buttons; large soft window light, each card shadowing the next
- video_motion: cards hinge in like heavy doors, buttons depress, a cable draws to the next card

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#31` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #31 Floating Screens · Products and screens · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `glass` của engine three.js, block Flow ngắn tự viết
