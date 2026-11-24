# Báo cáo Nghiệm thu Vòng 13 — Nâng Cấp Đẳng Cấp Agency Viral Toàn Cầu & Repo Hygiene

> Triển khai trọn bộ **7 Gói Việc (`WP-0` → `WP-6`)** theo đặc tả tại `docs/ROUND13_PROMPT.md` (reverse-engineered từ **Fern · LEMMiNO · Zack D. Films · Johnny Harris · Vox · Cleo Abram · Kurzgesagt · Ordinary Folk · Giant Ant · Buck**), đồng thời dọn sạch file/quy trình thừa và đóng gói **8 PR nhỏ nguyên tử** (`PR-01` → `PR-08`) chuẩn agency lên `origin` (`TaiThanhhhh/forward_studio`).

---

## 1. Tóm tắt nâng cấp cốt lõi ở tầng Tool

| Hạng mục | Giải pháp tổng quát trong tool | Gói việc / PR |
|---|---|---|
| **Repo Hygiene** | Xoá 7 script chết/1-lần, gỡ lệnh chết `setup`/`looks` & nhánh `ui` trùng trong `studio.py`, dọn tài liệu audit/archive cũ, gỡ tracking 220+ file rác `qa/` (giữ `qa/visreg/` & ảnh nghiệm thu), siết `.gitignore` | WP-0 / `PR-02` |
| **3 Beat Điện Ảnh 2D + `story_hud`** | Thêm `dossier` (hồ sơ LEMMiNO/Johnny Harris), `xray_cutaway` (mặt cắt giải phẫu + hạt dòng chảy Bézier), `hero_stat` (typography kiến trúc cỡ đại + nền phản ứng 4 motif), thanh telemetry bám dính xuyên shot `story_hud` ở Zone A, và `editorialStageGlow` + film grain mịn | WP-1 / `PR-03` |
| **3D Điện Ảnh Fern / Zack D. Films** | Sửa triệt để lỗi clear-color sRGB kép ở ACES (`engines/three/main.js`) đưa nền 3D `vox-editorial-black` về dark-mode sâu (`#040509`–`#07080C`), thêm `volumetricSpotlight` (`noFrame + ndSkip`), và 5 góc máy điện ảnh (`ecu_macro`, `low_hero`, `tracking_low`, `over_shoulder`, `dolly_zoom`) + tự luân phiên góc giữa các shot 3D | WP-2 / `PR-04` |
| **Chuyển Cảnh Agency & Seamless Loop** | Thêm 3 chuyển cảnh `iris_match`, `whip_match`, `tape_stop` chạy mượt mọi engine; chế độ `outro.mode: "loop"` bỏ thẻ outro tĩnh và pha cầu nối `apply_loop_bridge` về frame 0 kéo AVD > 100%; tự nội suy `story_hud` & nối archetype moves vào `spine.py` | WP-3 / `PR-05` |
| **Audio-Driven Tension Arc** | Nâng `musicgen.py` lên **5 mood nhạc điện ảnh khác biệt hoàn toàn** (`investigative_pulse`, `kinetic_editorial`, `visceral_thriller`, `clockwork_tension`, `minimal_cinematic`) + đường cong năng lượng + **0.35s Dead-Air Drop** trước twist; thêm **6 SFX agency** (`sub_drop`, `riser_long`, `tape_stop`, `paper_rustle`, `neural_pulse`, `swish_match`) tự động bơm theo beat/transition | WP-4 / `PR-06` |
| **6 Director Archetypes & Luật Viral** | Tạo `config/archetypes.json` với 6 bản sắc đạo diễn (`visceral_anatomy`, `forensic_dossier`, `editorial_clash`, `ticking_clock`, `myth_autopsy`, `one_object_odyssey`) xoay vòng `avoid_recent: 4`; nhúng 5 luật biên kịch viral (*Cold-Open*, *But/Therefore*, *Re-Hook 12–16s*, *≥40% Rich Craft*, *Seamless Loop*) vào `brief.py` & `storyboard_brief.md` | WP-5 / `PR-07` |
| **Viral & Craft Scorecard (0–100)** | Tạo `vidlib/viralscore.py` chấm 6 trục (0–100, hạng S/A/B/C/D), tích hợp vào `linter.py`, `motionplan.py` và `qa/report.md`/`report.html`, kèm bộ kiểm thử `tests/test_round13.py` | WP-6 / `PR-08` |

---

## 2. Kết quả kiểm định thực tế & soi ảnh trực quan

### 2.1 Kiểm định kỹ thuật
- `python -m ruff check .` → **0 lỗi** (`All checks passed!`)
- `python -m unittest discover -s tests -t .` → **332/332 pass** (0 fail, 6 skip — gồm `tests/test_round12.py` + `tests/test_round13.py`)
- `python -m vidlib.motionplan check` → **0 lỗi** (`kho cơ chế OK (175 mục)`)
- **3 beat điện ảnh mới + `story_hud` (`qa/round13/cinema_beats.jpg`)**: **0 cặp chồng chữ (`overlapPairs == []`), 0 lấn Zone C** trên cả `vox-editorial-black` lẫn `swiss-motion-black`.
- **3D điện ảnh (`qa/round13/cinema_3d.jpg`)**: nền dark-mode sâu (hết xám bệt), volumetric spotlight + rim light sắc cạnh, 5 góc máy điện ảnh (`ecu_macro`, `low_hero`, `tracking_low`, `over_shoulder`, `dolly_zoom`) khác biệt rõ rệt.

### 2.2 Kiểm chứng End-to-End 2 Video mang 2 Archetype hoàn toàn khác nhau

| Tiêu chí | Video 1 — `your-mouth-can-feed-your-brain` (v002) | Video 2 — `your-body-runs-out-of-heat-first` (v001) |
|---|---|---|
| **Director Archetype** | **`forensic_dossier`** (LEMMiNO · Vox · Fern) | **`ticking_clock`** (Fern · Kurzgesagt) |
| **Style & Visual Soul** | `vox-editorial-black` (Serif vàng kem + hồ sơ lưu trữ + X-ray não) | `swiss-motion-black` (Swiss đỏ/trắng + **`story_hud` CORE TEMP** chạy liên tục) |
| **Giọng đọc (VO)** | **ElevenLabs `eleven_v3` thật (George)** · 37.9s | Dry-run test · 26.6s |
| **Nhạc nền (`music_mood`)** | `investigative_pulse` (108 BPM + 52 SFX + dead-air twist) | `clockwork_tension` (120 BPM + 46 SFX + dead-air twist) |
| **Góc máy 3D & Transitions** | `low_hero` + `tracking_low` · `iris_match`, `whip_match`, `tape_stop` | `ecu_macro` + `dolly_zoom` + grounded `heat` · `whip_match`, `iris_match`, `tape_stop` |
| **Kết thúc** | **`seamless_loop`** (8f bridge về frame 0, bỏ outro tĩnh) | **`seamless_loop`** (8f bridge về frame 0, bỏ outro tĩnh) |
| **Điểm Viral & Craft** | **96/100 · Hạng S** | **100/100 · Hạng S** |
| **Cổng QA** | **0 ĐỎ · 1 vàng (nhắc gói ElevenLabs) · 25 XANH** (`33/33` OCR, `0` chồng chữ, sạch Zone C, `-14.1 LUFS`) | **XANH 26/26 · 0 ĐỎ · 0 vàng** (`23/23` OCR, `0` chồng chữ, sạch Zone C, `-14.0 LUFS`) |
| **Ảnh đối chiếu** | `qa/round13/forensic_dossier_qa_sheet.jpg` | `qa/round13/ticking_clock_qa_sheet.jpg` |

---

## 3. Chuỗi 8 PR nhỏ chuẩn Agency đã push & merge `--no-ff` vào `main`

1. **PR-01** `feat/round12-studio-standard` — Chuẩn Studio Vòng 12
2. **PR-02** `chore/cleanup-dead-files-and-workflows` — WP-0 Dọn 250 file/quy trình thừa & siết `.gitignore`
3. **PR-03** `feat/r13-2d-cinema-beats-and-story-hud` — WP-1 (`dossier`, `xray_cutaway`, `hero_stat`, `story_hud`, `editorialStageGlow`)
4. **PR-04** `feat/r13-3d-cinema-lighting-and-cameras` — WP-2 (Sửa nền dark-mode ACES, `volumetricSpotlight`, 5 góc máy điện ảnh 3D)
5. **PR-05** `feat/r13-matchcuts-and-seamless-loop` — WP-3 (`iris_match`, `whip_match`, `tape_stop`, `seamless_loop`, tiêm `story_hud`)
6. **PR-06** `feat/r13-audio-tension-and-music-moods` — WP-4 (5 mood nhạc điện ảnh, 6 SFX agency, tự động bơm tension arc)
7. **PR-07** `feat/r13-viral-director-archetypes` — WP-5 (`config/archetypes.json`, xoay vòng 6 archetype, luật viết kịch bản viral)
8. **PR-08** `feat/r13-viral-scorecard-and-verification` — WP-6 (`vidlib/viralscore.py`, tích hợp linter/motionplan/qareport, `tests/test_round13.py`, ảnh `qa/round13/` & báo cáo này)
