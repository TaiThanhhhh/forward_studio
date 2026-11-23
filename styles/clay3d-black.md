# Clay 3D Black (`clay3d-black`)

Hoạt hình 3D đất sét / mô hình thu nhỏ (stylized 3D clay diorama) trên sân khấu đen tuyền: bề mặt matte mịn như đất sét nặn, rim light rõ khối, bóng đổ mềm, kết hợp clip 3D Google Flow và cảnh 3D Three.js (`stage`).

- **Engine:** `flow`
- **Hợp chủ đề (tags):** 3d, diorama, clay, model, body, muscle, heart, organ, shoe, gym, hardware, gadget
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải photorealistic CGI hay ảnh chụp thật
- không có môi trường nền phức tạp (nền luôn đen tuyền #000000)
- không phẳng 2D (mọi vật thể có khối 3D tròn trịa, bóng đổ và rim light)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F4F1EA
- `a` #3F6BFF
- `b` #FF5A3C
- `c` #FFD27A
- trắng kem đất sét + xanh điện accent + cam đỏ cảnh báo + vàng ấm

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#FFD27A`

## Luật nhịp

- **fps:** twos
- **easing:** stop-motion / claymation bật nảy có squash-and-stretch và overshoot nhẹ
- **bounce:** có
- **camera:** orbit nhẹ quanh mô hình + push-in chậm tạo chiều sâu 3D
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
- thumbnail: một mô hình 3D đất sét nổi bật giữa nền đen tuyền, rim light xanh điện, một chi tiết đỏ cam sắp phát nổ

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D clay diorama — Tactile matte clay 3D models with smooth rounded edges, bright rim lighting, soft studio shadows, matte off-white and slate-grey surfaces
- video_motion: snappy stop-motion-inspired 3D timing with tactile squash-and-stretch, quick anticipation, and slight overshoot

## Nguồn

- three.js + cartoon-short-kit — https://github.com/mrdoob/three.js @ `e22995279d07` · license: MIT
- lấy từ: engines/three/main.js + engines/three/props.js (3-step toon/clay shading + rim light trên nền đen)
- cách chuyển: kết hợp prompt 3D diorama cho Google Flow (bỏ cấm 3D render/3D shading) với engine Three.js 3D cùng bảng màu
