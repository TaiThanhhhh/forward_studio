# Hologram 3D Black (`hologram3d-black`)

Hologram khung dây 3D trên nền đen: lưới wireframe phát sáng cyan, bloom, hạt nhiễu, không bóng đổ — kiểu màn hình quét tương lai. Toàn bộ bằng code.

- **Engine:** `three` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** ai, computer, data, network, internet, hacker, code, future, space, satellite, signal, virus, simulation, scan
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không vật đặc có bề mặt (chỉ khung dây phát sáng)
- không nền (đen #000000)
- không ảnh thật

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #BFFBFF
- `a` #00E5FF
- `b` #FF3D7F
- `c` #7CFFB2
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `RobotoMono-Variable.ttf` · cỡ 104 · IN HOA · vào bằng `pop` (7 frame) · số `#7CFFB2`

## Luật nhịp

- **fps:** full
- **easing:** mượt, có glitch ngắn
- **bounce:** không
- **camera:** quét chậm quanh vật
- **cut_rule:** cắt bằng glitch

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên dây sáng
- **circle:** vòng quét
- **label:** nhãn HUD [ ]

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, glitch
- gói SFX (cue chung → âm): pop→glitch, hit→impact, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: dark synth pulse, data blips, sub bass · 92 BPM
- persona giọng: giọng điềm tĩnh, hơi bí ẩn, như hệ thống phân tích
- thumbnail: một vật thể khung dây cyan phát sáng giữa nền đen, một điểm hồng cảnh báo

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D wireframe hologram render — Glowing cyan wireframe meshes with bloom, thin scan lines and faint digital noise, magenta warning accents, floating in pure black space
- video_motion: smooth scanning motion, slow rotations, glitch flickers on reveals

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
