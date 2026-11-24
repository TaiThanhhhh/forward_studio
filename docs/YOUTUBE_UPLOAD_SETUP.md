# Hướng dẫn cài đặt 2 phút: Gemini Video QA & YouTube Auto-Upload Draft

Tài liệu này giúp bạn kích hoạt 2 tính năng tự động hoá mới trong Forward Studio:
1. **Gemini Multimodal Video QA (`python studio.py review <slug>`)** & tạo kịch bản `--ai gemini` — tận dụng gói **Google AI Pro** ($10/tháng credit Gemini API).
2. **YouTube Auto-Draft Uploader (`python studio.py upload-yt <slug>`)** — tự đẩy `<slug>.mp4` + SEO Title/Description/Hashtags/Tags + `captions.srt` lên YouTube ở chế độ **Private** để bạn duyệt 5 giây rồi bấm Public/Lên lịch.

---

## Phần 1 — Kích hoạt Gemini API (`GEMINI_API_KEY`)

### Bước 1: Lấy API Key (và nhận $10/tháng credit từ Google AI Pro)
1. Đăng nhập tài khoản Google AI Pro tại **[Google AI Studio](https://aistudio.google.com/apikey)**.
2. Nếu bạn có gói **Google AI Pro** (Google Developer Program Premium), liên kết Cloud Billing để nhận **$10/tháng credit** (hoặc dùng ngay **Free Tier** của Gemini để test miễn phí).
3. Bấm **Create API Key** → sao chép khoá bắt đầu bằng `AIza...`.

### Bước 2: Lưu key vào file `.env` ở gốc dự án
Mở (hoặc tạo mới) file `.env` ngay tại thư mục gốc repo (file này đã nằm trong `.gitignore`, không bao giờ bị đẩy lên Git):

```env
GEMINI_API_KEY=AIzaSy...khoa_cua_ban...
```

### Bước 3: Cài SDK mới nhất & chạy thử
```powershell
pip install -U google-genai>=3.5.0
python studio.py review why-ai-cant-count-the-rs-in-strawberry
```

- Báo cáo chấm điểm AI sẽ được lưu vào `projects/<slug>/qa/ai_review.md` và `qa/ai_review.json`.
- Bạn cũng có thể nhờ Gemini viết storyboard tự động:
  ```powershell
  python studio.py video "Why airplanes don't fly in straight lines" --ai gemini
  ```

---

## Phần 2 — Kích hoạt YouTube Auto-Upload Draft (`upload-yt`)

### Bước 1: Cài 2 gói Python cho YouTube Data API v3
```powershell
pip install google-api-python-client google-auth-oauthlib
```

### Bước 2: Tạo OAuth Desktop Client trên Google Cloud (chỉ làm 1 lần duy nhất)
1. Vào **[Google Cloud Console](https://console.cloud.google.com/)** → tạo một Project mới (ví dụ: `Forward Studio Uploader`).
2. Vào **APIs & Services → Library** → tìm **YouTube Data API v3** → bấm **Enable**.
3. Vào **APIs & Services → OAuth consent screen**:
   - Chọn **External** → đặt tên app (vd `Forward Studio`) → điền email của bạn.
   - Ở mục **Test users** (Audience), bấm **Add users** và thêm **chính email Gmail quản lý kênh YouTube của bạn** (rất quan trọng nếu app đang ở trạng thái Testing).
4. Vào **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: chọn **Desktop app**.
   - Bấm **Create** → bấm **Download JSON**.
5. Đổi tên file tải về thành `yt_client_secret.json` và đặt vào:
   ```text
   config/yt_client_secret.json
   ```
   *(Cả `config/yt_client_secret.json` và `config/yt_token.json` đều đã được thêm vào `.gitignore` để bảo mật tuyệt đối.)*

### Bước 3: Xem trước (Dry-Run) & Upload Draft
Luôn test bằng `--dry-run` trước để kiểm tra Title, Description, Tags và đường dẫn file (không cần mạng / không cần đăng nhập):

```powershell
python studio.py upload-yt why-ai-cant-count-the-rs-in-strawberry --dry-run
```

Khi mọi thứ đã chuẩn, chạy lệnh tải lên chế độ **Private** (mặc định):

```powershell
python studio.py upload-yt why-ai-cant-count-the-rs-in-strawberry
```

- **Lần chạy đầu tiên**: trình duyệt sẽ mở trang đăng nhập Google → chọn đúng kênh YouTube → bấm **Allow**. Token sẽ được lưu cục bộ vào `config/yt_token.json` để các lần sau chạy tự động không cần đăng nhập lại.
- **Các cờ hữu ích**:
  - `--title-idx 2` — chọn phương án tiêu đề số 2 hoặc số 3 trong `caption.txt`.
  - `--no-srt` — bỏ qua bước tải phụ đề `captions.srt`.
  - `--comment` — tự đăng luôn câu Seed/Pinned Comment (bạn chỉ cần bấm Pin trên Studio).
  - `--privacy unlisted` hoặc `--privacy public` — đổi chế độ hiển thị (lưu ý: nếu dự án Google Cloud chưa qua *YouTube API Compliance Audit*, YouTube sẽ tự khóa mọi video upload qua API về `private`, nên giữ mặc định `private` rồi vào link `https://studio.youtube.com/video/<id>/edit` gạt **Public / Lên lịch** trong 5 giây là an toàn và nhanh nhất).
