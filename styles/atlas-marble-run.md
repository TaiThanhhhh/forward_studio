# Marble Run · dark stage (`atlas-marble-run`)

Biến thể dark-stage của style #09 "Marble Run" (Cỗ máy giải thích) trong 3D Style Atlas: phân loại, định tuyến, xác suất. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #09 Marble Run · nhóm Machines that explain · tier 2 · brand_fit `ok` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D handmade wooden marble run on a pure black stage (#000000): maple rails on a walnut board, brass pegs and flip gates, veined glass marbles, clear jars. Warm daylight top-left, soft rail shadows, coloured glints under each marble. One accent colour (electric blue) only on the key element. Leave blank wooden plaques under each jar empty (captions are added later).
- **Block Flow (chuyển động):** Gravity-driven roll, clack at each gate, sorted drops, marbles piling in jars.
- **Hợp chủ đề (tags):** sort, filter, route, probability, rules, count
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f4ead6
- `a` #3f78ff
- `b` #ff453a
- `c` #22c36e
- sân khấu đen + accent electric blue

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#22c36e`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** long lens tracking a single marble from hopper to jar, pausing at gates
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
- thumbnail: một vật chủ đạo kiểu 3d handmade wooden marble run nổi giữa nền đen, accent electric blue trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D handmade wooden marble run — Maple rails on a walnut board, brass pegs and flip gates, veined glass marbles, clear jars; warm daylight top-left, soft rail shadows, coloured glints under each marble
- video_motion: gravity-driven roll, clack at each gate, sorted drops, marbles piling in jars

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#09` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #09 Marble Run · Machines that explain · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
