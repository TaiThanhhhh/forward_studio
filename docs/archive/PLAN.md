# PLAN — nâng cấp tool video thành pipeline một lệnh

Branch: `feat/one-command-pipeline` · baseline commit `b3715a5` · mỗi phase một commit.

## 0. Quyết định kiến trúc

| Quyết định | Lý do |
|---|---|
| **Giữ Python + Pillow + numpy + ffmpeg**, không chuyển sang Remotion/Node | Stack đang chạy tốt, render frame-by-frame bằng Pillow đủ nhanh cho 40s@30fps (~1.300 frame). Không thêm dependency nặng. Vì vậy không cài `remotion-dev/skills`. |
| `/video` = **slash command Claude Code** + CLI `python studio.py video` (kèm `video.bat` cho Windows, `scripts/video.command` cho macOS) | Trong Claude Code, chính Claude đóng vai LLM viết `storyboard.json` (không cần API key). Chạy ngoài Claude Code thì dùng `--ai claude|gemini` hoặc dán `brief.md` vào app. |
| **`storyboard.json` là nguồn sự thật duy nhất** | Prompt, `scripts.html`, caption, outro, thumbnail và dựng đều sinh từ file này. Prompt đã compile được ghi ngược vào chính file (đúng schema R1). Muốn sửa tay thì dùng `override.*`, không sửa prompt đã compile. |
| `mode` do người viết đặt (mặc định `"auto"`), kết quả ghi vào `mode_resolved` | Khi đổi `--model`, mode được chọn lại theo capability của model mới. |
| `scripts.html` thay cho `prompts.html` | Theo yêu cầu R3. File `prompts.html` cũ (nếu có) không còn được sinh. |
| Hệ "6 look" bị bỏ, thay bằng **một style bible brand** | Brief yêu cầu nền đen + một màu accent cố định. Các look cũ (gradient, giấy, glass) trái ngược hoàn toàn. |
| Font **Be Vietnam Pro** (OFL) nhúng ở `assets/fonts/`, dự phòng Montserrat rồi Inter | R7. Đã render thử đủ dấu (Ữ Ỵ ặ ở đ). |
| Không cài `faster-whisper` mặc định | Khoảng 1 GB model + torch. Nếu đã cài, word timestamp lấy từ whisper. Nếu không, tool dùng **căn theo vùng có tiếng** (tách câu theo khoảng lặng, rồi chia âm tiết theo thời lượng có tiếng). Xem rủi ro bên dưới. |
| Test dùng `unittest` của stdlib, lint dùng `ruff` (dev only) | Không thêm dependency runtime. |
| ffmpeg tự dò (PATH → `FFMPEG_DIR` → thư mục winget/choco/scoop/brew) | winget không cập nhật PATH của shell đang mở. Người dùng không phải khởi động lại. |

## 1. Google Flow — kết quả kiểm chứng (12–13/11/2026)

Chi tiết và nguồn nằm ở `config/flow-models.json`.

| Model | Trạng thái | Độ dài | Frames | Ingredients |
|---|---|---|---|---|
| **Omni Flash 1.2** (mặc định của tool) | Khuyên dùng, ra mắt 05/11/2026 | 3–15s nguyên giây (gói free 3–10s). Từ giây 11 tính credit gấp đôi | first + last (first+last **chỉ khi ≤10s**) | Có. API cho tối đa 6, Flow chưa công bố → để **3** |
| Veo 3.1 Lite | Còn | 4/6/8s | first + last | Flow có nhưng chỉ cho 8s và số ảnh chưa rõ → tắt |
| Veo 3.1 Fast | **Gỡ 05/12/2026** | 4/6/8s | first + last | 3 (chỉ 8s) |
| Veo 3.1 Quality | **Gỡ 05/12/2026** | 4/6/8s | first + last | không |
| Omni Flash 1.1 | **Gỡ 05/12/2026** | 4/6/8/10s | first + last | có |

Hệ quả cho thiết kế:
- **Không có nút tắt tiếng** (chỉ có "Return silent videos" khi audio lỗi). Vì vậy prompt luôn có AUDIO block **và** ingest luôn chạy `-an`.
- **Frames và Ingredients là hai chế độ riêng**, không gộp được trong một lần tạo. Đây đúng là nguyên tắc vàng: dùng Ingredients ở bước **ảnh** (Nano Banana Pro nhận tới 14 ảnh ref), dùng Frames ở bước **video**.
- **Omni mặc định tạo video nhiều cảnh.** Mọi prompt video phải mở đầu bằng `Single continuous shot.`, và ingest có bước phát hiện scene cut.
- **Không có ô negative prompt**, Omni cũng không hỗ trợ negative riêng. Vì vậy block `Avoid:` nằm trong prompt chính, ở cuối.
- **Cú pháp timestamp khác nhau:** Omni dùng `[0-1.5s]`, Veo dùng `[00:00-00:01.5]`. Compiler chọn cú pháp theo `timestamp_style` của model.
- **Veo xuất 24fps**, tool dựng 30fps (theo brief). Ingest chuyển sang CFR 30 bằng cách lặp frame. Với animation 2D (vốn vẽ "on twos") thì không thấy giật.
- Flow có "Save frame" thủ công. Tool tự trích frame trước vùng giảm tốc nên chính xác hơn.

## 2. Thay đổi theo yêu cầu

| R | Thay đổi | File |
|---|---|---|
| R1 | Schema `storyboard.json` v2 (mở rộng brief: `subject`, `camera`, `action[]{t,do}`, `start_frame.desc`, `state_change`, `continues_from`, `layout_free`, `accent_on`, `punch_in[]`, `override`, `code`). Hàm validate + normalize. | `vidlib/storyboard.py` |
| R2 | Pipeline có trạng thái: `idea → script → storyboard → prompts → page → [CHỜ CLIP] → ingest → trim → assemble → captions → outro → audio → render → thumbnails → qa`. Mỗi stage có `done()` dựa trên file đầu ra so với mtime đầu vào. Flag `--from/--only/--dry-run/--model/--ai/--yes/--no-open`. Ingest map tên mặc định của Flow theo thời gian tải về và lưu `clips/_map.json`. | `vidlib/pipeline.py`, `vidlib/ingest.py`, `studio.py`, `.claude/commands/video.md` |
| R3 | `scripts.html` là bảng sản xuất: phần header (model, thời lượng, Copy style bible, Ingredients), card theo cảnh ①②③④, badge mode, VO + kinetic text, "Copy cả cảnh", tiến độ, phím J/K/C, localStorage bọc try/catch, tự tick khi file đã có trên đĩa, mục "Tạo 1 lần" (outro), mục thumbnail. Có `?selftest=1` để test nút copy bằng headless browser. | `vidlib/page.py` |
| R4 | Compiler ghép prompt từ `prompts/blocks/*.txt`. Chọn mode theo bảng quy tắc dưới. Linter tự chạy trước khi xuất HTML. | `vidlib/compiler.py`, `vidlib/linter.py`, `prompts/blocks/` |
| R5 | AUDIO block + `ffmpeg -an` khi ingest. SFX chuyển về `assets/sfx/` (thêm `hit`, `boom`). Mức SFX theo loại, ducking nhạc theo VO, loudnorm −14 LUFS/−1 dBTP. | `vidlib/ingest.py`, `vidlib/audio.py`, `vidlib/sfx.py` |
| R6 | Auto-trim theo motion energy, phát hiện scene cut, `seed_from` = frame trước vùng giảm tốc, speed-ramp, hard cut/flash/whip, tự chèn punch-in để có thay đổi ≤1,2s, snap theo beat nhạc, `qa/cuts/` + chỉ số velocity mismatch. | `vidlib/motion.py`, `vidlib/timeline.py`, `vidlib/fx.py`, `vidlib/qa.py` |
| R7 | Kinetic text 2 lớp (caption theo VO + label minh hoạ: counter/arrow/circle/tag/compare/label), preset ở `brand/text-presets.json`, căn thời gian bằng whisper (nếu có) hoặc theo vùng có tiếng, overlay safe-zone trong preview. | `vidlib/captions.py`, `vidlib/vo.py` |
| R8 | Outro Shorts có tham số (teaser + avatar pop + follow + loop về frame đầu), end-screen YouTube 16:9 có chừa đúng chỗ phần tử, prompt clip nền "Tạo 1 lần" được cache ở `assets/brand/outro/`. | `vidlib/outro.py` |
| R9 | 5 archetype, nền ảnh từ Flow (prompt không chữ) hoặc frame trích từ clip, chữ/mũi tên/vòng khoanh render bằng code. Xuất 1280×720, 1080×1920 + crop 4:5/3:4/1:1, contact sheet 120/168/320 px. | `vidlib/thumbs.py` |
| R10 | Gom config, xoá trùng lặp và code chết (`plan.py`, `planner.py`, `edit.py`, `cover.py`, `images.py`, `channel.py`, `page.py` cũ, `channel.json` gốc, `style_refs/`). Lệnh cũ thành wrapper mỏng. Test + ruff. Cập nhật README/CLAUDE.md/HUONG_DAN.md. | toàn repo |

### Quy tắc chọn mode (đọc capability từ config)

| Tình huống trong storyboard | Mode | Ghi chú |
|---|---|---|
| Mặc định | `frames_start` | |
| `state_change: true` | `frames_start_end` | Chỉ khi model có `first_last` **và** `gen_sec ≤ first_last_max_sec`. Nếu không, lùi về `frames_start` và linter báo. |
| `continues_from: "Cxx"` | `frames_start` + `seed_from` | Start frame được tool **tự trích** từ clip trước, ngay trước vùng giảm tốc. |
| `refs` + `layout_free: true` + đủ slot | `ingredients` | |
| Text-to-video | **Không bao giờ** | Schema không cho phép. |

## 3. Chỗ lệch so với brief (có lý do)

1. **Prompt ảnh frame: chừa 30% đáy thay vì 22%.** R7 cấm đặt chữ ở 20% đáy, và research về safe-zone đặt caption ở y≈1150–1450 (60–75%). Nếu ảnh chỉ chừa 22% thì caption sẽ đè lên chủ thể.
2. **Giới hạn từ của prompt video: tổng ≤175 từ, phần cảnh ≤70 từ.** Bốn block cố định do brief viết sẵn (MOTION/STYLE/AUDIO/AVOID) đã chiếm khoảng 100 từ. Nếu tổng bị giới hạn ở 120 thì chỉ còn khoảng 20 từ cho hành động. Google không công bố giới hạn độ dài prompt cho Omni/Veo.
3. **Từ đang nói: chữ trắng trên viên pill xanh brand**, không phải chữ màu xanh. Lý do: `#1849F7` trên nền đen chỉ đạt 3,3:1, còn trắng trên nền xanh đạt 6,3:1. Viên pill cũng chính là motif "chấm xanh" của avatar.
4. **Bổ sung crop 3:4** cho cover, vì lưới Instagram là 3:4 từ 01/2025. Contact sheet có thêm cỡ 168px (cỡ thumbnail mobile được trích dẫn nhiều nhất).
5. **Outro Shorts mặc định 2,2s** (thuộc khoảng 2–3s). Research chưa thấy dữ liệu cho thấy CTA "follow" ở cuối hiệu quả, và CTA dài làm gãy loop. Outro vẫn làm đủ theo yêu cầu, nhưng ngắn và nối về frame đầu. Tắt bằng `outro.enabled=false`.
6. **Mức SFX theo loại** (hit −5, whoosh −10, pop −16 dB so với VO) thay vì một mức chung 8–12 dB. Theo research: tiếng pop ở mỗi cụm caption phải nhỏ hơn nhiều, nếu không sẽ gây mệt tai.
7. **Giới hạn flash ≤3/giây** (WCAG 2.3.1; TikTok tự cảnh báo và cho người xem bỏ qua video nhấp nháy). Renderer tự bỏ flash vượt ngưỡng và linter báo.
8. `"dip"` (chớp tối) bị bỏ khỏi danh sách chuyển cảnh: trên nền đen nó trông như một frame chết.

## 4. Quy tắc lấy từ research (mặc định, chỉnh được trong config)

- **Hook:** frame 0 đã ở giữa hành động, không fade-in từ đen. VO bắt đầu trước frame 6. Teaser kết quả xuất hiện trước 1s. Câu hook khoảng 9–14 từ (tiếng Anh), tiếng Việt khoảng 12–18 âm tiết.
- **Leo thang:** 3 nấc, mỗi nấc cực đoan hoặc cụ thể hơn nấc trước. Twist phải được gài trước, không recap.
- **VO:** 5–6 âm tiết/giây sau khi tăng tốc, atempo ≤1,15×. Cắt lặng còn 70ms, nhưng giữ một nhịp ngừng 0,35s trước câu payoff.
- **Nhịp:** cứ ≤1,2s phải có một thay đổi nhỏ (chữ bật, punch-in, phần tử mới, bộ đếm). Không để khung tĩnh hoàn toàn quá 2s.
- **Punch-in:** 8–12%, xen kẽ 100/110% giữa các shot, không quá 125% (vượt thì nét trắng dày lên thấy rõ).
- **Flash:** 2 frame trắng rồi tắt dần trong 3 frame. Whip khoảng 5 frame có motion blur theo hướng. Crossfade ≤4 frame.
- **Âm thanh:** −14 LUFS, −1 dBTP (loudnorm 2-pass). Nhạc nằm dưới VO khoảng 20 dB, duck thêm 6 dB. Attack 40ms, release 300ms.
- **Thumbnail:** không có dữ liệu ủng hộ quy tắc "siêu bão hoà". Dữ liệu cho thấy mũi tên/vòng khoanh có lợi nhẹ (+3,7 điểm %). Chữ 4–6 từ có lợi nhẹ hơn ≤3 từ. Tool giữ ≤3 theo yêu cầu, có thể chỉnh `thumbnail.max_words` để A/B test.

## 5. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Auto-trim chọn sai đoạn với clip thật (nhiễu nén, chuyển động nền) | Ngưỡng tương đối theo phân vị và năng lượng nền. Cho phép `trim.in/out` thủ công trong storyboard. `qa/trim/*.png` vẽ đồ thị năng lượng để soi. |
| Căn caption không có whisper bị lệch ±150ms | Tách câu theo khoảng lặng (chính xác), chỉ chia trong câu theo vùng có tiếng. Có thể cài `faster-whisper` để lấy word timestamp. |
| Map tên file Flow theo mtime sai thứ tự (tải lại, copy) | In bảng map để xác nhận, lưu `clips/_map.json` để sửa tay. Đặt tên `C01.mp4` luôn được ưu tiên. |
| Capability Flow thay đổi | Mọi logic đọc `config/flow-models.json`, có ngày kiểm chứng và nguồn. Model bị gỡ được linter cảnh báo. |
| Render Pillow chậm trên máy yếu | Một pass encode duy nhất, sprite chữ được cache. Preview dùng contact sheet. |
| `.venv/` cũ là venv macOS | Không đụng. Trên Windows dùng Python hệ thống (đã có Pillow/numpy). `requirements.txt` không đổi phần runtime. |

## 6. Thứ tự làm

1. Phase 0: audit + plan + config (commit).
2. R1 + R4: storyboard, compiler, linter, blocks (commit).
3. R3 + R2: page, ingest, pipeline, CLI, `/video` (commit).
4. R5 + R6: audio, motion, timeline, fx, render, QA cuts (commit).
5. R7 + R8: captions, VO, outro (commit).
6. R9: thumbnails (commit).
7. R10: dọn code chết, test, ruff, docs (commit).
8. Verify: dry-run end-to-end bằng clip giả, ffprobe, screenshot `scripts.html`, CHANGELOG (commit).

## 7. Đề xuất cho đợt sau (không làm trong đợt này)

- **Tự động hoá Flow bằng trình duyệt:** khả thi về kỹ thuật (Claude in Chrome / Playwright với phiên đăng nhập sẵn), nhưng rủi ro cao. UI Flow đổi thường xuyên, có thể vi phạm điều khoản, và tốn credit khi chọn sai. Nên làm bản "bán tự động": chỉ điền prompt và đính kèm ảnh vào form, người dùng tự bấm Generate.
- Thay hoặc bổ sung bằng **Gemini API** (Omni/Veo có API chính thức) nếu chấp nhận trả phí theo API. Khi đó stage `[CHỜ CLIP]` có thể chạy tự động hoàn toàn.
