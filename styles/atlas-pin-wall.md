# Pin Wall · dark stage (`atlas-pin-wall`)

Biến thể dark-stage của style #21 "Pin Wall" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: địa hình, sóng, núi lửa, thứ trồi lên. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #21 Pin Wall · nhóm Flat content made physical · tier 1 · brand_fit `ok` · hợp kênh 4/5
- **Block Flow (ảnh):** 3D pin-art relief wall on a pure black stage (#000000): domed steel pins on tinted shafts in a black bolted frame. Low raking key far left, long soft shadows, blue fill opposite, warm glow where hot. One accent colour (lava orange) only on the key element. Leave a blank small plate at the bottom of the frame empty (captions are added later).
- **Block Flow (chuyển động):** Living height field: travelling swells, shapes pushing up, rings, pins lagging slightly.
- **Hợp chủ đề (tags):** volcano, lava, earthquake, wave, terrain, tsunami, magma
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #c3c7cf
- `a` #ff5a12
- `b` #46689e
- `c` #ffc890
- sân khấu đen + accent lava orange

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffc890`

## Luật nhịp

- **fps:** full
- **easing:** nặng, dừng gắt
- **bounce:** không
- **camera:** low raised three-quarter crane rising and orbiting until the relief reads
- **cut_rule:** cắt ở va chạm kim loại

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên thép
- **circle:** vòng sáng cam
- **label:** nhãn khắc chữ

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→ting, hit→impact, whoosh→whoosh, tick→click, ding→ting
- nhạc: industrial pulse, metallic hits, low synth · 100 BPM
- persona giọng: giọng trầm, chắc, nhịp mạnh
- thumbnail: một vật chủ đạo kiểu 3d pin-art relief wall nổi giữa nền đen, accent lava orange trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D pin-art relief wall — Domed steel pins on tinted shafts in a black bolted frame; low raking key far left, long soft shadows, blue fill opposite, warm glow where hot
- video_motion: living height field: travelling swells, shapes pushing up, rings, pins lagging slightly

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#21` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #21 Pin Wall · Flat content made physical · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `chrome` của engine three.js, block Flow ngắn tự viết
