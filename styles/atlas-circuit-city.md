# Circuit City · dark stage (`atlas-circuit-city`)

Biến thể dark-stage của style #14 "Circuit City" (Không gian và hành trình) trong 3D Style Atlas: dữ liệu/tín hiệu đi qua máy tính, chip. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #14 Circuit City · nhóm Spaces and journeys · tier 1 · brand_fit `ok` · hợp kênh 4/5
- **Block Flow (ảnh):** 3D macro circuit board city at night on a pure black stage (#000000): solder mask over copper, gold traces, tinned pins, black epoxy chips, aluminium cans. Night; travelling signal as key light with moving shadows, cool moonlit rim. One accent colour (warm signal amber) only on the key element. Leave blank white silkscreen label boxes on the board empty (captions are added later).
- **Block Flow (chuyển động):** Light pulse racing along traces, landmarks waking in turn.
- **Hợp chủ đề (tags):** chip, computer, processor, data, internet, transistor
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #d9a546
- `a` #ffb347
- `b` #35ff7a
- `c` #ff3b30
- sân khấu đen + accent warm signal amber

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#ff3b30`

## Luật nhịp

- **fps:** full
- **easing:** nặng, dừng gắt
- **bounce:** không
- **camera:** macro, razor-thin focus, low forward flight chasing the pulse, crane over the CPU
- **cut_rule:** cắt ở va chạm kim loại

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên thép
- **circle:** vòng sáng cam
- **label:** nhãn khắc chữ

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→ting, hit→impact, whoosh→whoosh, tick→click, ding→ting
- nhạc: industrial pulse, metallic hits, low synth · 100 BPM
- persona giọng: giọng trầm, chắc, nhịp mạnh
- thumbnail: một vật chủ đạo kiểu 3d macro circuit board city at night nổi giữa nền đen, accent warm signal amber trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D macro circuit board city at night — Solder mask over copper, gold traces, tinned pins, black epoxy chips, aluminium cans; night; travelling signal as key light with moving shadows, cool moonlit rim
- video_motion: light pulse racing along traces, landmarks waking in turn

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#14` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #14 Circuit City · Spaces and journeys · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `chrome` của engine three.js, block Flow ngắn tự viết
