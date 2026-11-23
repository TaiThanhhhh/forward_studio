# Spotlight Stage · dark stage (`atlas-spotlight-stage`)

Biến thể dark-stage của style #06 "Spotlight Stage" (Không gian và hành trình) trong 3D Style Atlas: lịch sử, chuyện kể theo cảnh. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #06 Spotlight Stage · nhóm Spaces and journeys · tier 2 · brand_fit `ok` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D toy theatre with flat card cut-outs on a pure black stage (#000000): gouache-painted card flats, cut-out actors on rods, velvet drapes, dark timber boards. Stage lamps only, visible beams in haze, follow spots plus per-scene colour wash. One accent colour (spotlight gold) only on the key element. Leave a blank easel card downstage empty (captions are added later).
- **Block Flow (chuyển động):** Flats slide in from wings, pieces fly in from above, cut-outs glide in floor slots.
- **Hợp chủ đề (tags):** history, invention, legend, century, first-flight
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #c9b78f
- `a` #ffd27a
- `b` #9e1f2a
- `c` #6f4622
- sân khấu đen + accent spotlight gold

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#6f4622`

## Luật nhịp

- **fps:** twos
- **easing:** gấp/mở như sách pop-up
- **bounce:** có
- **camera:** stalls-seat point of view, slow continuous move with each scene change
- **cut_rule:** cắt khi trang mở xong

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên giấy cắt
- **circle:** vòng giấy
- **label:** nhãn giấy dán

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: pizzicato strings, paper rustle, light percussion · 104 BPM
- persona giọng: người kể chuyện ấm, như đọc sách pop-up
- thumbnail: một vật chủ đạo kiểu 3d toy theatre with flat card cut-outs nổi giữa nền đen, accent spotlight gold trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D toy theatre with flat card cut-outs — Gouache-painted card flats, cut-out actors on rods, velvet drapes, dark timber boards; stage lamps only, visible beams in haze, follow spots plus per-scene colour wash
- video_motion: flats slide in from wings, pieces fly in from above, cut-outs glide in floor slots

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#06` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #06 Spotlight Stage · Spaces and journeys · Story
- cách chuyển: dark-stage: nền #000, look 3D `paper` của engine three.js, block Flow ngắn tự viết
