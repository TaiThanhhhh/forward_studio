# Inflated · dark stage (`atlas-inflated`)

Biến thể dark-stage của style #12 "Inflated" (Thế giới chất liệu) trong 3D Style Atlas: áp suất, giãn nở, nổi, chân không. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #12 Inflated · nhóm Material worlds · tier 1 · brand_fit `adapted` · hợp kênh 4/5 · gần `plastic-toy3d-black`
- **Block Flow (ảnh):** 3D glossy inflatable vinyl on a pure black stage (#000000): clear-coated candy vinyl, cream trim, welded seams, glossy dark floor. Overhead and side softboxes, long white specular streaks, soft top-left key. One accent colour (candy red) only on the key element. Leave a blank inflated banner tube beside the subject empty (captions are added later).
- **Block Flow (chuyển động):** Pump-up with overshoot to taut, wobble, float and sway; air drives everything.
- **Hợp chủ đề (tags):** pressure, balloon, inflate, vacuum, squeeze, expand, air
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #fffdf6
- `a` #ff3a2e
- `b` #2545f2
- `c` #ffc414
- sân khấu đen + accent candy red

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ffc414`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** slow long-lens crane locked to the hero object as it lies, stands and rises
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
- thumbnail: một vật chủ đạo kiểu 3d glossy inflatable vinyl nổi giữa nền đen, accent candy red trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D glossy inflatable vinyl — Clear-coated candy vinyl, cream trim, welded seams, glossy dark floor; overhead and side softboxes, long white specular streaks, soft top-left key
- video_motion: pump-up with overshoot to taut, wobble, float and sway; air drives everything

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#12` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #12 Inflated · Material worlds · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `plastic` của engine three.js, block Flow ngắn tự viết
