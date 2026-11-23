# Blueprint Build · dark stage (`atlas-blueprint-build`)

Biến thể dark-stage của style #05 "Blueprint Build" (Sơ đồ có chiều sâu) trong 3D Style Atlas: bản vẽ → vật thể, kích thước, cách bố trí. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #05 Blueprint Build · nhóm Diagrams with depth · tier 2 · brand_fit `adapted` · hợp kênh 3/5 · gần `blueprint` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D technical drawing that lifts into a wireframe and then a solid on a pure black stage (#000000): white plotter lines, dashed hidden edges, dimension arrows, then oak/steel/plaster solids. Single soft back-side key, long shadow toward lens, light cool fill. One accent colour (blueprint blue) only on the key element. Leave a blank title block in the corner empty (captions are added later).
- **Block Flow (chuyển động):** Pen-order line plotting with a glowing tip, parts extrude from their plan, notes peel up.
- **Hợp chủ đề (tags):** plan, layout, dimensions, engineering, design, desk
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f1f6ff
- `a` #5d97ff
- `b` #1f52ad
- `c` #dbe8ff
- sân khấu đen + accent blueprint blue

## Chữ (text_fx / thumbnail)

- font `RobotoMono-Variable.ttf` · cỡ 104 · IN HOA · vào bằng `pop` (7 frame) · số `#dbe8ff`

## Luật nhịp

- **fps:** full
- **easing:** mượt, có glitch ngắn
- **bounce:** không
- **camera:** crane from straight-down plan view tipping to three-quarter as height appears
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
- thumbnail: một vật chủ đạo kiểu 3d technical drawing that lifts into a wireframe and then a solid nổi giữa nền đen, accent blueprint blue trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D technical drawing that lifts into a wireframe and then a solid — White plotter lines, dashed hidden edges, dimension arrows, then oak/steel/plaster solids; single soft back-side key, long shadow toward lens, light cool fill
- video_motion: pen-order line plotting with a glowing tip, parts extrude from their plan, notes peel up

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#05` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #05 Blueprint Build · Diagrams with depth · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `holo` của engine three.js, block Flow ngắn tự viết
