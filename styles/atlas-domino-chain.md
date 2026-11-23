# Domino Chain · dark stage (`atlas-domino-chain`)

Biến thể dark-stage của style #26 "Domino Chain" (Cỗ máy giải thích) trong 3D Style Atlas: phản ứng dây chuyền, tăng theo cấp số. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #26 Domino Chain · nhóm Machines that explain · tier 1 · brand_fit `ok` · hợp kênh 4/5
- **Block Flow (ảnh):** 3D hand-made dominoes on a dark table on a pure black stage (#000000): bone faces with painted engraving on ebony backs, polished walnut tabletop. Low warm lamp at the head of the row, long shadows onto each next piece. One accent colour (red) only on the key element. Leave blank engraved faces on each domino empty (captions are added later).
- **Block Flow (chuyển động):** Hesitate, tip, accelerate, strike; tiny pieces tick quickly, large ones topple slowly.
- **Hợp chủ đề (tags):** chain-reaction, domino, exponential, double, compound, cascade
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ffe6cc
- `a` #d8302a
- `b` #2e1c10
- `c` #ffd2a0
- sân khấu đen + accent red

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffd2a0`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** long lens tracking the falling front, backing away, rising to high three-quarter
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
- thumbnail: một vật chủ đạo kiểu 3d hand-made dominoes on a dark table nổi giữa nền đen, accent red trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D hand-made dominoes on a dark table — Bone faces with painted engraving on ebony backs, polished walnut tabletop; low warm lamp at the head of the row, long shadows onto each next piece
- video_motion: hesitate, tip, accelerate, strike; tiny pieces tick quickly, large ones topple slowly

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#26` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #26 Domino Chain · Machines that explain · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
