# Data Skyline · dark stage (`atlas-data-skyline`)

Biến thể dark-stage của style #19 "Data Skyline" (Sơ đồ có chiều sâu) trong 3D Style Atlas: so sánh số liệu, xếp hạng, chuỗi theo thời gian. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #19 Data Skyline · nhóm Diagrams with depth · tier 1 · brand_fit `adapted` · hợp kênh 4/5 · gần `scale-zoom-black`
- **Block Flow (ảnh):** 3D architectural bar-chart model on a pure black stage (#000000): pale honed limestone towers with strata, one vermilion tower, dark printed scales. Low warm side sun, tower-to-tower shadows, cool sky in the shade. One accent colour (vermilion) only on the key element. Leave blank plates at the foot of each tower empty (captions are added later).
- **Block Flow (chuyển động):** Spring-loaded tower rise one after another, values counting up, taller means longer.
- **Hợp chủ đề (tags):** population, ranking, record, statistics, how-many, billion
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f6f3ee
- `a` #c8401f
- `b` #2a2622
- `c` #e9e1d2
- sân khấu đen + accent vermilion

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#e9e1d2`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** ground-level dolly along the row, tilt up past the tallest, crane out to the full set
- **cut_rule:** cắt đúng pha va chạm hoặc khoảnh khắc mô hình biến dạng

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên khối 3D nổi hoặc nét trắng dày
- **circle:** vòng sáng 3D bao quanh vật thể
- **label:** biển 3D trong cảnh hoặc chữ nổi viền đậm

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: nhịp plucky tactile, marimba + bass ấm kiểu mô hình sống động · 112 BPM
- persona giọng: người kể chuyện tò mò, giàu năng lượng, nhấn nhá rõ
- thumbnail: một vật chủ đạo kiểu 3d architectural bar-chart model nổi giữa nền đen, accent vermilion trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D architectural bar-chart model — Pale honed limestone towers with strata, one vermilion tower, dark printed scales; low warm side sun, tower-to-tower shadows, cool sky in the shade
- video_motion: spring-loaded tower rise one after another, values counting up, taller means longer

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#19` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #19 Data Skyline · Diagrams with depth · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `clay` của engine three.js, block Flow ngắn tự viết
