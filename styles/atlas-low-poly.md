# Low-Poly · dark stage (`atlas-low-poly`)

Biến thể dark-stage của style #01 "Low-Poly" (Bộ lọc trên 3D) trong 3D Style Atlas: chu trình, hành trình qua một vùng đất (mỗi chặng một lá cờ). Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #01 Low-Poly · nhóm Filters over 3D · tier 2 · brand_fit `ok` · hợp kênh 4/5 · gần `lowpoly3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** Stylized low-poly 3D miniature on a pure black stage (#000000): faceted low-poly geometry, flat tone per face, matte paper feel; water a touch glossy. Warm low side sun, soft shadow edges, cool sky fill on shade sides. One accent colour (teal) only on the key element. Leave a small blank paper flag on a pin empty (captions are added later).
- **Block Flow (chuyển động):** Facets unfold from a seed point, pop-up bounces, heaving water, bobbing droplets.
- **Hợp chủ đề (tags):** cycle, journey, river, landscape, route, rain, mountain
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ecd3a0
- `a` #63bfb4
- `b` #f08a64
- `c` #e6f5ea
- sân khấu đen + accent teal

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#e6f5ea`

## Luật nhịp

- **fps:** full
- **easing:** bậc, gọn
- **bounce:** có
- **camera:** long-lens crane, tilt-shift focus band, stop-by-stop then full model
- **cut_rule:** cắt khi khối lắp xong

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên đa giác
- **circle:** vòng đa giác
- **label:** nhãn phẳng

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: marimba arpeggios, soft kick, adventurous · 108 BPM
- persona giọng: người kể chuyện tò mò, ấm
- thumbnail: một vật chủ đạo kiểu stylized low-poly 3d miniature nổi giữa nền đen, accent teal trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized low-poly 3D miniature — Faceted low-poly geometry, flat tone per face, matte paper feel; water a touch glossy; warm low side sun, soft shadow edges, cool sky fill on shade sides
- video_motion: facets unfold from a seed point, pop-up bounces, heaving water, bobbing droplets

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#01` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #01 Low-Poly · Filters over 3D · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `lowpoly` của engine three.js, block Flow ngắn tự viết
