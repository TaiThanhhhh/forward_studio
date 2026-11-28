---
name: black-lab-toon
description: Làm short thí nghiệm "what happens if…" cho kênh forward. (tiếng Anh, nền đen) — 10 ý tưởng có nhãn True/Disputed/Hypothetical, script tiếng Anh theo nhịp 3.7 từ/giây, giọng ElevenLabs, clip Google Flow + shot code (engine three.js toon trên sân khấu đen, engine board kiểu evidence board + phim câm), text_fx trong cảnh, mix khoá mức, QA. Dùng cho mọi yêu cầu làm video/ý tưởng/script cho kênh này — kể cả khi người dùng nói "make a video about X", "explainer", "motion graphics", "animation", "documentary", "evidence board", "phim câm", "HUD", "synthwave", "Swiss", "isometric", "Manim" (trong repo này KHÔNG dùng skill bên ngoài: kaz-documentary, hyperframes, lemo-opuscar, mg-styles, anything2explainer, huashu-art-motion, dashi-animationstyle, zach-d-films — mọi yêu cầu làm video đi vào pipeline /video).
---

# black-lab-toon — short thí nghiệm nền đen, kênh tiếng Anh

Viết lại từ `cartoon-short-kit` (vendor/cartoon-short-kit/SKILL.md) cho hệ của kênh: **khán giả nghe/thấy tiếng Anh**,
**giao diện + báo cáo tiếng Việt**, nền đen + ink + một bảng màu tối giản theo style, ElevenLabs, pipeline Flow
(`python studio.py video …`) có thêm đường dựng **code-animated shot**. Trả lời người dùng bằng tiếng Việt.

## Giữ từ kit
- **10 ý tưởng** mỗi lần: title (5–8 từ), hook (nghịch lý nói như sự thật), twist (câu cuối, mỉa/bất ngờ), 2–3 khoảnh
  khắc thị giác, nhãn **True / Disputed / Hypothetical** (kiểm chứng bằng web search; không trình bày myth như sự thật).
  → `python studio.py ideas "<chủ đề>"` → viết `ideas/<slug>/ideas.json` → `--pick N` hoặc `--auto-pick`.
- **Script** (tiếng Anh tự nhiên, không dịch): ~3.7 từ/giây (20 s ≈ 75 từ, 30 s ≈ 110, 45 s ≈ 165); câu 8–15 từ; dạng
  rút gọn; **số viết bằng chữ trong lời đọc**; không tả lại thứ người xem đang thấy; câu 1 là hook, câu cuối là twist.
  Cấu trúc kênh: Hook → Setup → leo thang ×3 → Payoff → Twist → outro teaser.
- **Timing theo giọng**: mọi phản ứng hình (pop chữ, kick, flash, cắt cảnh) đặt **0–3 frame TRƯỚC** từ khoá (tool tự
  lùi `react_lead_default` = 2 frame). Khoá hình trước, làm âm thanh sau; timing đổi → chạy lại audio + mix.
- **Look-check**: trước render đầy đủ, pipeline dừng ở `look_check` với `qa/look/sheet.jpg` (giữa mỗi shot + hai
  phía mỗi điểm cắt). **Tự xem ảnh**, soi các bẫy: khung dọc hẹp (cắt mép đạo cụ/chữ), chữ bị che/lật gương, nét code
  khác nét Flow (bảng số đo in kèm), nhân vật bị cắt, chữ đè mặt. Đạt → chạy lại với `--look-ok`.

## Bỏ khỏi kit
- "No captions" → kênh dùng **text_fx** (chữ trong thế giới phim, 1–4 từ/shot, không chép lời).
- Thế giới nhiều màu, bầu trời, đồi cỏ, ánh sáng ngày/hoàng hôn → **sân khấu đen**, rim light accent, fog đen.
- `mix_raw.wav` của audio.py, `loudnorm` động của finish.sh → stems + `vidlib/mix.py` + master tuyến tính.

## Quy trình (lệnh `/video`)
1. `python studio.py video "<ý tưởng>"` → `need_storyboard`: đọc `brief.md`, kiểm chứng số liệu (WebSearch + mở trang
   bằng WebFetch; ghi `sources` có cấu trúc + `claims`, shot ghi `claims` — vòng 21, `python studio.py facts <slug>`), viết `storyboard.json` (chỉ trường ngữ nghĩa; Flow prompt do tool compile).
2. Chọn đường dựng từng shot: **`mode: code`** cho cảnh Flow làm kém — sơ đồ, mặt cắt, so sánh tỉ lệ, cân, thước,
   nhiệt kế, đồng hồ đo, bộ đếm, chữ trong cảnh cần đúng chính tả, outro/"next", cảnh nối loop, camera bay chính xác.
   `"code": {"scene": "<engines/three/scenes/*.js>", "params": {...}}`. **Mọi ý tưởng mới dùng cảnh tổng quát `stage`**:
   ghép đạo cụ từ thư viện (cốc, bi, đá, cân, nhiệt kế, đồng hồ, buồng kính, biển/chữ, khối/cầu/trụ màu palette, lông
   vũ, búa, nhân vật…) + keyframe (`u` 0..1 của shot, easing lib/motion) — KHÔNG viết JS. Để trống `camera` → tự căn
   khung 9:16. Preset (scale, thermometer, vacuum, outro) chỉ là lối tắt khi khớp đúng. Còn lại để `auto` (Flow).
3. `waiting_clips` → người dùng tạo clip Flow theo `scripts.html`. Shot Flow cạnh shot code có thể đặt
   `start_frame.seed_from` / `end_frame.seed_from` = id shot code → tool xuất frame cuối/đầu của shot code làm ảnh
   Start/End (hai đường dựng tham chiếu lẫn nhau).
4. Giọng: ElevenLabs (`config/voice.json`, key trong `.env`), `eleven_v3` để dùng audio tag ([excited],
   [dramatically]…); timestamp ký tự → mốc từ chính xác. v3 bỏ qua `speed` → atempo hậu kỳ `channel.json → vo.speed`.
5. `look_check` → tự xem sheet → `--look-ok` → shot code render song song (Edge headless, GPU, RESUME) → render →
   thumbnails → `publish.md` → QA (`qa/report.html`).
6. Báo người dùng: `out/final.mp4`, thời lượng, loudness, freeze, OCR, khớp nét/palette code↔Flow, `publish.md`.

## Style
- `styles/*.json`: chữ text_fx + `world` (palette, ink, rim, ánh sáng của engine). `forward` khớp clip Flow (khối
  trắng/xám, mực đen ~9–10 px, viền trắng ngoài, accent #1849F7). `toon3d-lab` = **toàn bộ bằng code** (không Flow):
  lab tối, mực trắng, rim light xanh, bóng đổ, DOF — dùng khi đổi gió, cần ra video nhanh không tốn credit Flow, hoặc
  chủ đề nhiều sơ đồ. `style: "auto"` chọn style chưa dùng trong 3 video gần nhất (tính cả toon3d-lab).

## Engine board — ngữ pháp evidence board (engines/board/, vòng 6)
- Style `board-black` · `lab-notebook-black` · `chalk-case-black` · `silent-film-black` → `assembly: board_spine`: CẢ video
  là MỘT camera trôi trên bảng đen; clip Flow / cảnh three.js là thẻ ghim (camera đẩy vào tới khi lấp khung → chiếu toàn
  màn hình → kéo ra); chữ là nhãn băng dính / trang sổ / thẻ số trong toạ độ thế giới. Đỏ #d0312d chỉ cho ý nghĩa.
- Mỗi shot điền `beat_recipe` + `board` (brief §4b): REVEAL_PHOTO (mặc định cho shot có hình), DOC_FOCUS (trang sổ +
  khoanh đỏ cụm từ đang đọc), NUMBER_CARD ("1,000°C" count-up), NAME_TAG, CONNECT (dây nguyên nhân → kết quả), STAMP
  (CONFIRMED / MYTH / DON'T TRY THIS, ≤ 2), HIGHLIGHT_LINE, **THESIS cho twist** (dòng "You'd think…" bị gạch → câu đúng +
  chấm đỏ), COUNTER, NETWORK_REVEAL (shot ngắn không lời trước outro), SILENT_FILM (đoạn chèn 3–4 s vẽ tay cho khoảnh khắc
  lịch sử: tableau + intertitle, vào/ra iris). Recipe thuần board không cần Flow.
- **Chọn từ khoá SỚM trong câu** cho nhãn/con dấu (cần ≥ 0.7 s đọc trước khi camera rời; tool cảnh báo nếu không kịp).
- Người thật (Leidenfrost…) chỉ VẼ bằng silhouette tối giản; ảnh public domain thì người dùng tự đưa vào `assets/user/`.
  Không vẽ logo/masthead báo đài; tai nạn/bạo lực chỉ bằng flash, khói, intertitle.
- Look-check kiểu board: sheet có still đầu/giữa/cuối mỗi beat + đúng lúc mỗi dấu đỏ hiện; dòng `▶ look` in kèm bảng ✔/✖
  (lệch frame, thời gian đọc, glyph, màu BGR, đứng hình, OCR). Soi thêm: thẻ bị cắt mép, nhãn đè lên chủ thể, chữ quá nhỏ ở
  network reveal (chấp nhận được), frame "đầu" là lúc camera đang lướt (bình thường).
- Đoạn phim câm đứng riêng: `python -m engines.board.render <proj>/work/board/board.json insert <id> out.mp4 --sec 4`.

## Engine code-shot (engines/three/)
- `main.js`: toon material, ink pass normal/depth (màu ink + viền rim theo style), DOF 48 tap, grade, flash.
  Cảnh là hàm thuần theo frame: `build(ctx, params) → {frame(f) → {cam, actors, dof, flash}, cues, texts}`.
- Chuyển động dùng `lib/motion` (cùng API với bản Python ở hậu kỳ): `camFromKeys` + creep (không bao giờ đứng ≥ 4
  frame) + kicks 7 frame; pop = back, slam = anticip → back + 2 frame nén, settle = spring, idle + blinkAt cho mọi nhân vật.
- Nhân vật: card 2D (`engines/three/cast.js` — nhà khoa học kính bảo hộ, theo REF_SCIENTIST). Render character test sheet
  trước khi dùng thiết kế mới: `python studio.py charsheet <style>`.
- Chữ trong cảnh: `ctx.textPlane` / `PROPS.sign` (UV phẳng, tự xuống dòng + thu cỡ cho vừa, quay mặt về camera để
  không lật gương). QA OCR kiểm 100%.
- Bẫy khung dọc 9:16: nửa bề ngang nhìn thấy = d·tan(vfov/2)·0.5625 (d = 4 m, fov 40 → ±0.8 m). Vật rộng → xoay vào
  chiều sâu (như cảnh cân), chữ đặt gần trục giữa.
- **Look 3D** theo style (`world.look3d`): toon · clay · plastic · glass · chrome · lowpoly · paper · holo · xray — cùng
  một storyboard `stage`, đổi style là đổi chất liệu. Soát đạo cụ: `python scripts/props3d_sheet.py <style>`.
- **Vật lý thật** (`engines/three/physics.js`, Rapier tất định): cảnh có rơi/nảy/ném/va chạm/đổ chồng vật → gắn `body`
  cho prop thay vì keyframe tay (`material`, `release`, `kind: kinematic|fixed`, `v`, `push`). Đặt **`hit_u` đúng từ khoá
  trong VO** → tool tự chọn lúc thả để cú chạm đầu rơi đúng đó (kể cả có `physics.slowmo`); SFX + kick + hạt tự sinh
  đúng frame chạm, không cần `cues`/`kicks` tay cho cú va. Vật bay vào từ ngoài khung: `"frame": false`. Soi:
  `python scripts/physics_sheet.py` → `qa/physics/`.
- **Tài sản người dùng** (brief liệt kê tên đang có, không bịa tên): `"icon": "svg:<tên>"` (icon SVG anh nhập bằng
  `studio.py svg`, vẽ theo bút của look; `stage` prop `"type": "svg:<tên>"` = khối 3D) · actor `scene` `"lottie": "<tên>"` /
  `"rive": "<tên>"` (animation dựng sẵn thay cho icon, `colors: palette` để hợp style). Hậu kỳ 3D theo style:
  `world.look3d.post` {smaa, ca, bloom}. Easing thêm: bounceOut, elastic, expoOut, circOut, sine, backIn, steps.

## Trộn engine trong một video (mặc định nên làm khi chủ đề có cả hành động lẫn số liệu)
- Mỗi shot chọn engine mạnh nhất cho ý đó: hook/va chạm/cơ thể/payoff → `stage` (3D, nhân vật `runner3d`… + `fx`);
  con số → `counter`/`graph`/`compare`/`scale` (html, `scale` cần `items`); cơ chế → `scene`/`process`/`callout`;
  lực/phương trình → `"engine": "manim"` (`vectors`, `equation`). Brief có khối MOTION MIX liệt kê cảnh thật.
- 3D cho 2–4 khoảnh khắc; đổi engine ở chỗ đổi beat, không đổi mỗi shot. Mẫu: `projects/demo-hybrid-3d`,
  `projects/demo-hybrid-xray` (cùng kịch bản, khác style). Soi look-check: chart 2D và cảnh 3D phải cùng palette.

## Engine html + manim — 14 style motion graphics nền đen (vòng 7)
Nguồn tham khảo nằm ở `vendor/` (ghim SHA trong `vendor/SOURCES.json`, license + rà soát ở `docs/STYLE_AUDIT.md`) — **chỉ
đọc, không cài, không gọi skill của chúng**. Mã đã được viết lại thành module của tool:
- `engines/html/` (Canvas 2D, chạy bằng harness `coderender` sẵn có): **look** = ngữ pháp phong cách (flat, boil, iso, hud,
  synth, sticker, swiss, spy, picto, zoom, flow, sketch, gallery) × **beat** = ngữ pháp giải thích (`title`, `drop`,
  `counter`, `compare`, `graph`, `process`, `scale`, `callout`, `fact`, `scene`, `outro`) × **icon** (đạo cụ có vai màu
  hot/cold/accent). Shot viết bằng dữ liệu: `"mode": "code", "code": {"scene": "<beat>", "params": {…}}` — không viết JS.
  **`scene`** = dàn cảnh tự do (actors có keyframe theo u, nhãn bám vật, mũi tên, fx splash/shockwave/burst/smoke/sparkle):
  dùng cho 1–3 khoảnh khắc hành động mỗi video. `layout` đổi bố cục beat mẫu (tool tự xoay nếu bỏ trống). Các shot html
  liền nhau thành **một cú máy liền** (`vidlib/spine.py`); QA `motiongate` báo đỏ khi video "như slide" (< 3,5%).
- `engines/manim/` (Manim CE, không cần LaTeX): `graph`, `vectors`, `equation`, `counter`, `compare`, `title`, `fact`,
  `outro` — style `physics-diagram-black`; beat manim không có thì tự dùng html cùng bảng màu.
- Engine của shot = `code.engine` nếu ghi, không thì theo `code_engine` của style (`engines/adapter.py` là giao diện chung
  cho three | html | manim | board: ShotSpec → Clip có frame đầu/cuối).
- Style mới (đều `*-black`, toàn code): flat-vector, line-boil, isometric, hud, synthwave, sticker-explainer, swiss-motion,
  spy-titles, pictogram, scale-zoom, flowchart, sketchnote, physics-diagram, gallery-pointillist (ánh sáng/màu sắc; trước là tập đặc biệt, giờ vào
  vòng xoay). Thẻ style: `styles/<id>.md` (có mục "nó KHÔNG phải là"). `style: "auto"` chấm điểm theo `tags` của style so
  với chủ đề (kích thước → scale-zoom; nhiệt/lực → physics-diagram; không gian/công nghệ → hud) rồi mới xoay vòng.
- Xem nhanh: `python studio.py styles --gallery` · `python scripts/html_sheet.py <style>` · `python studio.py perf engines`.

## Mỗi video khác nhau (vòng 7b)
- **Style theo chủ đề, chọn TRƯỚC khi viết kịch bản** (`plan.json`, `styles.plan`): có hôm dùng Flow, có hôm toàn code —
  brief ghi rõ "FLOW DAY"/"NO-FLOW DAY". Style motion dùng cho MỌI chủ đề: beat là ngữ pháp chung, đạo cụ có 190 icon chia
  theo mảng kênh (A chạy bộ/cơ thể · B tập tạ · C AI hình ảnh & motion · D công nghệ/dev · lab · vật chất · thiên nhiên ·
  vũ trụ · động vật & đồ ăn…; `engines/html/icons.js` + `icons_channel.js`, brief liệt kê theo nhóm), ~830 từ khoá
  ("marathon" → runner, "pull request" → branch) + icon tự ghép `{"parts": […]}`; tên icon lạ → lỗi kèm gợi ý.
  Soát hình: `python scripts/icon_sheet.py`.
- **Dạng kịch bản xoay vòng** (`vidlib/narratives.py`, `config/narratives.json`): classic, countdown, timeline, myth_fact,
  escalation, journey, versus, rewind, chain_reaction, mystery. Chọn theo chủ đề trong `plan.json` (không lặp 3 video gần
  nhất; tiêu đề "5 things…"/"… vs …" bắt buộc dạng tương ứng); brief §1 ghi "NARRATIVE SHAPE FOR THIS VIDEO" — viết
  ĐÚNG khung đó và ghi `"narrative": "<id>"`. Ép tay: `--narrative <id>`. Ý tưởng (`ideas.json`) có trường `narrative`.
- Ngày có Flow vẫn dùng được beat motion (`counter`, `graph`, `compare`…) với look khớp style (khối `html` trong mọi style).
- **Mỗi video một giọng** (`vidlib/voices.py`, kho `config/voice.json → pools`, 20 giọng tự chọn + 2 giọng nhân vật chỉ chọn
  tay): không lặp 5 video gần nhất, hợp `voice_tags` của style, đổi nam/nữ; giữ ổn định qua các lần chạy
  (`voice_resolved`). atempo tự tính theo nhịp thật của giọng (`vo.speed_auto`, trần 1.15). Video làm trước vòng 7b giữ
  giọng + tốc độ cũ (`legacy`).

## Âm thanh
- `audio.py` chỉ xuất stems (voice/music/sfx); `mix.py` khoá mức theo gated RMS: nhạc −6 dB, SFX ≤ nhạc, đỉnh SFX
  ≤ 0.7× đỉnh giọng (`config/mix.json`, mode `ducking` mặc định, `ratio` = đúng quy tắc kit). Master: một gain tuyến
  tính tới −14 LUFS + limiter true-peak −1 dBTP; độ dài theo video (voice + outro), không `-shortest`.
- Preset payoff ở câu twist: nhạc dừng, hit trầm (`sting_low`), camera ảo push-in + roll.

## QA bắt buộc
Freeze ≥ 0.4 s = lỗi (trừ shot `hold: true`), black frame, loudness, OCR text_fx + chữ trong cảnh, contact sheet,
nét/palette code↔Flow. Engine board thêm: dấu đỏ/nhãn 0–3 frame trước từ khoá, nhãn còn ≥ 0.6 s đọc, đủ glyph, đỏ đo
trên frame là đỏ (không đảo BGR), camera không đứng ≥ 0.4 s, OCR từng chữ board cắt từ video cuối. Tất cả trong
`qa/report.html`.
