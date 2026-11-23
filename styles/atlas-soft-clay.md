# Soft Clay · dark stage (`atlas-soft-clay`)

Biến thể dark-stage của style #03 "Soft Clay" (Thế giới chất liệu) trong 3D Style Atlas: chủ đề ấm áp, số lượng thành đống/chồng. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #03 Soft Clay · nhóm Material worlds · tier 2 · brand_fit `ok` · hợp kênh 4/5 · gần `clay3d-black` · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** Stop-motion plasticine 3D on a pure black stage (#000000): plasticine with thumbprints and tool dents, two-tone streaked clay, waxy sheen. Large soft source top-left, strong crease occlusion, contact shadows. One accent colour (teal) only on the key element. Leave a blank flat clay slab in front of the subject empty (captions are added later).
- **Block Flow (chuyển động):** Stop-motion on twos, no motion blur, squash-and-stretch hops and recoils.
- **Hợp chủ đề (tags):** money, savings, pile, stack, grow, compare, food
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #f3e6cd
- `a` #12808a
- `b` #de3a26
- `c` #f4ad08
- sân khấu đen + accent teal

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#f4ad08`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** macro, shallow depth of field, slow dolly from detail out to the full set
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
- thumbnail: một vật chủ đạo kiểu stop-motion plasticine 3d nổi giữa nền đen, accent teal trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stop-motion plasticine 3D — Plasticine with thumbprints and tool dents, two-tone streaked clay, waxy sheen; large soft source top-left, strong crease occlusion, contact shadows
- video_motion: stop-motion on twos, no motion blur, squash-and-stretch hops and recoils

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#03` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #03 Soft Clay · Material worlds · Explainer
- cách chuyển: dark-stage: nền #000, look 3D `clay` của engine three.js, block Flow ngắn tự viết
