# Vòng 23 — Kế hoạch (28/11/2026)

Yêu cầu chủ kênh (28/11 tối): dọn dung lượng + quy trình thừa; đầu ra chỉ giữ thứ dùng để đăng; QA chặt hơn (chủ kênh
không đọc QA → cổng phải tự chặn); người 2D chỉ một góc nghiêng + lặp đổi màu → chán; người tập tạ/đạp xe chưa thật;
thêm giọng + tông giọng; kịch bản giữ chân người xem tốt hơn (đúng chính sách nền tảng); visual + motion kiểu video viral.
13 video cũ (≤ 25/11) đã được chủ kênh chủ động xoá khỏi `projects/` để giảm dung lượng.

Quy trình đăng của chủ kênh: xem video → lấy caption theo từng nền tảng → bìa 16:9 → tag → đăng. Không mở QA.

## Việc

1. **Dọn**: `.venv` (bản macOS, không chạy được trên Windows), `__pycache__`, `.ruff_cache`, `qa/*/_work` + ảnh QA vòng
   cũ không theo dõi bằng git; mỗi dự án: khung render, stems, version cũ, gói nền tảng trùng lặp, ảnh QA.
2. **Đầu ra gọn** (`channel.json → output.lean`, `vidlib/lean.py`, stage `pack`): `out/final.mp4` · `out/cover-16x9.jpg` ·
   `out/captions.srt` · `out/post.md` (tiêu đề/mô tả/tag/hashtag/bình luận ghim/caption theo YouTube Shorts, TikTok,
   Instagram/Facebook Reels + nguồn + cài đặt đăng). Bỏ bước thừa khi lean: 3 bản MP4 giống nhau, 15 ảnh bìa, version,
   scripts.html cho dự án toàn code. Cổng QA đỏ → giữ nguyên mọi thứ để sửa.
3. **QA chặt** (tự chặn, không cần người đọc): chữ đè vật/tràn khung (engine báo), chuyển động "như slide", OCR, cùng
   một dáng người lặp nhiều shot / giữa video, hook 2 giây đầu, câu kịch bản yếu → đỏ.
4. **Giọng + tông**: mỗi giọng trong kho → một giọng Neural riêng (không dồn 5 giọng), tông (tốc độ/cao độ) theo persona,
   nhịp theo vai câu (hook nhanh hơn, câu chốt chậm lại).
5. **Người 2D**: góc nhìn chính diện / ¾ / sau lưng (không chỉ nghiêng), nhiều kiểu tóc/dáng/trang phục/tuổi (không chỉ đổi
   màu), chống lặp diễn viên giữa các video; tập tạ (squat/deadlift/bench/curl đúng cơ sinh học) + đạp xe (tư thế ngồi,
   góc hông/gối/cổ chân) giống thật.
6. **Kịch bản**: brief + linter giữ chân (hook có khoảng trống tò mò trong 1–2 câu đầu, mở vòng/đóng vòng, câu nối lại
   mỗi ~6–8 giây, kết nối về đầu để xem lại, cấm câu mở đầu chậm/xin like) — trung thực, không câu kéo gây hiểu lầm.
7. **Visual + motion**: cỡ cảnh đa dạng (toàn/trung/cận/đặc tả), camera luôn chuyển động có chủ đích, chữ động (kinetic)
   cho số chính, nhịp nhấn theo SFX.
8. **Làm lại các video chưa đăng** (29/11 → 10/12) bằng các nâng cấp trên, đóng gói gọn, cập nhật lịch.
