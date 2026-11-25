# DIRECTOR SKILL — Cẩm nang nghề sống của Forward Studio

File này được nạp tự động vào mọi `brief` viết kịch bản (`vidlib/brief.py`) và mọi lượt chấm video đa phương thức (`python studio.py review <slug>`).
Mỗi lần bạn sửa một lỗi trên video thật, chạy `python studio.py learn "<bài học cụ thể>"` để ghi vĩnh viễn vào đây — **càng làm nhiều video, AI càng chuẩn gu của kênh**.

## 1. Năm nguyên tắc Motion Graphics cốt lõi
- **Easing có trọng lượng:** Cấm chuyển động tuyến tính cứng nhắc cho vật thể/thẻ vào khung; luôn dùng `bounce` (Kurzgesagt / Cartoon), `smooth` êm ái (School of Life / Psych2Go), hoặc `snap` dứt khoát (Infographics / Editorial).
- **Timing & Stagger theo từng từ:** Các phần tử trong một nhóm phải vào lệch nhau 3–5 frame (~0.10–0.15s), không ùa ra cùng lúc; mọi dấu nhấn/nhãn bắt đầu 0–3 frame TRƯỚC từ khoá trong lời đọc.
- **Một điểm nhìn (Poster Rule):** Mỗi khung hình chỉ có ĐÚNG 1 chủ thể chính nổi bật nhất ở Zone B (`y: 390–1240`); tối đa ≤ 5 từ chữ on-screen; nếu hình đã diễn đạt rõ thì xoá bớt chữ.
- **Design System nhất quán:** Khoá cứng bảng màu (≤ 3 màu nhấn trên nền tối), 1–2 font chữ, bo góc và lề rộng đồng bộ từ đầu đến cuối video.
- **Chuyển cảnh có lý do:** Ưu tiên nối bằng logic thị giác (`iris_match`, `whip_match`, `tape_stop`) thay vì cắt nhảy ngẫu nhiên.

## 2. Năm lỗi AI phải chặn tuyệt đối (Anti-AI-Slop)
- **Không lắc lư / nhấp nháy vô tội vạ:** Vật thể phải biết dừng nghỉ đúng lúc sau khi hoàn thành động tác, không rung lắc liên tục gây mỏi mắt.
- **Không zoom chậm rì cả cảnh:** Không drift-zoom đều đều trên một khung hình trống tĩnh từ đầu đến cuối.
- **Không chữ karaoke nhồi nhét:** Phụ đề Zone C (`y: 1340–1460`) đã gánh lời thoại — tuyệt đối không bê cả câu thoại lên giữa sân khấu hình.
- **Không dùng icon trừu tượng chung chung:** Cấm thay thế khái niệm cụ thể bằng ngôi sao/bóng đèn/nguyên tử/bảng màu vô nghĩa; phải dùng vật thể thật, nhân vật 2D (`rig:adult`, `rig:kid`, `rig:bird`...), `code_terminal`, `chat_prompt`, hoặc sơ đồ đúng cơ chế thực tế.
- **Luôn bảo vệ vùng an toàn di động 9:16:** Toàn bộ chữ và mặt nhân vật nằm gọn trong `x: 65..940`, `y: 270..1240` để không bị thanh UI TikTok/Shorts che khuất.

## 3. Gu thẩm mỹ 2D Animated Explainer của kênh
- **Khoa học / Vũ trụ / Sinh học (`kurzgesagt-black`):** Cảm hứng *Kurzgesagt – In a Nutshell* & *Life Noggin* — vector phẳng sắc nét, bầu trời sao/chiều sâu khí quyển dịu mắt, màu nhấn rực rỡ có kiểm soát, nhân vật/hành tinh/tế bào rõ hình khối.
- **Tâm lý / Triết lý / Hành vi (`school-of-life-black`):** Cảm hứng *The School of Life*, *Psych2Go* & *TED-Ed* — nền giấy than ấm dịu mắt, nhân vật 2D biểu cảm gần gũi (`rig:adult`, `rig:cat`...), chuyển động chậm rãi điềm tĩnh, nhiều khoảng thở.
- **Lịch sử / Sự thật / Giả định nhanh (`infographics-show-black`):** Cảm hứng *The Infographics Show* — đồ hoạ viền đậm tương phản cao, số liệu so sánh trực diện, nhịp gãy gọn rõ ràng.
- **Vẽ tay / Phác thảo khoa học (`sketchnote-black`):** Cảm hứng *MinuteEarth* & *Minutephysics* — nét bút vẽ ra từng nét kèm sơ đồ tối giản dễ hiểu ngay khi tắt tiếng.

## 4. Bài học thực chiến đã tích luỹ (tự cập nhật bằng `studio.py learn`)
- [2d] Một video chỉ giữ 1 trục logic duy nhất dễ hiểu ngay lần xem đầu; tránh nhồi quá 3 thuật ngữ chuyên ngành hoặc nhảy cảnh quá nhanh khiến người xem không kịp đọc.
- [2d · 2026-11-26] Trong shot scene 2D, đặt size nhân vật rig:* từ 400–450 và đạo cụ phụ 230–280 ở y: 0.55–0.62 để lấp đầy sân khấu như poster.
