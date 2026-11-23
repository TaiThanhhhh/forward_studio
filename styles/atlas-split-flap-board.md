# Split-Flap Board · dark stage (`atlas-split-flap-board`)

Biến thể dark-stage của style #34 "Split-Flap Board" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: đếm ngược, xếp hạng, danh sách số. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #34 Split-Flap Board · nhóm Flat content made physical · tier 1 · brand_fit `ok` · hợp kênh 4/5
- **Block Flow (ảnh):** 3D mechanical split-flap board on a pure black stage (#000000): black plastic flaps with worn off-white print, dark brushed-steel frame, amber backlit sign. Soft overhead lamp in front, flash on every falling flap, faint cool side fill. One accent colour (amber) only on the key element. Leave every flap face left blank — letters are set in post empty (captions are added later).
- **Block Flow (chuyển động):** Characters riffle through the alphabet and land column by column.
- **Hợp chủ đề (tags):** countdown, ranking, top, fastest, list, schedule
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #fff1dc
- `a` #ffa530
- `b` #8fb4ff
- `c` #ffffff
- sân khấu đen + accent amber

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffffff`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** shallow-focus long lens, sideways track, pull-back, push toward the highlighted row
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
- thumbnail: một vật chủ đạo kiểu 3d mechanical split-flap board nổi giữa nền đen, accent amber trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D mechanical split-flap board — Black plastic flaps with worn off-white print, dark brushed-steel frame, amber backlit sign; soft overhead lamp in front, flash on every falling flap, faint cool side fill
- video_motion: characters riffle through the alphabet and land column by column

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#34` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #34 Split-Flap Board · Flat content made physical · Title
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
