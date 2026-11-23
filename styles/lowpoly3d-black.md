# Low-poly 3D Black (`lowpoly3d-black`)

Low-poly đa giác phẳng 3D trên nền đen: khối ít mặt, đổ bóng phẳng từng mặt, nét mảnh, màu đất ấm + teal. Toàn bộ bằng code (three.js flatShading + hình học ít cạnh).

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** mountain, planet, earth, volcano, animal, forest, geography, map, world, island, dinosaur, desert, ancient
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không mịn bóng (luôn thấy mặt đa giác)
- không nền phong cảnh (nền đen #000000)
- không ảnh thật

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #F3EFE6
- `a` #3FB8AF
- `b` #FF7A3D
- `c` #FFD166
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#FFD166`

## Luật nhịp

- **fps:** full
- **easing:** bậc, gọn
- **bounce:** có
- **camera:** orbit chậm kiểu diorama
- **cut_rule:** cắt khi khối lắp xong

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên đa giác
- **circle:** vòng đa giác
- **label:** nhãn phẳng

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: marimba arpeggios, soft kick, adventurous · 108 BPM
- persona giọng: người kể chuyện tò mò, ấm
- thumbnail: một hòn núi/hành tinh low-poly nhiều mặt phẳng giữa nền đen, một mặt cam rực

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized low-poly 3D render — Faceted low-polygon geometry with flat-shaded faces, warm earth tones and teal accents, thin outlines, soft directional light on a pure black stage
- video_motion: clean geometric motion, stepped rotations, pops into place

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
