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

## 3. Gu thẩm mỹ 2D Animated Explainer của kênh (tên style = thể loại, KHÔNG mang tên kênh khác)
- **Khoa học / Vũ trụ / Cơ thể (`cosmic-flat-black`):** vector phẳng sắc nét, bầu trời sao/chiều sâu khí quyển dịu mắt, màu nhấn rực có kiểm soát; nhân vật/hành tinh/tế bào rõ hình khối; zoom xuyên bộ phận (mắt → võng mạc → tế bào) để đi từ vĩ mô vào vi mô.
- **Tâm lý / Triết lý / Hành vi (`essay-ink-black`):** nền than ấm, nhân vật 2D biểu cảm gần gũi, bong bóng suy nghĩ (`labels[].bubble: "thought"`) cho giọng nội tâm, nhịp chậm nhiều khoảng thở.
- **Lịch sử / Sự thật / Giả định nhanh (`bold-infographic-black`):** viền đậm tương phản cao, số liệu so sánh trực diện, nhịp gãy gọn.
- **Vẽ tay / Phác thảo khoa học (`sketchnote-black`):** nét bút vẽ dần + sơ đồ tối giản hiểu được khi tắt tiếng.
- **Tham chiếu kênh lớn chỉ để học nghề** — tuyệt đối không ghi tên kênh/studio khác vào lời đọc, chữ trên màn, tiêu đề, mô tả, tag, hashtag hay prompt hình (linter chặn; rủi ro chính sách spam/metadata gây hiểu lầm).

## 3b. Zoom xuyên bộ phận & bộ phận sống (vòng 21)
- Mỗi video tối đa 1–2 cú `zoom_through`, đặt đúng khoảnh khắc "đi vào bên trong" (mắt → não, màn hình → mạch điện, cửa sổ → căn phòng). Shot trước kết thúc bằng camera `{"at": "hero.eye", "zoom": 12}` (2D) hoặc `frame.dive` (3D); shot sau `transition_in: "zoom_through"`, `through: "hero.eye"`.
- Cho thấy cơ chế BÊN TRONG nhân vật thay vì icon: `xray` 0→1 + `organs`, `focus` đúng bộ phận lời đọc đang nói, `hold` đồ vật thật trên tay, `talk` + bong bóng cho thoại, `look_at` để nhân vật phản ứng với nhau.
- Nhãn đặt trên bộ phận sẽ bị zoom tới phải có `out` trước cú lao (engine tự làm mờ khi zoom sâu, nhưng nhãn sát điểm đích vẫn nên rút sớm).

## 3c. Dữ kiện có nguồn & SEO
- Mọi con số/khẳng định → `claims` + `sources` (nguồn gốc: cơ quan, tạp chí, viện, bộ dữ liệu; mở trang để đối chiếu). Không chắc thì làm tròn + rào đón (`estimate`) hoặc bỏ. Hình đúng tỉ lệ thật (người ≈ 1.7 m, cửa ≈ 2 m).
- Từ khoá chính nằm trong 40 ký tự đầu tiêu đề, câu đầu mô tả và được NÓI ở 1–2 shot đầu; 2–4 hashtag; mô tả kết bằng dòng "Sources: …".

## 4. Bài học thực chiến đã tích luỹ (tự cập nhật bằng `studio.py learn`)
- [2d] Một video chỉ giữ 1 trục logic duy nhất dễ hiểu ngay lần xem đầu; tránh nhồi quá 3 thuật ngữ chuyên ngành hoặc nhảy cảnh quá nhanh khiến người xem không kịp đọc.
- [2d · 2026-11-26] Trong shot scene 2D, đặt size nhân vật rig:* từ 400–450 và đạo cụ phụ 230–280 ở y: 0.55–0.62 để lấp đầy sân khấu như poster.
