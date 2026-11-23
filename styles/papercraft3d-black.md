# Papercraft 3D Black (`papercraft3d-black`)

Mô hình giấy gấp 3D trên nền đen: mặt giấy phẳng, nếp gấp rõ, nét mảnh, hạt giấy, màu kem + đỏ + xanh mực. Ngày có Flow: clip giấy gấp 3D; shot code three.js cùng chất giấy.

- **Engine:** `flow`
- **Hợp chủ đề (tags):** paper, book, history, origami, letter, story, craft, school, recipe, kitchen, money, city, house
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải ảnh giấy thật
- không nền bàn làm việc (nền đen #000000)
- không bề mặt bóng

## Bảng màu (nền đen + tối đa 2–3 màu)

- `ink` #F5EBDD
- `a` #3E7CB1
- `b` #E8553E
- `c` #F2C14E
- `bg` #000000

## Chữ (text_fx / thumbnail)

- font `Baloo2-Variable.ttf` · cỡ 118 · IN HOA · vào bằng `pop` (7 frame) · số `#F2C14E`

## Luật nhịp

- **fps:** twos
- **easing:** gấp/mở như sách pop-up
- **bounce:** có
- **camera:** nghiêng nhẹ như nhìn sách
- **cut_rule:** cắt khi trang mở xong

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên giấy cắt
- **circle:** vòng giấy
- **label:** nhãn giấy dán

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→whoosh_soft, tick→tick, ding→ding
- nhạc: pizzicato strings, paper rustle, light percussion · 104 BPM
- persona giọng: người kể chuyện ấm, như đọc sách pop-up
- thumbnail: một mô hình giấy gấp nổi khối giữa nền đen, nếp gấp rõ, một mảnh đỏ bung ra

## Cho Flow (khi style này dùng clip Flow)

- image_style: Stylized 3D papercraft render — Folded paper models with crisp creases, matte cream, red and ink-blue paper, visible paper grain, thin cut edges, soft shadows on a pure black stage
- video_motion: pop-up book motion: pieces unfold, fold and flip into place, slight paper flutter

## Nguồn

- studio — engine three.js (look3d) — https://github.com/mrdoob/three.js @ `None` · license: MIT
- lấy từ: engines/three/main.js → LOOK3D (chất liệu + env map studio + hậu kỳ ACES/bloom/grain)
- cách chuyển: preset chất liệu 3D của engine three.js trên sân khấu đen; prompt Flow 3D cùng look cho ngày có Flow
