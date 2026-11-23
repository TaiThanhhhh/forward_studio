# Ink and Toon · dark stage (`atlas-ink-and-toon`)

Biến thể dark-stage của style #20 "Ink and Toon" (Bộ lọc trên 3D) trong 3D Style Atlas: công thức, các bước trên một vật chính. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **3D Style Atlas:** #20 Ink and Toon · nhóm Filters over 3D · tier 2 · brand_fit `adapted` · hợp kênh 4/5 · gần `toon3d-lab` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D cel-shaded toon with ink lines on a pure black stage (#000000): textureless: lit tone, shadow tone and one hard glint per glossy surface. Hard low side sun placed for shadow shape, no fill, cool shadow tints. One accent colour (teal) only on the key element. Leave a blank hand-drawn caption box empty (captions are added later).
- **Block Flow (chuyển động):** Held poses on twos, smear in-betweens, overshoot and settle, drawn speed lines.
- **Hợp chủ đề (tags):** recipe, coffee, how-to, cooking, kitchen
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f7ecd6
- `a` #1c7376
- `b` #c99766
- `c` #12565c
- sân khấu đen + accent teal

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#12565c`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** long-lens tabletop framing, drift on holds, whip pans between framings
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
- thumbnail: một vật chủ đạo kiểu 3d cel-shaded toon with ink lines nổi giữa nền đen, accent teal trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D cel-shaded toon with ink lines — Textureless: lit tone, shadow tone and one hard glint per glossy surface; hard low side sun placed for shadow shape, no fill, cool shadow tints
- video_motion: held poses on twos, smear in-betweens, overshoot and settle, drawn speed lines

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#20` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #20 Ink and Toon · Filters over 3D · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `toon` của engine three.js, block Flow ngắn tự viết
