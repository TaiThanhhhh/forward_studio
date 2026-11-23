# Voxel · dark stage (`atlas-voxel`)

Biến thể dark-stage của style #18 "Voxel" (Bộ lọc trên 3D) trong 3D Style Atlas: thứ lớn dần theo giai đoạn. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #18 Voxel · nhóm Filters over 3D · tier 2 · brand_fit `ok` · hợp kênh 3/5 · gần `lowpoly3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D voxel model on a pure black stage (#000000): chamfered matte cubes on an off-white plinth. Warm sun front-left, sky occlusion in corners, per-cube contact shadow. One accent colour (leaf green) only on the key element. Leave the blank front face of the display base empty (captions are added later).
- **Block Flow (chuyển động):** Column drop-ins and layer growth, swelling and popping cubes, bounce on landing.
- **Hợp chủ đề (tags):** plant, seed, grow, cube, blocks
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffffff
- `a` #86b84f
- `b` #8a5a38
- `c` #a5cf5c
- sân khấu đen + accent leaf green

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#a5cf5c`

## Luật nhịp

- **fps:** full
- **easing:** bậc, gọn
- **bounce:** có
- **camera:** long lens at ~26°, wide aperture miniature look, slow arc and pull-back
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
- thumbnail: một vật chủ đạo kiểu 3d voxel model nổi giữa nền đen, accent leaf green trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D voxel model — Chamfered matte cubes on an off-white plinth; warm sun front-left, sky occlusion in corners, per-cube contact shadow
- video_motion: column drop-ins and layer growth, swelling and popping cubes, bounce on landing

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#18` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #18 Voxel · Filters over 3D · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `lowpoly` của engine three.js, block Flow ngắn tự viết
