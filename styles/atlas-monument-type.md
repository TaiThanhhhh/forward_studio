# Monument Type · dark stage (`atlas-monument-type`)

Biến thể dark-stage của style #37 "Monument Type" (Không gian và hành trình) trong 3D Style Atlas: câu kết luận 2–5 từ. Viết lại bằng lời của tool trên sân khấu đen, một accent.

- **Engine:** `flow`
- **3D Style Atlas:** #37 Monument Type · nhóm Spaces and journeys · tier 2 · brand_fit `off-brand` · hợp kênh 2/5 · **chỉ chọn tay** (không vào vòng tự động)
- **Block Flow (ảnh):** 3D colossal concrete letters as architecture on a pure black stage (#000000): board-formed concrete with pour joints, rusted welded steel plates for the hero word. Low raking sun front-left, long shadows, blue shade. One accent colour (rusted steel) only on the key element. Leave blank terraces where the words will be set empty (captions are added later).
- **Block Flow (chuyển động):** Static lettering; all motion comes from the camera.
- **Hợp chủ đề (tags):** verdict, motto, monument, principle, slogan
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp thật / CGI quảng cáo
- không có phông nền sáng hay đường chân trời — sân khấu luôn đen
- không để AI vẽ chữ hay số: chữ do text_fx / engine thêm sau

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #b3afa6
- `a` #73391f
- `b` #c4a06a
- `c` #ffffff
- sân khấu đen + accent rusted steel

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#ffffff`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** single drone move, deep focus, eye height to low over the water
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
- thumbnail: một vật chủ đạo kiểu 3d colossal concrete letters as architecture nổi giữa nền đen, accent rusted steel trên chi tiết sắp xảy ra chuyện

## Cho Flow (khi style này dùng clip Flow)

- image_style: 3D colossal concrete letters as architecture — Board-formed concrete with pour joints, rusted welded steel plates for the hero word; low raking sun front-left, long shadows, blue shade
- video_motion: static lettering; all motion comes from the camera

## Nguồn

- 3D Style Atlas (Futurepedia / HubSpot Media) — https://www.futurepedia.io/resources/3d-style-atlas/view @ `#37` · license: HubSpot Website Terms of Use (cá nhân, phi thương mại) — chỉ lấy ý tưởng thị giác, chữ + mã viết mới; xem docs/CREDITS.md
- lấy từ: #37 Monument Type · Spaces and journeys · Title
- cách chuyển: dark-stage: nền #000, look 3D `clay` của engine three.js, block Flow ngắn tự viết
