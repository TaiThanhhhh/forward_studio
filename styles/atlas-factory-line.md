# Factory Line · dark stage (`atlas-factory-line`)

Biến thể dark-stage của style #16 "Factory Line" (Cỗ máy giải thích) trong 3D Style Atlas: quy trình nhiều bước, mỗi trạm làm một việc. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #16 Factory Line · nhóm Machines that explain · tier 2 · brand_fit `adapted` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D toy production line on a pure black stage (#000000): cobalt, orange and cream enamel housings, steel rods, ribbed rubber belt, printed page on a tray. Warm low key front-left under the tool heads, working lamps glinting. One accent colour (safety orange) only on the key element. Leave blank label panels on each machine empty (captions are added later).
- **Block Flow (chuyển động):** Indexing belt: stop, one heavy machine action, green lamp, advance.
- **Hợp chủ đề (tags):** factory, assembly, pipeline, manufacturing, conveyor
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffffff
- `a` #ff641a
- `b` #2a6cf0
- `c` #ffd033
- sân khấu đen + accent safety orange

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffd033`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** side dolly travelling with the tray, looking down around 35°
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
- thumbnail: một vật chủ đạo kiểu 3d toy production line nổi giữa nền đen, accent safety orange trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D toy production line — Cobalt, orange and cream enamel housings, steel rods, ribbed rubber belt, printed page on a tray; warm low key front-left under the tool heads, working lamps glinting
- video_motion: indexing belt: stop, one heavy machine action, green lamp, advance

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#16` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #16 Factory Line · Machines that explain · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
