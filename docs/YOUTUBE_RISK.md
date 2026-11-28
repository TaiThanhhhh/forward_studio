# Rủi ro bị hạn chế / tắt kiếm tiền trên YouTube — kênh forward. (rà 27/11/2026)

Kênh: Shorts tiếng Anh, hoạt hình code 2D/3D, giọng TTS, công cụ dựng theo khuôn. Tool kiểm tự động:
`python studio.py policy [slug|--all]` → `projects/<slug>/qa/policy.md`; cổng QA có 2 dòng mới (dòng "khung lặp giữa các
video" chặn đỏ khi ≥ 40% shot lặp khung của 10 video gần nhất).

| # | Rủi ro | Chính sách YouTube | Mức với kênh | Tool làm gì |
|---|---|---|---|---|
| 1 | **Khung lặp giữa các video** (cùng bố cục, đổi chữ đổi màu) | YPP "inauthentic content": *generic or repetitive* — "looks like it's made with a template", "minimal variation across numerous videos"; làm rõ 16/07/2026. Template được phép nếu phần lớn nội dung khác nhau. | **Cao** — đúng lỗi chủ kênh thấy (xray_cutaway, meter, dossier, compare lặp) | `policy.repetition` so khoá khung (beat + bố cục + bộ đạo cụ) với 10 video trước; ≥ 25% vàng, ≥ 40% đỏ. Brief + storyboard tay phải đổi cách giải thích. |
| 2 | **Giọng AI như chuyên gia sức khoẻ** | *AI personas* nói về sức khoẻ/tài chính/pháp lý như chuyên gia → không kiếm tiền. | Trung bình (mảng A/B là thể hình/sức khoẻ) | Bắt câu mệnh lệnh/liều lượng ("you should", "take 400 mg"), câu tự xưng ("as a doctor"); tự thêm dòng *"Educational content, not medical advice."* vào mô tả video sức khoẻ. |
| 3 | **Metadata hứa thứ video không có** | Spam & deceptive practices: tiêu đề/thumbnail/mô tả khiến người xem tin sẽ thấy điều video không có; siết từ 01/2025. | Trung bình | Số trong tiêu đề/thumbnail phải có trong lời đọc hoặc sổ dữ kiện (đọc cả số bằng chữ: "forty percent" = 40). |
| 4 | **Từ giật gân** (kill, deadly, crush, destroy…) | Không cấm, nhưng quảng cáo hạn chế + nhóm *unsatisfying or off-putting*. | Thấp–trung bình | Cảnh báo ở tiêu đề đầu, hook, chữ thumbnail. |
| 5 | **Bị xếp "Made for Kids"** | Hoạt hình + nhân vật dễ bị hệ thống gắn nhãn → tắt bình luận, mất đề xuất (FTC: hoạt hình không tự động là cho trẻ em). | Trung bình (rig hoạt hình) | Upload gửi `selfDeclaredMadeForKids: false`; cảnh báo chữ nhắm trẻ em; rig người tả thực mới giảm vẻ "phim thiếu nhi". |
| 6 | **Nhãn nội dung tổng hợp** | Chỉ bắt buộc với nội dung trông như thật; hoạt hình rõ ràng không cần khai. Khai không làm giảm hiển thị/kiếm tiền. | Thấp | Video toàn code → `containsSyntheticMedia: false`; có clip Flow trông thật → chủ kênh quyết (đã có từ vòng 21). |
| 7 | **Spam/kéo tương tác** | "sub4sub", "comment YES if…", bình luận lặp; hashtag quá nhiều. | Thấp | Bắt câu kéo tương tác, > 15 hashtag, mô tả/bình luận ghim chép từ video khác. |
| 8 | **Tên kênh khác trong metadata** | Spam/metadata gây hiểu lầm. | Đã xử lý ở vòng 21 | `seo.brand_blocklist` (đỏ). |
| 9 | **Repost / clip người khác** | Shorts ưu tiên nội dung gốc (cập nhật 01/10/2026); reused content không kiếm tiền. | Thấp (mọi hình do tool vẽ) | Sổ quyền; bản TikTok không đóng watermark YouTube. |
| 10 | **Giọng đọc** | Không có quy định riêng cho TTS; giọng đọc nội dung tự viết là được. | Thấp (về YouTube) | Rủi ro thật là giấy phép thương mại Edge TTS → lồng lại ElevenLabs trước khi bật kiếm tiền. |

## Nguồn
- YouTube Help — Channel monetization policies (inauthentic content, reused content): https://support.google.com/youtube/answer/1311392
- TechCrunch (20/07/2026) — YouTube clarifies policies around AI slop and upsetting videos: https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/
- Tubefilter (13/07/2026) — generic or repetitive content: https://www.tubefilter.com/2026/07/13/youtube-inauthentic-content-monetization-policy-update/
- YouTube Help — Disclosing altered or synthetic content: https://support.google.com/youtube/answer/14328491
- YouTube Help — Spam, deceptive practices & scams: https://support.google.com/youtube/answer/2801973
- YouTube Help — Medical misinformation policy: https://support.google.com/youtube/answer/13813322
- FTC — YouTube channel owners: is your content directed to children?: https://www.ftc.gov/business-guidance/blog/2019/11/youtube-channel-owners-your-content-directed-children
- Search Engine Journal — Shorts ưu tiên nội dung gốc: https://searchenginejournal.com/youtube-original-shorts-reposted-clips-reach/591774/

Không có nguồn chính thức nào nói "shadowban" như một cơ chế riêng; giảm hiển thị thực tế đến từ (1) tắt kiếm tiền/
không đề xuất nội dung khuôn mẫu, (2) nhãn Made for Kids, (3) vi phạm metadata/spam, (4) giữ chân người xem thấp.
