# Physics Diagram Black (`physics-diagram-black`)

Sơ đồ vật lý/toán kiểu bảng đen số: nền đen tuyệt đối, chỉ đặt 'thứ đang được nói', đồ thị vẽ dần có chấm chạy, vector lực, phương trình mà mỗi ký hiệu cùng màu với vật nó chỉ; biến đổi mượt thay cho cắt.

- **Engine:** `manim` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** heat, temperature, force, energy, math, equation, graph, pressure, speed, gravity, cooling, physics, freeze, melt, boil, degree, magnet, magnetic, bullet
- **Nền đen tối thiểu:** 80% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải slide chữ trên nền đen (không liệt kê gạch đầu dòng)
- không phải HUD (không trang trí dữ liệu giả)
- không phải Swiss (không lưới chữ, không khối đồ hoạ)
- không hợp câu chuyện/ý kiến — chỉ khi có thứ để 'biến thành' hoặc đo được

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #ECECEC
- `a` #FF6B3D
- `b` #58C4DD
- `c` #FFD866
- màu = tên khái niệm: cam = nóng/lực, xanh = lạnh/nước, vàng = kết quả; tối đa 4 màu ngữ nghĩa

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 112 · chữ thường · vào bằng `write_on` (10 frame) · số `#FFD866`

## Luật nhịp

- **fps:** ones
- **easing:** smooth (ease-in-out) cho mọi biến đổi; một hoạt cảnh 1–3 s rồi giữ
- **bounce:** không
- **rule:** đối tượng xuất hiện trước, chữ/phương trình đến sau; cùng lúc ≤ 2 ý trên màn hình
- **hold:** khi giữ chỉ còn camera trôi rất nhẹ
- **cut_rule:** ưu tiên biến đổi (Transform) thay cho cắt

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** vector mảnh đầu nhọn, màu theo khái niệm
- **circle:** khung nhấn (surrounding rectangle) vẽ một lượt
- **label:** chữ nhỏ cùng màu với vật

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→tick, hit→thud, whoosh→whoosh_soft, tick→tick, ding→ting
- nhạc: piano + dây tối giản, suy tư · 90 BPM
- persona giọng: thầy giáo điềm đạm, tò mò, nói như đang nghĩ
- thumbnail: một đường cong cam trên trục toạ độ + một con số vàng

## Cho Flow (khi style này dùng clip Flow)

- image_style: Mathematical animation diagram — Thin precise coloured lines and curves on a pure black background, clean axes, vectors and equations where colour encodes meaning, no decoration
- video_motion: curves draw on smoothly, shapes transform into one another, long calm holds

## Nguồn

- manim (Community Edition) — https://github.com/ManimCommunity/manim @ `pip` · license: MIT
- lấy từ: thư viện (pip install manim) + ngữ pháp t1 của huashu-art-motion (references/动画语法/t1_3b1b.md, MIT)
- cách chuyển: dùng làm thư viện; scene viết mới trong engines/manim; luật 'màu = tên khái niệm, ≤ 2 ý trên màn hình, đối tượng trước chữ sau' học từ grammar t1
