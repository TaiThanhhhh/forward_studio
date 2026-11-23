# Museum Gallery · dark stage (`atlas-museum-gallery`)

Biến thể dark-stage của style #24 "Museum Gallery" (Không gian và hành trình) trong 3D Style Atlas: dòng thời gian 3–5 mốc. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #24 Museum Gallery · nhóm Spaces and journeys · tier 2 · brand_fit `ok` · hợp kênh 3/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D dark museum gallery on a pure black stage (#000000): framed flat prints, gilt-and-black frames, engraved brass plaques, rope barrier. Tight warm overhead spot per exhibit and plaque, darkness between pools. One accent colour (warm spot gold) only on the key element. Leave blank brass plaques beside each frame empty (captions are added later).
- **Block Flow (chuyển động):** Single unbroken move: wide on the first piece, tracking the middle, pushing in on the last.
- **Hợp chủ đề (tags):** timeline, museum, moments, milestones, evolution
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f6f2e8
- `a` #ffdfb8
- `b` #0f4a4d
- `c` #ffd9aa
- sân khấu đen + accent warm spot gold

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffd9aa`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** low never-stopping dolly, focus pulled exhibit to exhibit
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
- thumbnail: một vật chủ đạo kiểu 3d dark museum gallery nổi giữa nền đen, accent warm spot gold trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D dark museum gallery — Framed flat prints, gilt-and-black frames, engraved brass plaques, rope barrier; tight warm overhead spot per exhibit and plaque, darkness between pools
- video_motion: single unbroken move: wide on the first piece, tracking the middle, pushing in on the last

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#24` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #24 Museum Gallery · Spaces and journeys · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
