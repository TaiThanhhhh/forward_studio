# Device Hero · dark stage (`atlas-device-hero`)

Biến thể dark-stage của style #32 "Device Hero" (Sản phẩm và màn hình) trong 3D Style Atlas: điện thoại, thiết bị (vd thả điện thoại vào…). Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #32 Device Hero · nhóm Products and screens · tier 2 · brand_fit `ok` · hợp kênh 3/5 · gần `chrome3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D phone launch shot on a pure black stage (#000000): satin titanium phone, black cover glass, mirror-gloss floor. Indirect strip lights and softbox reflections only, screen as the brightest element. One accent colour (warm screen white) only on the key element. Leave a blank glowing screen empty (captions are added later).
- **Block Flow (chuyển động):** Phone turns to camera under sliding strip reflections, interface layers peel away.
- **Hợp chủ đề (tags):** phone, smartphone, screen, device, drop-phone
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f1eee8
- `a` #fff3e2
- `b` #b9b2a8
- `c` #ffffff
- sân khấu đen + accent warm screen white

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffffff`

## Luật nhịp

- **fps:** full
- **easing:** nặng, dừng gắt
- **bounce:** không
- **camera:** low slow drift past the phone, push dipping below the screen, gentle arc
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
- thumbnail: một vật chủ đạo kiểu 3d phone launch shot nổi giữa nền đen, accent warm screen white trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D phone launch shot — Satin titanium phone, black cover glass, mirror-gloss floor; indirect strip lights and softbox reflections only, screen as the brightest element
- video_motion: phone turns to camera under sliding strip reflections, interface layers peel away

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#32` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #32 Device Hero · Products and screens · Product shot
- cách chuyển: dark-stage: nền #000, look 3D `chrome` của engine three.js, block Flow ngắn tự viết
