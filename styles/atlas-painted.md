# Painted · dark stage (`atlas-painted`)

Biến thể dark-stage của style #13 "Painted" (Bộ lọc trên 3D) trong 3D Style Atlas: chuyện kể đồng quê kiểu sách tranh. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #13 Painted · nhóm Filters over 3D · tier 2 · brand_fit `off-brand` · hợp kênh 2/5 · gần `gallery-pointillist-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D scene rendered as an oil painting on a pure black stage (#000000): simple rough forms under directional brush dabs, bristle streaks, canvas texture. Low golden back-side sun, blue-violet shadows, small warm practical lamps. One accent colour (sunset peach) only on the key element. Leave a bare unpainted corner of the canvas empty (captions are added later).
- **Block Flow (chuyển động):** Chained events inside the picture: gust through wheat, sails spinning, stone grinding.
- **Hợp chủ đề (tags):** painting, countryside, bread, farm, village
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #d69a5a
- `a` #f0a878
- `b` #5f8a36
- `c` #c08a56
- sân khấu đen + accent sunset peach

## Chữ (text_fx / thumbnail)

- font `Caladea-Bold.ttf` · cỡ 108 · chữ thường · vào bằng `write_on` (12 frame) · số `#c08a56`

## Luật nhịp

- **fps:** lớp sơn on twos (chấm đổi mỗi 2 frame); chữ on ones
- **easing:** smootherstep, chậm
- **bounce:** không
- **cut_rule:** cắt chậm, như bước sang bức kế trong phòng tranh
- **camera:** single walking-height camera travelling with the wind between places

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** không mũi tên trong tranh — chỉ nhãn bảo tàng
- **circle:** không khoanh
- **label:** nhãn bảo tàng: chữ kem viền đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→ting, hit→thud, whoosh→whoosh_soft, tick→tick, ding→sparkle
- nhạc: piano ấn tượng chậm, vang phòng tranh · 84 BPM
- persona giọng: giám tuyển thì thầm trong phòng tranh
- thumbnail: một vật chủ đạo kiểu 3d scene rendered as an oil painting nổi giữa nền đen, accent sunset peach trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D scene rendered as an oil painting — Simple rough forms under directional brush dabs, bristle streaks, canvas texture; low golden back-side sun, blue-violet shadows, small warm practical lamps
- video_motion: chained events inside the picture: gust through wheat, sails spinning, stone grinding

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#13` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #13 Painted · Filters over 3D · Story
- cách chuyển: dark-stage: nền #000, look 3D `toon` của engine three.js, block Flow ngắn tự viết
