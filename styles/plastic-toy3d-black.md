# Plastic Toy 3D Black (`plastic-toy3d-black`)

Đồ chơi nhựa bóng (vinyl toy) 3D trên sân khấu đen: màu kẹo bão hoà, lớp phủ bóng clearcoat, phản chiếu softbox, bóng đổ mềm. Ngày có Flow: clip 3D đồ chơi; shot code three.js cùng chất liệu nhựa.

- **Engine:** `flow`
- **Hợp chủ đề (tags):** toy, game, kid, candy, sugar, playground, brick, plastic, balloon, dice, gummy, lego
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh chụp đồ chơi thật hay thương hiệu đồ chơi có thật
- không nền phòng chơi (nền luôn đen #000000)
- không bề mặt nhám/đất sét (luôn bóng, có highlight)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #F7F4EE
- `a` #2EC4FF
- `b` #FF4F6D
- `c` #FFD23F
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#FFD23F`

## Luật nhịp

- **fps:** full
- **easing:** bật nảy squash-and-stretch
- **bounce:** có
- **camera:** orbit nhẹ + push-in
- **cut_rule:** cắt ở pha bật nảy

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên nhựa 3D bo tròn
- **circle:** vòng nhựa sáng
- **label:** nhãn dán sticker bo tròn

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: toy-box plucks, glockenspiel, bouncy bass · 118 BPM
- persona giọng: người kể vui nhộn, nhanh, nhấn từ như đang chơi
- thumbnail: một món đồ chơi nhựa bóng màu kẹo giữa nền đen, phản chiếu softbox, một chi tiết đỏ sắp bật tung

## Cho Flow (khi style này dùng clip Flow)

- image_style: Glossy 3D vinyl-toy render — Chunky rounded glossy plastic toys with candy colours, clear-coat highlights from a studio softbox, soft contact shadows, tiny bevels on every edge
- video_motion: bouncy toy-like keyframes with squash-and-stretch, quick pops and playful overshoot

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
