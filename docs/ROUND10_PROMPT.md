# Vòng 10 — prompt cho Opus 5.5 (effort xhigh)

> **90s low poly + bộ "10 style viral", motion có chiều sâu và không lặp, kho dữ liệu lớn hơn, hybrid 2D ↔ 3D.**
> Prompt này viết cho Claude Opus 5.5 chạy effort **xhigh** trong repo `studio` (kênh "forward."). Một agent điều phối
> (orchestrator) đọc toàn bộ file. Mỗi sub agent đọc toàn bộ file nhưng chỉ làm **gói việc (WP) của mình**, theo mục 5
> (phân quyền file). Người làm đọc tiếng Việt; khán giả đọc/nghe tiếng Anh.

---

## 0. Đọc trước khi động vào code

1. `CLAUDE.md` (luật kênh, bản đồ code, lệnh, quy ước) — **luật trong đó thắng mọi thứ trong file này**.
2. `docs/ARCHITECTURE.md` (4 tầng, quy tắc phụ thuộc, "thêm một thứ mới").
3. `.claude/skills/black-lab-toon/SKILL.md` (cách làm video của kênh).
4. Phần code của WP mình (mục 4) — đọc trọn file trước khi sửa, không đoán API.
5. Bộ nhớ chủ kênh (đã chốt, phải tôn trọng):
   - **Làm tổng quát, không one-off**: mọi tính năng chạy cho MỌI video sau này, điều khiển bằng dữ liệu
     (storyboard/config); video mẫu chỉ là phép thử, kiểm bằng một chủ đề KHÁC.
   - **Mỗi video khác nhau**: style theo chủ đề, giọng khác nhau, có ngày Flow có ngày toàn code; style mới phải vào cơ
     chế tự chọn + xoay vòng (`vidlib/styles.py plan`), có `tags`, `voice_tags`, khối `html`.
   - **"Làm luôn" = làm trọn** (code + test + tài liệu + ảnh kiểm). Chỉ dừng hỏi khi đổi chuẩn chung của cả kênh,
     đụng style Atlas, hoặc commit/push.

## 1. Bối cảnh đã kiểm tra (20/11/2026)

### 1.1 Ảnh tham chiếu
Bài "10 Claude animation styles (made to go viral)": 1 Soft 3D · 2 Flat cartoon · 3 Line art · 4 Halftone print ·
5 16-bit pixel · 6 Ink silhouette · 7 Vintage comic · 8 8-bit sprite · 9 Paper cutout · **10 90s low poly** (đang chọn).
Khung mẫu của #10: chú chó dachshund cam đang hít hoa trên bãi cỏ. Đặc điểm nhìn thấy:
- hình học **ít đa giác** nhưng **đổ bóng Gouraud mượt** theo đỉnh (không phải mặt phẳng gắt kiểu low-poly hiện đại);
- màu bão hoà, cam/xanh lá/xanh trời kiểu console cuối thập niên 90 (N64/PS1);
- chi tiết mặt **vẽ trên texture** (mắt trắng có chấm sáng, lông mày, miệng cười, mũi đen bóng), texture độ phân giải
  thấp được lọc mờ (bilinear);
- đồ vật rời rạc kiểu sprite/mesh đơn giản (cụm cỏ, bông hoa vàng), đồi xa mềm, sương xa;
- **không có nét viền**; nhân vật có cảm xúc, hành động nhỏ đời thường (hít, vẫy đuôi).

### 1.2 Tool đã có style nào trong 10 style đó

| # | Style trong ảnh | Trạng thái | Đang có gì | Thiếu gì |
|---|---|---|---|---|
| 1 | Soft 3D | **Có** | `clay3d-black` (look3d `clay`), `atlas-soft-clay`, `atlas-inflated`, `plastic-toy3d-black` | — |
| 2 | Flat cartoon | **Một phần** | `flat-vector-black`, `sticker-explainer-black` (look html `flat`/`sticker`) | không có **nhân vật hoạt hình 2D** (người/con vật có mặt, biểu cảm, đi/chạy) — chỉ có icon |
| 3 | Line art | **Có** | `line-boil-black` (`boil`), `sketchnote-black` (`sketch`), `ink` | — (xem lại có cần look nét đơn sạch không) |
| 4 | Halftone print | **Chưa** | — | look chấm Ben-Day/CMYK, lệch bản in |
| 5 | 16-bit pixel | **Chưa** | — | look pixel 16-bit (độ phân giải thấp, bảng màu giới hạn, dither) |
| 6 | Ink silhouette | **Chưa** | `ink` chỉ là kiểu chữ; `atlas-ink-and-toon` là 3D toon | bóng đen trên nền sáng có giới hạn (rối bóng) |
| 7 | Vintage comic | **Một phần** | `comic` (chữ Bangers + look `flat`) | chấm Ben-Day, khung tranh, bóng thoại, giấy ngả màu, lệch bản |
| 8 | 8-bit sprite | **Chưa** | — | look sprite 8-bit (≤4 màu/vật, chuyển động bậc) |
| 9 | Paper cutout | **Một phần** | `papercraft3d-black` (3D), `atlas-paper-pop-up`, `paper_cutout` (chỉ kiểu chữ + look `spy`) | cắt giấy 2D/2.5D nhiều lớp (multiplane), mép xé, nhịp stop-motion |
| 10 | 90s low poly | **Một phần** | `lowpoly3d-black`, `atlas-low-poly` = low-poly **hiện đại** (mặt phẳng gắt, nét viền) | Gouraud theo đỉnh, texture vẽ tay, độ phân giải/màu thời 90, rung đỉnh PS1, **nhân vật con vật có mặt**, bối cảnh (bãi cỏ) |

### 1.3 Bằng chứng motion bị lặp (5 video thật gần nhất)
Cả 5 video (`projects/*/storyboard.json`, trừ `_smoke-*`) đi theo **một khuôn**: `title` → `counter` → `compare` →
`scene` (icon trôi) → `fact`. Video "your-heart-rate…" có 4 `compare` + 3 `counter` trên 11 shot; "water-bottle" có
3 `title` + 3 `fact`. Nguyên nhân gốc (đã đọc code):
- `engines/html/__init__.py → LAYOUTS` chỉ 2–3 bố cục/beat; `codeshot.assign_layouts` chỉ tránh lặp **trong một video**,
  không nhớ video trước.
- `vidlib/brief.py → mix_help()` hướng LLM "numbers → counter/compare/graph" → beat chung chung thắng cơ chế riêng.
- Diễn viên 2D chỉ là **icon** trôi/nảy; không có nhân vật, không có động từ chuyển động (verb) theo nội dung
  (vd nhịp tim 157 bpm → tim đập đúng 157 nhịp/phút, vẽ điện tim; không phải con số chạy lên).
- 2D phẳng: không có lớp sâu (parallax/multiplane/DOF); 3D `stage` chỉ có mannequin người + ~54 đạo cụ, không có con
  vật, không có bối cảnh ngoài `black|lab|track`.
- Camera spine (`vidlib/spine.py MOVES`) ít kiểu bay; `config/narratives.json moves` giao với look nên hay ra cùng kiểu.

## 2. Mục tiêu và định nghĩa "xong"

Bốn trụ, tất cả **dạng tổng quát, chạy cho mọi chủ đề**:

1. **Style**: thêm các style còn thiếu của danh sách (giữ **sân khấu đen** của kênh), trong đó **`retro90-lowpoly-black`
   (90s low poly) là style chủ lực**. Mỗi style dùng được cho mọi beat của mọi engine liên quan, vào vòng tự chọn theo
   chủ đề.
2. **Motion có chiều sâu, không lặp giữa các video**: chuyển động gắn với **chi tiết nội dung** của từng video (giá trị,
   đơn vị, cơ chế thật), có lớp sâu, có nhớ lịch sử kênh để không lặp khuôn.
3. **Kho dữ liệu lớn hơn**: nhân vật/con vật 3D + 2D, mô hình 3D CC0, icon SVG có giấy phép rõ, thư viện "cơ chế hình
   ảnh" (metaphor), thư viện động từ chuyển động (verb), thêm bố cục/beat.
4. **Hybrid 2D ↔ 3D**: 2D trong 3D (thẻ/sprite/cắt giấy đặt trong không gian 3D, có ánh sáng/DOF), 3D trong 2D (lớp 2D
   bám vật 3D: nhãn, mũi tên, chart), và hậu kỳ 3D theo look 2D (pixel/halftone/rối bóng) để một video trộn engine vẫn
   cùng một look.

**Xong** khi: mọi WP qua tiêu chí nghiệm thu của nó · `python -m unittest discover -s tests -t .` xanh ·
`python -m ruff check .` sạch · `python scripts/smoke.py` qua mọi đường dựng · có ảnh kiểm trong `qa/` cho từng tính
năng · tài liệu (CLAUDE.md, HUONG_DAN.md, SKILL.md, CHANGELOG, ARCHITECTURE, CREDITS) cập nhật · một video demo dry-run
bằng `retro90-lowpoly-black` trên **chủ đề mới** chạy hết pipeline tới cổng QA · báo cáo tiếng Việt.

## 3. Luật bất biến (vi phạm = làm lại)

- **Sân khấu đen**: nền khung hình `#000`, tôn trọng `black_min` của style và QA. Bãi cỏ/bầu trời của ảnh tham chiếu
  KHÔNG phủ kín khung: làm dạng **đảo nổi / diorama** giữa khoảng đen, sương tan vào đen. Biến thể nền sáng toàn khung
  là **đổi chuẩn kênh** → không làm, chỉ ghi vào báo cáo cho chủ kênh quyết.
- **Không thêm engine thứ năm** (three · html · manim · board). Hybrid là chế độ của engine có sẵn (cùng trang Edge),
  đi qua `engines/adapter.py`.
- **Tất định**: mỗi frame là hàm thuần của số frame (+ dữ liệu job). Không `Math.random()`/thời gian thực; dùng
  `hash(...)` có hạt giống. Worker nào render frame nào cũng ra cùng ảnh (RESUME + render song song dựa vào điều này).
  Animation glTF: `mixer.setTime(f / fps)`, không `update(delta)` cộng dồn.
- **Không frame đứng yên ≥ 4 frame** (creep/trôi/thở). Chữ khán giả thấy: tiếng Anh, đi qua `text_fx`/chữ trong cảnh;
  OCR QA phải đọc được (`text_crops`).
- **Giấy phép**: chỉ tự dùng tài sản **CC0 / MIT / ISC / BSD / Apache-2.0**. CC-BY chỉ khi ghi công đầy đủ vào
  `docs/CREDITS.md` + `rights/ledger.json` và đánh dấu trong index; **không** dùng NC/ND/không rõ giấy phép/"free for
  personal use". Kiểm giấy phép **trên trang gốc** lúc tải, lưu URL + văn bản giấy phép + SHA-256. Không tải ảnh người
  thật, không vẽ lại logo/thương hiệu, không nhân vật có bản quyền (không Mario/Crash/Pikachu… — chỉ "phong cách thời
  90", nhân vật tự dựng).
- Repo vòng 7 trong `vendor/` chỉ đọc; không cài skill/plugin ngoài; mã bên thứ ba mới vào `vendor/<tên>/` + ghi
  `vendor/SOURCES.json` + `scripts/vendor_fetch.py` dựng lại được. three.js đang là **r160** (WebGL) — addon phải đúng
  r160 (`RetroPassNode` của three bản mới là TSL/WebGPU, KHÔNG dùng được; tự viết pass tương đương).
- Cấu hình không hard-code trong module: tham số đưa vào `styles/*.json`, `config/*.json`. JSON ghi qua
  `common.save_json`. Engine không đọc storyboard, chỉ nhận `job.json`; engine không tự quét đĩa — Python đổi tên tài
  sản thành URL/dữ liệu lúc dựng job (như `lottie_url` trong `engines/html/media.js`).
- Màu engine board: hex qua `engines/board/color.py`. Video tiếng Việt cũ không render lại.
- Không sửa vùng an toàn Instagram (đang chờ chủ kênh quyết). Không đổi snapshot prompt trừ khi đổi prompt là chủ ý
  (`UPDATE_SNAPSHOTS=1` chỉ khi đó, ghi lý do).
- **Không** `git commit/push/stash/checkout/reset/clean`, không xoá file mình không tạo. Chủ kênh tự commit.

## 4. Gói việc

Mỗi WP: **file sở hữu** (chỉ mình sửa) · **file chung** (sửa nhỏ theo giao thức mục 5) · yêu cầu · nghiệm thu.
Ảnh kiểm của WP để trong `qa/<thư mục WP>/`. Mỗi WP viết `docs/round10/<WP>.md` (tiếng Việt): làm gì, API/schema mới,
file đã sửa, cách kiểm, việc còn dở. Không sửa CLAUDE.md/HUONG_DAN.md/SKILL.md/CHANGELOG — để WP-I gom.

### WP-T — 3D thời 90 + nhân vật con vật 3D + bối cảnh (engine three)
**Sở hữu**: `engines/three/main.js`, `props.js`, `cast.js`, `paint.js`, `engines/three/creatures.js` (mới),
`engines/three/retro.js` (mới, nếu tách pass), `engines/three/scenes/stage.js` (trừ móc `model:` của WP-A),
`scripts/props3d_sheet.py`, `styles/retro90-lowpoly-black.json`, `tests/test_retro3d.py`, `qa/retro90/`, `qa/creatures/`.

1. **Look 3D `retro90`** (N64, mặc định) và **`psx`** (PS1) trong `LOOK3D`, đều là dữ liệu (ghi đè được trong
   `world.look3d`):
   - chiếu sáng **Gouraud theo đỉnh** (tính ánh sáng ở vertex shader, nội suy màu) — r160 `MeshLambertMaterial` đã là
     per-fragment nên phải tự làm (onBeforeCompile hoặc ShaderMaterial), có `ambient`, 1–2 đèn hướng, `spec` nhẹ tuỳ chọn;
   - hình học ít đỉnh (`facet`/số segment thấp) nhưng pháp tuyến mượt; `ink_px: 0` (thời 90 không có viền);
   - texture vẽ bằng code độ phân giải thấp (64–128 px) — `filter: bilinear` (N64) | `nearest` (PS1);
   - pass hậu kỳ: render nội bộ thấp `res_div` (N64 ≈ 2–3 + upscale mượt; PS1 ≈ 3–4 + nearest), lượng tử màu
     `color_bits` (PS1 15-bit) + **Bayer dither** `dither`, **rung đỉnh** `wobble` (snap toạ độ màn hình theo lưới,
     chỉ phụ thuộc hình học + camera → tất định), `affine` (méo texture, tuỳ chọn), sương `fog` tan vào **đen**;
   - grain nhân theo độ sáng như look khác → nền vẫn `#000`.
2. **Kho nhân vật 3D** `creatures.js` — sinh **thủ tục từ bảng dữ liệu loài** (không tải mô hình): ≥ 18 loài
   (dog, dachshund, cat, fox, wolf, bear, rabbit, mouse, pig, cow, horse, sheep, chicken, penguin, fish, frog, turtle,
   dino) + `kid`/`adult` hai chân có mặt (người chung chung, không người thật). Mỗi loài = tỉ lệ thân/đầu/chân, kiểu
   tai/đuôi/mõm, màu theo vai palette (đổi được bằng `color`). **Mặt vẽ trên texture** (mắt có chấm sáng, lông mày,
   miệng) với ≥ 7 biểu cảm (neutral happy shock sad angry sleepy sniff), chớp mắt tất định. Dáng đi/hành động là hàm
   thuần của frame: idle(thở) walk trot run sniff sit jump wag eat sleep fall + `look` (quay đầu nhìn điểm), chuyển động
   phụ (tai/đuôi trễ pha — follow-through). Chạy được trong MỌI look3d (toon/clay/…/retro90/psx).
   Prop `stage`: `{type: "creature", species, gait, expr, look:[x,y,z], color, keys:[{u, gait, expr, at, rot…}]}` +
   bí danh `dog`, `cat`… Cập nhật **khối chú thích đầu `stage.js`** (đó là nguồn sự thật mà brief đọc).
3. **Bối cảnh** (`set`) mới, mọi mép tan vào đen: `meadow` (đảo cỏ nổi: cụm cỏ, hoa, đá, đồi xa mờ dần), `tabletop`
   (mặt bàn/góc phòng), `street` (một đoạn phố low-poly). Tham số `set_opts` (r, màu, mật độ hoa…). Đạo cụ cũ vẫn đứng
   đúng trên mặt (như `BASE` của `lab`).
4. `styles/retro90-lowpoly-black.json` đủ trường như các style `*-black` (xem `lowpoly3d-black.json`): `world.look3d`
   = `retro90`, palette bão hoà thời 90 trên đen, `tags` (animal, pet, dog, cat, nostalgia, retro, gaming, childhood,
   nature, farm, zoo, cartoon…), `voice_tags`, `html` (tạm `flat`; WP-I đổi sang look pixel khi WP-H1 xong), `flow`
   (`is_3d`, mô tả "late-1990s console low-poly 3D" bằng lời của mình), `not`, `pacing`, `sfx_pack`, `music`,
   `thumbnail`, `black_min`, `code_engine: "three"`.
5. **Nghiệm thu**: contact sheet `qa/retro90/` (cùng cảnh ở `lowpoly` vs `retro90` vs `psx`) và `qa/creatures/`
   (mọi loài × 3 hành động × 2 look) ở 1080×1920; một cảnh `stage` "chó dachshund hít hoa trên `meadow`" giống tinh thần
   ảnh tham chiếu (liệt kê từng đặc điểm mục 1.1 và nói đạt/chưa); khoảng đen quanh đảo đạt `black_min`; render 2 lần
   cùng frame bằng 2 worker → giống hệt; ghi s/frame. Test: `retro90`/`psx` có trong LOOK3D (Python đọc từ main.js như
   `test_hybrid.look3d_kinds`), bảng loài đọc được từ Python (như `adapter.stage_physics_errors` đọc từ vựng physics.js),
   validate prop creature (loài/gait/expr sai → lỗi có gợi ý).

### WP-H1 — Look 2D mới + nhân vật hoạt hình 2D (engine html: look/bút/hậu kỳ)
**Sở hữu**: `engines/html/looks.js`, `engines/html/core.js`, `engines/html/rig2d.js` (mới), `engines/html/icons.js`,
`engines/html/icons_channel.js`, `scripts/html_sheet.py`, 6 style JSON dưới đây, `tests/test_looks2d.py`, `qa/looks2d/`.

1. Look mới trong `looks.js` (mỗi look = token + hành vi bút + hậu kỳ; tự áp cho cả 11 beat và mọi beat mới):
   - `halftone` — tô bằng chấm Ben-Day/CMYK theo góc tram, lệch bản nhẹ, nét mực; chấm chỉ trong hình, nền đen.
   - `comic` (vintage comic) — mực dày, 4 màu phẳng + Ben-Day, **khung tranh** và **bóng thoại/hộp chú thích** cho
     nhãn, giấy ngả vàng CHỈ trong khung, lệch bản, fx kiểu "Kirby dots"/tia tốc độ.
   - `pixel16` — render vào buffer thấp (≈ 1/5–1/6), lượng tử về bảng ≤ 64 màu sinh từ palette style, Bayer dither,
     upscale nearest, chuyển động snap theo lưới pixel.
   - `sprite8` — ≈ 1/8–1/10, ràng buộc kiểu NES: ≤ 4 màu/vật (kể cả đen), viền 1px, hoạt hoạ bậc (on 2s/3s), rung màn.
   - `silhouette` (ink silhouette) — mọi diễn viên là bóng đen đặc trước **đĩa/dải sáng giới hạn** (trăng, hoàng hôn,
     đèn chiếu), viền sáng mảnh, khớp kiểu rối bóng; chữ màu sáng trên vùng sáng; vẫn đạt `black_min`.
   - `cutout` (paper cutout 2D) — vân giấy, mép xé/răng cưa, bóng đổ theo độ sâu lớp, nhịp stop-motion (on 2s) + lệch
     nhẹ tất định từng frame.
   - Xem lại `boil`/`sketch`: nếu chưa có "line art" nét đơn sạch không tô, thêm `lineart`.
   Hậu kỳ tổng quát trong `core.js` (`post.pixel {div, colors, dither}`, `post.halftone {cell, angle, cmyk}`,
   `post.misregister`, `post.paper`), thứ tự cố định, tất định. **Chữ phải đọc được**: chọn rõ chữ vẽ trước hay sau pass
   pixel/halftone (font pixel chỉ khi có giấy phép OFL/CC0, để trong `assets/fonts/` + CREDITS) và giữ `text_crops`
   cho OCR. Cập nhật `engines/html/__init__.py → LOOKS` là việc của WP-H2 — ghi tên look mới vào `docs/round10/H1.md`;
   WP-I sẽ thêm (hoặc WP-H2 thêm nếu đã có).
2. **Kho nhân vật 2D** `rig2d.js`: nhân vật/con vật hoạt hình **sinh ra primitive** giống icon (để bút của look tự biến
   chúng thành pixel/halftone/bóng đen…): ≥ 12 loài (dog cat bird fish rabbit bear fox mouse frog cow pig horse) + người
   chung chung (kid/adult, vài kiểu tóc/áo theo vai màu). Biểu cảm ≥ 6, hành động (idle walk run jump point cheer sit
   sniff sleep eat fall) là hàm thuần của frame, chớp mắt + thở. Gọi bằng tên icon `"rig:<loài>"` (+ tham số
   `action/expr/face`) qua `iconFor`/đường vẽ icon hiện có để mọi beat dùng được ngay. Python đọc danh sách loài (một
   nguồn sự thật, test đối chiếu như icon).
3. 6 style JSON (đủ trường như `flat-vector-black.json`, `code_engine: "html"`, `world` 3D tối thiểu để shot 3D không
   lệch tông, `tags` rõ): `halftone-print-black`, `vintage-comic-black`, `pixel16-black`, `sprite8-black`,
   `ink-silhouette-black`, `paper-cutout-black`. Không xoá style cũ `comic`/`paper_cutout`/`ink`.
4. **Nghiệm thu**: `scripts/html_sheet.py <style>` cho từng style mới × mọi beat → `qa/looks2d/`; sheet nhân vật 2D
   (mọi loài × hành động × 3 look) ; OCR đọc được chữ ở mọi look (dùng `vidlib/ocr.py`); `black_min` đạt; tất định
   (render lại = cùng hash); thời gian/frame không tăng quá 40% so với `flat` (ghi số).

### WP-H2 — Beat/bố cục mới + chiều sâu 2D (engine html: beats)
**Sở hữu**: `engines/html/beats.js`, `engines/html/__init__.py`, `engines/html/demo.json`, `tests/test_beats_depth.py`,
`qa/beats2d/`.

1. **Bố cục mới**, mục tiêu **≥ 5 bố cục/beat** cho title/counter/compare/fact/process (hiện 2–3), ví dụ:
   counter `odometer` · `flap` (bảng lật) · `units` (isotype: số đơn vị THẬT tích dần, nhóm theo 10/100) · `gauge`;
   compare `race` (hai diễn viên chạy quãng tỉ lệ) · `units` · `stack` (chồng vật theo chiều cao) · `overlay`;
   title `kinetic` (chữ động từng từ) · `reveal`; fact `flip` · `quote`; process `loop` (vòng tuần hoàn) · `nest`
   (zoom lồng: vĩ mô → vi mô).
2. **Beat mới (≥ 4)**, có `PARAMS` + validate + mô tả một dòng cho brief: `units` (biểu đồ đơn vị đứng riêng) ·
   `timeline` (trục thời gian, camera đi dọc sự kiện) · `split` (chia đôi màn hình, hai hành động đồng bộ) · `meter`
   (đồng hồ vật lý bất kỳ: pin, bình, nhiệt kế, **điện tim theo bpm thật**) · tuỳ chọn `zoomin` (powers-of-ten theo dữ
   liệu).
3. **Chuyển động do dữ liệu lái**: giá trị quyết định nhịp/biên độ (bpm → tim đập đúng nhịp; % → mức đầy; tốc độ →
   quãng chạy), `hit` vẫn khớp từ khoá VO.
4. **Chiều sâu 2D** trong `scene` (và các beat dùng diễn viên): diễn viên có `z` → parallax theo camera, scale phối
   cảnh, **DOF** (mờ theo khoảng cách), tối dần theo không khí; lớp nền/tiền cảnh tự sinh theo look (bụi, mảnh xa, vật
   lướt qua tiền cảnh che khuất), hạt giống theo video; camera `scene` có thể dolly/truck/roll
   (`camera: [{u, x, y, z, rot}]`). Chi phí render thêm ≤ 30%.
5. Nhận động từ chuyển động (`verb`) trong keys của diễn viên khi `lib/motion` có API của WP-M — viết lớp kiểm có/không
   (feature-detect) để không phụ thuộc thứ tự xong việc.
6. **Nghiệm thu**: `html.validate` cho mọi beat/bố cục mới; `LAYOUTS` ≥ 5/beat (test); contact sheet từng bố cục +
   beat mới → `qa/beats2d/`; motiongate không chặn; tất định.

### WP-M — Bộ não motion: động từ chuyển động, kho cơ chế, chống lặp giữa video
**Sở hữu**: `lib/motion/**`, `vidlib/motionplan.py` (mới), `config/metaphors.json` (mới), khối `motion` trong
`config/channel.json`, `vidlib/spine.py`, `vidlib/motiongate.py`, `vidlib/brief.py`, `vidlib/linter.py`,
`prompts/storyboard_brief.md` + `prompts/storyboard_schema.json` + `prompts/blocks/`, `docs/MOTION_AUDIT.md`,
`tests/test_motion_depth.py`. **Chung**: `vidlib/codeshot.py` (chỉ phần `assign_layouts`), `vidlib/narratives.py`.

1. `docs/MOTION_AUDIT.md`: đo 5 video thật (chuỗi beat, bố cục, kiểu bay spine, kiểu vào, số verb khác nhau, ma trận
   giống nhau giữa video) → nguyên nhân gốc → chỉ số mục tiêu.
2. **Động từ chuyển động** trong `lib/motion` (JS + Python **cùng API**, test đối chiếu như `tests/test_motion_lib.py`):
   ≥ 30 verb chia nhóm vào (pop, drop-bounce, slide-overshoot, unfold, draw-on, iris, typewriter, assemble, grow-from,
   shatter-in…) · nhấn (pulse, shake, squash, wobble, jiggle, heartbeat(bpm), flip, flash, ripple…) · ra (fly-off,
   fall-away, dissolve, fold…) · phụ/nghỉ (breathe, float, sway, follow-through…), + mẫu so le (cascade, center-out,
   edges-in, wave, seeded-random). API thuần: `verb(name, t, args) → {x,y,z,sx,sy,sz,rot,alpha,glow,blur}`. Từ vựng
   xuất ra cho brief + validate.
3. **Kho cơ chế hình ảnh** `config/metaphors.json` ≥ 150 mục (khái niệm → cơ chế cụ thể), phủ mảng kênh (cơ thể/sức
   khoẻ/chạy, tập tạ, gaming/tech, AI, phòng thí nghiệm, thiên nhiên/con vật, vũ trụ, tiền/thời gian, giấc ngủ, ăn
   uống…). Mỗi mục: `id`, `keywords` (tiếng Anh, có dạng gốc), `mechanism` (tiếng Anh cho LLM), `recipe` (engine + cảnh/
   beat + khung params chỉ dùng tên CÓ THẬT), `verbs`, `depth` (lớp nào ở đâu), `avoid` (sáo mòn). Test: mọi tên trong
   recipe tồn tại trong từ vựng engine thật (beat/PARAMS html, prop/icon của stage, verb của lib/motion, loài của
   creatures/rig2d khi đã có — feature-detect).
4. `vidlib/motionplan.py`: khớp kho cơ chế với ý tưởng + từng câu VO/beat (khớp cả dạng gốc như `styles.py`); **chữ ký
   motion** mỗi video (beat, bố cục, verb, cơ chế, kiểu bay, engine, look) → `projects/<slug>/work/motion_signature.json`;
   lịch sử kênh N video gần nhất (bỏ `_smoke-*`); chấm điểm để **tránh lặp giữa video** (bố cục, kiểu bay, cơ chế);
   `assign_layouts` dùng lịch sử kênh chứ không chỉ trong video; chỉ số "khuôn" (tỉ lệ beat chung chung
   title/counter/compare/fact, độ giống khung xương với video gần nhất).
5. Cấu hình `config/channel.json → motion`: `avoid_recent`, `generic_max_share` (vd 0.45), `min_mechanism_shots`
   (vd 3), `skeleton_sim_max` (vd 0.6), `metaphors_top_k`. Linter **cảnh báo** (không chặn cứng, trừ khi cấu hình bật)
   khi vượt ngưỡng, có gợi ý cơ chế thay thế.
6. Brief: viết lại `mix_help` thành **cơ chế trước, số liệu sau**; chèn "MECHANISM IDEAS FOR THIS TOPIC" (top-k cơ
   chế), "DO NOT REPEAT" (khung xương video gần nhất), từ vựng verb + `z`/chiều sâu + beat/bố cục mới (đọc động từ
   engine, không viết tay tên). Snapshot prompt: cập nhật có chủ ý, ghi lý do.
7. `spine.py`: thêm ≥ 4 kiểu bay (vd `orbit_tilt`, `push_through` xuyên qua vật, `rack` đổi tiêu cự, `whip_rot`,
   `truck_parallax`) + chọn tránh kiểu bay video trước.
8. **Nghiệm thu**: chạy `motionplan` trên 5 video cũ → chỉ ra đúng khuôn lặp; tạo storyboard giả cho 2 chủ đề khác nhau →
   brief khác nhau rõ (in ra so sánh); test parity JS/Python cho mọi verb; test metaphors hợp lệ; test chống lặp
   (cùng chủ đề 2 lần liên tiếp → bố cục/kiểu bay/cơ chế khác).

### WP-A — Kho tài sản: mô hình 3D CC0 (glTF) + icon SVG có giấy phép
**Sở hữu**: `scripts/assets_fetch.py` (mới), `scripts/assets_sheet.py` (mới), `assets/lib/**` (mới),
`config/assets3d.json` (mới), `vidlib/assets3d.py` (mới), `engines/three/models.js` (mới), `vendor/three/addons/**`
(mới), `tests/test_assets3d.py`, `qa/assets3d/`, `qa/assetlib/`. **Chung** (sửa nhỏ): `vidlib/userassets.py`,
`vendor/SOURCES.json`, `scripts/vendor_fetch.py`, `docs/CREDITS.md`, `rights/ledger.json`, `docs/STYLE_AUDIT.md`,
`.gitignore`, `studio.py` (lệnh con `assets`), `vidlib/codeshot.py` (một móc gọi resolver), `engines/three/scenes/stage.js`
(một import + một nhánh `model:` + một dòng trong khối chú thích đầu file).

1. Vendor `GLTFLoader.js` (+ `BufferGeometryUtils`, `SkeletonUtils` nếu cần) **đúng tag r160** vào `vendor/three/addons/`,
   import map của `engines/three/index.html` trỏ được (`three/addons/`).
2. `models.js`: nạp glTF/GLB theo URL trong job (Python giải tên → URL, như `lottie_url`), clone đúng cách (skinned →
   SkeletonUtils), chuẩn hoá kích thước/đặt đáy ở y=0, **đổi chất liệu theo look3d hiện tại** (toon/clay/retro90…) và
   gán màu theo vai palette (gom màu gốc → vai), animation tất định `mixer.setTime`, chờ nạp xong trước `ready`.
   Prop: `{type: "model:<tên>", anim, anim_speed, anim_offset, keys}`.
3. Kho 3D: `scripts/assets_fetch.py` tải **từ nguồn chính thức** các gói **CC0** (Kenney — kenney.nl; Quaternius —
   quaternius.com; kiểm giấy phép trên trang gốc từng gói), ưu tiên glTF/GLB (gói chỉ có FBX/OBJ: bỏ qua hoặc chuyển đổi
   bằng công cụ có giấy phép rõ — ghi lại). Mục tiêu ≥ 150 mô hình: con vật có animation ≥ 20, người chung chung có
   animation ≥ 6, đồ ăn, nội thất, xe, thiên nhiên, đồ công nghệ, thể thao/tập luyện, phòng thí nghiệm. Index
   `config/assets3d.json` (tên, tags, keywords tiếng Anh, gói, giấy phép, URL, sha256, danh sách anim, bbox, vai màu).
   File nhị phân lớn: gitignore + dựng lại bằng script (ghi tổng dung lượng); index được commit.
4. `vidlib/assets3d.py`: nạp index, tìm theo từ khoá, `resolve(name)` → URL + meta, lỗi tên sai có gợi ý; móc vào lúc
   dựng job; `studio.py assets [search <q> | fetch | sheet | check]`.
5. Kho 2D: chọn lọc icon SVG giấy phép thoáng (vd Tabler MIT, Lucide ISC, Phosphor MIT — **kiểm giấy phép tại nguồn**),
   nhập hàng loạt qua đường nhập SVG có sẵn (SVGO + đo hình học trong Edge, `vidlib/userassets.py`) vào
   `assets/lib/svg/<gói>/` + index từ khoá; thứ tự tìm: icon kênh → SVG người dùng → SVG thư viện; mục tiêu thêm ≥ 500
   icon dùng được ở mọi look; sheet `qa/assetlib/`.
6. **Nghiệm thu**: `studio.py assets check` xanh (mọi mục có giấy phép trong danh sách cho phép, SHA khớp khi có file);
   `qa/assets3d/` sheet mỗi mô hình ở `toon` + `retro90`; một cảnh `stage` dùng ≥ 3 mô hình có animation chạy tất
   định (2 worker cùng frame = cùng ảnh); test resolver/validate.

### WP-X — Hybrid 2D ↔ 3D + nối verb vào engine (đợt 2, sau WP-T/H1/H2/M)
**Sở hữu**: `engines/three/hybrid.js` (mới), `tests/test_hybrid2d3d.py`, `qa/hybrid/`. **Chung**: `stage.js`,
`main.js`, `core.js`, `beats.js`, `engines/adapter.py`, `vidlib/codeshot.py`, `vidlib/brief.py`.

1. **2D trong 3D**: prop `card2d` {draw: icon | `rig:<loài>` | text | đoạn beat nhỏ, look (pixel/halftone/cutout/…),
   billboard, two_sided, thickness (giấy), cut_edge} — vẽ bằng bút html vào CanvasTexture **cập nhật mỗi frame** (2D động
   trong 3D), nhận ánh sáng/bóng/DOF của 3D. **Multiplane cắt giấy** (`layers` các thẻ ở z khác nhau, parallax + bóng thật)
   và **HD-2D** (sprite pixel trong thế giới 3D có ánh sáng/DOF).
2. **3D trong 2D / 2D bám 3D**: `overlay2d: [{beat|labels|arrows, params, z: "front"|"back"}]` trên shot `stage` —
   lớp html trong suốt ghép trước/sau khung 3D trong CÙNG trang; nhãn/mũi tên có `of: "<prop id>"` bám vị trí chiếu màn
   hình của prop 3D từng frame; `text_crops` vẫn đúng cho OCR.
3. **Hậu kỳ 3D theo look 2D**: `world.look3d.post` thêm `pixel`, `halftone`, `posterize`, `silhouette`, `paper` để shot
   3D trong style pixel16/sprite8/halftone/comic/silhouette/cutout cùng look với shot 2D; cập nhật `world` của 6 style
   WP-H1.
4. Nối **verb** của WP-M: `do: [{u, verb, dur, args}]` cho prop `stage` và `verb` trong keys diễn viên `scene` (nếu
   WP-H2 chưa nối).
5. Validate params mới trong `adapter`/`codeshot`; khối chú thích đầu `stage.js` cập nhật (brief tự đọc).
6. **Nghiệm thu**: `qa/hybrid/` — (a) chó retro90 3D + nhãn 2D bám mũi + chart 2D phía sau; (b) cắt giấy multiplane;
   (c) HD-2D sprite pixel trong bối cảnh 3D; (d) shot 3D trong style `halftone-print-black` đặt cạnh shot 2D cùng style;
   tất định; OCR đọc được; thời gian/frame ghi lại.

### WP-U — UI dễ dùng: không bao giờ phải mở source để copy/paste (song song đợt 1)
Chủ kênh (21/11): "app đã ok rồi nhưng hơi khó dùng, tôi phải tự vào source code để copy/paste cho đúng nơi". Đã kiểm:
`ui/server/app.py` **không có API ghi storyboard/ideas** — khi pipeline dừng ở `need_storyboard` (exit 2) / `need_ideas`
(exit 5) / `storyboard_invalid` (exit 3), người dùng phải mở `projects/<slug>/brief.md`, đưa cho AI, rồi tự dán JSON vào
`projects/<slug>/storyboard.json` hoặc `ideas/<lô>/ideas.json`; sửa một tham số shot (`code.params`, VO, `override.*`)
cũng phải mở JSON. `.env` chỉ có key ElevenLabs → nút `--ai claude|gemini` không chạy.
**Sở hữu**: `ui/**`, `tests/test_ui.py`, `docs/DESIGN_SYSTEM.md`, `docs/UI_AUDIT.md`, `ui/README.md`,
`vidlib/sbedit.py` (mới — sửa storyboard có kiểm). **Chung**: `studio.py` (lệnh con mới), `vidlib/storyboard.py` (chỉ thêm
hàm, không đổi schema).

1. **Nghiên cứu best practice của phần mềm lớn** (tra web, ghi `docs/research/UI_BEST_PRACTICES.md` ngắn, có nguồn):
   Adobe Premiere/After Effects (Properties panel, Essential Graphics: tham số mẫu lộ ra thành form), Figma UI3 (bảng
   thuộc tính theo ngữ cảnh, component props), Canva/CapCut (template + chỉnh trực tiếp), Descript (sửa video bằng sửa
   chữ), Frame.io (review theo timecode), Runway; hệ thiết kế Material 3 / Apple HIG / Fluent 2 (empty state có hành động
   kế tiếp, progressive disclosure, command palette, autosave + undo, xác thực tại chỗ, kéo-thả). Rút ra ≤ 12 nguyên tắc
   áp dụng được cho tool này, mỗi nguyên tắc → thay đổi cụ thể.
2. **Không copy/paste file**: kiến trúc giữ nguyên "UI chỉ chạy `studio.py` như job + đọc file" — thêm lệnh CLI có kiểm
   (vd `studio.py sb import <slug> <file|->`, `sb patch <slug> --shot C03 --set code.params.to=157`, `ideas import <lô>
   <file|->`) gọi `vidlib/sbedit.py` (normalize + validate + lint; sai → không ghi, trả lỗi có đường dẫn trường; đúng →
   ghi qua `save_json`, giữ bản cũ để hoàn tác) và UI gọi qua danh sách trắng job.
   - Bước "Cần storyboard / ideas": nút **Copy brief** (một cú), ô **Dán JSON từ AI** (kéo-thả file .json cũng được),
     kiểm tra tại chỗ hiển thị lỗi theo trường/dòng, **Lưu & chạy tiếp** tự chạy lại pipeline; nếu có key API → nút
     **AI viết giúp** (`--ai`); hướng dẫn ngắn dùng Claude Code (`/video <slug>`) có nút copy lệnh.
   - **Bảng thuộc tính shot** (kiểu Properties panel): sửa VO, thời lượng/hold, mode, style, `code.params` bằng **form sinh
     từ schema** (PARAMS html, khối chú thích `stage.js`, beat/bố cục/verb/loài mới của vòng 10 — đọc từ API catalog,
     feature-detect), có ô JSON nâng cao; **xem trước 1 frame** (job render still nhanh) trước khi render cả shot; undo.
   - Bước Flow: nút copy prompt từng shot + tải ảnh start/end frame, kéo-thả clip lên đúng thẻ shot (đã có upload — làm
     rõ trạng thái thiếu/đủ).
   - **Cài đặt key API** trong UI (ghi `.env`, không bao giờ hiển thị lại giá trị, chỉ "đã đặt/chưa đặt"; chỉ localhost).
   - Mỗi trạng thái dừng (exit 2/3/4/5/6/10/11/12) có **một thẻ "việc tiếp theo"** rõ ràng + nút làm ngay; không trạng thái
     nào bắt người dùng mở thư mục.
   - Thư viện: thêm tab xem style mới vòng 10, nhân vật/con vật, mô hình 3D, icon, kho cơ chế (đọc config khi có).
3. Bảo mật giữ nguyên chuẩn hiện có (Host/CSRF/danh sách trắng/không shell/chặn traversal); test mới trong
   `tests/test_ui.py` cho mọi API/lệnh mới; `scripts/ui_check.py --axe` 0 lỗi; ảnh trước/sau `qa/ui10/`.
4. **Nghiệm thu**: kịch bản e2e "tạo video từ ý tưởng → dán storyboard → sửa 1 tham số shot → xem trước → chạy tiếp tới
   cổng QA" làm được **chỉ bằng chuột trong UI** (`scripts/ui_e2e.py` mở rộng, dry-run); đếm số bước/số lần rời UI
   trước–sau ghi vào `docs/UI_AUDIT.md`.

### WP-C — Dọn file/quy trình dư (kiểm kê song song, áp dụng sau đợt 1)
Chủ kênh: "quy trình qua nhiều lần thử nghiệm quá nên có nhiều file/quy trình dư, tối ưu lại". **Sở hữu**:
`docs/CLEANUP_PLAN.md`, `docs/research/REPO_BEST_PRACTICES.md`, `docs/archive/` (mới). Áp dụng thay đổi lên file của WP
khác **chỉ sau khi WP đó xong** (orchestrator báo).

1. Nghiên cứu ngắn (có nguồn): cách các công ty lớn giữ repo/pipeline gọn — Google (code health, deprecation có hạn,
   một cách làm một việc), monorepo hygiene, ADR (quyết định kiến trúc), pipeline dựng kiểu DAG có cache theo nội dung
   (Bazel/Make), dọn artifact trung gian (GC), docs-as-code (một nguồn, tài liệu lỗi thời bị lưu trữ).
2. Kiểm kê có bằng chứng (grep tham chiếu, test, git log): tài liệu chồng chéo (`AUDIT*`, `PLAN`, `ROADMAP_V2`, `RUN_LOG`,
   `RUN_REPORT`, `BLOCKERS`, `DECISIONS`, `UI_AUDIT`…), launcher macOS `scripts/*.command`, script một lần
   (`verify_partc.py`, `build_audit_doc.py`, `ui_before_after.py`, `atlas_*`…), file sinh ra bị track trong git (`qa/` có
   134 file), style cũ chỉ-kiểu-chữ, mã chết (hàm/route/stage không ai gọi), CLAUDE.md mô tả lệch thực tế (vd bảng code ghi
   `ui/web/app/features/*` nhưng thực tế là `pages/`), stage/cổng chờ trùng việc, cache `work/` phình.
3. Phân loại: **xoá** (mã chết/file sinh lại được — `git rm`, không xoá file chưa track mà không sinh lại được) · **lưu trữ**
   (`docs/archive/`, có README chỉ mục) · **gộp** (một tài liệu một chủ đề) · **giữ** (lý do). Đề xuất quy trình gọn hơn
   (bớt bước tay, gộp cổng, lệnh `studio.py` nhất quán) kèm rủi ro.
4. Không xoá style đang trong vòng xoay, không đụng `projects/` của chủ kênh, không đổi chuẩn kênh. Mỗi thay đổi có
   test xanh trước/sau. **Nghiệm thu**: `docs/CLEANUP_PLAN.md` (bảng trước/sau: số file, số tài liệu, số lệnh, dung lượng
   repo) + thay đổi đã áp dụng + full test/ruff/smoke xanh.

### WP-I — Tích hợp, tài liệu, demo (orchestrator làm, đợt 3)
- `vidlib/styles.py PREFERENCE` + kiểm `plan()` chọn đúng style mới theo chủ đề (vd "dog", "8-bit", "comic"), không lặp;
  `studio.py styles --cards`, `styles --gallery`, `scripts/style_compare.py` cho style mới; đổi `html.look` của
  `retro90-lowpoly-black` sang look 2D hợp (pixel16/sprite8 hay flat — chọn theo ảnh kiểm).
- `engines/html/__init__.py LOOKS` có look mới; `scripts/smoke.py` qua; `scripts/visual_regression.py` (thêm golden cho
  tính năng mới, chỉ `--update` golden mới/đổi có chủ ý); full test + ruff.
- Tài liệu: CLAUDE.md (bản đồ code, lệnh mới), HUONG_DAN.md, SKILL.md, docs/ARCHITECTURE.md, CHANGELOG (vòng 10),
  CREDITS, STYLE_AUDIT; gom `docs/round10/*.md`.
- Demo: `python studio.py video "<chủ đề mới về con vật/hoài niệm>" --style retro90-lowpoly-black --dry-run …` chạy tới cổng
  QA; contact sheet; ghi kết quả thật (đỏ/vàng/xanh) — không tô hồng.
- Báo cáo tiếng Việt cho chủ kênh: đã làm / ảnh kiểm / số đo / việc chưa xong / **quyết định cần chủ kênh**
  (biến thể nền sáng toàn khung; gói CC-BY nếu có; commit).

## 5. Phối hợp nhiều agent trên CÙNG cây làm việc

- Không dùng worktree (cây làm việc có nhiều thay đổi chưa commit mà worktree không có).
- **Phân quyền file** theo mục 4. File "chung": đọc lại ngay trước MỖI lần Edit, sửa nhỏ đúng chỗ, không viết lại/định
  dạng lại cả file, không hoàn tác thay đổi của người khác; Edit báo file đã đổi → đọc lại rồi sửa lại.
- Không chạy lệnh ghi hàng loạt lên file của WP khác (formatter, `ruff --fix` toàn repo, `styles --cards` toàn bộ —
  việc của WP-I). `ruff check` chỉ trên file mình.
- Chỉ chạy test của mình + test liên quan trực tiếp; full suite để WP-I. Test của WP khác đang dở có thể đỏ — không sửa
  hộ, ghi vào báo cáo.
- Ảnh/video kiểm chỉ ghi vào `qa/<thư mục WP>/` hoặc scratchpad. Render nặng: đặt workers ≤ 2 để chừa GPU/CPU cho agent
  khác.
- Phụ thuộc API của WP khác chưa xong → feature-detect + stub, ghi rõ trong `docs/round10/<WP>.md`.
- Báo cáo cuối của agent (tiếng Việt, ≤ 40 dòng): đã làm · file đã sửa/tạo · API/schema mới · lệnh kiểm + kết quả thật
  · ảnh kiểm · việc dở/rủi ro · cần WP nào nối tiếp.

## 6. Nguồn tham khảo (đã tra, kiểm lại khi dùng)

- PS1/N64 trên three.js: [playshader-one](https://github.com/BucketOSoftware/playshader-one) (320×240, rung đỉnh,
  Gouraud, 16-bit + dither, affine — đọc ý tưởng, kiểm giấy phép trước khi chép bất cứ dòng nào) ·
  [Codrops: PS1 jitter shader](https://tympanus.net/codrops/2024/09/03/how-to-create-a-ps1-inspired-jitter-shader-with-react-three-fiber/) ·
  [gist PS1 ShaderMaterial](https://gist.github.com/bandinopla/497bcd86ba2bb662e0ab4cb47190748e) ·
  [three.js RetroPassNode](https://threejs.org/docs/pages/RetroPassNode.html) (chỉ tham khảo — bản TSL/WebGPU, không
  chạy trên r160) · [Godot PSX demo](https://github.com/MenacingMecha/godot-psx-style-demo) (mẹo: texture thấp, tắt
  lọc/mipmap).
- Tài sản CC0: [Kenney](https://kenney.nl/assets) (vd [Cube Pets](https://kenney.nl/assets/cube-pets), nhiều gói có
  glTF) · Quaternius (gói con vật có animation, CC0 trên
  [OpenGameArt](https://opengameart.org/content/lowpoly-animated-farm-animal-pack); kiểm định dạng glTF + giấy phép trên
  quaternius.com) · tránh gói CC-BY trừ khi ghi công đủ.
