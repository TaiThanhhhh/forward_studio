# Vòng 13 — Prompt cho Gemini 4 Neon (High)
## Từ "Sạch kỹ thuật" lên "Đẳng cấp Agency Viral Toàn Cầu" (Reverse-Engineered Blueprint)

> **Chuẩn Tham Chiếu Toàn Cầu (Reverse-Engineered):**
> **Fern** (điện ảnh 3D tối giản, ánh sáng kịch tính, nhịp thriller) · **LEMMiNO** (hồ sơ lưu trữ dark-mode, typography sắc lạnh, micro-foley) · **Zack D. Films** (cold-open cận cảnh cực đoan ở giây 0, cutaway giải phẫu trực diện, vòng lặp liền mạch AVD > 100%) · **Johnny Harris & Vox** (kể chuyện nhân-quả *"But / Therefore"*, biến dữ liệu thành nhân vật có động cơ) · **Ordinary Folk · Giant Ant · Buck** (Match Cut liền mạch, Camera Continuity không đứt gãy, bố cục giàu chiều sâu thay vì slide gắn icon).
>
> Prompt này viết cho **Gemini 4 Neon (High)** làm việc trong repo `forward_studio` (dự án `forward_video` — kênh **"forward."**).
> Một agent điều phối (**Orchestrator**) đọc trọn file này và chia việc cho **7 Gói Việc (`WP-0` → `WP-6`)**: dọn sạch file/quy trình thừa trước (`WP-0`), sau đó chạy song song 6 gói nâng cấp Viral Agency (`WP-1` → `WP-6`), và cuối cùng đóng gói **stage + commit + push theo từng PR nhỏ chuẩn Studio/Agency** (mục 6).
> **Nguyên tắc cốt lõi:** Toàn bộ nâng cấp làm **tổng quát ở tầng Tool/Engine/Brief/Audio/QA** — mọi video sinh ra sau này tự động khác biệt nhau, giàu điện ảnh và tối ưu giữ chân (Retention & Rewatch), **tuyệt đối không vá riêng từng video**.

---

## 0. Đọc bắt buộc trước khi động vào code

1. `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/ROUND12_REPORT.md` — nắm vững 4 tầng kiến trúc và toàn bộ chuẩn bất biến đã khóa ở Vòng 12 (Grid 3 tầng, Visual Budget, `studio_clean` Zone C, 0 chồng chữ).
2. `config/narratives.json`, `vidlib/narratives.py`, `prompts/storyboard_brief.md`, `vidlib/brief.py` — tầng kể chuyện & sinh kịch bản.
3. `engines/html/beats.js`, `engines/html/core.js`, `engines/html/looks.js`, `engines/html/__init__.py` — toàn bộ hệ 2D Motion Graphics.
4. `engines/three/main.js`, `engines/three/scenes/stage.js`, `engines/three/props.js` — hệ 3D, ánh sáng và góc máy.
5. `vidlib/spine.py`, `vidlib/render.py`, `vidlib/vcam.py`, `vidlib/pipeline.py` — chuyển cảnh, match-cut, seamless loop.
6. `vidlib/musicgen.py`, `vidlib/sfx.py`, `vidlib/audio.py`, `vidlib/mix.py` — kiến trúc âm thanh & nhạc nền.
7. `vidlib/linter.py`, `vidlib/motionplan.py`, `vidlib/qareport.py`, `vidlib/qagate.py` — kiểm định tự động.

---

## 1. Kết quả Reverse-Engineering: Tại sao video hiện tại "sạch nhưng chưa Viral / còn giống nhau"?

Sau khi phân tích đối chiếu các studio/agency trăm triệu view (**Fern · LEMMiNO · Zack D. Films · Johnny Harris · Vox · Cleo Abram · Kurzgesagt · Ordinary Folk · Giant Ant · Buck**) với mã nguồn thực tế của `forward_studio`, phát hiện **7 nút thắt gốc** khiến video trông giống "PowerPoint dark-mode đổi chữ" thay vì phim ngắn điện ảnh viral:

| # | Triệu chứng thực tế | Nút thắt gốc trong `forward_studio` | Cơ chế của Agency Viral toàn cầu |
|---|---|---|---|
| **1** | **Kịch bản các video na ná nhau, thiếu kịch tính & dễ đoán** | `storyboard_brief.md` & `narratives.json` tạo dòng chảy bài giảng tuyến tính (*Fact A → Fact B → Fact C → thẻ twist → thẻ outro "Follow for more"*); thiếu cấu trúc nhân-quả **"But / Therefore"**, thiếu **Re-Hook giây 12–16** và thẻ outro làm **gãy vòng lặp xem lại**. | **Zack D. Films · Fern · Johnny Harris**: (a) **In-Media-Res Cold Open** ném thẳng vào khoảnh khắc sốc nhất ở frame 0; (b) Chuỗi **But / Therefore** (mỗi câu lật đổ hoặc tạo áp lực lên câu trước); (c) **Mid-Video Pattern Interrupt** ở giây 12–16; (d) **Seamless Loop Ending** — câu cuối nối thẳng ngữ pháp & hình ảnh về câu 1 để đẩy tỷ lệ xem lại AVD > 100%! |
| **2** | **70% cảnh 2D trông như "1 icon bé lơ lửng giữa nền đen + 1 pill vàng"** | `beats.js` xoay quanh các thẻ đơn lẻ (`drop`, `callout`, `meter`, `fact:flip`) tách rời nhau, không có bố cục biên tập tạp chí, không có dòng chảy sinh lý/vật lý sống động, không có **Persistent Story HUD** xuyên suốt nhiều cảnh. | **LEMMiNO · Vox · Zack D. Films · Ordinary Folk**: Dùng **4 ngôn ngữ hình ảnh giàu chiều sâu**: (1) **`dossier`** (hồ sơ/bằng chứng có khung lưu trữ, highlight bút dạ quang đúng từ khóa); (2) **`xray_cutaway`** (mặt cắt 2 lớp + dòng hạt chảy sống động theo quỹ đạo Bézier); (3) **`hero_stat`** (typography kiến trúc cỡ đại tràn khung phản ứng theo chuyển động nền); (4) **`story_hud`** (đồng hồ/nhiệt kế/nhịp tim/tiến trình **bám dính xuyên suốt nhiều shot** tạo cảm giác áp lực leo thang liên tục!). |
| **3** | **Cắt cảnh kiểu "Slide 1 tắt → Slide 2 bật", thiếu liên kết mắt** | `render.py` & `spine.py` chỉ dùng `cut` / `dip` cơ học giữa `html ↔ three` và không có **Match Cut** (vật thể/tâm cảnh trước biến hình/phóng xuyên sang cảnh sau). | **Ordinary Folk · Giant Ant · Buck**: **Graphic Match Cut & Directional Momentum** — vật thể tâm cảnh A phóng to tràn khung (*scale-through / iris match*) hoặc quét đúng hướng vận tốc (*whip-match*) kéo mắt người xem trôi liền mạch sang cảnh B kể cả khi chuyển giữa 2D ↔ 3D! |
| **4** | **Cảnh 3D phẳng, nền bị xám bệt, 1 góc camera `diorama` lặp mãi** | `engines/three/main.js` bật ACES tone mapping làm nền `#0E1014` của `clay` (`vox-editorial-black`) bị đẩy sáng thành xám nhạt `#4A5566`; `stage.js` mặc định góc `diorama` từ trên nhìn xuống 20° cố định, thiếu các góc máy điện ảnh. | **Fern · Zack D. Films · Neo**: (a) Khóa nền dark-mode sâu có **volumetric spotlight cone + rim light sắc cạnh + fog chiều sâu** (không xám bệt); (b) **5 góc máy điện ảnh mới** (`ecu_macro`, `low_hero`, `tracking_low`, `over_shoulder`, `dolly_zoom`) + quỹ đạo camera động nhiều chặng trong 1 shot! |
| **5** | **Nhạc nền & SFX 1 màu ở mọi video, không có đường cong căng thẳng** | `vidlib/musicgen.py` phát đúng **1 vòng hòa âm duy nhất** `Am–F–G–E` với 1 kiểu kick/snare/pluck cho TẤT CẢ các video! `vidlib/audio.py` chưa tự bơm **Hook Sub-Drop**, **Escalation Riser**, hay **Dramatic Dead-Air Silence** trước cú twist. | **LEMMiNO · Fern · Johnny Harris**: **Audio-Driven Editing** — 5 bản sắc nhạc nền (`investigative_pulse`, `kinetic_editorial`, `visceral_thriller`, `minimal_cinematic`, `clockwork_tension`) tự biến đổi cường độ theo tiến trình câu chuyện (`hook impact` → `tension build` → `riser` → `0.35s dead-air drop` trước twist → `loop tail`) + micro-foley theo loại beat (`paper_rustle`, `sub_drop`, `tape_stop`, `neural_pulse`, `heartbeat_build`). |
| **6** | **Mỗi video thiếu "Bản sắc Đạo diễn" (Director Archetype) riêng biệt** | Hiện mới xoay `style` (màu/font) và `narrative` (gợi ý văn bản lỏng lẻo), nhưng cấu trúc nhịp, góc máy, nhạc, chuyển cảnh và loại beat vẫn ra gần giống nhau. | **Studio Showrunner System (`director_archetype`)**: Khóa **6 Phong Cách Đạo Diễn Hoàn Chỉnh** (tự động ghép bộ 5 trục: *Narrative Arc + Beat Palette + 3D Camera Grammar + Transition Style + Music Mood*) để **mỗi video trên kênh có cảm giác như một tập phim được đạo diễn riêng**, không bao giờ bị trùng khuôn! |
| **7** | **QA chỉ đo kỹ thuật — chưa chặn được video "nhạt / giống PowerPoint / dễ tuột view"** | `qareport.py` kiểm OCR, LUFS, chồng chữ rất tốt nhưng không chấm điểm độ đặc sắc, tính đa dạng góc máy, mật độ "slide đơn điệu", hay sự tồn tại của Re-Hook & Audio Arc. | **Viral & Craft Scorecard (`vidlib/viralscore.py`)**: Tự động chấm điểm **0–100** trên 6 trục Viral & Craft ngay trong `linter.py` + `qa/report.md`, cảnh báo rõ nếu video có quá nhiều thẻ icon trống trơn, thiếu re-hook, lặp archetype hoặc thiếu nhịp âm thanh kịch tính! |

---

## 2. Sáu Phong Cách Đạo Diễn Viral (Director Archetypes — `config/archetypes.json`)

Thay vì để mọi video tự trôi về 1 khuôn giống nhau, tool chọn/xoay vòng **1 trong 6 Archetype Đạo Diễn** (lưu trong `storyboard.json → "archetype"` và ghi nhớ lịch sử `avoid_recent: 4` để 5 video liên tiếp không bao giờ giống nhau):

| Archetype ID | Tham chiếu Agency | Cấu trúc Kể chuyện (Arc) | Ngôn ngữ Hình ảnh chủ đạo | Nhịp Camera & Transition | Bản sắc Âm thanh (`music_mood`) | Kết thúc |
|---|---|---|---|---|---|---|
| **`visceral_anatomy`** | **Zack D. Films** | Cold-open cận cảnh cực đoan (0–2s) → chuỗi nhân-quả sinh lý 3 tầng (*But → Therefore*) → lật ngược → nối vòng | `xray_cutaway` + 3D `ecu_macro` / `tracking_low` + `story_hud` đo chỉ số cơ thể | Zoom xuyên (`push_through` / `iris_match`), góc thấp sát chủ thể | `visceral_thriller` + `sub_drop` + `heartbeat_build` | **`seamless_loop`** (0s outro tĩnh) |
| **`forensic_dossier`** | **LEMMiNO · Fern** | Nêu nghịch lý có thật → mở hồ sơ bằng chứng #1, #2 → phá vỡ giả thuyết phổ biến ở giây 14 → "smoking gun" | `dossier` (thẻ lưu trữ + highlight) + `graph` / `timeline` + 3D `low_hero` ánh đèn spotlight | `rack` focus, `whip_match`, `pan_r` chậm kiểu phim tài liệu | `investigative_pulse` + `paper_rustle` + `dead_air_drop` | **`seamless_loop`** hoặc `teaser_card` |
| **`editorial_clash`** | **Vox · Cleo Abram** | Đặt 2 lực đối lập ngay giây 0 → 3 hiệp so găng bằng dữ liệu thật (mỗi hiệp lật tỷ số) → cú chốt bất ngờ | `hero_stat` cỡ đại + `compare` (`race`/`split`) + `split` đồng hồ chung + 3D `over_shoulder` | `whip_match` dứt khoát, `pan_r`/`pan_l` đối xứng | `kinetic_editorial` + `click`/`ding` + `riser` | `teaser_card` hoặc **`seamless_loop`** |
| **`ticking_clock`** | **Fern · Kurzgesagt** | Đếm tiến theo mốc thời gian thực (`00:00 → 00:10 → 01:00 → 04:00`) → áp lực tích tụ → điểm vỡ (`breaking point`) | **`story_hud`** (đồng hồ/nhiệt độ/nhịp tim bám dính xuyên suốt mọi shot) + `xray_cutaway` + 3D `dolly_zoom` | `pan_r` tuyến tính tăng tốc dần, `scale_through` vào điểm vỡ | `clockwork_tension` (tick đồng bộ BPM + riser dâng dần) | **`seamless_loop`** |
| **`myth_autopsy`** | **Veritasium · Johnny Harris** | Khẳng định lầm tưởng phổ biến (0–2.5s) → **CẮT NGANG BẰNG `tape_stop` + PHẢN CHỨNG** → mổ xẻ cơ chế thật → cú twist sâu hơn | `hero_stat` / `fact:stamp` (phá vỡ) + `dossier` + `xray_cutaway` + 3D `low_hero` | `tape_stop` cắt đột ngột ở giây 3, rồi `dive` vào cơ chế | `minimal_cinematic` → ngắt `tape_stop` → chuyển sang `investigative_pulse` | **`seamless_loop`** |
| **`one_object_odyssey`** | **Ordinary Folk · Giant Ant** | Theo chân **1 chủ thể duy nhất** xuyên suốt 100% các shot qua các thế giới biến hóa liên tục | `scene` liền mạch + `xray_cutaway` + 3D `tracking_low` (cùng 1 Hero màu & hình khối) | **Match Cut (`iris_match` / `whip_match`)** nối liên tiếp như cú máy 1-shot | `minimal_cinematic` + `swish_match` foley mượt | **`seamless_loop`** |

---

## 3. Phân chia 7 Gói Việc (Work Packages: `WP-0` → `WP-6`) cho Sub-Agents

**Quy chuẩn kế thừa Vòng 12 (TUYỆT ĐỐI KHÔNG PHÁ VỠ):**
- Giữ nguyên **Sacred 3-Zone Grid** (`header 250–370`, `stage 390–1240`, `captions 1340–1460`), `studio_clean` Zone C clearance, Visual Budget, đồng bộ 2D↔3D editorial, và **0 lỗi chồng chữ (`overlapPairs() == []`)**.
- **Tất định 100%** (không `Math.random()`, không clock thực); **tương thích ngược 100%** với mọi dự án cũ & toàn bộ test còn hiệu lực (`ruff check .` = 0 lỗi).
- **Quản trị Git chuẩn Agency:** Đóng gói **stage + commit + push theo từng PR nhỏ, gọn, có kiểm định độc lập trước khi push** (chi tiết ở mục 6).

---

### WP-0 — Dọn Sạch File Thừa, Script Chết & Quy Trình Lỗi Thời (Repo Hygiene)
**File / thư mục sở hữu độc quyền:**
- `.gitignore`, `.DS_Store`, `projects/.DS_Store`
- `scripts/` (các script 1 lần / không còn tham chiếu)
- `qa/` (dọn file sinh ra/tạm bị track trong git, giữ `qa/visreg/` làm baseline test)
- `docs/` (gọn hoá tài liệu cũ/thừa không còn dùng)
- `studio.py` (chỉ gỡ các lệnh/quy trình chết đã không còn dùng, giữ nguyên các lệnh chính & test pass)

**Kiểm kê thực tế đã quét trong repo (bắt buộc rà soát tham chiếu `git grep` trước khi xoá để 0 vỡ test):**
1. **Xoá hẳn script chết & script chạy 1 lần trong `scripts/`:**
   - `scripts/atlas_receiver.py` *(0 tham chiếu code, 0 tham chiếu docs — chết hoàn toàn)*
   - Các script nhập/kiểm 1 lần các vòng cũ nếu không được `studio.py` hay `tests/` gọi: `scripts/atlas_clip_save.py`, `scripts/atlas_extract.py`, `scripts/atlas_frames.py`, `scripts/verify_partc.py`, `scripts/ui_before_after.py`, `scripts/ui_shots.py`, `scripts/vendor_demo.py` *(kiểm tra `git grep` trước khi `git rm`, nếu test nào tham chiếu thì cập nhật hoặc giữ đúng phần cần)*.
2. **Dọn rác bị track trong `qa/` (hiện 229 file ảnh/tạm bị track trong git!) & siết `.gitignore`:**
   - Gỡ khỏi git (`git rm -r --cached` + xoá thư mục tạm cục bộ) toàn bộ 21 file `qa/looks2d/_work/` và các ảnh kiểm lịch sử vòng cũ (`qa/ui/`, `qa/ui10/`, `qa/assets3d/`, `qa/looks2d/`, `qa/sources/`, `qa/html/`, `qa/props3d/`, `qa/retro90/`, `qa/beats2d/`, `qa/physics/`, `qa/icons/`, `qa/creatures/`, `qa/manim/`, `qa/_*.jpg`, `qa/atlas-*.png`, `qa/part-c.*`, `qa/smoke.md`, `qa/style-compare.*`, `qa/styles-gallery.png`).
   - **GIỮ NGUYÊN `qa/visreg/`** (baseline cho `scripts/visual_regression.py` & tests) và ảnh nghiệm thu hiện hành `qa/round12/` / `qa/round13/` (hoặc gitignore `qa/**/_work/` và toàn bộ file tạm `.DS_Store`).
   - Xoá `.DS_Store` và `projects/.DS_Store`.
3. **Dọn quy trình & lệnh thừa trong `studio.py` + rà soát module/config chết:**
   - Rà soát `studio.py` (gỡ 2 lệnh chết `setup`/`looks` đã ghi nhận trong `docs/CLEANUP_PLAN.md` và các nhánh/quy trình legacy không còn dùng sau khi kiểm chứng không có test nào phụ thuộc; cập nhật help text của `studio.py` cho gọn sạch).
   - Quét `vidlib/` & `engines/` để phát hiện hàm/file thừa không còn được gọi ở bất kỳ đâu (loại bỏ dead code an toàn, không chạm các module đang dùng).
4. **Tinh gọn thư mục `docs/` (hiện 46 file lịch sử chồng chéo):**
   - Xoá hoặc gom gọn các báo cáo/audit cũ đã lỗi thời (`docs/perf.json`, `docs/perf_board.json`, `docs/perf_engines.json`, `docs/charsheet_*.jpg`, `docs/ROUND10_PROMPT.md`, `docs/RUN_REPORT.md`, `docs/UI_AUDIT.md`, `docs/STYLE_AUDIT.md`, `docs/MOTION_AUDIT.md`, `docs/3D_ATLAS_ANALYSIS.md`, `docs/BLENDER_MCP.md`, `docs/CLEANUP_PLAN.md`, `docs/round10/`, `docs/archive/`) — chỉ giữ lại bộ tài liệu sống gọn đẹp: `ARCHITECTURE.md`, `DESIGN_SYSTEM.md`, `DECISIONS.md`, `CHANGELOG.md`, `CREDITS.md`, `ROUND12_REPORT.md`, `ROUND13_PROMPT.md`, `ROUND13_REPORT.md`.

**Tiêu chí nghiệm thu WP-0:**
- Repo sạch bóng file tạm/script chết/quy trình thừa; số file track trong `qa/` giảm từ 229 xuống chỉ còn baseline cần thiết; `.gitignore` chặn triệt để `qa/**/_work/` và `.DS_Store`.
- `python -m ruff check .`, `python -m unittest discover -s tests -t .`, `python -m vidlib.motionplan check` **pass 100%** sau khi dọn!

---

### WP-1 — Hệ 4 Beat Điện Ảnh Mới & Persistent Story HUD (Engine 2D HTML)
**File sở hữu độc quyền:**
- `engines/html/beats.js`
- `engines/html/core.js`
- `engines/html/looks.js`
- `engines/html/__init__.py`

**Yêu cầu chi tiết:**
1. **Thêm 3 Beat Điện Ảnh Cao Cấp vào `engines/html/beats.js` & đăng ký schema trong `engines/html/__init__.py`:**
   - **`dossier`** *(kiểu LEMMiNO · Johnny Harris · Fern)*:
     - `params`: `{ tag, stamp, headline, evidence: [{k, v}], highlight, visual_icon?, cite? }`
     - Vẽ khung hồ sơ lưu trữ tinh xảo (viền mảnh `1.5px`, góc chữ thập kỹ thuật, lớp nền thẻ tối phân cấp sáng tinh tế `#141820`, nhãn dấu mốc `tag` mono ở góc trên, đường kẻ chia dữ liệu sắc nét, vệt bút dạ quang quét ngang từ khóa `highlight` đồng bộ nhịp `u`, tùy chọn đóng dấu `stamp` như `"VERIFIED"` / `"BUSTED"`). Toàn bộ dùng **Flow Layout động** trong Zone B (`y: 390–1240`), `overlapPairs() == []`.
   - **`xray_cutaway`** *(kiểu Zack D. Films · Fern)*:
     - `params`: `{ shell_icon, core_icon, flow: [{from: [x,y], to: [x,y], via?: [x,y], count, color_role, speed}], pulse_rate?, callout_num?, callout_label? }`
     - Vẽ lớp vỏ cơ thể/vật thể mờ kiểu X-ray blueprint (nét viền sáng mỏng + lưới quét scanline nhẹ) ôm lấy cơ quan/lõi hoạt động sáng rực bên trong, kết hợp **hệ dòng chảy hạt (`flow_particles`) chạy dọc đường cong Bézier mượt mà tất định** (máu, xung thần kinh, luồng nhiệt, oxy, năng lượng) + 1 cụm số liệu telemetry tối giản ở mép.
   - **`hero_stat`** *(kiểu Cleo Abram · Vox · Ordinary Folk)*:
     - `params`: `{ number, prefix?, suffix?, unit?, label, sub_bar?: {from, to}, bg_motif?: "rings"|"bars"|"grid"|"wave", role? }`
     - Typography kiến trúc cỡ cực đại (`180–240px`, tự `fitText` không bao giờ tràn biên) kết hợp hình nền đồ họa toàn khung phản ứng động theo giá trị số (vòng sóng đồng tâm lan tỏa, cột năng lượng dâng, hoặc sóng dao động) + thanh so sánh mảnh phía dưới. Chấm dứt cảm giác chữ nhỏ trống trải!
2. **Hệ `story_hud` (Persistent Story Thread xuyên suốt nhiều shot) trong `core.js`:**
   - Hỗ trợ trường tùy chọn `JOB.story_hud` (từ storyboard top-level hoặc từng shot): `{ kind: "clock"|"temp"|"bpm"|"meter"|"chapter", label, from, to, unit, progress_from, progress_to, role }`.
   - Vẽ 1 thanh telemetry siêu mảnh, sang trọng kiểu phim tài liệu ở đúng **Zone A (`y: 260–310`)** (1 dòng gọn: chấm sáng nhịp + nhãn + số chạy liên tục từ `from → to` + thanh tiến trình mỏng 3px), **tự né mọi `kicker`/`title`** và không bao giờ va chạm `overlapPairs()`.
3. **Chiều sâu điện ảnh (Atmospheric Craft) trong `looks.js` & `core.js`:**
   - Bổ sung lớp ánh sáng sân khấu tinh tế (`editorialStageGlow`: radial spotlight rất mềm phía sau chủ thể + film grain siêu mịn tất định 2% + khung định vị biên tập nhẹ ở 4 góc) cho các look người lớn (`vox`, `flat`, `swiss`, `hud`, `iso`) để khung hình có chiều sâu như After Effects thay vì nền đen phẳng trống rỗng.

**Tiêu chí nghiệm thu WP-1:**
- Cả 3 beat mới (`dossier`, `xray_cutaway`, `hero_stat`) + `story_hud` render đẹp trên `vox-editorial-black` & `swiss-motion-black`, `overlapPairs() == []` và 0 lấn Zone C (`y ≤ 1280`).
- Cập nhật `engines/html/demo.json` (nếu cần) hoặc xuất contact sheet riêng `qa/round13/cinema_beats.jpg`.

---

### WP-2 — Điện Ảnh 3D Chuẩn Fern / Zack D. Films (Lighting + Camera Grammar)
**File sở hữu độc quyền:**
- `engines/three/main.js`
- `engines/three/scenes/stage.js`
- `engines/three/props.js`
- `styles/vox-editorial-black.json`

**Yêu cầu chi tiết:**
1. **Khử nền xám bệt & Nâng cấp Ánh sáng Điện ảnh (`engines/three/main.js` & `styles/vox-editorial-black.json`):**
   - Sửa lỗi nền dark-mode bị ACES tone mapping đẩy lên thành xám sáng `#4A5566` ở preset `clay` (`vox-editorial-black`): tách rõ màu nền sâu dark-mode (`scene.background` luôn giữ tối sâu `#0B0E14` sau tone mapping bằng cách bù gamma/linear hoặc render sky-gradient tối sâu + vignette cạnh), tăng độ tương phản **Key + Rim Light sắc cạnh** (tách rõ viền nhân vật khỏi nền tối như Fern / Blender Cycles).
   - Thêm **Volumetric Spotlight Cone** tùy chọn (`set_opts.spotlight: true` hoặc mặc định cho `stadium`, `diorama`, `black` ở chế độ `editorial`): hình nón ánh sáng mờ mềm chiếu từ trên xuống chủ thể (AdditiveBlending, `userData.noFrame = true` để không lệch `Box3`!).
2. **5 Góc Máy Điện Ảnh Mới & Quỹ Đạo Động (`engines/three/scenes/stage.js`):**
   - Bổ sung 5 preset camera vào `PRESETS` trong `stage.js` (vẫn tôn trọng `footroom` Zone C và `boxNoFx`):
     - `ecu_macro`: cận cảnh cực sát (`margin: 0.78`, `fov: 32`, `elev: 8`, `azim: 18`, `push: 0.14`) — cho hook/chi tiết kịch tính kiểu Zack D. Films.
     - `low_hero`: góc thấp ngước lên (`elev: 4`, `azim: -24`, `fov: 35`, `orbit: 10`, `push: 0.12`) — tôn dáng nhân vật uy lực kiểu Fern.
     - `tracking_low`: máy chạy thấp ngang hông/đầu gối bám theo nhân vật (`elev: 7`, `azim: 42`, `margin: 0.92`, `orbit: 5`).
     - `over_shoulder`: góc qua vai nhìn về đích/đối thủ (`elev: 12`, `azim: -48`, `fov: 36`, `push: 0.10`).
     - `dolly_zoom`: hiệu ứng Vertigo — đồng thời đẩy camera gần lại và mở rộng `fov` (`fov: 30 → 44`, `push: 0.22`) cho khoảnh khắc căng thẳng / twist!
   - Tự động luân phiên góc máy khác nhau giữa các shot 3D trong cùng 1 video nếu storyboard không ép `frame.preset` (không bao giờ 2 cảnh 3D dùng y hệt 1 góc `diorama`).
3. **Chất liệu mặt đất & phản xạ mềm (`engines/three/props.js`):**
   - Nâng cấp `stadium` và `diorama` thêm viền sáng mềm ở đường chân trời (rim edge glow), độ sâu tối dần về mép sàn, và dải vạch đích / cột đèn studio tinh tế hơn.

**Tiêu chí nghiệm thu WP-2:**
- Ảnh đối chiếu 5 góc máy điện ảnh + ánh sáng volumetric dark-mode sâu (không nền xám bệt) lưu tại `qa/round13/cinema_3d.jpg`.
- Toàn bộ test cũ (`test_retro3d.py`, `test_round12.py`, `test_three*`) pass 100%.

---

### WP-3 — Match Cuts, Chuyển Cảnh Agency & Seamless Loop Engine
**File sở hữu độc quyền:**
- `vidlib/render.py`
- `vidlib/spine.py`
- `vidlib/pipeline.py` (chỉ phần xử lý `transition_in` mở rộng, `story_hud` injection, và `outro.mode == "loop"`)
- `vidlib/timeline.py`

**Yêu cầu chi tiết:**
1. **3 Chuyển cảnh Agency mới trong `vidlib/render.py` (chạy mượt giữa mọi engine `html ↔ three ↔ Flow`):**
   - **`iris_match`** *(Scale-Through Match Cut kiểu Ordinary Folk / Zack D. Films)*: 6–8 frame cuối shot A tăng tốc zoom vào tâm chủ thể (`1.0 → 1.45×`) kèm radial glow/blur nhẹ → cắt đúng đỉnh tốc độ → 6 frame đầu shot B bung từ `0.84 → 1.0×` giảm tốc mượt (`easeOutCubic`), tạo cảm giác lao xuyên qua vật thể sang thế giới bên trong!
   - **`whip_match`** *(Directional Momentum Whip kiểu Giant Ant / Cleo Abram)*: trượt đẩy ngang cực nhanh có motion-blur định hướng (`6 frame`, giữ cùng chiều chuyển động giữa 2 shot) thay vì `dip` đen ngắt nhịp.
   - **`tape_stop`** *(Pattern Interrupt kiểu Veritasium / Johnny Harris)*: 4 frame hãm tốc/rung nhẹ + flash khung tương phản sắc gọn dành riêng cho cú lật tẩy `myth_autopsy` hoặc re-hook giữa video!
2. **Chế độ `seamless_loop` (Vòng lặp không dấu nối — AVD > 100%):**
   - Hỗ trợ `"outro": {"mode": "loop", "bridge_frames": 8}` trong `storyboard.json` & `pipeline.py`:
     - Bỏ qua thẻ outro tĩnh *"Follow for more"* khi `outro.mode == "loop"`.
     - Trong `render.py`: pha trộn mượt 6–8 frame cuối cùng của shot cuối (`C_last`) nối về frame 0 của `C01` (cross-motion / subtle zoom bridge) để khi YouTube Shorts / TikTok / Reels tự lặp lại, **hình ảnh và câu nói cuối khớp liền mạch về giây 0 không hề khựng!**
3. **Truyền `story_hud` & Archetype Moves (`vidlib/pipeline.py` & `vidlib/spine.py`):**
   - `pipeline.py` đọc `sb.get("story_hud")` (nếu có) và tự động tính nội suy `progress_from`, `progress_to`, `from`, `to` theo thời gian thực của từng shot rồi tiêm vào `job.json` của mỗi shot code (cả 2D và 3D overlay!).
   - `spine.py` ưu tiên tập chuyển động khớp với `archetype` được chọn.

**Tiêu chí nghiệm thu WP-3:**
- Video dùng `outro.mode: "loop"` render sạch không cần thẻ outro tĩnh, độ lệch màu/chuyển động giữa frame cuối và frame 0 mượt mà; `iris_match`, `whip_match`, `tape_stop` đều chạy tất định không lỗi.

---

### WP-4 — Audio-Driven Editing: 5 Mood Nhạc Điện Ảnh & Tension Arc SFX
**File sở hữu độc quyền:**
- `vidlib/musicgen.py`
- `vidlib/sfx.py`
- `vidlib/audio.py`

**Yêu cầu chi tiết:**
1. **Nâng cấp `vidlib/musicgen.py` từ 1 vòng lặp cố định lên 5 Bản Sắc Nhạc Điện Ảnh (`mood`):**
   - Giữ tương thích ngược 100% chữ ký `bed(duration, stop_at=None, bpm=112, seed=7, mood="kinetic_editorial", cue_times=None)`.
   - 5 mood khác biệt rõ rệt về hòa âm, nhạc cụ tổng hợp và cấu trúc năng lượng:
     1. **`investigative_pulse`** *(LEMMiNO · Fern)*: bass synth tối sâu (D minor), nhịp pulse 1/8 tinh tế, pad atmospheric mở rộng dần, không snare ồn ào.
     2. **`kinetic_editorial`** *(Vox · Cleo Abram)*: marimba/plucked synth sáng thông minh (C major / A minor hiện đại), percussion gọn sắc.
     3. **`visceral_thriller`** *(Zack D. Films)*: sub-drone căng thẳng, nhịp mạch đập (heartbeat-like kick), âm cao kim loại lạnh.
     4. **`clockwork_tension`** *(Fern · Kurzgesagt)*: tiếng tích-tắc đồng hồ đồng bộ BPM + hợp âm dâng dần cường độ theo thời gian (escalation swell).
     5. **`minimal_cinematic`** *(Johnny Harris · Ordinary Folk)*: piano điện tối giản ấm áp + chuỗi hợp âm cảm xúc tinh tế, thoáng tai.
   - **Dynamic Energy Curve**: nhạc nền tự động biến đổi mật độ nhạc cụ theo cấu trúc shot (`hook`: gọn sắc → `setup`: mở thoáng → `escalate`: thêm tầng nhịp/arpeggio → trước `twist`: **Dramatic Dead-Air Drop `0.35s`** cắt sạch nhạc rồi thả drone trầm sâu!).
2. **Bổ sung Bộ SFX Agency mới vào `vidlib/sfx.py`:**
   - Thêm các âm thanh tổng hợp sạch, tất định, có trọng lượng điện ảnh:
     - `sub_drop` (cú rơi sub-bass 90Hz → 32Hz cho Hook frame 0 & cú chốt Payoff)
     - `riser_long` (âm dâng căng thẳng 1.8s dùng trước `payoff`/`twist`)
     - `tape_stop` (tiếng phanh băng từ hãm tốc đột ngột cho cú lật tẩy `myth_autopsy` / Re-Hook)
     - `paper_rustle` (micro-foley giấy/hồ sơ cho beat `dossier`)
     - `neural_pulse` (xung điện/sinh học mềm cho beat `xray_cutaway`)
     - `swish_match` (tiếng lướt không khí mượt cho `iris_match` / `whip_match`)
3. **Tự động hóa Audio Tension Arc trong `vidlib/audio.py`:**
   - Chọn `mood` tự động theo `archetype` (hoặc style).
   - Tự động đặt `sub_drop` ở hook (nếu chưa có impact), `riser_long` kết thúc ngay trước `payoff`/`twist`, `swish_match` đúng tại các chuyển cảnh `iris_match`/`whip_match`, `tape_stop` tại chuyển cảnh `tape_stop`, `paper_rustle` khi vào `dossier`, `neural_pulse` khi vào `xray_cutaway` — biến âm thanh thành "keo dán cảm xúc" thực thụ!

**Tiêu chí nghiệm thu WP-4:**
- 5 mood trong `musicgen.py` tạo ra 5 phổ âm thanh khác biệt hoàn toàn (kiểm chứng bằng unit test năng lượng/phổ & tính tất định).
- 6 SFX mới sinh sạch, không clip (`peak ≤ 0.98`), loudness tổng thể vẫn giữ chuẩn `-14 ± 1 LUFS`, `TP ≤ -1 dBTP`.

---

### WP-5 — Bộ Não Kể Chuyện Viral (Archetypes, "But/Therefore", Re-Hook & Anti-Sameness Brief)
**File sở hữu độc quyền:**
- `config/archetypes.json` *(mới)*
- `config/narratives.json`
- `vidlib/narratives.py`
- `vidlib/brief.py`
- `prompts/storyboard_brief.md`
- `prompts/storyboard_schema.json`
- `config/channel.json` (chỉ thêm block `viral` & cập nhật danh sách transition/outro modes hợp lệ)

**Yêu cầu chi tiết:**
1. **Tạo `config/archetypes.json` + Resolver trong `vidlib/narratives.py`:**
   - Khai báo đầy đủ 6 Director Archetypes ở mục 2 (`visceral_anatomy`, `forensic_dossier`, `editorial_clash`, `ticking_clock`, `myth_autopsy`, `one_object_odyssey`), mỗi archetype gồm: `name`, `reference_studios`, `arc_rules`, `required_beats`, `camera_presets`, `transitions`, `music_mood`, `outro_mode`, `tags`, `avoid_recent: 4`.
   - Thêm hàm `plan_archetype(topic, slug, want=None, idea=None)` tự động xoay vòng theo lịch sử kênh để **không bao giờ có 2 video liên tiếp trùng phong cách đạo diễn**.
2. **Nâng cấp `prompts/storyboard_brief.md` & `vidlib/brief.py` — Viết kịch bản như Biên kịch Agency Viral:**
   - Nhúng trực tiếp **5 Luật Viết Kịch Bản Viral Bắt Buộc**:
     1. **Cold-Open Paradox (0–2s)**: Cấm mở bài giáo khoa; frame 0 phải là hình ảnh cực đoan/nghịch lý đang diễn ra.
     2. **Luật "But / Therefore" (Cấm liệt kê "And then")**: Mọi chuyển đoạn giữa các shot phải có lực đẩy nhân-quả hoặc tương phản (*"Yet..."*, *"Instead..."*, *"Which forces..."*, *"Until..."*, *"Except..."*).
     3. **Mid-Video Re-Hook (Giây 12–16)**: Bắt buộc có 1 cú đảo chiều hoặc mở vòng tò mò mới ngay giữa video kèm đổi engine/chuyển cảnh mạnh (`iris_match` / `tape_stop` / `whip_match`).
     4. **Visual Craft Diversity (Chống PowerPoint)**: Ít nhất **40% số shot** phải là cảnh giàu chiều sâu (`dossier`, `xray_cutaway`, `hero_stat`, `stage` 3D điện ảnh với góc máy đa dạng, hoặc `scene` có hoạt cảnh nhiều tầng); **cấm có > 2 shot liên tiếp cùng kiểu thẻ phẳng đơn điệu**.
     5. **Seamless Loop Option**: Khi `archetype` yêu cầu `seamless_loop`, viết câu cuối (`C_last`) sao cho dẫn mạch tư duy/ngữ pháp nối mượt về câu mở đầu `C01` (không dùng thẻ *"Follow for more"*).
   - Bổ sung hướng dẫn khai báo `archetype`, `story_hud`, 3 beat mới (`dossier`, `xray_cutaway`, `hero_stat`), 5 góc máy 3D mới, và 3 chuyển cảnh mới (`iris_match`, `whip_match`, `tape_stop`) vào `storyboard_schema.json` & `brief.py`.

**Tiêu chí nghiệm thu WP-5:**
- `plan_archetype` tự động xoay 6 phong cách khác nhau qua 6 chủ đề chạy bộ/khoa học liên tiếp.
- `brief.build(...)` xuất trọn bộ luật Viral + Archetype + 3 beat mới + 5 góc máy 3D + `story_hud` một cách mạch lạc, rõ ràng.

---

### WP-6 — Viral & Craft Scorecard, Kiểm Thử Toàn Diện & Nâng Cấp Đối Chiếu Video Viral Thật
**File sở hữu độc quyền:**
- `vidlib/viralscore.py` *(mới)*
- `vidlib/linter.py`
- `vidlib/motionplan.py`
- `vidlib/qareport.py`
- `tests/test_round13.py` *(mới)*
- `docs/ROUND13_REPORT.md` *(mới)*

**Yêu cầu chi tiết:**
1. **Tạo `vidlib/viralscore.py` — Hệ thống Chấm Điểm Viral & Craft (0–100):**
   - Hàm `score_storyboard(sb, history=None)` trả về `{total, grade, axes: {hook_loop, narrative_freshness, visual_craft, camera_matchcut, audio_tension, retention_pacing}, suggestions[]}`:
     - **`hook_loop` (0–20)**: hook ngắn gọn ≤ 2.4s, không mở bài nhạt, điểm cộng cho `seamless_loop` hoặc cold-open visual action.
     - **`narrative_freshness` (0–15)**: có `archetype` riêng, không trùng khung xương > 55% với 4 video gần nhất, có từ nối tương phản/nhân-quả (*but, yet, instead, until, except, because, so, forces, triggers*) và re-hook giữa video.
     - **`visual_craft` (0–25)**: tỉ lệ shot giàu chiều sâu (`dossier`, `xray_cutaway`, `hero_stat`, `stage`, `scene` có nhiều actor/fx, hoặc có `story_hud`) ≥ 50%; trừ điểm mạnh nếu > 40% là thẻ đơn điệu lặp lại.
     - **`camera_matchcut` (0–15)**: có ít nhất 2 góc máy 3D khác nhau (nếu có ≥ 2 shot 3D) và có chuyển cảnh chủ đích (`iris_match`, `whip_match`, `tape_stop`, `match`, `whip`).
     - **`audio_tension` (0–15)**: có hook impact + escalation/riser + mood âm nhạc khớp archetype + cú ngắt/twist rõ ràng.
     - **`retention_pacing` (0–10)**: thời lượng shot 2.2–4.0s, nhịp ~3.0 wps, giữ sạch Visual Budget Vòng 12.
   - Tích hợp báo cáo **Viral & Craft Scorecard** vào `vidlib/qareport.py` (mục `## Điểm Viral & Craft (Agency Scorecard)` trong `qa/report.md` & `qa/report.html`) và cảnh báo nhẹ trong `linter.py` nếu điểm `< 75/100`.
2. **Cập nhật `vidlib/motionplan.py` & `vidlib/linter.py`:**
   - Nhận diện 3 beat mới (`dossier`, `xray_cutaway`, `hero_stat`) là `mechanism_scenes` hợp lệ, nhận diện 3 transition mới (`iris_match`, `whip_match`, `tape_stop`), 5 góc máy 3D mới, `outro.mode == "loop"`, và trường `archetype` + `story_hud` trong validator/linter.
3. **Bộ kiểm thử tự động `tests/test_round13.py`:**
   - Test 3 beat mới (`dossier`, `xray_cutaway`, `hero_stat`) + `story_hud` render không lỗi, `overlapPairs() == []`, không lấn Zone C.
   - Test 5 mood nhạc `musicgen.py` khác nhau rõ rệt + 6 SFX mới không clip.
   - Test 3 transition mới (`iris_match`, `whip_match`, `tape_stop`) và chế độ `seamless_loop`.
   - Test 6 Director Archetypes xoay vòng chống lặp + `viralscore.py` phân biệt rõ kịch bản PowerPoint nhạt (< 60 điểm) vs kịch bản Agency Viral (≥ 85 điểm).
4. **Kiểm chứng Thực Tế End-to-End (2 Video KHÁC BIỆT HOÀN TOÀN về Archetype):**
   - **Thử nghiệm 1 (Nâng cấp đối chiếu "Before vs After Vòng 13"):** Dựng phiên bản Vòng 13 cho **`your-mouth-can-feed-your-brain`** (hoặc tạo bản `v2` theo archetype **`visceral_anatomy` / `forensic_dossier`** — dùng `dossier`, `xray_cutaway` dòng tín hiệu thần kinh sống động, `hero_stat` `+2.9%`, 3D `low_hero` & `tracking_low` có volumetric spotlight, `iris_match` + `tape_stop`, nhạc `investigative_pulse`, và **`seamless_loop`** — **tái sử dụng `audio/vo.mp3` ElevenLabs sẵn có nếu giữ nguyên lời hoặc sinh mới khi chủ kênh yêu cầu**).
   - **Thử nghiệm 2 (Video thứ 2 hoàn toàn khác bản sắc):** Chọn 1 chủ đề mới trong `ideas/run/ideas.json` (ví dụ *"Your Body Runs Out Of Heat First"* — điểm **9.8**) dựng theo archetype **`ticking_clock`** (có **`story_hud` đồng hồ + nhiệt độ lõi tăng liên tục `37.2°C → 40.8°C`** xuyên suốt các shot, 3D `dolly_zoom` + `heat` gắn thân, nhạc `clockwork_tension`, `dry-run`) để chứng minh **2 video liền kề mang 2 linh hồn điện ảnh hoàn toàn khác nhau**, cả 2 đều đạt **Viral Score ≥ 85/100** và **QA 0 lỗi ĐỎ**!
   - Lưu trọn bộ ảnh soi trực quan vào `qa/round13/` (`cinema_beats.jpg`, `cinema_3d.jpg`, `viral_compare_two_archetypes.jpg`) và viết báo cáo tiếng Việt đầy đủ tại `docs/ROUND13_REPORT.md`.

---

## 4. Quy Chuẩn Kịch Bản Viral (Nhúng vào `prompts/storyboard_brief.md`)

Mọi kịch bản viết ra sau Vòng 13 phải vượt qua **"Bài test 3 Giây & Bài test Cuộn Lại"**:
1. **0–2s Cold Open**: Tuyệt đối không mở bằng câu giải thích khái niệm. Bắt đầu ngay bằng hành động/nghịch lý gây tò mò tức thì + `sub_drop`.
2. **Mạch "But / Therefore"**: Không được có 2 câu liền nhau chỉ nối kiểu *"Và rồi... Tiếp theo..."*. Mỗi shot phải **bẻ lái, nâng mức cược hoặc hé lộ tầng sâu hơn** của shot trước.
3. **Giây 12–16 Pattern Interrupt**: Phải có 1 cú đảo nhịp rõ rệt (đổi từ thế giới bên ngoài 3D → lặn sâu vào `xray_cutaway` hoặc lật `dossier` bằng chứng kèm `iris_match`/`tape_stop`).
4. **Show Inside the System**: Khi nói về cơ chế sinh lý/vật lý, dùng `xray_cutaway` (hạt dòng chảy chuyển động thực) hoặc 3D `ecu_macro`/`low_hero` — không dùng 1 icon đứng yên.
5. **Kết Vòng Lặp (Seamless Loop)**: Nếu dùng `outro.mode: "loop"`, câu chốt cuối cùng phải dẫn thẳng về câu mở đầu để khán giả xem sang vòng thứ 2 trong vô thức.

---

## 5. Phân quyền file & Giao thức tránh xung đột

| Gói việc | File sở hữu độc quyền | Không được chạm |
|---|---|---|
| **WP-0** | `.gitignore`, `scripts/` (script thừa), `qa/` (rác track), `docs/` (dọn tài liệu cũ), `studio.py` (lệnh chết) | `engines/*`, `vidlib/*` (trừ dead code đã xác minh 0 ref), `config/*` |
| **WP-1** | `engines/html/beats.js`, `engines/html/core.js`, `engines/html/looks.js`, `engines/html/__init__.py` | `engines/three/*`, `vidlib/render.py`, `vidlib/musicgen.py`, `vidlib/linter.py` |
| **WP-2** | `engines/three/main.js`, `engines/three/scenes/stage.js`, `engines/three/props.js`, `styles/vox-editorial-black.json` | `engines/html/*`, `vidlib/render.py`, `vidlib/audio.py` |
| **WP-3** | `vidlib/render.py`, `vidlib/spine.py`, `vidlib/pipeline.py`, `vidlib/timeline.py` | `engines/*`, `vidlib/musicgen.py`, `vidlib/brief.py` |
| **WP-4** | `vidlib/musicgen.py`, `vidlib/sfx.py`, `vidlib/audio.py` | `engines/*`, `vidlib/render.py`, `vidlib/qareport.py` |
| **WP-5** | `config/archetypes.json`, `config/narratives.json`, `vidlib/narratives.py`, `vidlib/brief.py`, `prompts/storyboard_brief.md`, `prompts/storyboard_schema.json`, `config/channel.json` | `engines/*`, `vidlib/render.py`, `vidlib/audio.py`, `vidlib/qareport.py` |
| **WP-6** | `vidlib/viralscore.py`, `vidlib/linter.py`, `vidlib/motionplan.py`, `vidlib/qareport.py`, `tests/test_round13.py`, `docs/ROUND13_REPORT.md` | Các file thuộc WP-0..WP-5 (chỉ đọc/tích hợp) |

**Giao thức phối hợp:**
- **Đợt 0 (chốt nền + dọn sạch trước):** Đóng **PR-01** (commit/push thay đổi Vòng 12 đang clean) → chạy **`WP-0`** dọn file thừa/quy trình thừa, verify test 100%, đóng **PR-02**.
- **Đợt 1 (song song):** Chạy đồng thời `WP-1`, `WP-2`, `WP-4`, `WP-5`.
- **Đợt 2 (song song sau Đợt 1):** Chạy `WP-3` (nối `story_hud` của WP-1, `archetype` của WP-5, SFX chuyển cảnh của WP-4) và `WP-6` (nối toàn bộ beat/camera/transition/archetype vào `viralscore`, `linter`, `motionplan`, `qareport` và test).
- **Bước cuối (Orchestrator):** Chạy toàn bộ kiểm định (`ruff`, `unittest`, `motionplan check`, `html_sheet.py`), dựng ảnh `qa/round13/*.jpg`, render 2 video khác archetype, **tự soi từng ảnh bằng mắt**, rồi **stage + commit + push từng PR nhỏ** theo mục 6.

---

## 6. Quy Trình Git & Small-PR Chuẩn Studio / Agency (Stage + Commit + Push)

Remote GitHub hiện tại: `origin = https://github.com/TaiThanhhhh/forward_studio.git` (nhánh chính `main`; máy chưa cài `gh` CLI).
Mọi thay đổi **KHÔNG gom vào 1 commit khổng lồ** — phải tách thành **chuỗi PR nhỏ gọn, nguyên tử (Atomic Small PRs)** chuẩn agency lớn (**Conventional Commits**, mỗi PR ≤ 1 trách nhiệm rõ ràng, chạy `ruff + unittest + motionplan check` xanh 100% trước khi push):

| Thứ tự PR | Nhánh đề xuất | Commit message (Conventional Commits) | Phạm vi độc lập |
|---|---|---|---|
| **PR-01** | `feat/round12-studio-standard` | `feat(studio): round 12 adult editorial, 3-zone grid, studio_clean captions & red overlap QA gate` | Toàn bộ thay đổi Vòng 12 đã nghiệm thu (WP-1..WP-6 Vòng 12 + `tests/test_round12.py` + `docs/ROUND12_REPORT.md`) |
| **PR-02** | `chore/cleanup-dead-files-and-workflows` | `chore(repo): prune dead scripts, obsolete workflows, stale docs and tracked qa temp artifacts` | **WP-0**: dọn file thừa, script chết, lệnh chết `studio.py`, rác track `qa/`, cập nhật `.gitignore` |
| **PR-03** | `feat/r13-2d-cinema-beats-and-story-hud` | `feat(html): add dossier, xray_cutaway, hero_stat beats and persistent story_hud` | **WP-1**: 3 beat điện ảnh 2D + `story_hud` + atmospheric craft |
| **PR-04** | `feat/r13-3d-cinema-lighting-and-cameras` | `feat(three): deep dark-mode lighting, volumetric spotlight and 5 cinematic camera presets` | **WP-2**: 3D dark-mode sâu, volumetric spotlight, 5 góc máy điện ảnh |
| **PR-05** | `feat/r13-matchcuts-and-seamless-loop` | `feat(render): add iris_match, whip_match, tape_stop transitions and seamless loop outro` | **WP-3**: chuyển cảnh agency + chế độ `outro.mode: loop` + tiêm `story_hud` |
| **PR-06** | `feat/r13-audio-tension-and-music-moods` | `feat(audio): add 5 cinematic music moods, 6 agency SFX and automatic tension arc` | **WP-4**: 5 mood nhạc + 6 SFX mới + dead-air drop trước twist |
| **PR-07** | `feat/r13-viral-director-archetypes` | `feat(story): add 6 viral director archetypes, but/therefore brief and re-hook rules` | **WP-5**: `config/archetypes.json` + xoay vòng archetype + nâng cấp brief/schema |
| **PR-08** | `feat/r13-viral-scorecard-and-verification` | `feat(qa): add viral & craft scorecard, round 13 tests and dual-archetype verification` | **WP-6**: `vidlib/viralscore.py` + tích hợp linter/qareport + `tests/test_round13.py` + `docs/ROUND13_REPORT.md` |

**Giao thức thực thi cho TỪNG PR:**
1. Tạo nhánh sạch từ `main` (`git checkout -b <branch>`), chỉ `git add` đúng các file thuộc phạm vi PR đó (tuyệt đối không stage `.env`, `projects/*`, file tạm).
2. Chạy cổng xanh bắt buộc trước commit: `python -m ruff check . && python -m unittest discover -s tests -t . && python -m vidlib.motionplan check`.
3. `git commit` với tiêu đề Conventional Commit + body tóm tắt rõ *Why / What / Verified*.
4. `git push -u origin <branch>` và (nếu chủ kênh muốn cập nhật thẳng `main` theo từng PR) merge `--no-ff` vào `main` + `git push origin main` sau mỗi PR, hoặc giữ nhánh mở và in sẵn link tạo PR GitHub `https://github.com/TaiThanhhhh/forward_studio/compare/main...<branch>?expand=1` kèm mô tả PR chuyên nghiệp!

---

## 7. Định nghĩa "Hoàn thành" (Definition of Done)

Nhiệm vụ Vòng 13 chỉ được tính là **XONG** khi đạt **100%** các tiêu chí sau:
1. **Repo sạch gọn (`WP-0`):** Đã xoá toàn bộ file thừa, script chết, quy trình lỗi thời và rác track trong `qa/`; `git status` sạch sẽ, không lọt `.env` hay file tạm.
2. `python -m ruff check .` → **0 lỗi**.
3. `python -m unittest discover -s tests -t .` → **100% pass** (toàn bộ test hiện có + `tests/test_round13.py`).
4. `python -m vidlib.motionplan check` → **0 lỗi**.
5. **0 lỗi chồng chữ (`overlapPairs == []`)** & **0 lấn Zone C** trên toàn bộ 18 beat HTML (15 beat cũ + 3 beat điện ảnh mới `dossier`, `xray_cutaway`, `hero_stat`) kể cả khi bật `story_hud`.
6. **3D Điện ảnh (`qa/round13/cinema_3d.jpg`)**: nền dark-mode sâu (không còn xám bệt), có volumetric spotlight & 5 góc máy điện ảnh khác biệt rõ rệt.
7. **Audio-Driven Tension**: 5 mood nhạc khác nhau rõ rệt + 6 SFX mới + tự động bơm tension arc (hook sub-drop, riser, dead-air drop trước twist).
8. **Đã render & soi trực quan 2 video mang 2 Archetype hoàn toàn khác nhau**: cả 2 đạt **QA 0 lỗi ĐỎ** và **Viral & Craft Score ≥ 85/100**, ảnh đối chiếu lưu tại `qa/round13/`, báo cáo đầy đủ tại `docs/ROUND13_REPORT.md`.
9. **Đã stage + commit + push đầy đủ 8 PR nhỏ gọn (PR-01 → PR-08)** lên `origin` theo đúng chuẩn Conventional Commits, kèm báo cáo danh sách nhánh/commit/PR cho chủ kênh.
