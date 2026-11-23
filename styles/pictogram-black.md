# Pictogram Black (`pictogram-black`)

Phim pictogram kiểu nhận diện truyền hình: mỗi thẻ = một pictogram làm một việc + tiêu đề 900 khổng lồ + số mục mono '03 / 07'; nền là hoạ tiết đĩa/nửa đĩa năm sắc độ của MỘT màu, cả hàng trượt ngang; khoá theo nhịp.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** list, steps, ranking, safety, rules, sport, catalogue, body, survive, survival, olympic
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải isometric (không chiều sâu)
- không phải Swiss (pictogram và hoạ tiết gánh ngang chữ)
- không phải hoạt hình (pictogram không có mặt, không biểu cảm)
- không phải phim dữ liệu (số là nhãn, không phải biểu đồ)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #FFFFFF
- `a` #FFC400
- trắng + MỘT màu (vàng) dùng ở 5 sắc độ cho hoạ tiết; mỗi chương có thể đổi màu bằng override

## Chữ (text_fx / thumbnail)

- font `Montserrat-Variable.ttf` · cỡ 128 · IN HOA · vào bằng `pop` (6 frame) · số `#FFC400`

## Luật nhịp

- **fps:** ones
- **easing:** exponential ease-out khi vào; in-out cho whip/wipe; back tối đa một lần
- **bounce:** không
- **beat:** mỗi shot bắt đầu trên nhịp; hành động chính đáp đúng nhịp nguyên; thẻ thường dài một ô nhịp, thẻ phụ nửa ô
- **type:** trượt lên từ mặt nạ: tiêu đề trước, dòng hai sau ~0.08 s
- **cut_rule:** chuyển cảnh bám lưới: hàng trượt, cột rơi, lật ô

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** thanh bo tròn dày
- **circle:** đĩa sân khấu sau pictogram
- **label:** dòng 900 căn trái + meta mono góc

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip
- gói SFX (cue chung → âm): pop→click, hit→thud, whoosh→whoosh, tick→tick, ding→ding
- nhạc: nhạc nhận diện truyền hình: trống gọn, bass tròn, đều nhịp · 120 BPM
- persona giọng: phát thanh viên thể thao gọn, đều nhịp
- thumbnail: một pictogram trắng trên đĩa vàng + tiêu đề 900 hai dòng

## Cho Flow (khi style này dùng clip Flow)

- image_style: Pictogram broadcast identity — Faceless flat pictograms built from round-capped bars, discs and half-discs, huge heavy grotesque titles, tonal disc pattern in five shades of one hue, black ground
- video_motion: every action lands on the beat, rows of the pattern slide sideways, type rises from a mask

## Nguồn

- lemo-opuscar — https://github.com/lemomo-ai/lemo-opuscar @ `3a7132b996be` · license: MIT cho mã; tài liệu chỉ đọc để hiểu, tự viết lại + ghi công
- lấy từ: styles/pictogram-motion/STYLE.md (CC BY-NC 4.0)
- cách chuyển: đọc để hiểu ngữ pháp rồi tự viết lại bằng lời và mã của tool (không chép tài liệu/mã nguồn)
