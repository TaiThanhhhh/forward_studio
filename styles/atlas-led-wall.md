# LED Wall · dark stage (`atlas-led-wall`)

Biến thể dark-stage của style #11 "LED Wall" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: phim hoạt hình pixel, cuộc đua, bản đồ. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #11 LED Wall · nhóm Flat content made physical · tier 2 · brand_fit `ok` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D giant LED lamp wall on a pure black stage (#000000): frosted round lamps in black collars, slatted cabinets, steel gantry, wet ground. Screen image as the only source, colour spill on frame, haze and puddles. One accent colour (signal green) only on the key element. Leave a blank dot-matrix ticker strip under the wall empty (captions are added later).
- **Block Flow (chuyển động):** One lamp per pixel animation, flat-colour characters with walk and run cycles.
- **Hợp chủ đề (tags):** pixel, game, race, screen, retro
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffffff
- `a` #2fb544
- `b` #ff3c3c
- `c` #1f9a30
- sân khấu đen + accent signal green

## Chữ (text_fx / thumbnail)

- font `RobotoMono-Variable.ttf` · cỡ 104 · IN HOA · vào bằng `pop` (7 frame) · số `#1f9a30`

## Luật nhịp

- **fps:** full
- **easing:** mượt, có glitch ngắn
- **bounce:** không
- **camera:** low macro across individual lamps pulling back until the image resolves
- **cut_rule:** cắt bằng glitch

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên dây sáng
- **circle:** vòng quét
- **label:** nhãn HUD [ ]

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, glitch
- gói SFX (cue chung → âm): pop→glitch, hit→impact, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: dark synth pulse, data blips, sub bass · 92 BPM
- persona giọng: giọng điềm tĩnh, hơi bí ẩn, như hệ thống phân tích
- thumbnail: một vật chủ đạo kiểu 3d giant led lamp wall nổi giữa nền đen, accent signal green trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D giant LED lamp wall — Frosted round lamps in black collars, slatted cabinets, steel gantry, wet ground; screen image as the only source, colour spill on frame, haze and puddles
- video_motion: one lamp per pixel animation, flat-colour characters with walk and run cycles

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#11` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #11 LED Wall · Flat content made physical · Story
- cách chuyển: dark-stage: nền #000, look 3D `holo` của engine three.js, block Flow ngắn tự viết
