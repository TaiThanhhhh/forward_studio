# Spy Titles Black (`spy-titles-black`)

Phim mở đầu điệp viên thập niên 60 bản tối: mảng giấy cắt tay mép gồ ghề, bóng giấy lệch, dải chéo trượt, chữ nghiêng tinh nghịch làm kiến trúc; hình rối on twos, kèn đồng cắt hình.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** mystery, secret, heist, cold-war, poison, crime, myth, spy, code, agent, escape
- **Nền đen tối thiểu:** 55% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải flat vector (mép là giấy cắt, có bóng giấy thật)
- không phải halftone (không chấm in)
- không phải Swiss (đường chéo, chữ nghiêng, tinh nghịch)
- không nhại điệp viên bằng súng/đồ chơi — chỉ hình khối và nhịp
- không phải paper_cutout (style chữ cho clip Flow)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #F1E6D0
- `a` #E8432A
- `b` #E8B32A
- 4 mực đặc: đen + kem + đỏ cam + mù tạt; không gradient

## Chữ (text_fx / thumbnail)

- font `Anton-Regular.ttf` · cỡ 132 · IN HOA · vào bằng `drop_letters` (10 frame) · số `#E8B32A`

## Luật nhịp

- **fps:** rối on twos (15 hình/giây); camera và băng chữ on ones
- **easing:** trượt theo đường lưới rồi DỪNG CHẾT đúng nhịp (ease-out ngắn)
- **bounce:** không
- **stop_time:** ở cú kèn: cả khung đứng 2 nhịp trong im lặng rồi chạy tiếp (đặt hold: true)
- **cut_rule:** kèn đồng là điểm cắt; cảnh vỡ thành dải song song trượt chéo

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên giấy cắt
- **circle:** khoanh bằng vành giấy cắt hở
- **label:** chữ trên băng giấy mù tạt, nghiêng 3°

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, whip, flash
- gói SFX (cue chung → âm): pop→snap, hit→sting, whoosh→scrape, tick→click, ding→sting_low
- nhạc: jazz điệp viên: kèn đồng giật, bongo, contrabass · 132 BPM
- persona giọng: người dẫn truyện bí ẩn, nửa đùa
- thumbnail: bóng một vật cắt giấy + dải chéo đỏ + chữ nghiêng 2 từ

## Cho Flow (khi style này dùng clip Flow)

- image_style: 1960s cut-paper title sequence — Flat opaque hand-cut paper shapes with slightly uneven edges and small offset paper shadows, diagonal bars, cream, red-orange and mustard on black, no gradients
- video_motion: puppet motion on twos, shapes slide along diagonals and stop dead on the beat

## Nguồn

- lemo-opuscar — https://github.com/lemomo-ai/lemo-opuscar @ `3a7132b996be` · license: MIT cho mã; tài liệu chỉ đọc để hiểu, tự viết lại + ghi công
- lấy từ: styles/spy-titles/STYLE.md (CC BY-NC 4.0)
- cách chuyển: đọc để hiểu ngữ pháp rồi tự viết lại bằng lời và mã của tool (không chép tài liệu/mã nguồn)
