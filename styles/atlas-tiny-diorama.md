# Tiny Diorama · dark stage (`atlas-tiny-diorama`)

Biến thể dark-stage của style #04 "Tiny Diorama" (Không gian và hành trình) trong 3D Style Atlas: hệ thống có nhiều điểm dừng và một thứ di chuyển giữa chúng. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #04 Tiny Diorama · nhóm Spaces and journeys · tier 1 · brand_fit `adapted` · hợp kênh 4/5
- **Block Flow (ảnh):** Stylized 3D tilt-shift diorama on a pure black stage (#000000): floating ground tile, cut soil-and-rock edge, matte model buildings, flocked grass, peg figures. Warm low sun front-left sinking over the clip, cool sky in creases, tiny lamps late. One accent colour (warm orange) only on the key element. Leave a blank sign board on each little building empty (captions are added later).
- **Block Flow (chuyển động):** Toy vehicle with braking weight, swinging doors, smoke puffs, hopping figures, flipping signs.
- **Hợp chủ đề (tags):** delivery, parcel, city, traffic, travel, supply-chain, transport
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #fff6e6
- `a` #ff6a2a
- `b` #bcd3ff
- `c` #e8f5b0
- sân khấu đen + accent warm orange

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#e8f5b0`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** three-quarter top view, long lens, tile on a turntable, camera rises and pushes in
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
- thumbnail: một vật chủ đạo kiểu stylized 3d tilt-shift diorama nổi giữa nền đen, accent warm orange trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D tilt-shift diorama — Floating ground tile, cut soil-and-rock edge, matte model buildings, flocked grass, peg figures; warm low sun front-left sinking over the clip, cool sky in creases, tiny lamps late
- video_motion: toy vehicle with braking weight, swinging doors, smoke puffs, hopping figures, flipping signs

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#04` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #04 Tiny Diorama · Spaces and journeys · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `clay` của engine three.js, block Flow ngắn tự viết
