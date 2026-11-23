# Shadow Box · dark stage (`atlas-shadow-box`)

Biến thể dark-stage của style #28 "Shadow Box" (Nội dung phẳng thành vật thật) trong 3D Style Atlas: dòng thời gian theo chiều sâu, trước/sau. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #28 Shadow Box · nhóm Flat content made physical · tier 2 · brand_fit `ok` · hợp kênh 3/5 · gần `papercraft3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D paper-cut light box on a pure black stage (#000000): cream paper silhouettes with bright cut edges, deep walnut frame. Warm back-wall lamp, lit gaps between sheets, front sheets in silhouette. One accent colour (warm glow) only on the key element. Leave a blank cut-out label in each layer empty (captions are added later).
- **Block Flow (chuyển động):** Sheets arrive one by one from different directions, each lighting the gap behind it.
- **Hợp chủ đề (tags):** era, before-after, shrink, silhouette, layers
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f6e6c8
- `a` #ffb547
- `b` #3a4fa6
- `c` #12161c
- sân khấu đen + accent warm glow

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#12161c`

## Luật nhịp

- **fps:** twos
- **easing:** gấp/mở như sách pop-up
- **bounce:** có
- **camera:** wide-aperture long lens, sideways slide for parallax, pull-back to square-on
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
- thumbnail: một vật chủ đạo kiểu 3d paper-cut light box nổi giữa nền đen, accent warm glow trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D paper-cut light box — Cream paper silhouettes with bright cut edges, deep walnut frame; warm back-wall lamp, lit gaps between sheets, front sheets in silhouette
- video_motion: sheets arrive one by one from different directions, each lighting the gap behind it

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#28` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #28 Shadow Box · Flat content made physical · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `paper` của engine three.js, block Flow ngắn tự viết
