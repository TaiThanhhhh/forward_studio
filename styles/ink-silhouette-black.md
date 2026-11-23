# Ink Silhouette Black (`ink-silhouette-black`)

Rối bóng / bóng mực: mọi diễn viên là bóng đen đặc trước một đĩa trăng-hoàng hôn và dải chân trời có giới hạn, viền sáng mảnh ở mép, khớp nối đinh kiểu rối; chữ sáng viền đen đọc được trên cả vùng sáng và vùng tối. Phần lớn khung vẫn là đêm đen.

- **Engine:** `html` · toàn bộ bằng code (không cần Flow)
- **Hợp chủ đề (tags):** night, shadow, moon, wolf, owl, myth, legend, folklore, fairy-tale, ancient, ghost, sunset, silhouette, nocturnal, fable, migration
- **Nền đen tối thiểu:** 50% khung hình (QA đo)

## Nó KHÔNG phải là

- không phải nền sáng toàn khung — nguồn sáng là đĩa/dải giới hạn
- không phải style `ink` cũ (chỉ kiểu chữ cọ)
- không chi tiết bên trong vật (chỉ bóng + viền + đinh khớp)

## Bảng màu (nền đen + tối đa 2–3 màu)

- `bg` #000000
- `ink` #FFE7C2
- `a` #FF6B35
- `b` #8FB3FF
- `c` #FFC15E
- ánh trăng/hoàng hôn vàng cam trong đĩa sáng; mọi vật đen; viền sáng kem

## Chữ (text_fx / thumbnail)

- font `Caladea-Bold.ttf` · cỡ 112 · IN HOA · vào bằng `pop` (7 frame) · số `#FFC15E`

## Luật nhịp

- **fps:** ones (30fps), chuyển động trôi chậm
- **easing:** smooth
- **bounce:** không
- **cut_rule:** cắt khi bóng rời khỏi đĩa sáng
- **rule:** mọi vật là bóng đen; chỉ nguồn sáng có màu

## Dấu (mũi tên / vòng / nhãn)

- **arrow:** mũi tên bóng đen viền sáng
- **circle:** vòng bóng đen
- **label:** chữ kem viền đen

## Chuyển cảnh · âm thanh · giọng · thumbnail

- chuyển cảnh: cut, fade
- gói SFX (cue chung → âm): pop→ting, hit→thud, whoosh→whoosh_soft, tick→tick, ding→sparkle
- nhạc: dây + sáo trầm như truyện cổ, 76 BPM · 76 BPM
- persona giọng: người kể chuyện cổ tích bên đống lửa, chậm, ấm
- thumbnail: bóng đen một con vật/người trước đĩa trăng vàng cam giữa nền đen, 2–3 từ chữ kem

## Cho Flow (khi style này dùng clip Flow)

- image_style: Shadow-puppet ink silhouette — Solid black silhouettes with thin warm rim light, jointed like shadow puppets, in front of a limited moon or sunset disc on a pure black night
- video_motion: slow drifting puppets, the light disc rises slowly

## Nguồn

- studio — engine html (looks.js + post2d.js, vòng 10) — engines/html/looks.js · engines/html/post2d.js (mã trong repo) @ `—` · license: mã của kênh; font OFL/Apache ghi ở docs/round10/H1.md
- lấy từ: bài tham khảo '10 Claude animation styles' (chỉ tên phong cách); kỹ thuật in tram/Bayer/rối bóng viết mới
- cách chuyển: look html mới (bút + hậu kỳ WebGL một pass) trên sân khấu đen; không chép mã/tài sản bên ngoài
