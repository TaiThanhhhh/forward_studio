# RUN REPORT — vòng 8 + 9 + UI (15–16/11/2026)

Branch `upgrade/atlas-and-audit` (tách từ `feat/one-command-pipeline` @ `d7597eb`). Không push, không merge, không sửa lịch sử.

## Tóm tắt (10 dòng)

1. **Phần A — 3D Style Atlas:** nhập đủ 37/37 style (metadata + prompt toàn văn + ảnh), phân tích, viết lại thành 37 preset dark-stage; 14 tier 1 vào vòng chọn tự động, 6 off-brand bị loại khỏi vòng tự động.
2. **Phần B — audit 13 mảng:** 142 phát hiện (1 Critical, 26 High). Đã sửa 47, sửa một phần 6, 6 việc chờ anh quyết định. Điểm trung bình **5.0 → 7.8**/10.
3. Pipeline mới có: cổng QA đỏ/vàng/xanh chặn xuất (exit 12), preset Shorts/Reels/TikTok/16:9, sổ quyền + nhãn AI, version `vNNN` + manifest/provenance, chi phí mỗi video, `doctor`, visual regression, CI (chưa push).
4. **Phần D — UI mới:** 8 trang theo công đoạn + design system; Nielsen **22 → 41**/50; axe **0 vi phạm** trên 11 route; chuyển trang < 10 ms.
5. **Phần C — kiểm chứng:** 4 video thử (Glass and Light, X-Ray, Particle Swarm + style cũ flat-vector-black) làm trọn qua UI bằng Playwright, không dùng CLI.
6. Gói xuất Shorts/Reels/TikTok: **12/12 ĐẠT** khi đo độc lập bằng ffprobe + ebur128 (màu BT.709, faststart, 48 kHz, −14 LUFS, true peak ≤ −1 dBTP…).
7. Tái lập: dựng lại 2 lần → **sha256 giống hệt**. Ngắt giữa lúc render (ở frame 3/55) → chạy lại **chỉ dựng 52 frame còn thiếu**.
8. 225 test OK · ruff sạch · visual regression 6/6 (SSIM 1.0) · doctor 0 FAIL (3 cảnh báo: 2 key AI tuỳ chọn + quyết định bản quyền).
9. ElevenLabs dùng **676 ký tự** (2 đoạn × 338, giới hạn ~3.000). Đoạn thứ 2 là ngoài ý muốn; đã tìm ra nguyên nhân và sửa (mục C).
10. Có **8 việc cần anh quyết định** (mục cuối). Quan trọng nhất: gói ElevenLabs và quyền dùng Atlas cho kênh thương mại.

---

## Phần A — 3D Style Atlas

| | Kết quả |
|---|---|
| Đã nhập | **37/37** metadata (số, tên, nhóm, tag, mô tả, shown_here, good_for) · **37/37** prompt toàn văn · **37/37** ảnh modal |
| Lưu ở đâu | `vendor/3d-style-atlas/raw/NN-<slug>.json` + `shots/NN.png` (**gitignore** — điều khoản HubSpot chỉ cho dùng cá nhân, phi thương mại, D-005) · mục lục + tóm tắt điều khoản: `vendor/3d-style-atlas/INDEX.md` |
| Cách lấy | Cloudflare chặn lúc đầu → anh tự xác minh (B-01). Hook clipboard không chạy khi tab nằm nền (B-02) → khi anh có mặt: nối extension với đúng Chrome máy này, bấm nút copy thật, đọc clipboard Windows. Hook đã gỡ, hàm gốc khôi phục. Không bịa prompt nào. |
| Phân tích | `docs/3D_ATLAS_ANALYSIS.md` — engine: three 24 · hybrid 11 · flow 2; độ hợp kênh 1–5; các cặp trùng nhau |
| Preset | `styles/atlas-*.json` + thẻ `.md`, sinh từ `config/atlas.json` bằng `python scripts/atlas_import.py`; bộ kiểm chặn chép ≥ 6 từ liên tiếp từ bản gốc (kể cả prompt toàn văn) |
| Không lấy được | không còn gì (B-01, B-02 đã gỡ) |

**Tier 1 (14 style — vào vòng chọn tự động):**

| # | Style | Nhóm | Engine | Hợp kênh |
|---|---|---|---|---|
| 04 | Tiny Diorama | Không gian và hành trình | hybrid | chỉnh lại |
| 07 | Neon Sign | Nội dung phẳng thành vật thật | three | hợp |
| 08 | Exploded View | Sơ đồ có chiều sâu | three | chỉnh lại |
| 10 | X-Ray | Bộ lọc trên 3D | three | hợp |
| 12 | Inflated | Thế giới chất liệu | hybrid | chỉnh lại |
| 14 | Circuit City | Không gian và hành trình | hybrid | hợp |
| 15 | Glass and Light | Thế giới chất liệu | hybrid | hợp |
| 17 | White Model | Sơ đồ có chiều sâu | three | chỉnh lại |
| 19 | Data Skyline | Sơ đồ có chiều sâu | three | chỉnh lại |
| 21 | Pin Wall | Nội dung phẳng thành vật thật | three | hợp |
| 23 | Particle Swarm | Nội dung phẳng thành vật thật | three | chỉnh lại |
| 26 | Domino Chain | Cỗ máy giải thích | three | hợp |
| 33 | Studio Product | Sản phẩm và màn hình | hybrid | hợp |
| 34 | Split-Flap Board | Nội dung phẳng thành vật thật | three | hợp |

**Off-brand (6 — không vào vòng tự động, vẫn chọn tay được):** Painted, Toy Blocks, Pencil Sketch, Floating Screens,
Hero Icon, Monument Type. **Tier 2 còn lại:** 17 style (chọn tay được).

Contact sheet: `qa/atlas-style-compare.png` (14 tier 1, engine three.js thật) · `qa/atlas-all.png` (37). Khi soát sheet đã
sửa thêm màu "nóng": bi thép 1.000°C luôn màu ấm, nước đá luôn màu lạnh, kể cả style có bảng màu toàn lạnh (D-010, D-010b).
Ghi công: `docs/CREDITS.md`.

---

## Phần B — audit + sửa

Báo cáo đầy đủ: `docs/archive/AUDIT_V2.md` (+ 7 báo cáo con `docs/archive/audit/area-*.md`, nguồn web có ngày) · lộ trình: `docs/ROADMAP_V2.md`.

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
| | **Trung bình** | **5.0** | **7.8** | |

Điểm "sau" do tôi tự chấm theo cùng thang của báo cáo gốc, dựa trên các mục đã sửa và số đo lại trên file thật.

**Đã sửa — Critical/High (22):** AUD-901 (Critical: QA đỏ không chặn), 101, 201, 203, 204, 301, 302, 401, 402, 501, 601,
701, 801, 803, 902, 903, 1001, 1101, 1102, 1201, 1202, 1301.
**Đã sửa — Medium (25):** AUD-102, 107, 112, 202, 205, 206, 208, 304, 305, 306, 307, 504, 505, 702, 703, 705, 805, 806,
807, 808, 905, 1003, 1104, 1302, 1303.

**Sửa một phần (6):**
- AUD-303: nguồn Flow 360p — cổng QA báo vàng; cần anh tải bản 1080p từ Flow.
- AUD-502: safe zone Reels — đỉnh/cạnh đã theo cả 3 nền tảng; phần đáy chờ anh quyết (D-009).
- AUD-604: C2PA — đã có metadata MP4 + `out/provenance.json`; muốn ký thật thì cần chứng chỉ.
- AUD-709: phiên bản đã ghi rõ trong `constraints.txt`; nâng Pillow cần anh duyệt.
- AUD-904: thêm test vòng 9 + CI; `pipeline.py`/`textfx.py` vẫn chủ yếu được test gián tiếp.
- AUD-908: deliver kiểm file và bìa từng nền tảng; endscreen riêng chưa có dòng QA.

**Chưa sửa (91, Medium/Low) — lý do:** chủ yếu là dọn kiến trúc (hàm trùng, module quá lớn, hằng số cứng), tối ưu nhỏ và mục
giá trị thấp so với công sức → đã xếp lịch ở `docs/ROADMAP_V2.md` (vòng 10: chất lượng tiếng + nguồn, vòng 11: độ bền +
kiến trúc). Đáng chú ý nhất: AUD-209 (engine board chưa RESUME khi bị ngắt), AUD-406–409 (fade SFX, mix float32, khoá mức
theo LUFS), AUD-111 (75 chỗ độ phức tạp cao). Danh sách đủ kèm lý do: `docs/archive/AUDIT_V2.md` mục "Chưa sửa".

---

## Phần D — UI

- Ảnh: trước `qa/ui/before/` · sau `qa/ui/after/` (1440×900 + 1920×1080) · ghép trước/sau **`qa/ui/before-after.png`**.
- Audit + đo lại: `docs/UI_AUDIT.md` (mục 5) · design system: `docs/DESIGN_SYSTEM.md`, xem trực tiếp ở `#/_design`.
- Chạy: `python studio.py ui` (hoặc `ui.bat`). Backend chỉ thêm endpoint `/api/v2/...`, API cũ giữ nguyên.

| Tác vụ | Trước: thao tác / màn hình | Sau: thao tác / màn hình |
|---|---|---|
| 1. Tạo video từ ý tưởng | 4 / 3 | **2–3 / 2** |
| 2. Bảng sản xuất Flow + nạp clip | ~65 / 3 (15 shot) | **nạp clip 3–4 bất kể số shot · chép prompt 1 phím `C` mỗi prompt / 1** |
| 3. Sửa một shot rồi render lại riêng shot đó | không làm được | **3–4 / 1** |
| 4. Review + comment một bản render | không làm được | **4 / 1** (comment theo timecode + vẽ khoanh, so A/B) |
| 5. Xuất Shorts / Reels / TikTok | không có preset | **1 / 1** (cổng QA đỏ thì nút bị khoá) |

**axe-core 4.10.2 (WCAG 2 A/AA):** 0 vi phạm ở mọi mức trên 11 route. **Hiệu năng:** chuyển trang 1.8–10 ms, mở video ở
Review 41–100 ms (mục tiêu: chuyển trang < 100 ms, mở video < 1 s).

**Phím tắt** (bảng đầy đủ: bấm `?` trong app):

| Phím | Việc |
|---|---|
| `1`–`8` | chuyển trang công đoạn |
| `Ctrl+K` · `Ctrl+P` · `Ctrl+J` | command palette · chọn dự án · hàng đợi job |
| `Ctrl+Z` · `Ctrl+Shift+Z` | hoàn tác · làm lại |
| `Space` · `J` `K` `L` | phát/dừng · lùi / dừng / tiến |
| `←` `→` · `Shift+←/→` | 1 frame · 10 frame |
| `I` · `O` · `Alt+X` | điểm vào · điểm ra · xoá vùng |
| `C` · `X` · `↑/↓` · `Tab` (Generate) | chép prompt · đánh dấu đã tạo · đổi thẻ · đổi prompt |
| `N` · `D` · `M` · `Ctrl+Enter` (Review) | comment mới · vẽ khoanh · tới comment kế · gửi |
| `R` (Board/Edit) · `Alt+←/→` (Board) | render lại shot đang chọn · dời shot |
| `N` · `/` (Projects) | gõ ý tưởng mới · lọc |
| `?` · `Esc` | bảng phím tắt · đóng |

---

## Phần C — kiểm chứng cuối

| Bước | Kết quả |
|---|---|
| C1 doctor | 20 mục · 0 FAIL · 3 WARN (ANTHROPIC/GEMINI key tuỳ chọn; quyết định bản quyền đang chờ) |
| C2 video thử | 4 dự án, câu hỏi "What happens if you drop a 1,000°C steel ball into ice water?", 16.9–19.3 s. 3 style tier 1 thuộc 3 nhóm (Glass and Light — chất liệu, hybrid: 3 shot Flow dùng prompt + clip giả; X-Ray — bộ lọc trên 3D; Particle Swarm — nội dung phẳng) + 1 style cũ `flat-vector-black`. Shot code render thật. |
| C3 gói xuất | **12/12 ĐẠT** (4 dự án × Shorts/Reels/TikTok) — khung, CFR, H.264 High L4.2 + AAC, yuv420p, BT.709 tv, faststart, 48 kHz, −13.8…−14.0 LUFS, TP −1.7…−3.2 dBTP, thời lượng, dung lượng, bitrate — `qa/part-c.md` |
| C4 tái lập | 2 lần dựng lại: sha256 `final.mp4` giống hệt, pHash lệch 0 trên 17 mốc |
| C4 resume | ngắt cả cây tiến trình ở frame 3/55 → chạy lại chỉ dựng 52 frame, đủ 55/55 |
| C5 qua UI | Playwright làm 5 tác vụ trên cả 4 dự án (Projects → Script → Board → Generate → Edit → Review → Deliver): mọi job exit 0 — `qa/ui/e2e.json` |
| C6 contact sheet | `qa/atlas-style-compare.png` |
| C7 kiểm | 225 test OK · ruff sạch · visual regression 6/6 · cổng QA: 0 đỏ ở cả 4 video |

**Cổng QA cả 4 video đang VÀNG, không đỏ.** Vàng chỉ vì các mục quyền đang chờ anh quyết (Atlas, ElevenLabs, Flow); mọi
mục kỹ thuật đều xanh. Riêng gói Reels vàng vì dải chữ nằm trong vùng đáy của Reels (D-009).

**Lỗi tìm ra trong lúc kiểm và đã sửa:**
- Windows khoá `final.mp4` khi UI đang phát video → "Render lại shot" chết giữa chừng. Đã sửa: ghi đè có thử lại (`replace_retry`) và UI nhả trình phát trước khi chạy job.
- Job trên dự án chạy thử có thể gọi API thật. Đã sửa: mọi job trên dự án chạy thử đều giữ chế độ chạy thử.
- **Lần gọi ElevenLabs ngoài ý muốn** (swarm, 338 ký tự): script e2e bấm *đảo* ô "Chạy thử", mà UI nhớ trạng thái lần trước → thành tắt. Đã sửa: script đặt trạng thái tường minh và kiểm lại trước khi tạo.
- Slug trùng khi 4 ý tưởng cùng câu hỏi (D-011): dừng ngay, khôi phục dự án bị ghi đè, đổi tên. Không mất dữ liệu.
- Bi thép xanh/xám ở vài preset Atlas, nước màu cam ở style nền chrome (D-010, D-010b).
- 2 lần đo RESUME đầu không hợp lệ (đếm nhầm frame cũ, ngắt quá muộn) → đã sửa script đo; kết quả đúng ở bảng trên.
- Tự soát UI: nút "Sửa ở…" bị cắt ở Deliver, ô prompt rỗng ở Board → đã sửa.

---

## Cần anh quyết định

| Việc | Lựa chọn | Đề xuất |
|---|---|---|
| Gói ElevenLabs (AUD-602) | free: cấm dùng thương mại, phải ghi elevenlabs.io · Creator/Pro: được dùng thương mại | Dùng gói trả phí; điền `rights/ledger.json → decisions.elevenlabs_plan` + đơn giá trong `config/costs.json` |
| Dùng 3D Style Atlas cho kênh thương mại | chỉ lấy ý tưởng (hiện tại) · hỏi Futurepedia/HubSpot · bỏ 37 preset | Giữ "chỉ lấy ý tưởng" (chữ và mã đều viết mới, bản gốc không vào git). Muốn chắc chắn thì email xin phép. |
| Gói Google Flow + watermark (AUD-603) | gói hiện tại · Ultra (không có watermark hiển thị) | Ghi gói vào `decisions.flow_plan`; kiểm watermark trước khi crop |
| Safe zone Reels (D-009) | giữ dải chữ kiểu Shorts · dời lên 960–1240 cho mọi video · render bản Reels riêng | Dời lên nếu anh đăng Reels thường xuyên |
| Ký C2PA (AUD-604) | không ký (metadata + provenance.json như hiện tại) · chứng chỉ tự ký · chứng chỉ CA (trả phí) | Thử bằng c2pa-python + chứng chỉ tự ký trước |
| Nâng Pillow (AUD-709) | giữ 11.3.0 · `pip install -U pillow` (≥ 12.3) | Nâng rồi chạy test + `scripts/visual_regression.py` |
| License cartoon-short-kit (AUD-605) · bỏ `vendor/kaz-documentary` khỏi git (AUD-606) | xác nhận license · viết lại đoạn trùng · `git rm --cached` | Xác nhận license với người đưa kit |
| Số liệu retention/CTR (AUD-1206) | nhập CSV tay từ YouTube Studio · API OAuth | Nhập CSV tay trước |

Ngoài ra, `.github/workflows/ci.yml` đã có nhưng **chưa push**. Push lên thì CI mới chạy.

---

## Đường dẫn

| Thứ | Ở đâu |
|---|---|
| Video thử | `projects/atlas-glass-test-what-happens-if-you-drop-a-1/out/final.mp4` · `projects/atlas-xray-test-what-happens-if-you-drop-a-1/out/final.mp4` · `projects/atlas-swarm-test-what-happens-if-you-drop-a-1/out/final.mp4` · `projects/e2e-classic-flat-vector/out/final.mp4` |
| Gói nền tảng | `projects/<dự án>/out/deliver/{youtube_shorts,instagram_reels,tiktok}/` (video + bìa + .srt) · version cũ: `out/versions/vNNN/` |
| QA report | `projects/<dự án>/qa/report.html` (+ `report.md`, `qa_sheet.jpg`) · kiểm chứng độc lập: `qa/part-c.md` |
| Contact sheet | `qa/atlas-style-compare.png` (tier 1) · `qa/atlas-all.png` (37) · style frame: `qa/styles/atlas-*.jpg` |
| Ảnh UI | `qa/ui/before/` · `qa/ui/after/` · `qa/ui/before-after.png` · axe/hiệu năng: `qa/ui/check.json` · e2e: `qa/ui/e2e.json` |
| Nhật ký | `docs/archive/RUN_LOG.md` · `docs/DECISIONS.md` (D-001…D-011) · `docs/archive/BLOCKERS.md` (đã gỡ hết) |

Dự án phụ sinh ra lúc kiểm: `projects/_e2e-partial-glass-run1` (lượt dở bị slug trùng, ẩn khỏi UI, không xoá). Nếu không cần
thì anh xoá tay được.

## Cách xem lại · merge · quay lại

```
git log --oneline feat/one-command-pipeline..upgrade/atlas-and-audit   # 15 commit của lượt này
git diff --stat feat/one-command-pipeline..upgrade/atlas-and-audit     # ~266 file
python studio.py ui                                                    # xem UI mới
python -m unittest discover -s tests -t . ; python scripts/visual_regression.py
```

- **Merge (nếu hài lòng):** `git checkout feat/one-command-pipeline && git merge --ff-only upgrade/atlas-and-audit`.
  `feat/one-command-pipeline` đang đi trước `master` 21 commit; muốn đưa cả hai lên `master` thì merge tiếp vào `master`.
- **Quay lại bản cũ:** `git checkout feat/one-command-pipeline`. Branch cũ không bị đụng tới, và `upgrade/atlas-and-audit`
  vẫn giữ nguyên để xem lại sau.
- **Tương thích:** storyboard cũ tự nâng lên schema v3 khi đọc (`storyboard.migrate()`, có test). Video và dự án cũ không bị
  render lại. Không xoá style, engine hay dự án cũ nào.
