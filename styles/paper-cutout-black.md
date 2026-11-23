# Paper Cutout Black (`paper-cutout-black`)

Cắt giấy 2D nhiều lớp: mép xé răng cưa có lõi giấy trắng, vân giấy, bóng mềm theo độ sâu lớp, nhịp stop-motion on 2s và mỗi lần chụp lệch nhẹ; nền là các dải giấy rất tối trôi thị sai trên đen.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** kids, children, craft, paper, origami, school, toy, pet, farm, garden, dog, cat, bird, season, picnic, puppy
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải papercraft 3D (đây là lớp giấy phẳng 2D/2.5D)
- không phải style `paper_cutout` cũ (chỉ kiểu chữ + look spy)
- không nền giấy toàn khung — các lớp nền là giấy rất tối, khung vẫn đen

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F4EAD5
- `a` #E2552D
- `b` #2F86A6
- `c` #F3C246
- giấy kem + cam đất + xanh mòng két + vàng mù tạt

## Chữ (text_fx / thumbnail)

- font `LuckiestGuy-Regular.ttf` · cỡ 120 · IN HOA · vào bằng `pop` (7 frame) · số `#F3C246`

## Luật nhịp

- **fps:** on 2s (stop-motion) + lệch nhẹ mỗi lần chụp
- **easing:** dead — trượt rồi dừng
- **bounce:** không
- **cut_rule:** cắt khi một lớp giấy trượt che khung
- **rule:** mọi vật là mảnh giấy có độ sâu lớp

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên giấy xé
- **circle:** vòng giấy
- **label:** băng giấy xé, chữ in đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→pop, hit→thunk, whoosh→scrape, tick→click, ding→ting
- nhạc: ukulele + glockenspiel vui, 104 BPM · 104 BPM
- persona giọng: cô giáo mầm non kể chuyện, vui, rõ ràng
- thumbnail: con vật/vật cắt giấy mép xé thật to trên đen, bóng mềm, 2–3 từ chữ tròn

## Cho Flow (khi style này dùng clip Flow)

- image_style: 2D paper cutout stop-motion — Layered torn-paper cutouts with white fibrous edges, visible paper grain and soft drop shadows between layers, floating over pure black
- video_motion: stop-motion on twos with tiny jitter each frame, layers slide in

## Nguồn

- studio — engine html (looks.js + post2d.js, vòng 10) — engines/html/looks.js · engines/html/post2d.js (mã trong repo) @ `—` · license: mã của kênh; font OFL/Apache ghi ở docs/round10/H1.md
- lấy từ: bài tham khảo '10 Claude animation styles' (chỉ tên phong cách); kỹ thuật in tram/Bayer/rối bóng viết mới
- cách chuyển: look html mới (bút + hậu kỳ WebGL một pass) trên sân khấu đen; không chép mã/tài sản bên ngoài
