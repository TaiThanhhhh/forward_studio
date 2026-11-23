# Halftone Print Black (`halftone-print-black`)

In tram trên sân khấu đen: mỗi vật là một mảnh giấy in 4 màu CMYK — chấm tram theo góc, bản màu lệch nhẹ, viền mực đen; chữ khối kiểu poster/báo in sắc nét trên lớp chấm. Giấy chỉ có trong hình, nền luôn đen.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** print, newspaper, headline, poster, advertising, magazine, pop-art, vintage, 1950s, 1960s, propaganda, invention, factory, industry, election, news
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải pop-art Lichtenstein toàn khung — giấy chỉ có TRONG hình, nền đen
- không phải comic (không khung tranh, không bóng thoại)
- không phải pointillism (chấm theo lưới tram đều góc, không phải vệt cọ)
- không gradient mượt — mọi tông màu là mật độ chấm

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F6EEDD
- `a` #E5432F
- `b` #2A6FB5
- `c` #F4B42E
- kem giấy + đỏ son + xanh cyan đậm + vàng mực in; nền đen

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 124 · IN HOA · vào bằng `pop` (7 frame) · số `#F4B42E`

## Luật nhịp

- **fps:** ones (30fps)
- **easing:** out — dập nhanh rồi dừng như máy in
- **bounce:** không
- **cut_rule:** cắt như lật trang báo: một mảng in mới trượt vào
- **rule:** mỗi vật là một mảnh in phẳng

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên mực đặc
- **circle:** vòng nét mực
- **label:** tem vé xé góc khuyết, chữ mực đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→stamp, hit→thud, whoosh→whoosh, tick→click, ding→ding
- nhạc: swing/big-band ngắn, kèn đồng, 112 BPM · 112 BPM
- persona giọng: phát thanh viên thời báo in, rành mạch, hơi kịch
- thumbnail: một vật in tram thật to giữa nền đen, chấm CMYK thấy rõ + 2–3 từ chữ khối kem

## Cho Flow (khi style này dùng clip Flow)

- image_style: Halftone print collage — Objects printed as CMYK halftone dots with slight plate misregistration and bold black ink outlines, like cut-out newspaper print, floating on pure black
- video_motion: snappy press-like entrances, small paper flutter, slow push

## Nguồn

- studio — engine html (looks.js + post2d.js, vòng 10) — engines/html/looks.js · engines/html/post2d.js (mã trong repo) @ `—` · license: mã của kênh; font OFL/Apache ghi ở docs/round10/H1.md
- lấy từ: bài tham khảo '10 Claude animation styles' (chỉ tên phong cách); kỹ thuật in tram/Bayer/rối bóng viết mới
- cách chuyển: look html mới (bút + hậu kỳ WebGL một pass) trên sân khấu đen; không chép mã/tài sản bên ngoài
