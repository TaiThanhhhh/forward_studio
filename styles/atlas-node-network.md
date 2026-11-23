# Node Network · dark stage (`atlas-node-network`)

Biến thể dark-stage của style #27 "Node Network" (Sơ đồ có chiều sâu) trong 3D Style Atlas: lan truyền, mạng lưới. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #27 Node Network · nhóm Diagrams with depth · tier 2 · brand_fit `ok` · hợp kênh 3/5 · gần `flowchart-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D porcelain-and-brass network model on a pure black stage (#000000): ivory porcelain tokens, cobalt enamel faces, brass rods and number plaques. Warm overhead spot, soft rod shadows on the wall, pool widening with the model. One accent colour (cobalt enamel) only on the key element. Leave blank number plaques on each ring empty (captions are added later).
- **Block Flow (chuyển động):** Link-by-link growth: rod extends, token clicks in, light bead travels, token flips.
- **Hợp chủ đề (tags):** network, spread, viral, infection, connection
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f3eee2
- `a` #15369c
- `b` #c9a04a
- `c` #935a47
- sân khấu đen + accent cobalt enamel

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#935a47`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** long lens, close start on the first token, steady pull-back drifting left to right
- **cut_rule:** cắt ở pha bật nảy

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên nhựa 3D bo tròn
- **circle:** vòng nhựa sáng
- **label:** nhãn dán sticker bo tròn

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: toy-box plucks, glockenspiel, bouncy bass · 118 BPM
- persona giọng: người kể vui nhộn, nhanh, nhấn từ như đang chơi
- thumbnail: một vật chủ đạo kiểu 3d porcelain-and-brass network model nổi giữa nền đen, accent cobalt enamel trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D porcelain-and-brass network model — Ivory porcelain tokens, cobalt enamel faces, brass rods and number plaques; warm overhead spot, soft rod shadows on the wall, pool widening with the model
- video_motion: link-by-link growth: rod extends, token clicks in, light bead travels, token flips

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#27` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #27 Node Network · Diagrams with depth · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
