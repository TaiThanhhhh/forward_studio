# Vòng 23 — Báo cáo (28/11/2026)

Yêu cầu: dọn dung lượng + quy trình thừa; đầu ra chỉ giữ thứ dùng để đăng; QA chặt (chủ kênh không đọc QA); người 2D chỉ
một góc nghiêng + lặp đổi màu; tập tạ/đạp xe chưa thật; thêm giọng + tông; kịch bản giữ chân; visual/motion như video
viral. Kế hoạch: `docs/ROUND23_PLAN.md`. Chi tiết thay đổi: CHANGELOG 4.3.0.

## 1. Dung lượng

| Mục | Trước | Sau |
|---|---|---|
| `projects/` (13 video) | 5,6 GB | ~0,35 GB (mỗi video: final.mp4 + bìa + phụ đề + post.md + storyboard + lời đọc) |
| `vendor/` repo tham khảo (gitignore, tải lại bằng `scripts/vendor_fetch.py`) | ~2,3 GB | 18 MB (chỉ thư viện engine dùng) |
| `.venv` (bản macOS Python 3.14 — không chạy trên Windows, không file nào dùng) | 148 MB | 0 |
| `qa/` ảnh kiểm sinh ra | 87 MB | 6,7 MB (giữ ảnh đã commit) |
| Tổng (không tính `.git`) | ~8,3 GB | ~0,5 GB |

Quy trình bỏ bước thừa khi `output.lean`: 3 bản MP4 giống nhau cho 3 nền tảng, version vNNN, 15 ảnh bìa các tỉ lệ,
báo cáo QA html/ảnh (giữ khi cổng đỏ để sửa), scripts.html của dự án toàn code.

## 2. QA tự chặn

Lỗi thấy được bằng mắt đều thành dòng ĐỎ (pipeline dừng, không xuất video):

- chữ còn đè hình > 30% (engine tự báo phần đè sau khi né — `window.labelReport`), video "như slide" (< 4,5% cặp khung
  chuyển động nhanh), OCR đọc được < 80%, số liệu thiếu nguồn, SEO < 70;
- mới (`vidlib/retention.py`, chặn cả ở linter TRƯỚC khi render): hook (≤ 16 từ, có khoảng trống tò mò, không mở đầu
  chậm), kịch bản giữ chân (không câu độn / xin like trong lời đọc, có câu nối lại giữa video, câu ≤ 24 từ, câu kết ngắn
  hoặc nối về đầu), diễn viên (≥ 2 góc nhìn khi ≥ 4 shot người; người chính không trùng video trước).

Lần render đầu với cổng mới: 9/13 video bị chặn (chữ đè hình ở 8 video, "như slide" ở 2 video). Sửa: nhãn né theo từng
mảnh hình (hình thưa như chuỗi glucose không còn là khối đặc), đúng góc nhìn chính diện và đúng camera bám bộ phận, lưới
chỗ thử rộng hơn (nhãn nhảy được lên trên đầu người); video 0.1 và "chạy chậm" camera đẩy sâu + lia xen kẽ, nền sáng hơn.

## 3. Người, giọng, kịch bản

- Người: góc chính diện / sau lưng; 9 người mới; tóc/râu/kính/trang phục; deadlift; đạp xe gối gập ra trước (trước đây
  gập ngược); squat bàn chân đứng yên, tay nắm đòn sau gáy; curl cầm tạ đơn. 13 video: người chính khác nhau, ≥ 2 góc.
- Giọng: 27 giọng Neural khác nhau, tông riêng; hook nhanh/sáng hơn, câu chốt chậm/trầm (đọc theo đoạn rồi nối).
- Kịch bản: 3 hook rút còn ≤ 16 từ, 4 video thêm câu nối lại, 1 câu dài tách đôi, 1 câu kết rút ngắn — dữ kiện giữ nguyên.

## 4. Giọng TTS và kiếm tiền

YouTube không cấm giọng TTS/AI trong video bật kiếm tiền; điều bị chặn là nội dung "inauthentic" (sản xuất hàng loạt,
lặp khuôn, ít giá trị riêng) và persona AI tư vấn y tế/tài chính. Rủi ro của kênh nằm ở **giấy phép dịch vụ TTS**: Edge
TTS (thư viện `edge-tts`) gọi tính năng đọc to của trình duyệt Edge, không có điều khoản thương mại công khai; Azure
Speech trả phí / ElevenLabs trả phí thì cho dùng thương mại. Trước khi bật kiếm tiền: lồng lại bằng ElevenLabs
(`--tts-force`) hoặc chuyển sang Azure Speech.

## 5. Kiểm chứng

- `python -m unittest discover -s tests -t .` → 419 test OK (7 skip) · `python -m ruff check .` sạch.
- 13/13 video qua cổng QA mới (0 đỏ; vàng còn lại: quyền giọng Edge TTS + mật độ thị giác), đã đóng gói gọn —
  lịch `projects/WEEK_2026-11-28.md`. Thứ tự sửa: lần 1 chặn 9 video (chữ đè hình 8, như slide 2) → engine né theo
  từng mảnh hình + bố cục 5 cảnh → lần 2 chặn 3 → video "chạy chậm" đổi sang `cartoon-story-black` (halftone quá tối:
  6,6/255), thu nhỏ lưới bit (0.1) và ảnh nhiễu (AI tạo video) → lần 3 đạt cả 13.
- Cổng chuyển động: thước đo cũ (lệch xám trung bình ≥ 9) phạt oan look tối — video 0.1 có 64% cặp khung đổi điểm ảnh
  rõ (ngang video sáng ~65%) mà chỉ đo được 3,5%. Thước đo mới theo độ sáng + tỉ lệ khung đứng yên + kiểm quá tối.
- 11 giọng khác nhau trên 13 video; giọng xoay theo thứ tự tạo dự án nên 04/12 và 05/12 trùng giọng Aria.

## 6. Giới hạn còn lại

- Góc ¾ chưa có (chỉ nghiêng / chính diện / sau lưng); đạp xe chỉ góc nghiêng.
- Đo "chữ đè hình" dùng hộp bao từng mảnh hình, chưa đo theo điểm ảnh thật.
- Video qua cổng ở lần render đầu (ngủ, caffeine, AI nói dối, ice bath) dựng trước bản sửa né-nhãn thứ hai — đã qua
  cổng, không dựng lại.
- Xoay giọng theo thứ tự tạo dự án, chưa theo lịch đăng.
