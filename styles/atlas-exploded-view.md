# Exploded View · dark stage (`atlas-exploded-view`)

Biến thể dark-stage của style #08 "Exploded View" (Sơ đồ có chiều sâu) trong 3D Style Atlas: bên trong có gì, vật làm từ những phần nào. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #08 Exploded View · nhóm Diagrams with depth · tier 1 · brand_fit `adapted` · hợp kênh 5/5
- **Block Flow (ảnh):** 3D product teardown on a pure black stage (#000000): one finish per part: clear plastic, chrome, brass, coil spring, black rubber, one orange piece. Huge soft overhead source, soft floor shadows, dark cards streaking the chrome. One accent colour (ink blue) only on the key element. Leave small blank numbered tags on thin leader lines empty (captions are added later).
- **Block Flow (chuyển động):** Unscrew, separate into sub-assemblies, fan out part by part with overshoot, reassemble.
- **Hợp chủ đề (tags):** inside, parts, teardown, battery, engine, made-of, components
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #e6e8ec
- `a` #1b2f8c
- `b` #ff6a1c
- `c` #fbf7ee
- sân khấu đen + accent ink blue

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#fbf7ee`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** long lens along the object axis, slow crane, focus hopping part to part
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
- thumbnail: một vật chủ đạo kiểu 3d product teardown nổi giữa nền đen, accent ink blue trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D product teardown — One finish per part: clear plastic, chrome, brass, coil spring, black rubber, one orange piece; huge soft overhead source, soft floor shadows, dark cards streaking the chrome
- video_motion: unscrew, separate into sub-assemblies, fan out part by part with overshoot, reassemble

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#08` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #08 Exploded View · Diagrams with depth · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
