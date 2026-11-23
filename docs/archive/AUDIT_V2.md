# AUDIT V2 — 13 mảng (15/11/2026, branch `upgrade/atlas-and-audit`)

Audit chạy song song bằng 7 subagent (mỗi agent 1–2 mảng), chỉ đọc repo; mảng 3/4/5/6/12 tra chuẩn hiện hành bằng web search (nguồn + ngày trong từng báo cáo). Báo cáo đầy đủ: `docs/audit/area-*.md`.

**142 phát hiện:** 1 Critical · 26 High · 61 Medium · 54 Low. Đã sửa 47, sửa một phần 6, chờ anh quyết định 6.

## Điểm 0–10 (trước → sau vòng 9 → mục tiêu)

| # | Mảng | Trước | Sau | Mục tiêu |
|---|---|---|---|---|
| 1 | Kiến trúc và code | 6.5 | **7.5** | 8.5 |
| 2 | Độ tin cậy | 6 | **8** | 8.5 |
| 3 | Chuẩn hình | 5 | **8.5** | 9 |
| 4 | Chuẩn âm thanh | 7 | **8** | 9.5 |
| 5 | Preset xuất file | 3 | **8** | 8 |
| 6 | Bản quyền và tuân thủ | 5 | **7.5** | 9 |
| 7 | Bảo mật | 6 | **8** | 9 |
| 8 | Hiệu năng và chi phí | 5 | **7** | 8 |
| 9 | QA | 4 | **8** | 8 |
| 10 | UI/UX (kỹ thuật) | 5 | **7.5** | 8 |
| 11 | Asset và version | 3 | **8** | 8 |
| 12 | Xuất bản | 4 | **7.5** | 8.5 |
| 13 | Tài liệu và môi trường | 5.5 | **8** | 8.5 |

Điểm "sau" là tự chấm theo cùng thang của báo cáo gốc, dựa trên các mục đã sửa + đo lại trên file thật (ffprobe/loudness của `_smoke-html` sau sửa: BT.709 đủ tag, tv, High L4.2, GOP 15, 2 B-frame, faststart, −13.97 LUFS / −2.31 dBTP, cổng QA 23/23 xanh).

## Critical + High

| Mã | Mức | Vấn đề | Trạng thái |
|---|---|---|---|
| AUD-101 | High | Dấu vân tay engine board chỉ hash engines/board/*.py, bỏ sót lib/motion/__init__.py mà board import → sửa thư  | ĐÃ SỬA — code_rev() hash lib/motion + board |
| AUD-201 | High | Dấu vân tay render không gồm mã pipeline Python: chỉ có codeshot.engine_rev() (JS three/html + py manim) và _b | ĐÃ SỬA — dấu vân tay gồm mã vidlib + font + ffmpeg |
| AUD-203 | High | Ghi thẳng vào file đích, không kiểm mã thoát của ffmpeg. Bị ngắt giữa chừng thì còn lại file hỏng, và fresh()  | ĐÃ SỬA — ghi tạm → kiểm mã thoát → đổi tên; fresh() dùng valid_media |
| AUD-204 | High | Không có timeout ở ffmpeg, worker Edge, Manim hay tiến trình board. Cảnh JS lặp vô hạn, driver GPU treo, hoặc  | ĐÃ SỬA — timeout ffmpeg/ffprobe, canh treo render 240 s, board, Manim |
| AUD-301 | High | Không gắn tag màu và chuyển RGB→YUV bằng ma trận BT.601 | ĐÃ SỬA — RGB→YUV BT.709, tag đủ VUI + container |
| AUD-302 | High | Board engine xuất 40–81 Mbps, vượt giới hạn level 4.0 và vượt xa mức cần | ĐÃ SỬA — CRF + maxrate 16M/bufsize 32M |
| AUD-303 | High | Nguồn Flow 360×640 @ 24 fps bị phóng 3× và chuyển 24→30 fps bằng lặp frame | MỘT PHẦN — cổng QA báo VÀNG khi nguồn Flow < 720p; cần anh tải bản 1080p từ Flow |
| AUD-401 | High | True peak sát trần −1 dBTP, cổng QA còn nới lên −0.7 dBTP | ĐÃ SỬA — trần −1.5 dBTP, QA chặn > −1.0 |
| AUD-402 | High | Limiter làm việc của compressor: nén tới 4.5 dB, release 60 ms, gain tính trước limiter nên lệch target | ĐÃ SỬA — master 2 lượt bù phần limiter làm hụt |
| AUD-501 | High | Không có preset theo nền tảng — chỉ một đầu ra 9:16 / 30 fps / CRF 17 cho mọi nơi | ĐÃ SỬA — config/delivery.json + vidlib/deliver.py (Shorts/Reels/TikTok/16:9) |
| AUD-502 | High | Safe zone gộp một bộ, xung đột với hướng dẫn Meta cho Reels (đáy 35%, đỉnh 14%, cạnh 6%) | MỘT PHẦN — đỉnh/cạnh theo union; đáy Reels chờ quyết định (D-009) |
| AUD-601 | High | Không có sổ quyền (ledger) và không ghi nguồn gốc theo từng video | ĐÃ SỬA — rights/ledger.json + kiểm quyền từng video vào cổng QA |
| AUD-602 | High | Chưa xác định gói ElevenLabs → quyền thương mại của giọng đọc chưa được đảm bảo — CẦN CHỦ KÊNH QUYẾT ĐỊNH | CHỜ ANH QUYẾT ĐỊNH |
| AUD-604 | High | File xuất không mang metadata nguồn gốc / C2PA; ingest xoá mọi Content Credentials của clip nguồn | MỘT PHẦN — metadata MP4 + out/provenance.json; ký C2PA cần chứng chỉ (quyết định) |
| AUD-701 | High | Một request làm chết worker hàng đợi job (DoS tới khi khởi động lại) | ĐÃ SỬA — worker job không chết, chặn ký tự điều khiển |
| AUD-801 | High | Không theo dõi chi phí của mỗi video | ĐÃ SỬA — work/cost.json + config/costs.json |
| AUD-803 | High | Dấu vân tay render không gồm mã vidlib/, font hay phiên bản công cụ | ĐÃ SỬA — = AUD-201 |
| AUD-901 | Critical | QA đỏ không chặn: exit code vẫn 0, video và publish.md đã xuất trước khi QA chạy | ĐÃ SỬA — cổng QA đỏ chặn publish/deliver, exit 12 qa_failed |
| AUD-902 | High | Stage render được đánh dấu "xong" trước QA, nên lần chạy sau không chạy QA lại | ĐÃ SỬA — state qa riêng; chưa qua cổng thì lần sau chạy lại |
| AUD-903 | High | Không có visual regression (golden frame, SSIM, pHash) | ĐÃ SỬA — 6 golden + SSIM/pHash (vidlib/visreg.py) |
| AUD-904 | High | Module lõi không có unit test, không có CI | MỘT PHẦN — thêm test vòng 9 + CI; pipeline.py/textfx.py vẫn chủ yếu test gián tiếp |
| AUD-1001 | High | Lỗi của mọi nút hành động bị nuốt im lặng | ĐÃ SỬA — UI mới (Phần D): lỗi API/job thành toast + callout có nút sửa, kiểm bằng e2e |
| AUD-1101 | High | Ghi đè out/final.mp4, không có v001/v002. Thumbnail (T1_9x16.png…), publish.md, qa/report.* cũng bị ghi đè. Re | ĐÃ SỬA — out/versions/vNNN/ (hard link) |
| AUD-1102 | High | commit\ | ĐÃ SỬA — out/manifest.json: git SHA + dirty, phiên bản, style/giọng/model, seed, hash đầu ra, QA, chi phí |
| AUD-1201 | High | publish.md không nhắc bật nhãn AI theo nền tảng | ĐÃ SỬA — publish.md: nhãn AI theo nền tảng |
| AUD-1202 | High | Không có checklist trước khi đăng | ĐÃ SỬA — publish.md: checklist trước khi đăng |
| AUD-1301 | High | Không có CI: ruff + 189 test chỉ chạy tay; không có gì chặn merge khi test đỏ | ĐÃ SỬA — .github/workflows/ci.yml + .pre-commit-config.yaml (chưa push) |

## Medium / Low đã sửa

- **AUD-102** (Medium) Trường version được setdefault(2) nhưng không chỗ nào đọc; không có migration theo version, chỉ có suy đoán rả → storyboard SCHEMA_VERSION 3 + migrate()
- **AUD-107** (Medium) Tham số x264 (preset/CRF/pix_fmt) viết tay ở 7 nơi, CRF 14/17/18/20/config; chỉ board và adapter đọc CRF từ co → vidlib/encode.py dùng chung
- **AUD-112** (Medium) Lệnh con gõ sai (vd python studio.py doctor, stauts) rơi vào run_video(argv) → tạo dự án mới tên đó → lệnh gõ sai → exit 2, không tạo dự án
- **AUD-202** (Medium) fp render được chụp trước s_voice, mà s_voice ghi audio/vo.mp3 + vo_alignment.json (hoặc vo.wav giả khi dry-ru → VO sinh ra không vào dấu vân tay
- **AUD-205** (Medium) Không tự thử lại: ElevenLabs gọi một lần, gặp 429/5xx/URLError là StudioError. Worker Edge crash thì chỉ báo " → ElevenLabs thử lại 429/5xx
- **AUD-206** (Medium) Phản hồi LLM (tới 64k token, tốn tiền) không được lưu trước khi parse. json.loads lỗi thì ném JSONDecodeError  → lưu brief_response.txt trước khi parse
- **AUD-208** (Medium) Ghi VO không nguyên tử: đổi tên mp3 cũ → ghi thẳng vo.mp3 → save_json alignment sau cùng. Ngắt giữa chừng thì  → VO ghi nguyên tử
- **AUD-304** (Medium) Level/profile/khung không được khoá tường minh → High@L4.2 khoá tường minh
- **AUD-305** (Medium) GOP 250 frame và 3 B-frame — khác khuyến nghị YouTube (GOP đóng = ½ fps, 2 B-frame) → GOP đóng 15 (½ fps), 2 B-frame
- **AUD-306** (Medium) MP4 có edit list ở cả hai track — YouTube khuyên "No Edit Lists" → -use_editlist 0
- **AUD-307** (Medium) endscreen_16x9.mp4 không faststart, không kiểm mã thoát, để lại file hỏng 48 byte → endscreen ghi nguyên tử + faststart + kiểm mã thoát
- **AUD-504** (Medium) Endscreen 16:9 là clip rời 15 s im lặng, không có video 16:9 nào để gắn → bản 16:9 pillarbox + endscreen nối cuối
- **AUD-505** (Medium) Ảnh bìa: kích thước theo spec cũ, thiếu bìa riêng TikTok, không kiểm cỡ file → bìa riêng từng preset, ép dưới trần dung lượng
- **AUD-702** (Medium) target của job video nhận đường dẫn → pipeline ghi file ra ngoài projects/ → target chỉ nhận ý tưởng hoặc slug trong projects/
- **AUD-703** (Medium) Không có header chống iframe / nosniff / CSP → clickjacking → X-Frame-Options, nosniff, CSP, Referrer-Policy
- **AUD-705** (Medium) Tải clip: xoá clip cũ TRƯỚC khi nhận clip mới; không khoá khi job đang chạy → nhận hết file mới rồi mới thay clip cũ; từ chối khi job đang chạy
- **AUD-805** (Medium) Endscreen hỏng 48 byte được coi là "mới": ghi không nguyên tử, không kiểm mã lỗi → = AUD-203
- **AUD-806** (Medium) Engine board xuất khoảng 80 Mb/s (417 MB cho 41 s), lưu hai bản → trần bitrate engine board
- **AUD-807** (Medium) Không dọn file trung gian, không có lệnh clean → studio.py clean
- **AUD-808** (Medium) Worker render không có timeout, có thể treo vô hạn → = AUD-204
- **AUD-905** (Medium) Báo cáo QA chỉ có hai mức ĐẠT/CẦN XEM, không có đỏ/vàng/xanh → ĐỎ/VÀNG/XANH trong report + qa.json
- **AUD-1003** (Medium) Form "Tạo video" mất toàn bộ lựa chọn khi F5/rời trang → UI mới (Phần D): form Tạo video tự lưu nháp (localStorage)
- **AUD-1104** (Medium) Phình dung lượng, không có lệnh dọn. steel-ball-1000c-board 1,1 GB: work/video.mp4 397 MB bị nhân đôi với out/ → = AUD-807
- **AUD-1302** (Medium) Không có lệnh kiểm tra môi trường trên CLI; bản kiểm trong UI thiếu Tesseract/tessdata/Playwright/Python/node; → studio.py doctor
- **AUD-1303** (Medium) Phụ thuộc không ghim: chỉ >=, anthropic/google-genai không có phiên bản; không file lock → constraints.txt (phiên bản đã kiểm)

## Chưa sửa (Medium/Low) và lý do

- AUD-103 (Medium) job_hash chép y hệt ở hai module; codeshot.py:249 dùng bản coderender, adapter.py:430 dùng bản adapter để so c — để vòng sau (ROADMAP_V2)
- AUD-104 (Low) Hai cách hash mã board khác nhau (listdir một cấp vs os.walk) cho cùng một mục đích — để vòng sau (ROADMAP_V2)
- AUD-105 (Low) clamp/lerp/ease_out định nghĩa hai lần; vidlib/outro.py:16,19 và vidlib/textfx.py:17,20 import cả hai bản — để vòng sau (ROADMAP_V2)
- AUD-106 (Low) Ba bản parse hex; bản của common không nhận #abc, không báo lỗi khi sai độ dài — để vòng sau (ROADMAP_V2)
- AUD-108 (Low) Danh sách engine viết lại dạng literal thay vì dùng adapter.ENGINE_NAMES — để vòng sau (ROADMAP_V2)
- AUD-109 (Low) Hằng 30 fps cứng trong walk() và _bounce() trong khi format.fps là config — để vòng sau (ROADMAP_V2)
- AUD-110 (Low) 6 hàm/thuộc tính chết (grep chỉ thấy đúng dòng định nghĩa) — để vòng sau (ROADMAP_V2)
- AUD-111 (Medium) Module/hàm quá lớn; 75 vi phạm độ phức tạp khi bật C90/PLR — để vòng sau (ROADMAP_V2)
- AUD-113 (Low) Module schema import muộn textfx, codeshot, engines.adapter, boardplan bên trong vòng lặp validate (noqa: PLC0 — để vòng sau (ROADMAP_V2)
- AUD-114 (Low) Logic dò Edge/Chrome chép hai nơi với thứ tự ưu tiên khác nhau; coderender.py:70 lại dùng browser_channel của  — để vòng sau (ROADMAP_V2)
- AUD-207 (Medium) Key để trong .env (theo quy ước của CLAUDE.md) không dùng được cho --ai, trong khi trang Cài đặt vẫn báo "có t — để vòng sau (ROADMAP_V2)
- AUD-209 (Medium) Engine board không RESUME: mỗi lần render_full đều rmtree(_parts) từ đầu. Bị ngắt ở 90% là dựng lại 100% (stee — để vòng sau (ROADMAP_V2)
- AUD-210 (Low) Ngắt hoặc lỗi để lại rác: CLI Ctrl+C không terminate các worker Edge (không có try/finally quanh Popen; UI thì — để vòng sau (ROADMAP_V2)
- AUD-211 (Medium) Ingest bỏ qua clip thay mới nếu file mới có mtime cũ hơn bản ingest và cùng tên. Ví dụ: tải 2 bản lúc 10:00, d — để vòng sau (ROADMAP_V2)
- AUD-212 (Medium) Không khoá theo dự án: CLI + UI (hoặc 2 terminal, hoặc /video trong Claude Code + UI) có thể cùng chạy một slu — để vòng sau (ROADMAP_V2)
- AUD-213 (Low) _fp băm đường dẫn tuyệt đối + mtime_ns. Chuyển repo sang thư mục hoặc máy khác, hay git checkout (đặt lại mtim — để vòng sau (ROADMAP_V2)
- AUD-214 (Medium) Chạy trên máy khác: (1) không có file khoá phiên bản (manim>=0.18, playwright>=1.40, opencv>=4.8); (2) không k — để vòng sau (ROADMAP_V2)
- AUD-215 (Low) Lịch sử chống lặp style/giọng/dạng kịch bản xếp theo mtime của out/final.mp4. Render lại một video cũ (--from  — để vòng sau (ROADMAP_V2)
- AUD-216 (Low) Cache SFX dựng sẵn assets/sfx/_builtin/<tên>.wav khoá chỉ theo tên. Sửa bộ sinh _make thì máy đã có cache vẫn  — để vòng sau (ROADMAP_V2)
- AUD-308 (Low) File phụ (clip.mp4 engine, insert phim câm, video.mp4) thiếu faststart/tag — để vòng sau (ROADMAP_V2)
- AUD-309 (Low) Tag màu lẫn lộn ở nguồn Flow (BT.601 matrix + sRGB transfer + BT.709 primaries) không được ghi nhận — để vòng sau (ROADMAP_V2)
- AUD-310 (Low) Thumbnail PNG không có chunk sRGB; ảnh nền JPEG mang đuôi .png; không chặn dung lượng 2 MB (mobile) — để vòng sau (ROADMAP_V2)
- AUD-311 (Low) Audio 192 kb/s (YouTube khuyên 384 kb/s stereo) — để vòng sau (ROADMAP_V2)
- AUD-403 (Medium) mix.wav trung gian là int16 có np.clip, không có đệm headroom trước master — để vòng sau (ROADMAP_V2)
- AUD-404 (Medium) Chuỗi nguồn VO bị nén mất dữ liệu hai lần và resample — để vòng sau (ROADMAP_V2)
- AUD-405 (Low) AAC 192 kbps bằng một nửa khuyến nghị upload của YouTube — để vòng sau (ROADMAP_V2)
- AUD-406 (Medium) SFX không có fade-in/out, nhiều file kết thúc giữa sóng ở mức lớn — để vòng sau (ROADMAP_V2)
- AUD-407 (Low) Nối VO sau khi rút lặng không có crossfade — để vòng sau (ROADMAP_V2)
- AUD-408 (Medium) Nhạc người dùng lặp bằng np.tile không crossfade; "dừng ở twist" thực chất fade dài vài giây và thay đổi theo  — để vòng sau (ROADMAP_V2)
- AUD-409 (Medium) Cân bằng VO/nhạc khoá theo RMS không trọng số K; nhạc chỉ thấp hơn lời khoảng 12 dB; duck không có look-ahead — để vòng sau (ROADMAP_V2)
- AUD-410 (Low) Cấu hình âm thanh trùng hoặc chết, tài liệu sai — để vòng sau (ROADMAP_V2)
- AUD-411 (Low) Đo loudness bằng loudnorm (không phải máy đo chuẩn); LRA không được kiểm — để vòng sau (ROADMAP_V2)
- AUD-412 (Low) Đồng bộ tiếng–hình tốt nhưng chưa được QA tự động (Low, ghi nhận) — để vòng sau (ROADMAP_V2)
- AUD-413 (Low) Sample rate 48000 hard-code ở nhiều chỗ thay vì đọc channel.audio.sample_rate — để vòng sau (ROADMAP_V2)
- AUD-503 (Medium) Engine board vượt cột icon phải; three.js/Manim không nhận safe zone — để vòng sau (ROADMAP_V2)
- AUD-506 (Medium) .srt: cue mồ côi 0.18–0.25 s, không có thời lượng tối thiểu/tốc độ đọc — để vòng sau (ROADMAP_V2)
- AUD-507 (Low) Không có cổng QA "chuẩn upload" (tag màu, level/bitrate, faststart, edit list, cỡ file) — để vòng sau (ROADMAP_V2)
- AUD-508 (Low) Đầu ra 30 fps cố định — không có lựa chọn 60 fps / 4K cho preset — để vòng sau (ROADMAP_V2)
- AUD-509 (Low) Thời lượng kênh 30–45 s an toàn; ghi rõ ràng buộc nền tảng trong preset — để vòng sau (ROADMAP_V2)
- AUD-603 (Medium) Clip Flow: watermark hiển thị có thể bị crop mất; gói Flow chưa ghi — CẦN CHỦ KÊNH QUYẾT ĐỊNH — chờ quyết định
- AUD-605 (Medium) Mã chép gần nguyên văn từ cartoon-short-kit nhưng license kit không rõ — CẦN CHỦ KÊNH XÁC NHẬN — chờ quyết định
- AUD-606 (Medium) vendor/kaz-documentary/ không có license nhưng được commit vào git — chờ quyết định
- AUD-607 (Low) Ảnh chụp màn hình bài đăng của người khác nằm trong git — để vòng sau (ROADMAP_V2)
- AUD-608 (Low) Font: thiếu file license Inter và thiếu dòng CREDITS cho 9 họ font — để vòng sau (ROADMAP_V2)
- AUD-609 (Medium) SFX/nhạc do người dùng thả vào được ưu tiên mà không kiểm license — để vòng sau (ROADMAP_V2)
- AUD-610 (Low) Nhạc tổng hợp giống hệt nhau ở mọi video — để vòng sau (ROADMAP_V2)
- AUD-611 (Low) Repo NC/PolyForm: hiện đạt, nhưng chưa có test canh tự động — để vòng sau (ROADMAP_V2)
- AUD-612 (Low) Nguồn style tương lai (Futurepedia atlas) chưa có bước kiểm điều khoản — để vòng sau (ROADMAP_V2)
- AUD-704 (Low) Không chặn request cross-site theo Origin/Sec-Fetch-Site; CSRF chỉ dựa vào header tuỳ biến — để vòng sau (ROADMAP_V2)
- AUD-706 (Low) Ngoại lệ chưa bắt: 500 lộ thông điệp nội bộ hoặc đóng kết nối không trả lời — để vòng sau (ROADMAP_V2)
- AUD-707 (Low) Xử lý Range lệch chuẩn — để vòng sau (ROADMAP_V2)
- AUD-708 (Low) HTML do pipeline sinh được phục vụ cùng origin với UI có quyền tạo job — để vòng sau (ROADMAP_V2)
- AUD-709 (Medium) Phụ thuộc có lỗ hổng đã biết; requirements không ghim phiên bản — constraints.txt ghi rõ; nâng Pillow cần anh duyệt (đổi gói ngoài repo)
- AUD-710 (Low) .gitignore còn hở — để vòng sau (ROADMAP_V2)
- AUD-802 (Medium) Cache TTS chỉ nhớ bản hiện tại của từng dự án; sửa một từ là trả tiền cả bài — để vòng sau (ROADMAP_V2)
- AUD-804 (Medium) Hash job three/html không gồm harness, chất lượng JPEG hay nội dung font — để vòng sau (ROADMAP_V2)
- AUD-809 (Low) code_render.resume = false không có tác dụng — để vòng sau (ROADMAP_V2)
- AUD-810 (Low) Mỗi shot mở trình duyệt nhiều lần — để vòng sau (ROADMAP_V2)
- AUD-811 (Low) Look-check với Manim dựng cả shot; have_all bỏ qua hash của Manim — để vòng sau (ROADMAP_V2)
- AUD-812 (Low) PERF.md đo một lần, không có RAM, nhãn GPU dễ nhầm — để vòng sau (ROADMAP_V2)
- AUD-813 (Low) Gọi ElevenLabs không retry hay backoff — để vòng sau (ROADMAP_V2)
- AUD-906 (Medium) Motiongate đo trung bình toàn video, đoạn "như slide" có thể lọt — để vòng sau (ROADMAP_V2)
- AUD-907 (Medium) Thiếu Tesseract thì kiểm OCR lặng lẽ biến mất, bảng lại toàn ✗ — để vòng sau (ROADMAP_V2)
- AUD-908 (Medium) QA chỉ kiểm final.mp4; endscreen, thumbnail, srt và cỡ file không được kiểm — deliver kiểm file từng nền tảng + bìa; endscreen riêng chưa có dòng QA
- AUD-1002 (Medium) Job không bền: log chỉ ghi khi kết thúc, hàng đợi mất khi server khởi động lại, tiến trình con mồ côi — để vòng sau (ROADMAP_V2)
- AUD-1004 (Medium) Rò kết nối SSE và vòng nối lại vô hạn — để vòng sau (ROADMAP_V2)
- AUD-1005 (Low) Hợp đồng API: không version, lỗi không có mã máy, phương thức lạ trả HTML 501 — để vòng sau (ROADMAP_V2)
- AUD-1006 (Low) Hiệu năng: poll liên tục, quét lại mọi dự án mỗi request, danh sách không phân trang — để vòng sau (ROADMAP_V2)
- AUD-1007 (Low) URL hash hỏng làm kẹt điều hướng — để vòng sau (ROADMAP_V2)
- AUD-1008 (Medium) Test UI mỏng, không có test frontend — để vòng sau (ROADMAP_V2)
- AUD-1009 (Low) Huỷ job có tranh chấp trạng thái — để vòng sau (ROADMAP_V2)
- AUD-1103 (Medium) Không backup/lưu trữ dự án. Bỏ projects/ khỏi git là đúng với media nặng, nhưng kéo theo cả nguồn sự thật nhẹ  — để vòng sau (ROADMAP_V2)
- AUD-1105 (Low) Quy ước đặt tên ngầm, không nhất quán. Tiền tố _/cmp- là "cờ" loại khỏi lịch sử nhưng chỉ nằm trong mã. Slug c — để vòng sau (ROADMAP_V2)
- AUD-1106 (Low) .gitignore gốc không bỏ *.tmp, trong khi save_json/coderender ghi <file>.tmp (rủi ro nhỏ: bị ngắt khi ghi conf — để vòng sau (ROADMAP_V2)
- AUD-1107 (Medium) Asset ngoài (clip Flow) không có nguồn gốc. _ingest.json chỉ ghi tên, fps, kích thước, thời lượng; không có ha — để vòng sau (ROADMAP_V2)
- AUD-1203 (Medium) Nguồn và nhãn sự thật (True/Disputed/Hypothetical) không vào mô tả — để vòng sau (ROADMAP_V2)
- AUD-1204 (Medium) Phụ đề .srt ghi số bằng chữ (theo lời TTS) — để vòng sau (ROADMAP_V2)
- AUD-1205 (Medium) A/B thumbnail: sinh 3 biến thể nhưng không có quy trình dùng cho Shorts, không ghi lại lựa chọn — để vòng sau (ROADMAP_V2)
- AUD-1206 (Medium) Không nhập số liệu retention/CTR để làm điểm tham khảo cho style/hook — CẦN CHỦ KÊNH QUYẾT ĐỊNH (CSV tay hay A — chờ quyết định
- AUD-1207 (Medium) Rủi ro chính sách "inauthentic content" của YPP với pipeline sản xuất hàng loạt — để vòng sau (ROADMAP_V2)
- AUD-1208 (Low) Không ghi lại cái đã thực sự đăng — để vòng sau (ROADMAP_V2)
- AUD-1304 (Medium) .venv trong repo là venv macOS (Python 3.14 Homebrew), không chạy trên Windows; hướng dẫn cài không nói tạo ve — chờ quyết định
- AUD-1305 (Low) Không dùng formatter: ruff format --check báo 81/141 file sẽ đổi — để vòng sau (ROADMAP_V2)
- AUD-1306 (Low) Không pre-commit hook cho ruff/test nhanh — để vòng sau (ROADMAP_V2)
- AUD-1307 (Medium) Runbook sự cố chỉ 6 dòng; thiếu Edge/GPU, Manim, Tesseract, ElevenLabs lỗi key/hết quota, ý nghĩa exit code 2– — để vòng sau (ROADMAP_V2)
- AUD-1308 (Low) 8 script macOS cũ vẫn được track, gọi .venv/bin/python — để vòng sau (ROADMAP_V2)
- AUD-1309 (Low) Mục cài đặt của README thiếu: Edge, tải tessdata, node (test đối chiếu JS), phiên bản Python khuyên dùng — để vòng sau (ROADMAP_V2)
- AUD-1310 (Low) Lint hẹp (E,F,W,B,UP), không giới hạn độ phức tạp; bật C90/PLR ra 75 vi phạm — để vòng sau (ROADMAP_V2)
- AUD-1311 (Low) Danh sách stage viết ở 4 nơi; ARCHITECTURE không có sơ đồ stage → file vào/ra — để vòng sau (ROADMAP_V2)
- AUD-1312 (Low) Audit cũ (13/11, "trước khi nâng cấp") vẫn nằm cạnh tài liệu hiện hành, mô tả trạng thái đã hết đúng (vd "Khôn — để vòng sau (ROADMAP_V2)

## Cần anh quyết định

| Việc | Lựa chọn | Đề xuất |
|---|---|---|
| Gói ElevenLabs (AUD-602) | free (cấm thương mại, phải ghi elevenlabs.io) · Creator/Pro (thương mại) | Gói trả phí; điền `rights/ledger.json → decisions.elevenlabs_plan` + đơn giá `config/costs.json` |
| Gói Google Flow + watermark (AUD-603) | gói hiện tại · Ultra (không watermark hiển thị) | Ghi gói vào `decisions.flow_plan`; kiểm watermark trước khi crop |
| Dùng 3D Style Atlas cho kênh thương mại | chỉ lấy ý tưởng (hiện tại) · hỏi Futurepedia/HubSpot · bỏ 37 preset | Giữ "chỉ ý tưởng" (chữ/mã viết mới, bản gốc không vào git); nếu muốn chắc chắn: email xin phép |
| Ký C2PA (AUD-604) | không ký (metadata + provenance.json như hiện tại) · chứng chỉ tự ký · chứng chỉ CA (trả phí) | Bắt đầu bằng c2pa-python + chứng chỉ tự ký để thử, mua CA khi cần |
| Safe zone Reels (D-009) | giữ dải chữ Shorts · dời lên 960–1240 cho mọi video · render bản Reels riêng | Dời lên nếu đăng Reels thường xuyên |
| Nâng Pillow (AUD-709) | giữ 11.3.0 · `pip install -U pillow` (≥ 12.3) | Nâng rồi chạy `python -m unittest` + `scripts/visual_regression.py` |
| License cartoon-short-kit (AUD-605) / bỏ vendor/kaz-documentary khỏi git (AUD-606) | xác nhận license · viết lại đoạn trùng · git rm --cached | Xác nhận license với người đưa kit |
| Số liệu retention/CTR (AUD-1206) | nhập CSV tay từ YouTube Studio · API OAuth | CSV tay trước |
