# CHANGELOG

## 4.3.0 — 28/11/2026 · Vòng 23: đầu ra gọn · QA tự chặn · người nhiều góc/nhiều kiểu · giọng + tông · kịch bản giữ chân

Kế hoạch `docs/ROUND23_PLAN.md`, báo cáo `docs/ROUND23_REPORT.md`.

- **Dọn dung lượng** (~8,3 GB → ~0,5 GB không tính .git): khung render/version/gói trùng của 13 dự án, `.venv` bản macOS
  (không chạy trên Windows), repo tham khảo trong `vendor/` (tải lại bằng `scripts/vendor_fetch.py`), ảnh QA sinh ra.
- **Đầu ra gọn** (`channel.json → output.lean`, `vidlib/lean.py`, `studio.py clean <slug|--all> --lean`): sau khi qua cổng QA
  chỉ còn `out/final.mp4` + `out/cover-16x9.jpg` + `out/captions.srt` + `out/post.md` (tiêu đề/mô tả/tag/caption theo YouTube
  Shorts, TikTok, Instagram/Facebook Reels + nguồn + cài đặt đăng). Bỏ bước thừa: 3 bản MP4 giống nhau, version vNNN,
  15 ảnh bìa, báo cáo QA (cổng đỏ thì giữ để sửa).
- **QA tự chặn** (chủ kênh không đọc QA): chữ còn đè hình > 30% (engine tự báo `labelReport`), video "như slide"
  (< 4,5% khung chuyển động nhanh), OCR < 80%, số liệu thiếu nguồn, SEO < 70, và mới: **hook** (≤ 16 từ, có khoảng trống
  tò mò, không mở đầu chậm), **kịch bản giữ chân** (không câu độn/xin like, có re-hook giữa video, kết ngắn hoặc nối
  về đầu, câu ≤ 24 từ), **diễn viên** (≥ 2 góc nhìn khi ≥ 4 shot người, người chính không trùng video trước) —
  `vidlib/retention.py`, chặn cả ở linter trước khi render.
- **Người tả thực**: góc **chính diện / sau lưng** (`view`, đổi được theo key) cho idle/đi/chạy/nhảy/vẫy/chỉ/mệt/curl/squat/
  deadlift/ngồi; 9 người mới (coach, lifterf, bigguy, elder, student, office, cyclist, medic, trailrunner); tóc afro/đầu
  đinh/mũ bảo hiểm, râu, kính, trang phục hoodie/sơ mi/áo đấu/áo blouse; **deadlift** (gập hông, đòn thẳng đứng);
  **đạp xe** sửa gối gập ngược → gối ra trước, khuỷu gập xuống; squat bàn chân đứng yên, tay nắm đòn sau gáy, bánh tạ
  không che mặt; curl cầm tạ đơn đúng tư thế.
- **Giọng**: 27 giọng Neural khác nhau (trước 22 tên dồn vào 5 giọng), tông riêng mỗi giọng (tốc độ/cao độ), tông theo
  vai câu (`voice.json → edge_tone`: hook nhanh/sáng, payoff chậm/trầm) — đọc từng đoạn rồi nối, mốc từng từ khớp.
- **Motion**: cảnh không khai camera tự đẩy chậm + trôi về vật chính (`auto_camera`). Cổng chuyển động tính ngưỡng theo
  độ sáng video (look tối không bị phạt oan), thêm "> 25% cặp khung đứng yên" và **video quá tối** (< 8/255) → đỏ.
- Nhãn né theo **từng mảnh hình** (`iconParts`), đúng góc nhìn và camera bám bộ phận; lưới chỗ thử tới ±720 px.
- Brief: luật giữ chân + cách chọn diễn viên/góc nhìn. Làm lại 13 video (người chính khác nhau mỗi video, ≥ 2 góc, hook
  và re-hook mới).

## 4.2.1 — 28/11/2026 · Vòng 22 (bổ sung): nhãn né vật

Duyệt lại 13 video vòng 22: chữ còn đè lên vật (nhãn chỉ né nhãn khác và kính lúp).

- **Beat `scene`**: nhãn tự do và nhãn bám vật chọn chỗ ít đè nhất (dưới/trên/trái/phải vật; nhãn tự do: lưới dời quanh
  chỗ đặt, phạt theo quãng dời) từ quỹ đạo keyframe + camera của cảnh — chọn MỘT LẦN cho cả đời nhãn (không nhảy giữa
  frame, worker nào cũng giống nhau). Vật cản: hình (khung bao thật `iconBox` trong `core.js`, rig người đối xứng), kính lúp,
  tag tiêu đề kính, nhãn chọn trước. Không còn chỗ trống → lót nền tối mờ sau chữ. `labels[].fixed: true` giữ đúng chỗ.
- Tag tiêu đề kính lúp: dưới/trên kính + dời ngang, chừa khe theo chiều cao thật của tag (tag 2 dòng từng đè viền kính).
- Lượt chống chồng mỗi frame dùng cùng hình hộp với bước chọn chỗ và dời tối đa 160 px (trước đây đẩy nhãn tụt cả nửa khung).
- Sửa bố cục 4 video (twos, wall, shorter, hồng cầu) cho vật nhỏ lại/lên cao chừa chỗ chữ; render lại 13 video.

## 4.2.0 — 28/11/2026 · Vòng 22: hình nhận ra được · người tả thực · bối cảnh đêm · kính lúp · rủi ro YouTube

Góp ý chủ kênh cho 11 video (26–27/11) + rà rủi ro ban/giảm hiển thị. Kế hoạch `docs/ROUND22_PLAN.md`, báo cáo
`docs/ROUND22_REPORT.md`, căn cứ chính sách `docs/YOUTUBE_RISK.md`.

- **Rủi ro YouTube** (`vidlib/policy.py`, `studio.py policy`): khoá khung (beat + bố cục + đạo cụ + bối cảnh) so 10 video
  trước → dòng QA "khung lặp giữa các video" (đỏ ≥ 40%); lặp trong video; persona sức khoẻ (mệnh lệnh/liều lượng/tự xưng
  chuyên gia); số trong tiêu đề/thumbnail phải có trong lời đọc (đọc cả số bằng chữ); từ giật gân; spam/kéo tương tác;
  Made for Kids. Upload + publish.md tự thêm "Educational content, not medical advice." cho video sức khoẻ.
- **Đạo cụ chi tiết** (`engines/html/icons_detail.js`): ~47 vật vẽ bằng path SVG có tô bóng, ghi đè bản đơn giản cùng tên.
- **Người tả thực** (`engines/html/rig_human.js`): 6 loài, dáng đi/chạy theo đường cong góc khớp sinh cơ học, chạm đất
  đúng, đạp xe (IK chân theo bàn đạp, tay theo ghi đông), x-ray cột sống/cơ/mạch/nhiên liệu/gan; vai màu `skin`/`hair`.
- **Bối cảnh đêm** 2D (`engines/html/backdrops.js`, 8 loại, lớp tĩnh vẽ sẵn → nhanh ~10×) + 3D (`set: gym | bedroom`).
- **Beat `scene`**: kính lúp `lenses`, `freeze`, nhãn tự né nhau + kẹp vùng an toàn, tag tiêu đề kính lúp kẹp mép.
- **Nhịp**: profile `explainer` (shot 4–6.5 s, hook ≤ 5.6 s), `vo.target_wps` 2.8, không punch-in tự chèn cho shot
  code, kiểu bay spine êm (`spine.CALM`); viral score đếm khung khác nhau thay vì loại beat và thôi gợi ý khung mẫu.
- Look nét (boil, sketch…): nét vai `bg` tự thành màu mực (hình vẽ trong khung phim/tờ giấy không biến mất).
- Làm lại 13 video từ 26/11 (+ caffeine) với kịch bản và nguồn kiểm lại.

## 4.1.0 — 27/11/2026 · Vòng 21: zoom xuyên bộ phận · nhân vật có bộ phận sống · sổ dữ kiện có nguồn · SEO Shorts · trung lập thương hiệu

Prompt: `docs/ROUND21_PROMPT.md` (Claude Opus 5.5 xhigh). Kiểm định vòng 19–20 ở mục 1 của prompt.

- **Trung lập thương hiệu**: style `kurzgesagt-black` / `school-of-life-black` / `infographics-show-black` → `cosmic-flat-black`
  / `essay-ink-black` / `bold-infographic-black` (look `cosmic` / `essay` / `bold`); tên cũ là bí danh
  (`textstyle.STYLE_ALIASES`, `looks.js → LOOK_ALIASES`). Bỏ bí danh rig `kurzbird`. Brand-safety (`vidlib/seo.py`):
  tên kênh/studio tham chiếu trong chữ khán giả thấy = **lỗi chặn** ở bước prompts + dòng đỏ ở cổng QA.
- **Rig 2D có bộ phận** (`engines/html/rig2d.js`): `PARTS` (21 điểm neo) + `rigAnchors()` theo đúng dáng frame;
  `xray` + `organs` (não, tim đập theo `bpm`, phổi thở, dạ dày, xương); miệng nói (`talk`); mắt nhìn theo (`gaze`);
  chống trượt chân (pha bước theo quãng đường); cú/vịt/nhà khoa học có đặc điểm riêng (túm lông + đĩa mặt; mỏ dẹt +
  chân màng; áo blouse + kính).
- **Beat `scene`**: tham chiếu `"id.part"` ở labels/arrows/fx/camera/look_at; camera `at` + `zoom` (0.5–40, vector
  sắc nét, nhãn tự lui); `focus`, `hold`, `talk`, `look_at`; nhãn `bubble: speech|thought`; nhãn có `out`.
- **Chuyển cảnh `zoom_through`** + `through` (`vidlib/partzoom.py`): html→html trong cú máy liền = kiểu bay `portal`
  (ô sau nằm trong bộ phận, lộ qua lỗ tròn rồi nở ra — vẽ lại vector); mọi cặp khác = hậu kỳ (đuôi lao về điểm neo đọc
  từ `meta.json → anchors_end`, đầu shot sau mở qua lỗ tròn). SFX `swish_match` tự thêm.
- **3D**: `stage` `frame.dive {of, part, u, dist, fov}` — camera tự căn khung rồi lao vào đầu/mắt/ngực của prop.
- **Sổ dữ kiện** (`vidlib/facts.py`): `sources` có cấu trúc + `claims` + shot `claims`; lint nguồn yếu/thiếu URL/
  không rào đón/số lệch claim/khẳng định tuyệt đối/tỉ lệ phi thực tế; chip "Source: …" trên màn; `qa/facts.md`;
  `python studio.py facts <slug>`. Brief `--ai claude` bật **web search + web fetch** (`web_search_20260209`,
  `web_fetch_20260209`, xử lý `pause_turn`) và ghi URL thật vào `work/research.json` để đối chiếu.
- **SEO** (`vidlib/seo.py`): từ khoá chính trong tiêu đề/câu đầu mô tả/lời đọc 1–2 shot đầu, 2–4 hashtag, tag ≤ 500
  ký tự, dòng nguồn trong mô tả; `publish.md` có mục SEO check; upload YouTube đặt category theo chủ đề,
  `status.containsSyntheticMedia`, `localizations`.
- Công cụ kiểm hình: `scripts/parts_sheet.py`, `scripts/portal_check.py` (→ `qa/round21/`).

## 3.9.0 — 23/11/2026 · Vòng 10: 90s Low Poly + 10 Style Viral · Bộ não Motion · Kho tài sản CC0/MIT · Hybrid 2D ↔ 3D · UI không copy/paste · Dọn repo

- **3D thời 90 & Nhân vật 3D (WP-T)**:
  - Look `retro90` (N64) và `psx` (PS1) trong `engines/three/main.js → LOOK3D`: shader Gouraud tính sáng theo đỉnh, lượng tử màu + Bayer 4×4 dither, rung đỉnh `wobble`, nội suy texture affine, chữ HD cho OCR (`text_hd`), bóng tròn `blob`.
  - `engines/three/creatures.js`: 22 loài con vật + người (`dog`, `dachshund`, `cat`, `fox`, `wolf`, `bear`, `rabbit`, `mouse`, `pig`, `cow`, `horse`, `sheep`, `chicken`, `penguin`, `fish`, `frog`, `turtle`, `dino`, `kid`, `adult`…) × 13 dáng × 9 biểu cảm, mặt vẽ trên texture, tai/đuôi trễ pha.
  - Bối cảnh mới (`set`): `meadow` (đảo cỏ nổi tan vào đen), `tabletop`, `street`. Style chủ lực `styles/retro90-lowpoly-black.json` (html look `pixel16`).
- **Look 2D mới & Nhân vật 2D (WP-H1)**:
  - 7 look mới (`halftone`, `comic`, `pixel16`, `sprite8`, `silhouette`, `cutout`, `lineart`) + pass WebGL2 `engines/html/post2d.js`.
  - `engines/html/rig2d.js` + `rig2d.py`: 17 loài nhân vật hoạt hình 2D (`"icon": "rig:<loài>"`), 12 hành động, 8 biểu cảm.
  - 6 style mới (`halftone-print-black`, `vintage-comic-black`, `pixel16-black`, `sprite8-black`, `ink-silhouette-black`, `paper-cutout-black`) + 2 font OFL (`PressStart2P`, `PixelifySans`).
- **Beat/bố cục mới & Chiều sâu 2D (WP-H2)**:
  - Mở rộng `engines/html` lên **15 beat** và **29 biến thể bố cục** (`title` 5, `counter` 7, `compare` 7, `fact` 5, `process` 5) + 4 beat cơ chế mới (`units`, `timeline`, `split`, `meter` điện tim theo BPM thật).
  - Chiều sâu 2D trong `scene` (`z`, parallax, DOF, không khí, camera dolly/truck/roll/rack focus).
- **Bộ não Motion & Chống lặp giữa video (WP-M)**:
  - `lib/motion` (JS + Python parity 100%): **58 động từ chuyển động (`verb`)** + 7 mẫu `stagger`.
  - `config/metaphors.json`: **175 cơ chế hình ảnh** tự kiểm từ vựng động với engine.
  - `vidlib/motionplan.py`: chữ ký motion từng video, lịch sử kênh tránh lặp bố cục/kiểu bay/cơ chế, brief ưu tiên cơ chế trước số liệu, `spine.py` thêm 6 kiểu bay mới, báo cáo `docs/MOTION_AUDIT.md`.
- **Kho tài sản CC0 / MIT (WP-A)**:
  - Vendor three.js r160 addons (`GLTFLoader`, `SkeletonUtils`, `BufferGeometryUtils`), `engines/three/models.js`, `vidlib/assets3d.py`, `studio.py assets [search|fetch|sheet|check]`.
  - 479 mô hình 3D CC0 (Kenney/KayKit/Poly Haven) + 926 icon SVG Phosphor MIT (`assets/lib/3d/` & `assets/lib/svg/phosphor/` gitignored, dựng lại qua script).
- **Hybrid 2D ↔ 3D (WP-X)**:
  - `engines/three/hybrid.js`: prop `card2d` (2D động trong 3D, HD-2D), `multiplane` (cắt giấy nhiều lớp 3D), `overlay2d` (nhãn/mũi tên 2D bám prop 3D + OCR `textBoxes`), hậu kỳ 3D theo look 2D, và nối `do: [{verb}]` vào prop 3D `stage.js`.
- **UI không cần mở source copy/paste (WP-U)**:
  - `vidlib/sbedit.py` + `studio.py sb check|import|patch|history|restore|preview` + `studio.py ideas import`.
  - Giao diện web (`ui/server/app.py`, `ui/web/app/pages/*`): Copy brief 1 click, dán/kéo-thả JSON storyboard/ideas có kiểm lỗi theo trường/dòng, Lưu & chạy tiếp, lịch sử hoàn tác, Properties panel sửa shot + Xem trước 1 frame, thẻ "Việc tiếp theo", tab **Kho Vòng 10** & tab **API Keys** (ghi `.env` cục bộ).
- **Dọn file/quy trình dư (WP-C)**:
  - Lưu trữ 12 tài liệu lịch sử vào `docs/archive/`, xoá 9 script macOS/một lần, cập nhật `docs/CLEANUP_PLAN.md` và `docs/research/REPO_BEST_PRACTICES.md`.

## 3.8.1 — 18/11/2026 · Sửa lỗi đường board, SMAA mặc định, thumbnail từ frame code, số thập phân

- **Board render ra 30.015 fps (cổng QA "fps" đỏ)**: `render_full` nối các đoạn bằng concat mà không khai độ dài, nên
  concat tự đoán từ container (có trễ B-frame, không edit list). Mỗi chỗ nối hụt 10 tick (1/15360 s). Giờ ghi
  `duration` chính xác (số frame / fps) cho từng đoạn → 30/1, mọi bước frame đều 512 tick.
- **Board vượt trần bitrate nền tảng (24.9 > 20 Mb/s, gói giao đỏ)**: mỗi đoạn ~1 s encode riêng với VBV riêng, nên mỗi
  đoạn được "vốn" bộ đệm ban đầu. Giờ các đoạn encode `intermediate` (gần như không mất), nối lại rồi encode master MỘT
  lượt cho cả video → 16.4 Mb/s. Smoke `board` lại chạy hết (exit 0).
- `scripts/smoke.py` đọc nhãn QA mới ("Cổng QA") — trước đó cột QA/thời lượng luôn "—".
- **SMAA mặc định** cho mọi look 3D (`world.look3d.post` = {smaa: true} trừ khi style ghi `"post": false`). Golden three.js
  cập nhật (SSIM so với bản cũ 0.9985–0.9995: chỉ mép nét).
- **Thumbnail video toàn code**: nền lấy frame thật của shot code (ưu tiên shot nhiều hình: scene/stage/callout…) thay vì
  motif "bậc thang"; chỉ định tay bằng `thumbnail.variants[].frame: {"shot": "C05", "u": 0.6}`.
- **Số thập phân của `compare`/`scale` html**: đọc `decimals` riêng của mục → `decimals` chung của beat → tự đếm từ giá trị
  (tối đa 2). Trước đây 1.33 hiện thành "1" nếu quên `decimals` ở từng bên.

## 3.8.0 — 18/11/2026 · SVG, Lottie, Rive, hậu kỳ postprocessing, bộ easing chuẩn

Phần còn lại của danh sách 20 repo (`docs/STYLE_AUDIT.md` mục 7): lấy mọi thứ thêm được năng lực thật mà vẫn giữ hàm
thuần theo frame và không cần Node/build lúc render. Gói npm tải về đều khớp integrity, chọn bản ≥ 2 tuần tuổi, không chạy
script cài.
- **SVG** (`vendor/svgo` 4.1.0): `python studio.py svg <file.svg> [--name] [--role] [--license]`.
  - SVGO dọn file (style → thuộc tính, hình → path, lệnh tuyệt đối), rồi Edge đo hình học (`engines/html/svgimport.js`).
  - Ra `parts` toạ độ -1..1, vai màu tự nhận (xám = ink, đỏ–vàng = hot, lam = cold, khác = accent), lỗ (`holes`), viền
    hở thành `line`. Lưu `assets/user/svg/<tên>.json` + bản gốc.
  - Dùng `"icon": "svg:<tên>"` mọi chỗ nhận icon (vẽ bằng bút của từng look: boil, sketch, iso…). `stage` prop
    `"type": "svg:<tên>"` ép khối 3D, lỗ thật, viền thành ống liền.
- **Lottie** (`vendor/dotlottie` 0.82.0) và **Rive** (`vendor/rive` 2.49.0): actor `"lottie"`/`"rive"` của beat `scene`
  (`engines/html/media.js`).
  - Lottie: `setFrame` đồng bộ. JSON được đổi màu theo vai (`colors: palette | <vai> | keep`), WASM nạp từ máy.
  - Rive: chạy từ 0 theo lưới 1/120 s, nên frame render lẻ trùng từng pixel với frame render liền (đã đo: sai khác 0).
- **Hậu kỳ 3D** (`vendor/postprocessing` 6.38.3, import map `three`): `world.look3d.post` {smaa, ca, bloom} tuỳ chọn.
  - SMAA chờ ảnh tra cứu nạp xong trước `ready`.
  - Bloom mặc định giữ nền #000 (đo góc nền = 0).
  - Không khai thì đường dựng cũ y nguyên.
- **Easing** (học từ GSAP/Anime.js/Motion, không nhúng thư viện): `lib/motion` thêm bounceOut, elastic, expoOut, circOut,
  sine, backIn, steps (JS = Python, test đối chiếu). Engine html nhận cả bộ (`EASE` = `MO.M` + tên riêng của look).
- `vidlib/userassets.py`: tên → dữ liệu engine lúc dựng job; kiểm tên khi validate storyboard; brief liệt kê tài sản đang
  có; linter nhắc tài sản thiếu ghi chú giấy phép. Server render thêm MIME `.wasm`/`.riv`/`.lottie`.
- `tests/test_userassets.py` (8 test; ca trình duyệt cần `STUDIO_VISUAL=1`), fixture `tests/fixtures/svg|lottie|rive/`.
- Không lấy (lý do ở STYLE_AUDIT mục 7): Remotion, Motion Canvas (engine thứ năm + Node/build), React Three Fiber/Drei
  (React), Howler (phát tiếng trong trình duyệt), Mediabunny (encode trong trình duyệt, mất RESUME), Satori, các repo skill.

## 3.7.0 — 18/11/2026 · Vật lý thật cho cảnh `stage` (Rapier)

Rà soát danh sách 20 repo motion/3D/âm thanh (chi tiết: `docs/STYLE_AUDIT.md` mục 7): chỉ Rapier (lõi của React Three
Rapier) thêm năng lực mới. Engine three.js trước đó **không có dòng vật lý nào**, nên mọi cú rơi, nảy và va chạm đều phải
đặt keyframe tay.
- `vendor/rapier/rapier.mjs`: Rapier 3D bản **tất định đa nền tảng** 0.21.0 (Apache-2.0, WASM nhúng; tarball khớp
  integrity npm, không chạy script cài). `main.js` chỉ nạp khi params có `physics`/`body`; cảnh khác không đổi.
- `engines/three/physics.js`:
  - Collider dựng từ chính hình 3D của prop (ball/box/cylinder/capsule/bao lồi/trimesh).
  - 10 vật liệu (khối lượng riêng, độ nảy, ma sát, cản khí; lông vũ/giấy chao bằng lực tất định).
  - `release` (theo keyframe rồi bay tiếp với đà) · `kind: kinematic` (theo keyframe, đẩy vật khác) · `fixed` · `push`.
  - `hit_u` tự tìm frame thả để **cú chạm đầu rơi đúng u** (đơn điệu + chặn hai đầu, đúng cả khi có slow-mo; cần thì
    mô phỏng từ trước shot).
  - `slowmo` vào/ra mượt.
  - Va chạm → cue SFX theo vật liệu/khối lượng, kick camera (3 cú mạnh nhất), hạt một đợt (`fx3d once`: vòng bụi sát
    sàn, tia). Va chạm cách nhau ≤ 2 frame gộp thành một cú.
- `stage.js`: mô phỏng MỘT LẦN trong `build`, `frame(f)` đọc quỹ đạo, nên cảnh vẫn là hàm thuần theo frame (render song
  song/RESUME an toàn). Camera tự căn lấy mẫu 5 thời điểm khi có vật lý. Schema ở đầu file, nên brief tự có.
- `adapter.stage_physics_errors` kiểm dữ liệu storyboard (từ vựng đọc từ `physics.js`).
- `scripts/physics_sheet.py`: hai thí nghiệm mẫu (thả bi/hộp/lông vũ; bi thép lăn vào tháp 10 hộp). Mỗi cảnh dựng bằng
  keyframe tay và bằng vật lý, ra `qa/physics/compare.mp4` có tiếng, `sheet.jpg` và `report.md`.
  - Đo trên máy này: 120 frame/bản ~6.5 s, vật lý không làm chậm.
  - Thả bi 1 m chạm ở frame 13 (lý thuyết 13.5).
  - Tháp đổ: hit_u muốn frame 50, chạm đúng frame 50.
- `tests/test_physics.py` (9 test) + `tests/fixtures/stage_harness.mjs` (chạy `stage` trong Node).

## 3.6.0 — 15/11/2026 · Trộn engine trong một video · 9 look 3D · giao diện web · sắp xếp thư mục

### Trộn 3D + chart + sơ đồ trong MỘT video (rà soát phần Gemini làm + sửa)
- Đã có từ trước: mỗi shot tự đi engine của nó. Phần mới (Gemini): `stage` có nhân vật 3D khớp nối (`mannequin`,
  `runner3d`, `lifter3d`, `pose`), ~54 đạo cụ 3D theo mảng kênh, icon html ép khối (`icon3d`), `parts`, `fx[]` hạt 3D,
  `set: track`; three.js/Manim tự lấy palette html khi style không khai `world`/token manim; style `clay3d-black`.
- Kiểm thử bằng `projects/demo-hybrid-3d` (13 shot: 4 three.js + 8 html + 1 Manim): chạy hết pipeline nhưng có lỗi thật:
  - **Định tuyến sai cảnh trùng tên**: C11 `scale` (thang kích thước html, `items`) bị dựng bằng cảnh cân đĩa three.js →
    video hiện "100 G STEEL / 75 G ICE" lạc đề mà QA vẫn ĐẠT. Sửa: `codeshot.engine_of` xét params
    (`adapter.three_param_names` đọc dòng `// params:`).
  - **Brief nói sai tên cảnh** (`gauge` không phải cảnh three.js) → LLM viết storyboard lỗi. Thay bằng khối **MOTION MIX**
    sinh từ danh sách cảnh thật (`brief.mix_help`), kèm nguyên tắc: 3D cho 2–4 khoảnh khắc cần chiều sâu, số liệu ở chart
    2D, đổi engine ở chỗ đổi nhịp kể.
  - **Manim trong style khác**: nhãn vector nằm ngang đè lên vật + màu xanh navy chìm trên nền đen (OCR "AIR DRAG" 57%).
    Nhãn đặt trên thân mũi tên, nằm giữa mép vòng và mép khung; nhãn vật vừa trong vòng; màu tối được nâng sáng
    (`manim._lift`). OCR → 100%, QA ĐẠT.
  - Phần trả lời của Gemini có vài lệnh/tên không tồn tại (`studio.py plan`, `storyboard_brief.txt`, beat `anatomy`/
    `timeline`, cảnh `sizzle`, params `dx/dy`): không nằm trong code, chỉ trong lời giải thích — đã thay bằng tài liệu đúng
    (HUONG_DAN mục 7e).
- `tests/test_hybrid.py`.

### 9 look 3D cho engine three.js (`world.look3d`)
- `engines/three/main.js → LOOK3D`: `toon` (cũ, mặc định) · `clay` (matte + vân bump) · `plastic` (clearcoat) · `glass`
  (transmission + fresnel) · `chrome` (metalness 1, softbox rộng) · `lowpoly` (hình học ít cạnh + flat shading) · `paper`
  · `holo` (wireframe phát sáng) · `xray` (fresnel cộng sáng). Env map "studio" dựng bằng code (softbox trắng + dải rim màu
  accent), tone map ACES, bloom theo mip, grain nhân theo độ sáng (nền đen vẫn #000). Style cũ không đổi hình.
- 7 style mới: `plastic-toy3d-black`, `papercraft3d-black` (có Flow, prompt Flow 3D), `glass3d-black`, `chrome3d-black`,
  `lowpoly3d-black`, `hologram3d-black`, `xray3d-black` (toàn code); `clay3d-black` dùng look `clay`. Tổng 34 style.
- `scripts/props3d_sheet.py` → `qa/props3d/<style>.jpg`. Demo `projects/demo-hybrid-xray` (cùng kịch bản, style X-quang): QA ĐẠT.
- Trang "3D Style Atlas" của Futurepedia chặn truy cập tự động (HTTP 403) nên chưa lấy được 37 style/prompt của trang đó;
  9 look trên dựng từ các kiểu 3D explainer phổ biến.

### Giao diện web (`ui/`, `python studio.py ui`, `ui.bat`)
- Backend Python thuần (`ui/server/`): API dự án/style/giọng/dạng kịch bản/kế hoạch, hàng đợi job chạy `studio.py`
  (danh sách trắng lệnh + tham số), log trực tiếp SSE, huỷ cả cây tiến trình, tải clip Flow theo shot, file có Range.
  Chỉ nghe 127.0.0.1, chặn DNS rebinding/CSRF/path traversal, không lộ key.
- Frontend ES module thuần (`ui/web/`): design token (tối/sáng), thư viện component, tổ chức theo tính năng — Tổng quan,
  Tạo video (xem kế hoạch trước), Dự án (thanh bước, việc tiếp theo theo trạng thái, thanh trộn engine, tab Shot với kéo
  thả clip, Kết quả, QA), Ý tưởng, Style/Giọng/Dạng kịch bản, Job, Cài đặt. `tests/test_ui.py`.

### Sắp xếp thư mục
- `engine/` → `engines/three/`: bốn engine dựng nằm chung `engines/` (three, html, manim, board) cạnh `adapter.py`.
- `fonts/*.otf` → `assets/fonts/` (một thư mục font; `brand/style.json` cập nhật).
- `docs/ARCHITECTURE.md`: bốn tầng (giao diện → pipeline → engine → dữ liệu) + bản đồ thư mục + "thêm X ở đâu".
- Mã engine three.js đổi (look 3D, đường dẫn) → shot three.js của dự án cũ dựng lại khi chạy lại (RESUME theo hash).

## 3.5.0 — 15/11/2026 · Chống "video nào cũng như slide"

Chẩn đoán: các video toàn code (engine html) dùng chung một mẫu bố cục (tiêu đề trên, một icon giữa, nhãn dưới) và
chung một khung kể. Đo tỉ lệ khung hình có chuyển động nhanh: html bản cũ 1–4%, clip Flow 55–67%, phim demo MG 26–39%.

### Một cú máy liền (`vidlib/spine.py`, `engines/html/core.js`)
- Các shot html liền nhau là các ô trên một canvas lớn. Camera bay liền qua điểm cắt bằng các kiểu: lia ngang/dọc, chéo
  nghiêng, xoay 90°, lao vào vật ở giữa ô trước, kéo lùi ra. Nội suy zoom theo log, không cắt cứng.
- Kiểu bay xáo theo từng video (hạt giống = slug) và theo ngữ pháp của look: swiss chỉ lia thẳng, sketchnote cuộn dọc,
  scale-zoom lao vào/kéo ra.
- Mỗi shot chỉ cần biết ô trước/sau (`job.json → spine`) → vẫn render song song + RESUME.
- `render.py` không chồng transition giữa hai shot cùng cú máy.
- **Manim cũng vào cú máy liền**: shot Manim nằm cùng chuỗi với shot html. Manim dựng xong thì frame trong chặng bay
  được warp affine theo đúng camera của html (`spine.travel_matrix`, cùng công thức `interp`). Khung chữ cho OCR được
  biến đổi theo. Với shot html, hàng xóm Manim là "ô ma": camera vẫn bay qua nhưng html không vẽ lại sơ đồ Manim.
  Ca smoke Manim: 0,7% → 5,8%.
- Camera trong ô có reframe (đẩy + nghiêng nhẹ giữa shot) thay vì đứng yên.

### Dàn cảnh và bố cục
- Beat mới **`scene`**: nhiều đạo cụ/nhân vật di chuyển theo keyframe (u 0..1 của shot), nhãn bám vật, mũi tên nối vật,
  fx `splash|shockwave|burst|smoke|sparkle` kèm SFX.
- Nhãn bám vật kẹp trong vùng an toàn theo bề rộng chữ thật (trước đây nhãn dài bị cắt mép phải).
- **Biến thể bố cục** (`layout`): `title` center/left/hero · `counter` ring/giant/bar · `compare` bars/split/balance ·
  `fact` center/stamp/left · `process` list/path. Shot không ghi `layout` → tool xoay theo video và theo thứ tự shot
  cùng beat (`codeshot.assign_layouts`).
- Đạo cụ mới `kidney` (thận). Tổng 190 đạo cụ.
- HUD: viên nhãn rộng hơn (`maxW` 940) để dấu `]` không rớt dòng.

### Dạng kịch bản xoay vòng (`vidlib/narratives.py`, `config/narratives.json`)
- 10 khung kể: `classic`, `countdown`, `timeline`, `myth_fact`, `escalation` (×10 mỗi bước), `journey`, `versus`,
  `rewind`, `chain_reaction`, `mystery`.
- Mỗi khung có cách kể (`shape`) và hình hợp nó (`visual`, cho cả ngày code lẫn ngày Flow), đưa vào brief §1.
- Chọn trong `plan.json` theo nhãn chủ đề, không lặp 3 video gần nhất. Tiêu đề "5 things…", "… vs …", "after 72 hours…"
  bắt buộc đúng khung dù vừa dùng. Ý tưởng trong `ideas.json` gợi ý khung qua trường `narrative`.
- Khung kể ảnh hưởng cả camera: `timeline` lia phải như trục thời gian, `versus` lia qua lại, `escalation` lao vào vật.
  Danh sách này giao với ngữ pháp của look; giao rỗng thì theo look.
- Lệnh mới: `--narrative <id>`, `python studio.py narratives ["<chủ đề>"]`. `styles --plan` hiện thêm khung kể.
- Dự án cũ (không có trường `narrative`) giữ nguyên.

### QA chống slide (`vidlib/motiongate.py`)
- Đo tỉ lệ cặp khung có chuyển động nhanh (12 fps, 320 px, lệch xám ≥ 9; cắt cứng không tính).
- Dưới 3,5% → đỏ, CẦN XEM. Dưới 6% → vàng. Ngưỡng ở `config/channel.json → qa.motion_red / motion_yellow`.
- Kết quả ghi vào `work/motion_gate.json` và report.

### Đo trên video thật
- `the-marathon-danger-hiding-in-your-water-bottle` dựng lại (giữ giọng cũ; C03, C05 đổi sang `scene`): 3,4% → **15,0%**,
  độ lệch khung trung vị 0,44 → 2,3. So sánh cùng mốc thời gian: `qa/_water_before_after.jpg`.
- `_demo-no-sleep`: → 11,5%.

## 3.4.1 — 14/11/2026
- `gallery-pointillist-black` không còn là "tập đặc biệt": vào vòng chọn tự động theo chủ đề (ánh sáng, màu sắc, cầu vồng,
  lăng kính, hoàng hôn, cực quang, pháo hoa, phát quang sinh học…). Cơ chế `special` vẫn còn cho style khác.

## 3.4.0 — 14/11/2026 · Chốt dự án: bộ đạo cụ theo mảng kênh + kiểm tra toàn bộ

### Đạo cụ (engine html) — 77 → 189, chia theo các mảng của kênh
- `engines/html/icons_channel.js` (mới): đạo cụ cho **A chạy bộ & cơ thể** (runner có tay chân chuyển động, shoe, stopwatch,
  ecg chạy ngang, lungs thở, mitochondria, oxygen, bloodcell, smartwatch, bathtub, medal, trophy, flag, track…), **B tập tạ**
  (dumbbell, barbell, kettlebell, lifter squat theo nhịp, weightplate, shaker, muscle, calendar, trendup/down, target),
  **C AI hình ảnh & motion** (camera, videocam, clapper, play, film, image, layers, bezier, keyframe, timeline, wand,
  sparkle, palette, cursor, mic, waveform, frame, brush), **D công nghệ & dev** (code, terminal, bug, database, server,
  plug, lock, key, branch, document, scan có vạch quét, network, keyboard, window, folder, check, cross, question,
  spinner), **phòng thí nghiệm** (beaker, burner, petri, dropper, belljar, nitrogen, goggles, gauge, pendulum, lever, anvil,
  bowlingball, feather, extinguisher), thiên nhiên/vũ trụ/động vật/đồ ăn (smoke, shockwave, iceberg, cactus, rock, asteroid,
  astronaut, wind, raincloud, solarpanel, windturbine, apple, banana, elephant, whale, shark) + nhân vật **scientist** của
  kênh, flask, testtube, microscope, telescope, magnifier, balance, ruler, earth, bed, cup, hourglass, speaker, radiation,
  umbrella, chart, syringe, candle (icons.js).
- Vẽ lại đạo cụ yếu: bird, blackhole, plant, snow, tooth, crack, brain, ice. Hình elip xoay được (`rot`).
- `GROUPS`: mỗi đạo cụ thuộc đúng một nhóm → brief liệt kê đạo cụ **theo mảng chủ đề** cho người viết kịch bản.
- ~830 từ khoá; khớp **cụm dài trước** ("magnifying glass" → kính lúp, không phải cốc), chuỗi con chỉ với từ ≥ 4 ký tự
  ("nope" không còn khớp "no"); không từ khoá nào trỏ hai đạo cụ. JS và Python dùng cùng thuật toán (test đối chiếu bằng node).
- Sửa lỗi: tuỳ chọn độ dày nét `w` của hình chữ nhật ghi đè chiều rộng (làm méo track, dropper, syringe).
- `python scripts/icon_sheet.py [style,…]` → `qa/icons/<style>.jpg`: bảng xem mọi đạo cụ theo từng look (beat nội bộ `catalog`).

### Kiểm tra toàn bộ (`python scripts/smoke.py` → `qa/smoke.md`)
- Smoke test mọi đường dựng ở chế độ dry-run: ngày có Flow (Flow + three.js + beat html theo look của chalk), evidence board
  (thẻ html được ghim), three.js toàn code, Manim (+ html dự phòng), html với đạo cụ tự ghép.
- Tìm và sửa: tham số sai của cảnh three.js (vd `beat` không có trong cảnh `vacuum`) làm render crash → giờ báo lỗi ngay ở
  bước storyboard (đọc danh sách giá trị từ dòng `// params:` của cảnh). QA "frame đen" dùng ngưỡng của kênh nền đen
  (`qa.black_pic_th = 0.997`; mặc định ffmpeg 98% báo nhầm đồ thị nét mảnh).
- Manim vào `requirements.txt`; máy chưa cài Manim → chế độ tự chọn bỏ qua style Manim. README viết lại theo hiện trạng.

## 3.3.0 — 14/11/2026 · Vòng 7b: mỗi video một style và một giọng khác nhau

- **Kế hoạch trước khi viết kịch bản** (`projects/<slug>/plan.json`, `styles.plan`): style chọn theo chủ đề (`tags` của mọi
  style, có xét đuôi từ: sleeping → sleep), không lặp 3 video gần nhất, và **cân ngày có Flow / ngày toàn code**
  (`channel.json → styles.flow_share = 0.5`, `balance_window = 6`). Brief báo cho người viết "FLOW DAY" / "NO-FLOW DAY"
  + style + giọng → kịch bản viết đúng loại shot. `styles.default` đổi sang `auto` (dự án tiếng Việt cũ giữ `forward`).
- Cờ mới: `--style <id>`, `--voice <tên|id>`, `--flow`, `--no-flow`; lệnh `python studio.py voices [--for <style>]`,
  `styles --plan "<ý tưởng>"`.
- **Mỗi video một giọng** (`vidlib/voices.py`): kho 22 giọng tiếng Anh lấy từ tài khoản ElevenLabs (`config/voice.json →
  pools.en`, có giới tính/giọng vùng/nhãn; 2 giọng nhân vật chỉ chọn tay) + 3 giọng tiếng Việt. Không lặp 5 video gần nhất,
  hợp `voice_tags` của style, đổi nam/nữ so với video trước; lưu `storyboard.voice_resolved` (chạy lại không đổi, không tốn
  credit). **atempo tự tính** theo nhịp nói thật của giọng (`vo.speed_auto`, mục tiêu 3.7 từ/giây, trần 1.15). Video làm
  trước bản này giữ giọng Liam + atempo 1.12 (`legacy`).
- **Style motion dùng cho mọi chủ đề**: thư viện đạo cụ 28 → **77 icon** (đồ vật, cơ thể, sinh vật, thiên nhiên, vũ trụ,
  công nghệ, xe cộ) + ~260 từ khoá ("elephant" → animal) + **icon tự ghép** `{"parts": […]}`; tên icon lạ → lỗi kèm gợi ý
  (Python đọc thẳng `icons.js`, một nguồn sự thật). Mọi style cũ có khối `html` → ngày có Flow vẫn dùng beat motion với
  màu/font của style.
- Thử đầu cuối với chủ đề mới (`projects/_demo-no-sleep`, "stop sleeping for 11 days", dry-run): kế hoạch tự chọn
  `flat-vector-black` + giọng Jessica; QA ĐẠT.
- Engine html: mặc định 2 worker (đo nhanh nhất, `docs/PERF.md` mục 3); thẻ `fact` không còn vòng nhấn đè chữ.

## 3.2.0 — 14/11/2026 · Vòng 7: rà soát và nhập style/engine từ GitHub

Chi tiết nguồn, license, rà soát bảo mật, quyết định lấy/bỏ: `docs/STYLE_AUDIT.md` · ghi công: `docs/CREDITS.md` ·
SHA: `vendor/SOURCES.json` (dựng lại `python scripts/vendor_fetch.py`; các thư mục clone không nằm trong git).

### Engine (thêm đúng 2, chung một adapter)
- `engines/adapter.py`: giao diện chung cho `three | html | manim | board` — `ShotSpec` → `Clip` (frame đúng số frame,
  MP4 đúng thời lượng, frame đầu/cuối để nối mạch). `vidlib/codeshot.py` điều phối theo engine; `code.engine` ép tay,
  không thì theo `code_engine` của style.
- `engines/html/` (Canvas 2D trong Edge headless, dùng chung harness `coderender` — chỉ thêm `job.page`): 13 **look**
  (flat, boil, iso, hud, synth, sticker, swiss, spy, picto, zoom, flow, sketch, gallery) × 10 **beat** (title, drop,
  counter, compare, graph, process, scale, callout, fact, outro) × icon có vai màu. Chữ báo khung bao + texture phẳng cho
  QA OCR; mọi frame là hàm thuần của số frame.
- `engines/manim/` (Manim CE 0.22, không LaTeX): graph, vectors, equation, counter, compare, title, fact, outro; pre-roll
  để frame 0 có hình, khớp đúng số frame.
- HyperFrames **không** thay harness: chậm hơn ~3× trên cùng nội dung + cần Node/telemetry/CDN (`docs/PERF.md` mục 4).
  GSAP không dùng. Blender: hướng dẫn tuỳ chọn `docs/BLENDER_MCP.md`.

### 14 style mới (đều nền đen, toàn bằng code) — thẻ `styles/<id>.json` + `styles/<id>.md`
flat-vector-black, line-boil-black, isometric-black, hud-black, synthwave-black, sticker-explainer-black (MG Styles 15) ·
swiss-motion-black, spy-titles-black, pictogram-black, scale-zoom-black (Lemo Opuscar — viết lại, không chép tài liệu
CC BY-NC) · flowchart-black, sketchnote-black (Dashi, bản đảo tối) · physics-diagram-black (Manim + grammar t1 của Huashu) ·
gallery-pointillist-black (tranh lồng khung, tập đặc biệt). Mỗi thẻ có palette ≤ 3 màu trên đen, luật nhịp, "nó KHÔNG
phải là", dấu, chuyển cảnh, gói SFX (áp vào cue shot code), nhịp nhạc, persona giọng, thumbnail, khối Flow.
- QA: ngưỡng frame đen theo style nét mảnh (`qa_black_pic_th`), engine html cho phần tử vào sớm vài frame (frame đầu shot
  không trống).

### Kiểm chứng
- Cùng một ý tưởng 20 s ("drop a 1,000°C steel ball into ice water"), 5 style mới, chạy qua pipeline thật (giọng
  ElevenLabs dùng chung): `qa/style-compare.mp4` + `qa/style-compare.md` — cả 5 **ĐẠT** QA: 21.1 s, nền đen 92–95%,
  đứng hình 0, frame đen 0, OCR 24/24 (physics 25/25), −14.0…−14.1 LUFS, TP ≤ −1.0 dBTP.
- Demo gốc của 5 nguồn chạy được trên máy, mạng ngoài bị chặn: `qa/sources/<repo>/`.
- Không skill bên ngoài nào tự kích hoạt: `.claude/skills` chỉ có `black-lab-toon`; thư mục agent trong `vendor/` bị loại
  bằng sparse-checkout; test `TestNoForeignSkills`.


## 3.1.0 — 14/11/2026 · Vòng 6: phong cách "Evidence Board" (từ plugin kaz-documentary)

Plugin giải nén ở `vendor/kaz-documentary/` (chỉ tham khảo, KHÔNG gọi skill `kaz-documentary` trong repo này).
Máy vẽ viết lại thành engine thứ hai của `mode: code`: `engines/board/` (Python + OpenCV, CPU).

### Engine board
- Tách máy vẽ khỏi dữ liệu: thư viện `engines/board/` (camera keys ease + zoom log, thẻ polaroid, giấy ghi chép, nhãn
  băng dính đen, dây đỏ, vòng tròn vẽ tay, con dấu, thẻ số, thẻ luận điểm, đồng hồ số, tiêu đề glitch, grain/vignette/
  flicker, phim câm) + mô tả cảnh `work/board/board.json` do `vidlib/boardplan.py` sinh từ `storyboard.json`.
  Không còn mốc thời gian nào trong mã (có test quét mã).
- Khung 9:16 (1080×1920): mặt bảng cao hơn rộng, thẻ xếp lưới rắn bò, khung theo safe zone. 16:9 qua
  `config/channel.json → board.size = [1920, 1080]`.
- Màu: chỉ nhập hex; `engines/board/color.py` bọc BGR của OpenCV (test đo pixel đỏ trên frame thật).
- Font FreeMono Bold + Caladea Bold (+ FreeSerif Bold dự phòng từng ký tự) trong `assets/fonts/` kèm license; QA glyph.
- Render chia đoạn theo số core (mỗi tiến trình 1 luồng OpenCV) rồi `concat -c copy`, CRF 17. Benchmark trong `docs/PERF.md`
  (`python studio.py perf board`): 0.045 s/frame với 12 tiến trình, 0.14 s/frame một tiến trình.

### Ngữ pháp → beat recipe (`shot.beat_recipe` + `shot.board`)
REVEAL_PHOTO · DOC_FOCUS · NUMBER_CARD · NAME_TAG · CONNECT · STAMP (≤ 2/video) · HIGHLIGHT_LINE · THESIS (mặc định cho
twist) · NETWORK_REVEAL · COUNTER · TITLE_GLITCH · SILENT_FILM. Recipe thuần board tự thành `mode: code` +
`code.engine: "board"` (không cần Flow). `board.marks` thêm nhãn/vòng tròn/dấu/dây vào bất kỳ beat nào.

### Style + cách ghép
- 4 preset nền tối, vào vòng xoay chống lặp: `board-black`, `chalk-case-black`, `lab-notebook-black`,
  `silent-film-black` (đơn sắc bạc trên #0b0b0b, twos, nét rung, iris, intertitle viền đôi). Đỏ #d0312d chỉ cho ý nghĩa.
- `storyboard.assembly`: `board_spine` (một camera liên tục; clip Flow/cảnh three.js là thẻ ghim, camera đẩy vào tới khi
  lấp khung → chiếu toàn màn hình → kéo ra; phim câm vào/ra bằng iris) | `cuts` (cắt cứng như cũ; shot board render
  thành frame riêng) | `auto` (theo style).

### Nhịp Shorts + âm thanh + QA
- Beat 1.5–2.5s, nhãn mờ sau ~3s (quay lại ở NETWORK_REVEAL), vòng tròn vẽ trong 8 frame, mọi dấu bắt đầu 2 frame trước
  từ khoá. Nhãn tự gõ nhanh hơn để còn ≥ 0.7s đọc trước khi camera rời; không kịp thì cảnh báo "chọn từ khoá sớm hơn".
- SFX từ `sound_bed.py`: `typing:<giây>` (22 ký tự/giây), `stamp`, `scratch:<giây>`, `projector:<giây>`; cue tự sinh
  từ board.json. Không dùng `mix_and_mux.sh` (CRF 24) — vẫn `mix.py` + master −14 LUFS.
- QA board (`vidlib/boardqa.py`, trước render lúc look-check VÀ trên video cuối): bảng lệch frame dấu↔từ khoá, thời gian
  đọc, glyph, màu đỏ đo trên frame, camera không đứng ≥ 0.4s, OCR từng chữ cắt đúng vùng trong frame (xoay thẳng chữ
  nghiêng, tách chữ đỏ theo hướng màu để chịu được yuv420).
- Sửa: ffmpeg 7+ bỏ `-vsync` (dùng `-fps_mode passthrough`).

### Video mẫu
`projects/steel-ball-1000c-board/` — bản viên bi tiếng Anh dựng lại bằng `board-black` + `board_spine` (dùng lại clip Flow
và giọng ElevenLabs của bản gốc). Đoạn phim câm Leidenfrost 1756 đứng riêng: `out/insert_leidenfrost_1756.mp4`.

## 3.0.0 — 14/11/2026 · Vòng 5: kênh tiếng Anh + tích hợp cartoon-short-kit

Kit giải nén ở `vendor/cartoon-short-kit/` (kèm SKILL.md gốc, chỉ để tham khảo). Skill riêng của kênh:
`.claude/skills/black-lab-toon/SKILL.md`. Chi tiết nguồn: `docs/CREDITS.md`. Tốc độ engine: `docs/PERF.md`.

### Chuyển kênh sang tiếng Anh
- `config/channel.json`: `language: en`, `locale: en-US`, `ui_language: vi`; chuỗi khán giả thấy ở `copy.<lang>`
  (đổi ngôn ngữ = sửa 2 dòng + thêm một khối copy). `vidlib/lang.py`: số theo locale ("1,000°C"), số → chữ, âm tiết.
- Script theo quy tắc kit (3.7 từ/giây, câu 8–15 từ, rút gọn, số bằng chữ, hook nghịch lý, kết twist) — brief LLM
  viết lại bằng tiếng Anh + linter kiểm. Stage `ideas`: 10 ý tưởng có nhãn True/Disputed/Hypothetical, `--auto-pick`.
- ElevenLabs (`config/voice.json`, `vidlib/tts.py`): một lần gọi cho cả bài, timestamp từng ký tự, audio tag v3,
  bảng phát âm (Leidenfrost…), cache theo nội dung (chạy lại không tốn credit). Key trong `.env` (gitignored).
- Font display tiếng Anh theo style (Anton, Luckiest Guy — nhúng cục bộ); OCR `eng`; thumbnail ≤ 3 từ;
  `publish.md` (3 tiêu đề ≤ 60 ký tự, mô tả 2 câu, 5–8 hashtag); `out/captions.srt`.
- Rà repo: số kiểu Việt, Be Vietnam Pro cho chữ khán giả, gói OCR `vie`, CTA "Follow để…", tag "THÍ NGHIỆM #" →
  đọc từ config/lang. Font UI (QA, contact sheet) vẫn có dấu tiếng Việt.

### Lấy từ kit
- `lib/motion` (JS + Python cùng API, test đối chiếu bằng node): smooth/easeOut/back/anticip/spring/spline/
  camFromKeys(creep, kicks)/idle/blinkAt/q. Dùng cho text_fx (pop=back, slam=anticip→back+2 frame nén,
  shake=kick 7 frame, settle=spring), camera ảo, outro.
- Camera ảo trên clip Flow (`vidlib/vcam.py`): creep liên tục, kick 7 frame ở mỗi SFX hit, quán tính qua điểm cắt
  (easeOut), payoff push-in + roll, upscale ≤ 112%, tính trước cả shot để không lộ mép và không kẹt ở trần.
- Timing theo giọng: chữ/kick/cắt cảnh đặt 0–3 frame TRƯỚC từ khoá; khoá hình rồi mới làm âm thanh.
- Look-check: `qa/look/sheet.jpg` + số đo nét/palette code↔Flow; pipeline dừng `look_check` cho tới `--look-ok`.
- Engine code-shot (`engine/main.js` port từ kit): toon material, ink pass normal/depth, DOF, grade, flash, card 2D
  — đổi sang SÂN KHẤU ĐEN (không sky/hills, fog đen), màu ink + viền rim theo style, palette từ `styles/*.json`.
  Nhân vật riêng (nhà khoa học kính bảo hộ, `engine/cast.js`), `python studio.py charsheet`.
- `mode: code` + tự chọn cho cảnh Flow làm kém. **Cảnh tổng quát `stage`** (dữ liệu → shot code cho MỌI ý tưởng, không
  viết JS: thư viện đạo cụ + keyframe + camera tự căn khung 9:16), brief LLM có đủ schema; preset `scale`,
  `thermometer`, `outro`, `vacuum`, `charsheet`;
  chữ trong cảnh là texture phẳng quay về camera (không lật gương), tự vừa khung; `seed_from` xuất frame code cho Flow.
- Style `toon3d-lab` (toàn code), chống lặp style 3 video gần nhất (`vidlib/styles.py`).
- SFX tổng hợp (thunk, rumble, crash, scrape, ting, sting, sting_low, creak, snap, splash, sizzle, bubbles), nhạc nền
  tổng hợp có điểm dừng ở twist (`musicgen.py`), cue table.
- QA của finish.sh (freezedetect, blackdetect, loudness, qa_sheet) gộp vào `qa/report.html`; freeze ≥ 0.4 s = lỗi
  trừ `hold: true`; OCR text_fx + chữ trong cảnh (engine báo khung bao từng chữ).

### Tổng quát cho mọi video (không chỉ video mẫu)
- Cảnh `stage`: shot code cho ý tưởng mới mô tả bằng dữ liệu (đạo cụ + keyframe + camera tự căn khung 9:16).
- Style quyết định cả **chất liệu trong prompt Flow** (`styles/*.json → flow.medium/look`: chalk, comic, blueprint,
  neon, ink, paper_cutout); `forward` giữ prompt brand (snapshot không đổi).
- **Ngôn ngữ theo dự án**: `storyboard.language` (dự án cũ tự nhận `vi` từ lời đọc) → số, OCR, font (`font_vi`),
  chuỗi CTA theo đúng ngôn ngữ của dự án, kể cả khi kênh đã là `en`.
- Kiểm chữ 2 lớp cho MỌI chữ khán giả thấy: (1) tất định — chuỗi do code vẽ + font có đủ glyph từng ký tự
  (`ocr.missing_glyphs`) = đúng chính tả; (2) OCR chứng minh đọc được (giống ≥ 70%: sprite sạch / texture phẳng
  engine trả về / ảnh cắt trong frame). Lý do: Tesseract đọc nhầm font display đặc (g→9, °C→°G) ngay cả trên sprite
  sạch, whitelist ký tự của LSTM thì cho kết quả thất thường.

### Dọn code chết
- Xoá `vidlib/captions.py` (caption chạy liên tục, đã thay bằng text_fx) + `brand/text-presets.json`.
- Xoá `vidlib/anims.py` + đường `code.template` (đồ hoạ 2D PIL) — thay bằng engine (`stage`/preset).
- Xoá `fx.zoom_at/shake_offset/transform` (camera ảo thay thế), `track.PlaneTracker` (Tầng 2 chưa làm),
  `textfx.stage_words`, `vcam.still_frames`, `ocr.scan_frame`, `qareport._ocr_full`, `codeshot.clear`,
  `storyboard.total_target/require`, `common.keyframes/ease_in_out/back_out/presets/frames_of/fmt_sec/IMAGE_EXT`,
  `lang.ui_language`, `audio.loudnorm_*`, `render.mux`, whisper cũ trong `vo.py`.
- `textfx.validate_fx` (trước đó không ai gọi) nay chạy trong `storyboard.validate`.

### Lỗ hổng của kit đã sửa
1. `timing.py`: ưu tiên timestamp ElevenLabs → whisper → căn khoảng lặng; số/ký hiệu đổi sang chữ TRƯỚC khi đếm âm
   tiết ("1,000°C" = 7, kit cũ = 2); không tách cụm ở dấu phẩy trong số; in rõ khi chạy chế độ khoảng lặng; bỏ lặng
   vi mô < 0.12 s (như silencedetect của kit) và có dự phòng khi DP không khớp.
2. Thiếu `mix.py` + `audio.py` tự trộn `mix_raw.wav` (còn duck + tanh, trái SKILL): viết `vidlib/mix.py` khoá mức
   gated RMS cho cả hai pipeline; `audio.py` chỉ xuất stems.
3. `finish.sh` dùng loudnorm động một lượt + `-shortest`: thay bằng đo → MỘT gain tuyến tính → limiter true-peak
   −1 dBTP (oversample ×4); độ dài theo video (voice + outro).
4. Phụ thuộc mạng: three.js r160 + `toon.ts` (mromidev/claude-animated-shorts) tải một lần, vendor kèm LICENSE MIT.
5. Render chậm: chạy GPU thật (ANGLE/D3D11, ép card rời RTX bằng `gpu: high`) + worker song song + RESUME theo hash job
   (gồm hash mã engine của đúng cảnh đó) + chỉ render shot code. Đo (`docs/PERF.md`): **0,031 s/frame** với RTX + 2 worker
   (kit: 3–10 s/frame) — nhiều worker hơn chỉ tranh GPU nên mặc định là 2. Sửa thêm: backlog HTTP server mặc định 5
   làm trình duyệt thứ 2 trở đi treo vô hạn khi chạy song song; cập nhật nhóm "facing" SAU khi đặt camera của frame
   (trước đó frame đầu mỗi worker có thể lệch cạnh kính).

### Ghi chú đo thực tế
- ElevenLabs eleven_v3/v4 nói ~3.0–3.2 từ/giây và gần như bỏ qua `voice_settings.speed` → giữ v3 (audio tag), dùng
  atempo 1.12 ở hậu kỳ; script video viên bi rút còn 127 từ.
- Số liệu viên bi kiểm lại: 100 g thép 1,000°C ≈ 68 kJ (JANAF) ≈ tan ~200 g đá (334 J/g) — video tiếng Việt cũ nói
  "cỡ 100 g" là thấp; bản tiếng Anh nói "about twice its weight".

## 2.0.0 — 13/11/2026 · Pipeline một lệnh

Branch `feat/one-command-pipeline`, mỗi phase một commit (`git log --oneline`). Baseline trước nâng cấp: `b3715a5`.

### Cách dùng mới
```
/video "Điều gì xảy ra nếu …?"        # Claude Code: tự viết storyboard (có kiểm chứng số liệu) → scripts.html → dừng chờ clip
/video <slug>                          # sau khi thả clip vào projects/<slug>/clips/ → final.mp4 + thumbnail + QA
python studio.py video <ý tưởng|slug> [--dry-run] [--from S] [--only S] [--model M] [--ai claude|gemini] [--yes]
```
Windows: `video "…"` (video.bat) · macOS: `scripts/video.command "…"`. Lệnh cũ (`new/prompts/build/cover/preview`,
`scripts/1–5_*.command`) vẫn chạy được, chúng là wrapper gọi pipeline mới.

### Đã đổi (theo yêu cầu)
| | Trước | Sau |
|---|---|---|
| R1 | `plan.json` (clips + shots) + `channel.json` có 6 "look" | `storyboard.json` là nguồn sự thật duy nhất; prompt, trang, caption, outro, thumbnail đều sinh từ đây |
| R2 | 8 lệnh lẻ + 6 script | `/video` một lệnh, có trạng thái, idempotent, `--from/--only/--dry-run/--model`; chỉ dừng chờ clip Flow |
| R3 | `prompts.html` in cả Frames lẫn Text-to-Video + ô Negative | `scripts.html`: Ingredients trước, card ①②③④ theo thứ tự thao tác, badge mode, độ dài cần chọn, tên file, copy cả cảnh, tiến độ, phím J/K/C |
| R4 | Prompt ghép từ ~15 trường tự do, motion "ease-in-out, settles" | Compiler từ block cố định; chọn mode theo `config/flow-models.json` (kiểm chứng web); linter tự chạy |
| R5 | Prompt xin Flow tạo SFX; `audio_source: both` trộn tiếng Flow | AUDIO block + `-an` khi ingest (đã kiểm: tương quan audio cuối với audio rác của Flow = 0,002) |
| R6 | `in/dur` đoán trước, không biết đầu tĩnh/đuôi giảm tốc | Auto-trim theo motion energy (16/16 clip giả khớp ground truth), né scene cut, seed frame trước vùng giảm tốc, punch-in tự chèn ≤1,2s, flash ≤3/giây, snap beat, `qa/cuts` + velocity mismatch |
| R7 | 1 nhãn pill tĩnh/shot | Caption theo VO (1–3 từ, từ đang nói trong pill xanh, pop 0.6→1.08→1.0, ±2°) + counter/label/tag/compare/arrow/circle, xếp chồng không đè, safe-zone |
| R8 | Không có | Outro Shorts 2,2s (teaser + avatar + follow + loop về frame đầu); end screen YouTube 16:9 15s có chừa ô phần tử + ảnh guide |
| R9 | Chữ hook dán lên frame giây 1 | 5 archetype, nền Flow không chữ / frame clip, chữ & đồ hoạ bằng code; 1280×720, 1080×1920 + crop 4:5/3:4/1:1; contact sheet 120/168/320px |
| R10 | Trùng lặp màu/hằng số ở 3 nơi, code mac-only | Hằng số trong `config/` + `brand/`; xoá 6 module chết; 60 test; ruff sạch; tự dò ffmpeg (winget/brew/choco/scoop) |

Brand từ avatar: nền đen, nét trắng, accent `#1849F7` (xem `brand/style-bible.md`). Font Be Vietnam Pro nhúng sẵn.

### Kết quả verify (dry-run, dự án mẫu "chạy marathon với cái bụng rỗng")
- `/video "…" --dry-run`: need_storyboard → (Claude viết storyboard, kiểm chứng 3 nguồn) → done, khoảng 75 giây trên máy này.
- `out/final.mp4`: 1080×1920 · 30fps · h264 · **1 audio track** · 33,8s (31,6s nội dung + 2,2s outro) · **−14,0 LUFS**.
- Auto-trim: đầu tĩnh khớp chính xác frame trên 16/16 clip; điểm cắt đuôi nằm 2–4 frame sau khi bắt đầu giảm tốc; scene cut
  của C04 được né.
- `scripts.html`: selftest headless 60/60 nút copy đúng nội dung, J/K/C chạy; không tràn ngang ở 360/390px.
- `python -m unittest discover -s tests -t .` → 60 OK · `python -m ruff check .` → sạch.

### Giới hạn còn lại (nói thẳng)
1. **Mới kiểm bằng clip giả.** Ngưỡng auto-trim (`config/channel.json → trim`) được chỉnh trên clip giả có nhiễu nén.
   Clip Flow thật có thể cần chỉnh `tail_ratio`/`diff_threshold`. Có `trim.in/out` thủ công và đồ thị `qa/trim/*.png`
   để soi.
2. **Mốc từng từ không có whisper chỉ là xấp xỉ.** Tool tách câu theo khoảng lặng (chính xác), rồi chia âm tiết theo vùng
   có tiếng. Lời đọc giả dùng để test không phải giọng thật. Nên `pip install faster-whisper` khi dùng VO thật.
3. **Flow chưa kiểm chứng được 3 điểm:** số ảnh Ingredients tối đa trong Flow (đặt 3, an toàn), Omni 1.2 có phải model
   mặc định không (Flow chỉ ghi "recommended"), và Frames + Ingredients có gộp được không (giả định là không).
   Veo 3.1 Fast/Quality và Omni 1.1 bị gỡ ngày **05/12/2026**; linter sẽ cảnh báo nếu chọn.
4. **`--ai claude|gemini` chưa chạy thử với API thật** (máy này không có API key). Đường chính được kiểm là `/video`
   trong Claude Code.
5. Veo xuất 24fps, tool dựng 30fps bằng cách lặp frame. Với animation 2D thì không thấy giật, nhưng không phải nội suy.
6. Velocity mismatch đo trọng tâm vùng sáng. Hợp với 2D trên nền đen, nhưng đây không phải optical flow, nên chỉ dùng để
   khoanh vùng cần soi.
7. Kích thước ô end screen YouTube lấy từ đo đạc của bên thứ ba (YouTube không công bố toạ độ). Test & Compare không áp
   dụng cho Shorts.
8. Chưa tự động hoá thao tác trên Flow (đề xuất ở cuối `docs/PLAN.md`).
9. `.venv/` cũ là venv macOS. Trên Windows tool chạy bằng Python hệ thống (đã có Pillow/numpy).
