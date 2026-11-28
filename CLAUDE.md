# CLAUDE.md — studio (kênh "forward.")

Tool sản xuất short "thí nghiệm" phong cách **darkmode** (nền tối — đen `#000` hoặc nền tối sâu có chiều sâu môi trường/bầu trời đêm tuỳ style, không nhất thiết đen tuyền 100%). Python 3.10+ · Pillow · numpy · OpenCV · ffmpeg · Playwright (điều khiển
Edge/Chromium headless cho engine code-shot; không Node lúc chạy, không Remotion).
**Kênh tiếng Anh**: mọi thứ khán giả THẤY/NGHE (VO, text_fx, nhãn trên bảng, outro, thumbnail, tiêu đề, mô tả, hashtag,
.srt) viết tiếng Anh tự nhiên. **Giao diện cho người làm** (trả lời, scripts.html, log, báo cáo QA) viết **tiếng Việt**.
Prompt Flow: tiếng Anh. Skill làm video: `.claude/skills/black-lab-toon/SKILL.md`. Hướng dẫn người dùng: `HUONG_DAN.md`.

**Trong repo này luôn dùng pipeline `/video`. Chỉ dùng mã của kaz-documentary qua engine `board` đã được tích hợp.**
Không gọi skill `kaz-documentary` (plugin cài trong Claude Code vẫn để đó): nó kích hoạt với câu "make a documentary
video" và có quy tắc xung đột với kênh (16:9, không hard cut, CRF 24, dùng ảnh người thật). `vendor/kaz-documentary/`
chỉ để tham khảo. Tương tự với mọi repo vòng 7 trong `vendor/` (lemo-opuscar, mg-styles-15, hyperframes, huashu-art-motion,
dashi-animationstyle, anything2explainer, claude-animation-skills): **chỉ đọc**, không cài skill/plugin của chúng, không chạy
script cài đặt; license + rà soát ở `docs/STYLE_AUDIT.md`, SHA ở `vendor/SOURCES.json` (dựng lại: `python scripts/vendor_fetch.py`).

## Lệnh
- **Giao diện web**: `python studio.py ui [--port 8765] [--no-open]` (hoặc `ui.bat`) — `ui/` (backend Python thuần
  `ui/server/`, frontend ES module thuần `ui/web/`, không Node/không build). UI chỉ chạy `studio.py` như job trong danh sách
  trắng + đọc file pipeline đã ghi; không tự làm việc của pipeline. Kiến trúc/API/bảo mật: `ui/README.md`.
- `/video "<ý tưởng>"` hoặc `/video <slug> [flags]` — xem `.claude/commands/video.md` (vòng lặp theo dòng `::stage=`).
- `python studio.py video <ý tưởng|slug> [--dry-run] [--from S] [--only S] [--model M] [--ai claude|gemini] [--yes]
  [--look-ok] [--tts-force] [--no-open]`
- `python studio.py ideas "<chủ đề>"` → 10 ý tưởng → `ideas <slug> --pick N | --auto-pick`
- `python studio.py styles | charsheet [style] | perf [frames] | perf board [board.json] | status <slug> | models | stages`
- Mỗi video: `--style <id>` · `--voice <tên>` · `--narrative <id>` · `--flow` / `--no-flow` (mặc định auto theo chủ đề) ·
  `python studio.py voices [--for <style>]` (kho giọng + lần dùng gần nhất) · `narratives ["<chủ đề>"]` (10 dạng kịch bản) ·
  `styles --plan "<ý tưởng>"` (xem trước style + giọng + dạng kịch bản)
- Style: `python studio.py styles --gallery` (→ `qa/styles-gallery.png`) · `--cards` (sinh `styles/<id>.md` từ JSON) ·
  `--rank "<chủ đề>"` (điểm hợp chủ đề) · `python studio.py perf engines` (html/manim/HyperFrames → `docs/PERF.md`)
- `python scripts/props3d_sheet.py [style,…] [--props a,b]` (đạo cụ 3D của `stage` theo từng look 3D → `qa/props3d/`)
- `python scripts/physics_sheet.py [--style s] [--scenes drop,topple]` (vật lý `stage`: keyframe tay vs Rapier → `qa/physics/`)
- `python studio.py svg <file.svg> [--name n] [--role auto|ink|hot|cold|accent] [--license "…"]` (nhập icon SVG → `parts`)
- `python scripts/smoke.py` (mọi đường dựng, dry-run → `qa/smoke.md`) · `python scripts/icon_sheet.py [style,…]` (190 đạo cụ
  theo từng look → `qa/icons/`) · `python scripts/html_sheet.py <style> [beat,…]` (contact sheet engine html) ·
  `python scripts/style_compare.py --styles a,b,c` (cùng một storyboard, nhiều style → `qa/style-compare.mp4` + bảng đo)
- Phim câm đứng riêng: `python -m engines.board.render <board.json> insert <id> <out.mp4> [--sec 4]`
  (cũng có `stills <f1,f2…> <dir>`, `range <f0> <f1> <out.mp4>`, `full <out.mp4> [--workers N]`).
- Vòng 22: `python studio.py policy [slug…|--all]` (rủi ro chính sách YouTube: khung lặp giữa video, persona sức khoẻ,
  metadata, spam, Made for Kids → `qa/policy.md`; căn cứ `docs/YOUTUBE_RISK.md`) · `python scripts/icon_sheet.py <style>
  --detail` (đạo cụ chi tiết)
- Vòng 21: `python studio.py facts <slug>` (sổ dữ kiện + điểm SEO → `qa/facts.md`) · `python scripts/parts_sheet.py [style]` · `python scripts/portal_check.py [style]` (zoom xuyên bộ phận → `qa/round21/`)
- Vòng 23: **đầu ra gọn** (`channel.json → output.lean`, mặc định bật): qua cổng QA → chỉ giữ `out/final.mp4`,
  `out/cover-16x9.jpg`, `out/captions.srt`, `out/post.md` (+ storyboard, lời đọc, file nhỏ trong work/) · `clean <slug|--all>
  --lean` (đóng gói gọn dự án cũ) · cổng giữ chân `vidlib/retention.py` (hook / re-hook / diễn viên — chặn đỏ + linter).
- Vòng 9: `python studio.py doctor` (kiểm môi trường) · `deliver <slug> [--platforms …|all]` (gói Shorts/Reels/TikTok/16:9) ·
  `versions <slug>` · `cost <slug>` · `clean <slug> [--yes]` · `rerender <slug> <C03>` (dựng lại MỘT shot) ·
  `trim <slug> <C03> --in s --out s | --auto` · `shots <slug> --order C02,C01,…` · cờ video `--accept-qa`, `--platforms`
- 3D Style Atlas: `python scripts/atlas_import.py [--from atlas-capture.json] [--check]` · `scripts/atlas_extract.py` ·
  `scripts/atlas_frames.py` (style frame + `qa/atlas-style-compare.png`)
- Kiểm: `python scripts/visual_regression.py [--update]` (golden + SSIM/pHash) · `scripts/ui_check.py --axe <axe.min.js>` ·
  `scripts/ui_shots.py <dir>` · `scripts/ui_e2e.py` (làm trọn video qua UI)
- Test: `python -m unittest discover -s tests -t .` · Lint: `python -m ruff check .` (cấu hình `ruff.toml`)
- Snapshot prompt: `UPDATE_SNAPSHOTS=1 python -m unittest tests.test_compiler` (chỉ khi thay đổi prompt là chủ ý)

## Luồng & nguồn sự thật
`projects/<slug>/storyboard.json` là **nguồn duy nhất**. Stage:
`idea → script → storyboard → prompts → page → [CHỜ CLIP] → ingest → trim → voice → assemble → text → outro → audio →
look → [CHỜ XEM SHEET: --look-ok] → code → render → thumbnails → qa → [CỔNG QA: đỏ = dừng, exit 12] → publish → pack`
(`pack` = đầu ra gọn vòng 23; `output.lean: false` → `deliver` + version như cũ)
(+ `out/versions/vNNN/` + `out/manifest.json` + `out/provenance.json` sau khi qua cổng).
**Kế hoạch** `plan.json` (style + giọng + dạng kịch bản `narrative`, chọn theo chủ đề TRƯỚC khi viết brief; brief báo ngày
có Flow / toàn code và khung kể của video — `config/narratives.json`, không lặp 3 video gần nhất).
Idempotent nhờ dấu vân tay trong `work/state.json` (gồm hash mã `engines/board/*.py`). Exit code: 0 done ·
2 need_storyboard · 3 storyboard_invalid/lint_failed · 4 confirm_map · 5 need_ideas · 6 pick_idea · 10 waiting_clips ·
11 look_check · 12 qa_failed (cổng QA đỏ: `config/channel.json → qa.blocking`). Trường do tool sinh bị ghi đè mỗi lần chạy (`*.prompt`, `video_prompt`, `mode_resolved`, `gen_sec`,
`assembly_resolved`…); sửa tay bằng `override.*`.

## Các đường dựng (bản đồ thư mục + các tầng: `docs/ARCHITECTURE.md`)
- **Flow** (`mode: auto|frames_*|ingredients`): clip Google Flow → ingest (`-an`) → auto-trim → **camera ảo** (`vcam.py`).
- **Code three.js** (`mode: code`, `"code": {"scene": "<engines/three/scenes/*.js>", "params": {…}}`): engine toon trên sân khấu
  đen (`engines/three/`), render song song bằng `coderender.py` (Edge headless, GPU, RESUME). Ý tưởng mới dùng cảnh tổng quát
  `stage` (đạo cụ + keyframe trong storyboard, không viết JS; schema ở đầu `engines/three/scenes/stage.js`). Tự chọn cho cảnh Flow
  làm kém (cân, nhiệt kế, đồng hồ đo, sơ đồ, chữ trong cảnh, outro). Style `toon3d-lab` = toàn code. `stage` có nhân vật
  3D khớp nối (`mannequin`/`runner3d`/`lifter3d`, `pose`), ~54 đạo cụ 3D theo mảng kênh, mọi icon html ép khối (`icon3d`),
  `parts` tự ghép, `fx[]` hạt 3D (steam|smoke|sparks|burst|splash|bubbles|shockwave|fire), `set: track`.
  **Look 3D** = `styles/<id>.json → world.look3d` (chuỗi hoặc object ghi đè tham số): `toon` (mặc định) · `clay` · `plastic`
  · `glass` · `chrome` · `lowpoly` · `paper` · `holo` · `xray` — preset trong `LOOK3D` của `engines/three/main.js`
  (chất liệu, env map studio dựng bằng code, ACES, bloom theo mip, grain nhân theo độ sáng → nền đen vẫn #000). Style 3D:
  `toon3d-lab`, `clay3d-black`, `plastic-toy3d-black`, `papercraft3d-black` (có Flow, `flow.is_3d` → prompt Flow 3D),
  `glass3d-black`, `chrome3d-black`, `lowpoly3d-black`, `hologram3d-black`, `xray3d-black` (toàn code).
  **Vật lý** (`engines/three/physics.js`, Rapier 3D bản tất định `vendor/rapier/`, chỉ nạp khi params có `physics`/`body`):
  prop có `body` {kind dynamic|fixed|kinematic, material, shape auto = từ hình prop, release, `hit_u` = tự canh cú chạm đầu
  vào u đó, v, spin, push, sfx, fx}; `physics` {gravity, slowmo, settle, fx}. Mô phỏng MỘT LẦN trong `build` → quỹ đạo
  từng frame (vẫn hàm thuần theo frame, worker nào cũng ra y hệt); va chạm tự sinh cue SFX + kick + hạt đúng frame chạm.
  Python kiểm dữ liệu: `adapter.stage_physics_errors` (từ vựng đọc từ physics.js).
  **Hậu kỳ thêm**: `world.look3d.post` {smaa, ca, bloom} → pmndrs/postprocessing (`vendor/postprocessing`, nạp qua import map
  "three" của `index.html`); mặc định {smaa: true} cho mọi look, style tắt bằng `"post": false`. SMAA chờ nạp ảnh tra cứu
  trước `ready`.
- **Code board** (engine thứ hai của `mode: code`, `engines/board/`, Python + OpenCV, CPU): shot có `beat_recipe` thuần board
  (DOC_FOCUS, NUMBER_CARD, THESIS, COUNTER, NETWORK_REVEAL, SILENT_FILM, hoặc NAME_TAG/STAMP/CONNECT/HIGHLIGHT_LINE không có
  hình riêng) tự thành `mode: code` + `code.engine: "board"`. `vidlib/boardplan.py` sinh `work/board/board.json` từ
  storyboard + timeline + mốc từ VO (không mốc thời gian nào nằm trong mã engine).
- **Code html** (engine thứ ba, `engines/html/`, Canvas 2D trong Edge headless, dùng chung harness `coderender`): motion
  graphics nền đen. `"code": {"scene": "<beat>", "params": {…}}` với beat `title|drop|counter|compare|graph|process|scale|
  callout|fact|scene|outro` (`scene` = dàn cảnh tự do: actors + keyframe theo u, nhãn bám vật, mũi tên, fx; `layout` =
  biến thể bố cục của title/counter/compare/fact/process, tool tự xoay theo video); **một cú máy liền** (`vidlib/spine.py`):
  các shot html (+ manim: warp affine sau khi dựng, là "ô ma" với html) liền nhau là ô trên một canvas lớn, camera bay
  liền qua điểm cắt (kiểu bay theo look ∩ dạng kịch bản), mỗi shot vẫn render riêng (job.json → `spine` {prev,next,L});
  QA `motiongate` chặn video "như slide"; **look** (flat, boil, iso, hud, synth, sticker, swiss, spy, picto, zoom, flow, sketch, gallery) lấy từ
  `styles/<id>.json → html`. Thêm look = thêm một khối trong `looks.js` + token trong style; thêm beat = một hàm trong
  `beats.js` + mục trong `engines/html/__init__.py` (PARAMS).
  **Tài sản người dùng** (`vidlib/userassets.py`, thư mục `assets/user/svg|lottie|rive`, gọi bằng tên; tool đổi tên → dữ
  liệu lúc dựng job, engine không đọc đĩa): `"icon": "svg:<tên>"` (SVG nhập bằng `studio.py svg`: SVGO `vendor/svgo` + đo
  hình học trong Edge → `parts` có vai màu + `holes`, vẽ bằng bút của look; three.js `stage` prop `"type": "svg:<tên>"` ép
  khối) · actor `scene` `"lottie": "<tên>"` (dotLottie `vendor/dotlottie`, WASM từ máy, đổi màu theo palette) · `"rive":
  "<tên>"` (Rive `vendor/rive`, chạy từ 0 theo lưới 1/120 s → tất định) — `engines/html/media.js`. Giấy phép: linter nhắc
  khi thiếu (`--license` / `<tên>.license.txt`). Easing chung `lib/motion` (cả html + three + hậu kỳ): smooth, easeOut,
  easeIn, back, anticip, spring, linear, bounceOut, elastic, expoOut, circOut, sine, backIn, steps.
- **Code manim** (engine thứ tư, `engines/manim/`, Manim CE, CPU, không LaTeX): `graph|vectors|equation|counter|compare|
  title|fact|outro` cho style `physics-diagram-black`. Chậm (~0.3–0.6 s/frame) → chỉ cho shot sơ đồ.
- **Chọn engine cho shot code** (`codeshot.engine_of`): `code.engine` nếu ghi → không thì `code_engine` của style (beat style
  đó không có → html) → cảnh three.js. Cảnh trùng tên three/html (`scale`, `outro`): params có trường bắt buộc của beat html
  mà dòng `// params:` của cảnh three.js không khai (vd `items`) → html. **Trộn engine trong một video** là bình thường:
  3D cho hook/va chạm/payoff, chart html cho số liệu, `scene`/`process`/Manim cho cơ chế; mọi engine lấy màu/font của style
  (three.js không có `world` → suy từ palette html; Manim không có token → palette html, màu tối được nâng sáng).
  Brief có khối **MOTION MIX** sinh từ danh sách cảnh thật (`brief.mix_help`). Mọi engine đi qua **`engines/adapter.py`** (`ShotSpec` → `Clip`: frame đủ + MP4 đúng thời lượng + frame
  đầu/cuối); không thêm engine thứ năm (Remotion/HyperFrames/Blender không vào pipeline — xem `docs/STYLE_AUDIT.md`).
- **Cách ghép** `storyboard.assembly` (`auto` = theo style): `board_spine` — CẢ video là một camera chạy liên tục trên bảng
  đen; clip Flow/cảnh three.js là thẻ ghim (camera đẩy vào tới khi lấp khung → chiếu toàn màn hình → kéo ra), phim câm
  vào/ra bằng iris, outro = TITLE_GLITCH · `cuts` — cắt cứng như cũ, shot board render thành frame riêng.
  Style board-* (`board-black`, `lab-notebook-black`, `chalk-case-black`, `silent-film-black`) mặc định `board_spine`.
- Nối Flow ↔ code: `start_frame.seed_from` / `end_frame.seed_from` = id shot code → xuất frame của shot code làm ảnh Flow.
- **Vòng 22 — hình nhận ra được, có chiều sâu, không lặp**: đạo cụ chi tiết `engines/html/icons_detail.js` (path SVG →
  poly, tô bóng bằng `tone`; ghi đè icon đơn giản cùng tên) · người tả thực `engines/html/rig_human.js` (bộ xương `human`:
  athlete/marathoner/runnerf/lifter/casual/casualf + vòng 23 coach/lifterf/bigguy/elder/student/office/cyclist/medic/
  trailrunner, `view` side|front|back (đổi theo key), `outfit`/`hair`/`beard`/`glasses`/`build`, deadlift, dáng đi/chạy
  theo đường cong góc khớp, đạp xe IK (gối gập ra trước), x-ray
  spine/muscles/vessels/fuel/liver; vai màu `skin`/`hair`) · bối cảnh đêm nhiều lớp `engines/html/backdrops.js`
  (`params.backdrop`, lớp tĩnh vẽ sẵn vào canvas phụ rồi đặt theo thị sai) · kính lúp `params.lenses` + `freeze` + nhãn
  tự né vật/kính/nhau (chọn chỗ một lần cho cả đời nhãn, `fixed: true` giữ chỗ) + kẹp vùng an toàn trong beat `scene` · profile `explainer` (`length_profile`, shot 4–6.5 s, không punch-in tự
  chèn cho shot code, kiểu bay spine êm `spine.CALM`) · `vidlib/policy.py` (cổng QA: dòng "khung lặp giữa các video" chặn đỏ).
- **Zoom xuyên bộ phận (vòng 21)**: `transition_in: "zoom_through"` + `through: "hero.eye"` | `[x, y]` (bộ phận của shot
  TRƯỚC). html→html liền mạch = kiểu bay `portal` (`spine.py`, core.js vẽ khô tìm điểm neo, lỗ tròn); cặp khác = hậu kỳ
  `vidlib/partzoom.py` (điểm neo từ `meta.json → anchors_end`, job có `anchors_out`). Rig 2D: `PARTS`/`rigAnchors`,
  `xray`+`organs`, `talk`, `gaze`, `hold`, `focus`, bong bóng; 3D: `frame.dive`.

## Bản đồ code
| Module | Việc |
|---|---|
| `lib/motion/` | **thư viện chuyển động dùng chung**: `motion.js` (engine) + `__init__.py` (hậu kỳ), cùng API, test đối chiếu |
| `engines/three/` | `main.js` (look 3D `LOOK3D` gồm `retro90`/`psx` Gouraud theo đỉnh, ink normal/depth + rim, DOF, grade, ACES/bloom/grain, card), `creatures.js` (22 loài con vật + người 3D thủ tục), `models.js` (nạp glTF/GLB CC0), `hybrid.js` (2D trong 3D `card2d`/`multiplane`, `overlay2d` bám prop 3D, hậu kỳ 3D theo look 2D), `cast.js`, `props.js` (đạo cụ 3D, mannequin, icon3d, fx3d, bối cảnh `meadow`/`tabletop`/`street`), `physics.js` (Rapier), `paint.js`, `scenes/*.js` |
| `ui/server/` | `app.py` (HTTP: /api, /api/v2/projects/<slug>/sb/*, /api/v2/env, /api/v2/catalog/schema, SSE log job, file có Range, chốt Host/CSRF) · `services/` projects, catalog, jobs (hàng đợi + làn nhẹ `LIGHT`, danh sách trắng lệnh, huỷ cây tiến trình), files (chặn traversal), system, workspace |
| `ui/web/` | `styles/tokens.css` (design token) · `components.css` · `app/core` (api, dom, icons, format) · `app/ui/` (kit, media, overlays) · `app/pages/*` (projects, script, board, generate, edit, review, deliver, library, design) |
| `engines/board/` | engine board: `color.py` (hex → BGR, KHÔNG nhập BGR tay), `fonts.py` (mono/serif/hand + dự phòng từng ký tự), `camera.py`, `sprites.py` (thẻ, giấy, nhãn băng dính, con dấu), `draw.py` (warp ROI, nét đỏ), `surface.py` (mặt bảng + grain/phim), `vintage.py` (phim câm), `scene.py` (board.json → frame), `render.py` (CLI, chia đoạn + concat) |
| `engines/adapter.py` | **giao diện chung 4 engine** (three, html, manim, board): job, render, meta, text_crops, `render_clip`, validate physics/creatures/hybrid |
| `engines/html/` | `core.js` (bút vẽ theo look, chữ + khung OCR, hậu kỳ), `post2d.js` (WebGL2 halftone/comic/pixel/paper), `rig2d.js` / `rig2d.py` (17 loài nhân vật 2D), `looks.js` (20 look), `beats.js` (15 beat + 29 biến thể `layout` + chiều sâu 2D + công cụ nội bộ `catalog`), `icons.js` + `icons_channel.js` = 190 đạo cụ kênh (+ 926 SVG Phosphor MIT), `parts` tự ghép, `demo.json` |
| `engines/manim/` | `scenes.py` (lớp `Shot`, beat `b_*`), `run.py` (tiến trình con), `__init__.py` (job, render → frame, meta, boxes OCR) |
| `vidlib/enginebench.py` | benchmark html/manim/HyperFrames (`perf engines`) · `styles_gallery` |
| `vidlib/common.py` | đường dẫn, config (cache), `env()` (.env), ffmpeg, font + `glyph_safe`, easing |
| `vidlib/lang.py` | ngôn ngữ/locale kênh, `copy()` chuỗi khán giả thấy, định dạng số, số → chữ, âm tiết tiếng Anh |
| `vidlib/storyboard.py` | schema: normalize/validate (beat/mode gồm `code`/transition/archetype, style, `beat_recipe`/`board`/`assembly`, hold) |
| `vidlib/boardplan.py` / `boardqa.py` | storyboard → board.json (bố cục, camera, dấu đỏ theo từ khoá, cue SFX, frame media) · QA board (lệch frame, thời gian đọc, glyph, màu, đứng hình, OCR) |
| `vidlib/compiler.py` / `linter.py` | prompt Flow + tự chọn mode code · lint prompt + quy tắc script tiếng Anh |
| `vidlib/brief.py` / `ideas.py` | brief LLM (`prompts/storyboard_brief.md`, schema) · 10 ý tưởng (`prompts/ideas_brief.md`) |
| `vidlib/tts.py` / `vo.py` / `timing.py` | ElevenLabs (timestamp ký tự, cache) · xử lý VO · mốc từ: ElevenLabs → whisper → khoảng lặng |
| `vidlib/timeline.py` | thời lượng theo VO, cắt sớm 0–3 frame trước câu, punch-in, chặn flash |
| `vidlib/textfx.py` / `textstyle.py` / `track.py` | chữ trong thế giới phim (Tầng 1, neo vật, occlusion, behavior) · kiểu chữ theo style · bám vật |
| `vidlib/vcam.py` | camera ảo: creep, kick 7 frame ở SFX hit, quán tính qua điểm cắt, payoff push+roll, ≤112% không lộ mép |
| `vidlib/codeshot.py` / `coderender.py` | job.json cho engine + tự chọn cảnh · render song song/RESUME/GPU, `text_crops` cho OCR |
| `vidlib/audio.py` / `mix.py` / `sfx.py` / `musicgen.py` | stems + cue table · khoá mức gated RMS + master tuyến tính/limiter TP · SFX tổng hợp (cả `typing:<s>`, `scratch:<s>`, `projector:<s>`, `stamp`) · nhạc nền |
| `vidlib/render.py` / `fx.py` | render 1 lượt (`cuts`) + contact sheet look · transition |
| `vidlib/styles.py` | thư viện style + `plan()` chọn theo chủ đề (`tags`, có xét đuôi từ) + cân bằng Flow/code (`flow_share`) + chống lặp + thẻ `styles/<id>.md` |
| `vidlib/narratives.py` | dạng kịch bản xoay vòng (`config/narratives.json`): chọn theo nhãn chủ đề + regex tiêu đề, chống lặp, khối brief, kiểu bay ưa dùng |
| `vidlib/spine.py` / `motiongate.py` | "một cú máy liền" cho shot html (vị trí ô, kiểu bay) · cổng QA chống slide (tỉ lệ khung chuyển động nhanh) |
| `vidlib/voices.py` | mỗi video một giọng: kho `config/voice.json → pools`, không lặp N video, hợp `voice_tags` của style, atempo tự tính |
| `vidlib/qa.py` / `qareport.py` / `ocr.py` | QA cắt/trim · freeze/black/loudness, OCR, khớp nét/palette, .srt, publish.md, report.md/html |
| `vidlib/outro.py` / `thumbs.py` / `page.py` / `ingest.py` / `motion.py` | outro 2D dự phòng + end screen · thumbnail · scripts.html · ingest · motion energy/auto-trim |
| `vidlib/tools.py` | `charsheet`, `perf` / `perf_board` → `docs/PERF.md` (hai engine cạnh nhau) |
| `vidlib/encode.py` | **tham số H.264 chung** (BT.709 + tag, GOP ½ fps, 2 B-frame, maxrate, faststart, không edit list) |
| `vidlib/qagate.py` | cổng QA đỏ/vàng/xanh + kiểm spec file bằng ffprobe (màu, faststart, bitrate, 48 kHz) + loudness/TP |
| `vidlib/deliver.py` | gói theo nền tảng (`config/delivery.json`): remux 9:16, pillarbox 16:9 + endscreen, bìa, .srt, đo lại spec |
| `vidlib/rights.py` / `manifest.py` / `cost.py` | sổ quyền `rights/ledger.json` + nhãn AI · version vNNN + manifest + provenance · chi phí/video |
| `vidlib/doctor.py` / `cleanup.py` / `visreg.py` | `studio.py doctor` · `studio.py clean` · visual regression (golden `tests/golden/`) |
| `vidlib/atlas.py` | 3D Style Atlas → 37 preset dark-stage (`config/atlas.json`, bộ kiểm không chép 6 từ, `auto_ok`) |
| `vidlib/userassets.py` | tài sản người dùng (SVG/Lottie/Rive): tìm theo tên, đổi thành dữ liệu engine, kiểm tên/giấy phép, `studio.py svg` |
| `vidlib/assets3d.py` | kho mô hình 3D CC0 (glTF/GLB) + icon SVG thư viện (`config/assets3d.json`, `studio.py assets`) |
| `vidlib/motionplan.py` | bộ não motion: kho 175 cơ chế (`config/metaphors.json`), chữ ký motion, chống lặp bố cục/kiểu bay/cơ chế giữa các video |
| `vidlib/policy.py` | rủi ro chính sách YouTube (vòng 22): khoá khung + so 10 video trước, persona sức khoẻ, số trong tiêu đề/thumbnail, giật gân, spam, Made for Kids, dòng "not medical advice" |
| `vidlib/retention.py` / `lean.py` | vòng 23: cổng giữ chân (hook / re-hook / câu độn / xin tương tác / diễn viên đa góc, không lặp người chính) · đầu ra gọn (bìa 16:9 + post.md theo nền tảng, dọn phần còn lại) |
| `vidlib/partzoom.py` / `facts.py` / `seo.py` | zoom_through hậu kỳ + kiểm `through` · sổ dữ kiện (claims/sources, lint, chip nguồn, `qa/facts.md`) · SEO đa nền tảng + brand-safety + category/nhãn nội dung tổng hợp cho upload |
| `vidlib/sbedit.py` | sửa `storyboard.json` & `ideas.json` có kiểm + lịch sử hoàn tác + xem trước 1 frame (`studio.py sb`, UI gọi qua job) |

## Cấu hình (không hard-code ở module)
- `config/channel.json`: **language/locale/ui_language**, `copy.<lang>` (CTA, tag…), `script` (3.7 từ/giây…), nhịp,
  camera ảo (`pacing.vcam_*`), trim, VO (`vo.speed` = atempo), audio (`sfx_db`), safe-zone, outro, `styles`, `code_render`,
  `board` (nhịp Shorts của engine board, kích thước thẻ, `size` [1920,1080] để xuất 16:9, `workers`, `crf`), `qa`.
- `config/narratives.json` (10 dạng kịch bản: `shape`/`visual` tiếng Anh cho brief, `tags`, `strong` regex tiêu đề, `moves`
  kiểu bay camera, `avoid_recent`).
- `config/voice.json` (ElevenLabs: `pools.<ngôn ngữ>` kho giọng có tags/giới tính, `rotation.avoid_recent`, model v3, audio
  tags, phát âm; `voice` = giọng dự phòng/video cũ; vòng 23: mỗi giọng có `edge` {voice, rate, pitch} riêng khi đọc bằng
  Edge, id `edge:<ShortName>` = giọng chỉ có trên Edge, `edge_tone` = tông theo vai câu) · `channel.json → vo.speed_auto/target_wps/speed_min/speed_max`
  (atempo theo giọng) · `styles.default = auto`, `flow_share`, `balance_window` · `config/mix.json` (khoá mức, ducking, payoff, master).
- `config/delivery.json` (preset nền tảng + safe zone + nguồn spec) · `config/costs.json` (đơn giá) · `config/atlas.json`
  (phân tích 37 style Atlas) · `rights/ledger.json` (sổ quyền + quyết định chờ chủ kênh)
- `config/flow-models.json` (capability Flow) · `styles/*.json` (chữ + `world` của engine three.js + `board` token màu hex của
  engine board + `assembly`) · `brand/*` · `prompts/*`.
- Thẻ style vòng 7 (`styles/<id>.json`, 14 style `*-black`): ngoài kiểu chữ còn có `code_engine`, `tags`, `palette`,
  `not` (nó KHÔNG phải là gì), `pacing`, `marks`, `transitions`, `sfx_pack` (cue chung → âm, pipeline áp vào cue shot code),
  `music.bpm` (nhịp nhạc tổng hợp), `voice_persona`, `thumbnail`, `flow` (`medium`/`look`/`motion`), `black_min`, `source`,
  `special` (không vào vòng xoay auto; hiện không style nào dùng). `styles/<id>.md` là bản sinh từ JSON — sửa JSON rồi chạy `styles --cards`.
- `config/channel.json → code_render.html_workers` (0 = 2 — nhanh nhất theo `docs/PERF.md` mục 3).
- Key API trong `.env` (gitignored) — không bao giờ ghi vào repo.

## Quy ước
- **Dữ kiện có nguồn**: mọi số/khẳng định → `claims` + `sources` (nguồn gốc, đã mở trang); giả định/tranh cãi phải rào
  đón trong VO. **Không ghi tên kênh/studio khác** vào bất cứ chữ nào khán giả thấy/nghe hay prompt hình (`seo.brand_blocklist`).
- Không để Flow vẽ chữ/số: chữ qua `text_fx` (hậu kỳ), chữ 3D trong shot three.js, hoặc nhãn/thẻ của engine board. Linter chặn.
- Không bao giờ text-to-video. Ingredients ở bước ẢNH, Frames ở bước VIDEO.
- Âm thanh cuối chỉ gồm VO + nhạc + SFX của pipeline; tiếng Flow bị bỏ khi ingest. audio.py chỉ xuất stems. Không dùng
  `mix_and_mux.sh` của kaz-documentary (CRF 24, ducking riêng).
- Không shot nào đứng yên ≥ 4 frame (camera ảo/creep/trôi chậm); QA từ chối freeze ≥ 0.4 s trừ `hold: true`.
- Engine board: đỏ accent `#d0312d` CHỈ cho ý nghĩa (khoanh, dây, dấu, nhãn chính, tiêu đề cuối); ≤ 2 con dấu/video; dấu
  đỏ/nhãn bắt đầu 0–3 frame trước từ khoá và còn ≥ 0.7 s đọc. Không tự tải ảnh người thật — vẽ bằng code hoặc người dùng
  tự đưa ảnh public domain vào `assets/user/`; không vẽ lại logo/masthead báo đài; bạo lực chỉ bằng flash/khói/intertitle.
- Ghi JSON qua `common.save_json` (UTF-8, LF). Viết code bằng Write/Edit hoặc script Python; tránh heredoc shell có `\`.
- Video tiếng Việt cũ không render lại (dự án cũ giữ nguyên).
