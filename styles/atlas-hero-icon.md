# Hero Icon · dark stage (`atlas-hero-icon`)

Biến thể dark-stage của style #35 "Hero Icon" (Sản phẩm và màn hình) trong 3D Style Atlas: biểu tượng sản phẩm. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #35 Hero Icon · nhóm Products and screens · tier 2 · brand_fit `off-brand` · hợp kênh 1/5 · gần `plastic-toy3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D chunky app-icon tile on a pure black stage (#000000): glossy plastic tile, soft-touch white parts, polished metal waist band, rounded edges. Big soft key upper right, large tile shadow, gloss softboxes. One accent colour (amber) only on the key element. Leave a blank wall beside the tile empty (captions are added later).
- **Block Flow (chuyển động):** Wind-up, flip, click home past the mark; symbol parts slide and press into place.
- **Hợp chủ đề (tags):** icon, brand, tool, logo, symbol
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #fffdf6
- `a` #f0a000
- `b` #e03a27
- `c` #5aa8ff
- sân khấu đen + accent amber

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#5aa8ff`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** near square-on long lens, slow push, then a pull-back with a sideways track
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
- thumbnail: một vật chủ đạo kiểu 3d chunky app-icon tile nổi giữa nền đen, accent amber trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D chunky app-icon tile — Glossy plastic tile, soft-touch white parts, polished metal waist band, rounded edges; big soft key upper right, large tile shadow, gloss softboxes
- video_motion: wind-up, flip, click home past the mark; symbol parts slide and press into place

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#35` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #35 Hero Icon · Products and screens · Title
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
