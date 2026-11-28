# Vòng 22 — Báo cáo (28/11/2026)

Đầu vào: góp ý của chủ kênh cho 11 video (từ 26/11) + video caffeine, và yêu cầu rà chỗ YouTube có thể ban/giảm hiển thị.
Kế hoạch: `docs/ROUND22_PLAN.md`. Căn cứ chính sách + nguồn: `docs/YOUTUBE_RISK.md`.

## 1. Nguyên nhân gốc (đo trên contact sheet 1 fps của video cũ)

| Góp ý | Nguyên nhân trong tool | Đã sửa |
|---|---|---|
| Nhịp quá nhanh (caffeine, 0.1) | profile `short` ép shot 2.2–3.8 s, hook ≤ 2.2 s; tự chèn punch-in mỗi 1.8 s (caffeine: 24 cú); viral score khuyên thêm loại beat | profile `explainer` (shot 4–6.5 s), `vo.target_wps` 2.8, không punch-in tự chèn cho shot code, kiểu bay spine êm |
| Chữ chồng chéo, `NaN` lọt lên màn | nhãn không né nhau, nhãn tự do không kẹp mép, beat mẫu (compare) hiện `NaN` | nhãn né nhau + kẹp vùng an toàn; storyboard mới không dùng beat mẫu lỗi |
| Laptop/điện thoại/chip/phim/mỡ/carb… nhìn không ra | icon = 2–4 hình học | `icons_detail.js`: ~47 vật vẽ bằng path có tô bóng |
| Người chạy không giống thật, zoom vào chân đang chạy "kỳ" | rig hoạt hình đầu to, chân sin; camera lao vào bộ phận đang chuyển động | `rig_human.js` (tỉ lệ thật, gait theo góc khớp) + `freeze` + kính lúp `lenses` |
| Zoom vào não không ra não | não là vài hình elip | não có thuỳ/rãnh/tiểu não; kính lúp nối về đúng đầu nhân vật |
| Đoạn x-ray/glycogen lặp ở mọi video, khung giống nhau chỉ đổi chữ/màu | brief + viral score đẩy `xray_cutaway`/`meter`/`dossier`…; không có kiểm lặp giữa video | `policy.py` (khung lặp → cổng đỏ), brief cấm khuôn đã dùng, viral score đếm khung khác nhau |
| 3D: người như hình nộm, nền đen trơn, zoom vào cơ không có chi tiết | mannequin; set mặc định `black` | video đau cơ làm lại bằng 2D tả thực + phòng gym đêm + kính lúp sợi cơ; 3D có `set: gym` / `bedroom` |
| Pac-man không đớp | icon tĩnh | `macrophage`/`chomper` đớp liên tục |
| Đạp xe không thật | icon `bike` 3 vòng tròn | xe đạp đua có nan quay + người đạp bằng IK |

## 2. Rủi ro YouTube (tóm tắt — đầy đủ ở `docs/YOUTUBE_RISK.md`)

1. **Nội dung khuôn mẫu/lặp** (YPP "inauthentic content", làm rõ 16/07/2026) — rủi ro lớn nhất, trùng góp ý của chủ kênh.
2. **AI persona tư vấn sức khoẻ** — kênh mảng A/B là sức khoẻ: kể như thông tin có nguồn, không ra lệnh; mô tả có dòng
   "Educational content, not medical advice."
3. **Metadata hứa thứ video không có** — số trong tiêu đề/thumbnail phải có trong video.
4. **Made for Kids** — hoạt hình dễ bị gắn nhầm; upload luôn khai `selfDeclaredMadeForKids: false`.
5. Từ giật gân, spam/kéo tương tác, tên kênh khác, nhãn nội dung tổng hợp (hoạt hình không cần khai).

Video đã đăng (≤ 25/11) — không sửa video, chỉ ghi nhận để chỉnh metadata nếu muốn (`python studio.py policy --all`):
- Lặp khung cao: `your-body-runs-out-of-heat-first` (75%), `your-mouth-can-feed-your-brain`, `lifting-half-the-weight…`
  (50%), `your-heart-can-drift-without-speed` (40%).
- Số trong tiêu đề không nói trong video: `one-line-of-code-blew-up-a-370-million-rocket` ($370M), `why-ai-cant-count-the-rs-in-strawberry`.
- Từ giật gân: `why-a-penny-from-a-skyscraper-cant-kill-you` ("kill").

## 3. Làm lại video

Storyboard viết tay theo nguồn đã mở lại (mỗi video có `claims` + `sources`); 100% shot code, dùng người tả thực, bối
cảnh đêm, kính lúp, đạo cụ chi tiết. Kết quả QA + file: xem bảng ở `projects/WEEK_2026-11-28.md`.

## 4. Kiểm chứng
- `python -m unittest discover -s tests -t .` → 407 test OK (6 skip) · `python -m ruff check .` sạch.
- Ảnh kiểm: `qa/icons/cosmic-flat-black.jpg` (đạo cụ chi tiết), `qa/round22/rigtest/` (người tả thực), `qa/round22/lens.jpg`,
  `qa/round22/cycle.jpg`, `qa/round22/bd_cosmic-flat-black.jpg` (bối cảnh 2D), `qa/round22/set3d.jpg` (phòng đêm 3D).

## 5. Giới hạn còn lại
- Giọng vẫn là Edge Neural TTS (ElevenLabs hết quota) — trước khi bật kiếm tiền: nạp ElevenLabs, `--tts-force`.
- Người tả thực là 2D nhìn nghiêng (không quay chính diện); 3D vẫn dùng mannequin/creature — người 3D tả thực cần làm riêng.
- `policy` so khung theo bộ đạo cụ + bối cảnh, không so điểm ảnh; hai cảnh khác đạo cụ nhưng bố cục giống nhau vẫn lọt.

## 6. Bổ sung (28/11, tối) — duyệt khung hình cuối, nhãn né vật

Duyệt contact sheet 2 giây/khung của cả 13 video sau đợt render đầu: chữ còn đè lên vật ở ~10 cảnh ("6 KM" đè người
chạy, "FAT CELLS"/"SLOWER FUEL" đè tế bào mỡ, "~1,200 MG AT ONCE" đè hàng cốc, "SAME DRAWING, TWO FRAMES" đè dải phim,
"anandamide went up" đè hình nghiên cứu, tiêu đề kính lúp chạm viền kính/đè người). Nguyên nhân: nhãn chỉ né nhãn khác
và kính lúp, không né hình; lượt chống chồng mỗi frame tính hộp theo đường chân chữ nên có lúc đẩy nhãn tụt cả nửa khung.

Sửa trong engine (beat `scene`, xem CHANGELOG 4.2.1) + bố cục 4 video; test `test_labels_dodge_props_stable_and_fixed`.
Kiểm bằng `python studio.py sb preview <slug> <shot> --u …` trên từng cảnh lỗi trước khi render lại cả 13 video.
