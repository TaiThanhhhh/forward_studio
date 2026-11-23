# Studio Product · dark stage (`atlas-studio-product`)

Biến thể dark-stage của style #33 "Studio Product" (Sản phẩm và màn hình) trong 3D Style Atlas: một vật + một câu khẳng định được thử. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #33 Studio Product · nhóm Products and screens · tier 1 · brand_fit `ok` · hợp kênh 4/5 · gần `chrome3d-black`
- **Block Flow (ảnh):** 3D flagship product shot on a pure black stage (#000000): precise product finishes: textured powder coat, lathe-marked steel, knurling, anodised flutes. Strip softboxes only: sweeping graded key, twin back rims, overhead box. One accent colour (teal) only on the key element. Leave blank space beside the object for one line of type empty (captions are added later).
- **Block Flow (chuyển động):** Static product, moving light sweeps repeating across its surfaces.
- **Hợp chủ đề (tags):** bottle, insulated, durable, waterproof, lasts, product
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #cfd3d8
- `a` #0b6a7c
- `b` #9a9a9a
- `c` #ffffff
- sân khấu đen + accent teal

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffffff`

## Luật nhịp

- **fps:** full
- **easing:** nặng, dừng gắt
- **bounce:** không
- **camera:** slider long lens: two macro detail passes, pull-back, slow push
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
- thumbnail: một vật chủ đạo kiểu 3d flagship product shot nổi giữa nền đen, accent teal trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D flagship product shot — Precise product finishes: textured powder coat, lathe-marked steel, knurling, anodised flutes; strip softboxes only: sweeping graded key, twin back rims, overhead box
- video_motion: static product, moving light sweeps repeating across its surfaces

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#33` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #33 Studio Product · Products and screens · Product shot
- cách chuyển: dark-stage: nền #000, look 3D `chrome` của engine three.js, block Flow ngắn tự viết
