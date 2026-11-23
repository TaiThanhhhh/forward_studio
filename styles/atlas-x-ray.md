# X-Ray · dark stage (`atlas-x-ray`)

Biến thể dark-stage của style #10 "X-Ray" (Bộ lọc trên 3D) trong 3D Style Atlas: giải phẫu, bên trong máy móc, dòng nhiệt/khí xuyên qua. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #10 X-Ray · nhóm Filters over 3D · tier 1 · brand_fit `ok` · hợp kênh 5/5 · gần `xray3d-black`
- **Block Flow (ảnh):** 3D radiograph view on a pure black stage (#000000): steel and black plastic becoming glowing film where thickness accumulates. Soft overhead key pre-scan; afterwards emitted light only from film, accent and grid. One accent colour (warm orange) only on the key element. Leave a blank scanner label strip along the bottom edge empty (captions are added later).
- **Block Flow (chuyển động):** Scan plane sweep, glowing cross-section, interior parts lighting in sequence.
- **Hợp chủ đề (tags):** bone, anatomy, skeleton, scan, organ, inside-body
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #b0d0ec
- `a` #ff9a22
- `b` #c4c8ce
- `c` #ffffff
- sân khấu đen + accent warm orange

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffffff`

## Luật nhịp

- **fps:** full
- **easing:** mượt, nhịp tim
- **bounce:** không
- **camera:** long lens, low three-quarter rising to plan view, then a steady push
- **cut_rule:** cắt theo nhịp tim

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên sáng mảnh
- **circle:** vòng quét đỏ
- **label:** nhãn y khoa mảnh

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→pop, hit→heartbeat, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: heartbeat pulse, soft drones, clinical blips · 88 BPM
- persona giọng: giọng bác sĩ điềm tĩnh, rõ ràng
- thumbnail: một vật chủ đạo kiểu 3d radiograph view nổi giữa nền đen, accent warm orange trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D radiograph view — Steel and black plastic becoming glowing film where thickness accumulates; soft overhead key pre-scan; afterwards emitted light only from film, accent and grid
- video_motion: scan plane sweep, glowing cross-section, interior parts lighting in sequence

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#10` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #10 X-Ray · Filters over 3D · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `xray` của engine three.js, block Flow ngắn tự viết
