# Neon Sign · dark stage (`atlas-neon-sign`)

Biến thể dark-stage của style #07 "Neon Sign" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: cơ chế bật sáng theo thứ tự: điện, tín hiệu, nhiệt, dòng chảy. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #07 Neon Sign · nhóm Flat content made physical · tier 1 · brand_fit `ok` · hợp kênh 5/5 · gần `neon`
- **Block Flow (ảnh):** 3D neon tube sign on a pure black stage (#000000): glowing glass tubing, hot cores, milky unlit glass, dark mounts and standoffs. Tubes as sole light, coloured spill on the wall, faint cold street light. One accent colour (amber) only on the key element. Leave an unlit blank tube frame empty (captions are added later).
- **Block Flow (chuyển động):** Snap-on flicker then hold slightly over-bright; never fades, never slides.
- **Hợp chủ đề (tags):** electricity, current, circuit, glow, voltage, spark, wire
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffe2b8
- `a` #ff8a00
- `b` #00c8a8
- `c` #6aa8ff
- sân khấu đen + accent amber

## Chữ (text_fx / thumbnail)

- font `RobotoMono-Variable.ttf` · cỡ 104 · IN HOA · vào bằng `pop` (7 frame) · số `#6aa8ff`

## Luật nhịp

- **fps:** full
- **easing:** mượt, có glitch ngắn
- **bounce:** không
- **camera:** long-lens crane, oblique start, follows the lit section down the sign
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
- thumbnail: một vật chủ đạo kiểu 3d neon tube sign nổi giữa nền đen, accent amber trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D neon tube sign — Glowing glass tubing, hot cores, milky unlit glass, dark mounts and standoffs; tubes as sole light, coloured spill on the wall, faint cold street light
- video_motion: snap-on flicker then hold slightly over-bright; never fades, never slides

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#07` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #07 Neon Sign · Flat content made physical · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `holo` của engine three.js, block Flow ngắn tự viết
