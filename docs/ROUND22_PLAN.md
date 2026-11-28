# Vòng 22 — Kế hoạch (27/11/2026)

Nguồn: góp ý của chủ kênh cho 11 video (từ 26/11 trở đi + caffeine theo yêu cầu riêng) và yêu cầu rà rủi ro YouTube
(ban / giảm hiển thị). Video ≤ 25/11 đã đăng: KHÔNG động vào.

## Chẩn đoán chung (từ contact sheet 1 fps)
- Chữ: tiêu đề tràn khỏi băng (`Same race. Different finish`), nhãn chồng nhau (`RECEPTOR/CAFFEINE/ADENOSINE`), `NaN`
  lọt lên màn, chữ đè phụ đề.
- Vật thể: laptop/điện thoại/chip/bàn phím = 2–3 hình chữ nhật → không nhận ra; tế bào, mỡ, carb, đĩa đệm cũng vậy.
- Lặp khung: đồng hồ nền ở mọi cảnh, số chương "01/04/05" khổng lồ, `xray_cutaway`, `meter`, `dossier`, `compare` đổi
  chữ đổi màu giữa các video.
- Nhịp: caffeine 14 shot × 2 s; float 0.1 giải thích dồn dập.
- Nhân vật: rig người kiểu hoạt hình đầu to, dáng chạy sin → không giống người chạy thật; zoom vào bộ phận đang chạy bị kỳ.
- 3D: nền đen trơn, người tập không giống người tập gym, zoom vào cơ không có chi tiết bên trong.

## Gói việc
- [x] A. Rủi ro YouTube: `vidlib/policy.py` (lặp mẫu giữa các video, AI persona sức khoẻ, metadata/thumbnail không có
      trong video, từ ngữ giật gân, Made for Kids, nhãn nội dung tổng hợp) + cổng QA + payload upload
      (`selfDeclaredMadeForKids: false`) + báo cáo `docs/YOUTUBE_RISK.md`.
- [x] B. Chữ: co chữ vừa băng tiêu đề, gỡ chồng nhãn (bộ giải va chạm), chặn `NaN/undefined`, cổng đỏ chồng chữ.
- [x] C. Thư viện vật thể chi tiết (path SVG → poly, có tô bóng): laptop, phone, chip, keyboard, film strip, brain,
      neuron, RBC, bạch cầu (có miệng đớp), mỡ, glycogen/carb, đĩa đệm/đốt sống, cơ, sợi cơ, ty thể, giường, cà phê…
- [x] D. Rig người tả thực `human` (tỉ lệ 7.5 đầu, dáng chạy theo đường cong khớp sinh cơ học, quần áo/giày) + cơ quan
      chi tiết (não có thuỳ, cột sống, gan, cơ chân, mạch máu).
- [x] E. Kính lúp/inset (`lens`) trong beat `scene` + `freeze` (đứng hình nhân vật khi camera lao vào).
- [x] F. Chống lặp giữa các video (sổ mẫu khung) + nhịp: shot tối thiểu, wps thấp hơn cho explainer.
- [x] G. 3D: bối cảnh đêm (phòng gym ban đêm, phòng ngủ, đường chạy đêm) thay nền đen trơn.
- [x] H. Làm lại video: caffeine, twos, shorter, wall, sore-muscles, runner's high, float, RBC, how-ai (làm xong),
      ai-lies, muscles-sleep (5.5 h) + kiểm ice-baths, running-slow.
