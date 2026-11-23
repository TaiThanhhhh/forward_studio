# Sketchnote Black (`sketchnote-black`)

Trang sổ nghiên cứu vẽ tay bản tối: nét bút trắng ngà đứng yên + MỘT màu cam, bóng bằng hatching chéo, khung tiêu đề nét đứt góc vẽ lố, nhãn '@' khối đặc; nét vẽ ra từng nét, camera đọc từ trên xuống.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** biology, nature, observation, anatomy, plant, animal, discovery, diary, insect, bee, tree, forest
- **Nền đen tối thiểu:** 70% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải line boil (nét ở đây KHÔNG rung, có hatching, vẽ ra dần rồi đứng)
- không phải lab-notebook-black (đó là bảng bằng chứng có thẻ ghim, engine board)
- không phải chalk (không phấn, không bảng)
- không hợp nhiều số liệu/biểu đồ hoặc cắt nhanh

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #E8E6DC
- `a` #F8711C
- ĐẢO từ giấy trắng ngà mực xanh đen: nét trắng ngà trên đen + một màu cam

## Chữ (text_fx / thumbnail)

- font `PatrickHand-Regular.ttf` · cỡ 128 · chữ thường · vào bằng `write_on` (12 frame) · số `#F8711C`

## Luật nhịp

- **fps:** ones
- **easing:** nét vẽ ra tuyến tính, chữ viết ra từng chữ
- **bounce:** không
- **camera:** trôi đọc từ trên xuống, không zoom
- **cut_rule:** cắt như lật trang

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** đường dẫn mảnh, đầu có chấm đặc
- **circle:** khoanh tay elip hở màu cam
- **label:** '@nhãn:' khối cam đặc, chữ tay

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→scratch, hit→thud, whoosh→scrape, tick→scratch, ding→ting
- nhạc: guitar mộc/piano nhỏ, thong thả · 92 BPM
- persona giọng: nhà tự nhiên học kể nhỏ nhẹ
- thumbnail: một hình vẽ nét có hatching + khoanh cam + chữ tay

## Cho Flow (khi style này dùng clip Flow)

- image_style: Hand-drawn research sketchnote — Steady off-white pen linework with diagonal hatching for shade, one orange accent, dashed title box with overshooting corners, black page
- video_motion: lines draw on stroke by stroke, the view reads slowly from top to bottom

## Nguồn

- dashi-animationstyle — https://github.com/chuspeeism/dashi-animationstyle @ `aa620f3b859a` · license: MIT
- lấy từ: styles/手绘笔记/风格卡.md (MIT)
- cách chuyển: port ý tưởng kỹ thuật từ mã MIT, viết lại thành module của engine html (không chạy repo gốc); bỏ xử lý chữ Trung; đối chiếu để không trùng lab-notebook-black (engine board)
