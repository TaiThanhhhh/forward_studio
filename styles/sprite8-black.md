# Sprite 8-bit Black (`sprite8-black`)

Sprite 8-bit kiểu máy console đời đầu: lưới 1/10, bảng 16 màu, mỗi vật ≤ 4 màu kể cả đen, viền đen 1 khối, hoạt hoạ bậc on 2s, rung màn theo lưới khi va chạm; chữ Press Start 2P đúng lưới pixel.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** 8-bit, arcade, chiptune, coin, score, high-score, lives, platformer, glitch, cheat, 1980s, sprite, pixel-art, retro, insert, joystick
- **Nền đen tối thiểu:** 60% khung hình (QA đo)

## Nó KHÔNG phải là

- không nhân vật/logo game có bản quyền — sprite tự dựng
- không phải 16-bit (không dither, ≤ 4 màu/vật, lưới thô hơn)
- không chuyển động mượt — mọi thứ nhảy bậc

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #FCFCFC
- `a` #E83A3A
- `b` #3CBCFC
- `c` #F8B800
- bảng kiểu console 8-bit: trắng + đỏ + xanh trời + vàng cam, mỗi màu 3 nấc

## Chữ (text_fx / thumbnail)

- font `PressStart2P-Regular.ttf` · cỡ 96 · IN HOA · vào bằng `pop` (7 frame) · số `#F8B800`

## Luật nhịp

- **fps:** on 2s (giữ khung), hoạt hoạ bậc 4 frame
- **easing:** steps — nhảy bậc
- **bounce:** không
- **cut_rule:** cắt cứng như đổi màn
- **rule:** ≤ 4 màu mỗi vật

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên khối
- **circle:** 4 góc con trỏ menu
- **label:** hộp thoại viền đôi

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, glitch
- gói SFX (cue chung → âm): pop→pop, hit→crash, whoosh→whoosh_soft, tick→tick, ding→ting
- nhạc: chiptune 8-bit 3 kênh, nhịp nhanh, 140 BPM · 140 BPM
- persona giọng: người dẫn arcade hào hứng, câu ngắn như dòng chữ trên màn game
- thumbnail: một sprite 8-bit 4 màu cực to trên nền sao đen + chữ PRESS START-style 2 từ

## Cho Flow (khi style này dùng clip Flow)

- image_style: 8-bit sprite art — Very low-resolution 8-bit console sprites, at most four colours per sprite including black, 1-pixel black outlines, on a pure black background with blocky stars
- video_motion: stepped animation on twos, screen shake snapped to the pixel grid

## Nguồn

- studio — engine html (looks.js + post2d.js, vòng 10) — engines/html/looks.js · engines/html/post2d.js (mã trong repo) @ `—` · license: mã của kênh; font OFL/Apache ghi ở docs/round10/H1.md
- lấy từ: bài tham khảo '10 Claude animation styles' (chỉ tên phong cách); kỹ thuật in tram/Bayer/rối bóng viết mới
- cách chuyển: look html mới (bút + hậu kỳ WebGL một pass) trên sân khấu đen; không chép mã/tài sản bên ngoài
