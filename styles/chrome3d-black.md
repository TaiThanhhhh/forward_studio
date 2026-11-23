# Chrome 3D Black (`chrome3d-black`)

Kim loại chrome / thép bóng 3D trên nền đen: phản chiếu softbox trắng + dải rim cam nóng, không nét mực, bloom. Toàn bộ bằng code (three.js metalness = 1).

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** metal, steel, iron, gold, car, engine, machine, robot, coin, rocket, magnet, money, knife, sword
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh sản phẩm thật
- không nền xưởng (nền đen #000000)
- không bề mặt nhám không phản chiếu

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #F2F4F8
- `a` #FF9A3D
- `b` #8FB8FF
- `c` #FFD27A
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#FFD27A`

## Luật nhịp

- **fps:** full
- **easing:** nặng, dừng gắt
- **bounce:** không
- **camera:** dolly chậm bắt phản chiếu
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
- thumbnail: một khối chrome bóng gương phản chiếu dải cam nóng giữa nền đen

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D liquid-chrome render — Mirror-polished chrome and brushed steel objects reflecting a white studio softbox and a hot orange rim strip, crisp specular highlights, pure black void
- video_motion: heavy weighty motion, slow turns that catch reflections, sharp impact stops

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
