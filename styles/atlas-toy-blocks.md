# Toy Blocks · dark stage (`atlas-toy-blocks`)

Biến thể dark-stage của style #22 "Toy Blocks" (Thế giới chất liệu) trong 3D Style Atlas: tỉ lệ, ngân sách, danh sách. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #22 Toy Blocks · nhóm Material worlds · tier 2 · brand_fit `off-brand` · hợp kênh 2/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D painted wooden toy blocks on a pure black stage (#000000): maple blocks with true grain, chipped milk paint (blue, coral, green, mustard). Late-afternoon window sun with frame-shadow stripes, long block shadows. One accent colour (dusty blue) only on the key element. Leave blank block faces empty (captions are added later).
- **Block Flow (chuyển động):** Weighted drops: corner hit, one bounce, rocking, settling knock.
- **Hợp chủ đề (tags):** budget, percent, proportion, blocks, building-blocks
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #e6dcc4
- `a` #3d6a97
- `b` #cf6a4a
- `c` #e3a83a
- sân khấu đen + accent dusty blue

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#e3a83a`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** child-eye-height long lens, rise to the first tower, slow arc round the stacks
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
- thumbnail: một vật chủ đạo kiểu 3d painted wooden toy blocks nổi giữa nền đen, accent dusty blue trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D painted wooden toy blocks — Maple blocks with true grain, chipped milk paint (blue, coral, green, mustard); late-afternoon window sun with frame-shadow stripes, long block shadows
- video_motion: weighted drops: corner hit, one bounce, rocking, settling knock

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#22` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #22 Toy Blocks · Material worlds · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `clay` của engine three.js, block Flow ngắn tự viết
