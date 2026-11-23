# STYLE_AUDIT — vòng 7: rà soát và nhập style/engine từ GitHub

Ngày rà soát: 14/11/2026 · máy Windows 11, Python 3.13.5, Node 22.16 (chỉ dùng để thử HyperFrames), ffmpeg 9.0.2.
Mọi URL, license, số sao, commit dưới đây được xác minh lại bằng GitHub API ẩn danh + `git ls-remote` + đọc file LICENSE
thật trong bản clone. SHA đầy đủ: `vendor/SOURCES.json`.

## 1. Kiểm kê — đã có gì trước vòng 7

Tìm trong `vendor/`, `styles/`, `engines/`, `engines/three/`, `package.json` (không có), `.claude/skills/`, `~/.claude/skills/`,
plugin đã cài (`~/.claude/plugins`): **không nguồn nào trong danh sách đã có sẵn**, trừ three.js và FFmpeg.

| Nguồn | Đã có? | Phiên bản/commit lấy về | ★ | License thật | Trùng với thứ đã có | Giá trị thêm | Quyết định |
|---|---|---|---|---|---|---|---|
| **A1 Lemo Opuscar** `lemomo-ai/lemo-opuscar` | chưa | `3a7132b9` (12/11/2026) · 101 style | 15.902 | **hỗn hợp**: mã MIT · mọi `*.md` (STYLE.md…) **CC BY-NC 4.0** · phim/poster CC BY 4.0 · Clawd và nhãn hiệu bên thứ ba không cấp phép | `silent-film`, `blueprint`, `chalkboard`, `neon-tubes`, `ink-wash`, `papercut` của họ trùng ý với silent-film-black / blueprint / chalk / neon / ink / paper_cutout đã có → **không lấy** | 4 ngữ pháp chưa có: Swiss, 60s spy titles, pictogram, scale zoom; cách viết mục "what it is not" | **Lấy 4 style, viết lại** (không chép STYLE.md vì NC; ghi công trong CREDITS) |
| **A2 MG Styles 15** `Vincentwei1021/mg-styles-15` | chưa | `269f6ed7` (09/11/2026) | 3.517 | MIT (font không kèm) | line boil: cơ chế boil đã có ở text_fx (vòng 4) và phim câm (vòng 6) → chỉ học chi tiết (on twos, smear, tô lệch khuôn), không nhập engine | flat vector, isometric, HUD, synthwave, sticker explainer + cách "trang vẽ được mọi thời điểm t" | **Lấy 6 style** (port ý tưởng kỹ thuật thành look) |
| A2b `Vincentwei1021/anything2explainer` | chưa | `0b85f6c7` (09/11/2026) | 3.308 | **PolyForm Noncommercial 1.0.0** — dùng thương mại phải xin phép tác giả | explainer nền đen + TTS + phụ đề: pipeline của kênh đã có VO, .srt, QA | ý tưởng thanh tiến độ chương (chưa làm) | **Bỏ mã** (cấm thương mại + phụ thuộc Remotion). Chỉ xem ảnh `examples/contrast` |
| **A3 Huashu Art Motion** `alchaincyf/huashu-art-motion` | chưa | `14681965` (09/11/2026) | 6.890 | MIT; ảnh nhân vật Huashu, frame library, clip Clawd **ngoài MIT** | `17_ink`, `34_shadowpuppet`, `33_rubberhose` gần ink / silent-film đã có | grammar t1 (kiểu 3Blue1Brown) và y1 (đi giữa các thang); ý tưởng cổng QA `film_gate`; "era = một hàm vẽ" | **Lấy 2 grammar + 1 art style lồng khung**; không dùng tài sản nhân vật |
| **A4 Dashi AnimationStyle** `chuspeeism/dashi-animationstyle` | chưa | `aa620f3b` (13/10/2026) · 8 style | 195 | **MIT** (đã có LICENSE; file giọng mẫu ngoài license) | `手绘笔记` gần lab-notebook-black (board) và chalk; `黑底科技`, `霓虹赛博` gần hud/neon | flowchart phẳng; sổ tay vẽ tay (nét đứng yên + hatching, khác line boil) | **Lấy 2 style** (bản tối, bỏ xử lý chữ Trung, 9:16) |
| **B5 HyperFrames** `heygen-com/hyperframes` | chưa | `ff9c3b76` (14/11/2026) · npm 0.9.45 | 84.143 | Apache-2.0 | harness render HTML → frame: tool đã có `vidlib/coderender.py` (Playwright + Edge, song song, RESUME) | catalog component để tham khảo | **Không đưa vào pipeline** — xem mục 4 và `docs/PERF.md` mục 4 |
| B6 Remotion | chưa | — | — | license riêng (công ty vượt ngưỡng phải mua) | — | — | **Bỏ** (không có sẵn trong repo; đúng yêu cầu) |
| B7 three.js | **có** | r160 (`vendor/three`, vòng 5) | — | MIT | engine `engines/three/` | — | giữ nguyên |
| B8 GSAP | chưa | — | — | đã kiểm tra gsap.com/community/standard-license (hiệu lực 30/04/2025, sửa 30/05/2025): "Standard 'No Charge' GSAP License" của Webflow — miễn phí cả thương mại và mọi plugin, nhưng là license độc quyền (không phải mã nguồn mở), cấm dùng cho công cụ dựng animation trực quan cạnh tranh với Webflow, Webflow được sửa điều khoản bất kỳ lúc nào | `lib/motion` (easing, spring, spline) đã đủ cho engine html | — | **Không dùng** — engine html tự tính easing; không thêm phụ thuộc có điều khoản riêng |
| **B9 Manim CE** | chưa | pip `manim 0.22.1` | — | MIT | không | đồ thị, vector, phương trình | **Lấy** làm engine thứ tư (không cần LaTeX) |
| B10 Blender MCP | chưa | — | — | — | — | shot 3D hero | chỉ viết hướng dẫn: `docs/BLENDER_MCP.md` |
| B11 FFmpeg | **có** | 9.0.2 | — | — | — | — | giữ nguyên |
| C `artemnovitckii/claude-animation-skills` (zach-d-films) | chưa | `5dbea55c` (01/11/2026) | 746 | MIT (font OFL) | "what if" 3D cartoon 9:16 bằng three.js = `toon3d-lab` + engine three.js đã có | slow-motion lúc va chạm, whip cut, caption 1–3 từ: kick 7 frame, whip, text_fx đã có | **Chỉ học**, không lấy mã |
| C `zhuyansen/awesome-claude-video-skills` | chưa | `d51e496f` (13/11/2026) | 2.047 | CC0 (danh sách) | — | danh mục để tra nguồn sau này | chỉ tra cứu |

## 2. Rà soát bảo mật (tĩnh, trước khi chạy bất cứ thứ gì)

Cách làm: clone shallow, `GIT_LFS_SKIP_SMUDGE=1`, **không chạy script nào của repo**; quét mọi file văn bản tìm `curl|sh`,
lệnh tải binary, ghi vào `~/.claude`, đọc biến môi trường bí mật, telemetry, gọi mạng; đọc `package.json` (script
`preinstall/install/postinstall/prepare`), `setup.sh`, `install.sh`.

| Repo | Script npm tự chạy | `curl \| sh` | Tải binary / gọi mạng | Ghi ngoài thư mục project | Thư mục tự kích hoạt agent | Kết luận |
|---|---|---|---|---|---|---|
| lemo-opuscar | không | không | `build.sh`/`fonts.sh` của từng demo tải font từ Google Fonts, vài demo tải ảnh/tif công cộng; `setup.sh` của plugin cài phụ thuộc | không thấy | `.claude-plugin/`, `plugin/.claude-plugin/`, `CLAUDE.md`, `AGENTS.md` | Không chạy script nào. Demo chạy bằng trình duyệt bị chặn mạng (mục 3). |
| mg-styles-15 | không (`render` chỉ khi gọi tay) | không | `lib/audio/tools/download_vcsl.sh` tải mẫu nhạc cụ | không | không | Sạch. Không chạy `download_vcsl.sh`. |
| anything2explainer | không | không | không | không | `SKILL.md` ở gốc | Sạch nhưng **cấm thương mại** → không dùng. |
| huashu-art-motion | — (không có package.json) | không | vài script Python gọi API TTS/ảnh khi người dùng chủ động chạy | đọc `~` để tìm cấu hình giọng | `SKILL.md` ở gốc | Không chạy script; chỉ mở trang engine trong trình duyệt bị chặn mạng. |
| dashi-animationstyle | — | không | không | `render.mjs` tạo thư mục tạm của Chrome | `SKILL.md` ở gốc | Sạch. |
| **hyperframes** | `prepare: lefthook install` (gốc), `prepare: npm run build` (packages/share) | chỉ trong chuỗi test và thông báo lỗi | **có**: CLI tự tải Chrome headless-shell vào `~/.cache`; composition mẫu tải GSAP từ jsdelivr, font từ Google Fonts, 1 mp4 từ `static.heygen.ai` lúc render; **telemetry bật mặc định** (tắt bằng `HYPERFRAMES_NO_TELEMETRY=1`/`DO_NOT_TRACK=1`) | **có**: lệnh `hyperframes skills update` ghi skill vào `~/.claude/skills`; cache ở `~/.cache/hyperframes` | `.claude/skills/` (6 skill), `.agents/`, `.codex*`, `.cursor-plugin`, `plugin.json`, `CLAUDE.md` | **Đáng lưu ý nhất.** Đã thử trong hộp cát (bên dưới); không cài skill, không để tải Chrome. |
| claude-animation-skills | không | không | `kit/setup.sh` tải GSAP từ cdnjs, `npm install`; **`install.sh` chép mọi skill vào `~/.claude/skills/`** | `install.sh` ghi `~/.claude/skills` | `.claude-plugin/` | **Không chạy `install.sh`/`setup.sh`.** |
| awesome-claude-video-skills | — | không | không | không | không | Chỉ là danh sách. |

Biện pháp đã áp dụng:
- **Không cài skill/plugin nào**: `~/.claude/skills` và `.claude/skills` không đổi (vẫn chỉ `black-lab-toon` + lệnh `/video`).
- **Gỡ thư mục tự kích hoạt khỏi bản vendor** bằng sparse-checkout ở mọi độ sâu: `.claude/`, `.claude-plugin/`, `.agents/`,
  `.codex/`, `.codex-plugin/`, `.cursor/`, `.cursor-plugin/` (ghi ở `SOURCES.json → stripped`; `scripts/vendor_fetch.py` lặp lại
  đúng như vậy). Test `tests/test_engines.py::TestNoForeignSkills` canh việc này.
- HyperFrames thử trong `vendor/_hf_run/` (ngoài git): `npm install hyperframes@0.9.45 --ignore-scripts` (77 gói, 118 MB),
  `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_UPDATE_CHECK=1`, cache trỏ vào `vendor/_hf_run/cache`, trình duyệt
  trỏ vào Chrome đã cài (không tải Chrome), ffmpeg của máy. Không chạy `skills update`.
- Không có gì ở mức "đáng ngờ phải dừng": mọi hành vi trên đều được ghi công khai trong README/mã của repo tương ứng và
  đều tránh được bằng cách không chạy script cài đặt.

**Lưu ý còn lại cho bạn:** `kaz-documentary.plugin` + `vendor/kaz-documentary/.claude-plugin` (vòng 6, do bạn đưa vào) và file
`SKILL.md` ở gốc repo (bản skill gốc của cartoon-short-kit) tôi để nguyên — chúng không nằm trong `.claude/skills` nên
không tự kích hoạt.

## 3. Chạy demo gốc (≥ 1 demo mỗi nguồn) — `qa/sources/<repo>/`

Demo được mở bằng `scripts/vendor_demo.py`: Playwright + Edge headless của tool, server chỉ phục vụ thư mục repo nguồn,
**mọi request ra ngoài 127.0.0.1 bị chặn và ghi lại**. Không `npm install`, không chạy script của nguồn.

| Nguồn | Demo | Kết quả | Gọi mạng lúc render | Ghi chú |
|---|---|---|---|---|
| mg-styles-15 | `demos/01-flat-vector` (t = 1, 5, 9 s) | ✓ 3 frame · 0.05–0.08 s/frame | 0 request | Font không kèm (Fredoka, Resource Han Rounded) → thế bằng Baloo 2 có sẵn. |
| lemo-opuscar | `styles/swiss-motion/demo` (t = 8, 22, 33.4 s) | ✓ 3 frame · 0.06–0.08 s/frame | 0 request | Font không nằm trong git (`fonts.sh` tải) → thế bằng Montserrat/Caladea có sẵn. |
| dashi-animationstyle | `styles/黑底科技/示例_Token.html` | ✓ 3 frame · 0.13–0.42 s/frame | 0 request | — |
| huashu-art-motion | `scripts/engine` · film `demos/t1_3b1b` | ✓ 3 frame · 0.05–0.09 s/frame | 0 request | — |
| hyperframes | `registry/examples/kinetic-type` qua CLI 0.9.45 | ✓ MP4 15 s · 450 frame trong 28.7 s chụp (6 worker) | **có**: GSAP (jsdelivr), Google Fonts, 1 mp4 (static.heygen.ai) | 3 frame trích từ MP4. |
| claude-animation-skills | `skills/zach-d-films/engine` | ✖ không chạy | — | Cần `three/examples/jsm` (EffectComposer, Bokeh…) từ `npm install`; tool chỉ vendor `three.module.js`. Chỉ tham khảo nên không cài. |
| anything2explainer | — | không chạy | — | Cần Remotion (bị loại) + license cấm thương mại. |
| awesome-claude-video-skills | — | không có gì để chạy | — | Danh sách. |

Contact sheet: `qa/sources/_sheet.jpg` · log từng lần chạy: `qa/sources/<repo>/run.json`.

## 4. Engine — hợp nhất, không phình

- Trước vòng 7: `three` (three.js qua Edge) và `board` (Python/OpenCV). Thêm đúng **2**: `html` và `manim`. Cả bốn đi qua
  `engines/adapter.py` (`ShotSpec` → `Clip`: thư mục frame đúng số frame, MP4 đúng thời lượng, frame đầu/cuối để nối mạch).
- **HyperFrames không thay harness**: số đo trên cùng nội dung ở `docs/PERF.md` mục 4. Ngoài tốc độ, nó kéo theo Node ≥ 22
  lúc chạy (tool hiện không cần Node), telemetry mặc định, tải tài nguyên từ CDN lúc render và không có RESUME theo frame.
  Engine html dùng lại `vidlib/coderender.py` (thêm một dòng: trang theo `job.page`) → **không có mã harness trùng để xoá**.
- GSAP không dùng: engine html tính mọi thứ theo số frame bằng `lib/motion` (render song song, RESUME).
- Mã demo không được chạy nguyên: ngữ pháp được viết lại thành `engines/html/looks.js` (13 look) + `beats.js` (10 beat) +
  `icons.js`; nội dung video chỉ đến từ storyboard (test canh: không có chữ của ý tưởng mẫu trong mã engine).

## 5. Style đã nhập (14) và đã bỏ

| Style | Nguồn | Chuyển sang nền đen | Engine |
|---|---|---|---|
| `flat-vector-black` | MG 01 | bản đảo: khối màu trên đen, mảnh hình học trôi ở nền | html |
| `line-boil-black` | MG 05 | nét kem sôi trên đen (bỏ nền giấy) | html |
| `isometric-black` | MG 03 | sân khấu tối + sàn lưới đẳng trục | html |
| `hud-black` | MG 22 | vốn tối — giữ tinh thần | html |
| `synthwave-black` | MG 10 | vốn tối — giữ tinh thần | html |
| `sticker-explainer-black` | MG 19 | bản tối: canvas đen chấm lưới, sticker viền trắng | html |
| `swiss-motion-black` | Lemo swiss-motion | **bản đảo**: nền đen, chữ/khối trắng ngà, một màu tín hiệu | html |
| `spy-titles-black` | Lemo spy-titles | bản tối: giấy cắt kem/đỏ/mù tạt trên đen | html |
| `pictogram-black` | Lemo pictogram-motion | hoạ tiết 5 sắc độ của một màu pha về đen | html |
| `scale-zoom-black` | Lemo flat-space-explainer (+ Huashu y1) | vốn là nền đêm — giữ | html |
| `flowchart-black` | Dashi 扁平流程图 | **bản đảo** từ nền kem | html |
| `sketchnote-black` | Dashi 手绘笔记 | **bản đảo** từ giấy trắng ngà | html |
| `physics-diagram-black` | Manim + Huashu t1 | vốn nền đen | manim (+ html cho beat manim không có) |
| `gallery-pointillist-black` | Huashu (ý tưởng) | **tranh lồng khung** trên tường đen (vào vòng xoay auto từ 3.4.1) | html |

Đã bỏ và lý do:
- **Van Gogh / Monet phủ kín khung** (Huashu 08, 28…): không thể tối mà còn bản sắc → chỉ giữ dạng "tranh lồng khung" bằng
  một bộ chấm màu tự viết (không sao chép bức tranh nào).
- **MG 02 line-art, 08 morph, 07 liquid, 09 bauhaus, 12 aurora-glass, 20 pixel, 04 3D render, 06 collage, 18 variety
  captions**: ngoài danh sách ưu tiên; aurora-glass và 3D render mất bản sắc trên nền đen phẳng (cần gradient/HDRI); collage
  cần ảnh thật (kênh không dùng ảnh người thật); variety captions trùng vai text_fx.
- **Lemo**: 97 style còn lại không nhập (nhiều style trùng preset đã có; nhiều style dựa vào ảnh/footage/bản đồ bên thứ ba).
- **Dashi 复古报刊 (báo cũ), 复古剪纸, 超现实拼贴, 立体卡通**: báo cũ cần nền giấy sáng + nguy cơ giống masthead báo (kênh cấm);
  cắt giấy trùng spy-titles/paper_cutout; 立体卡通 trùng toon3d-lab.
- **Huashu 7 grammar còn lại** (keynote UI, finance chart, Vox, whiteboard, storytime, kinetic type, presenter): không hợp
  thí nghiệm khoa học hoặc trùng text_fx/board.
- **anything2explainer, Remotion, GSAP, Blender trong pipeline**: lý do license/độ nặng ở bảng mục 1.

## 6. Kết quả kiểm chứng

Xem cuối file `docs/CHANGELOG.md` (mục 3.2.0) và `qa/style-compare.md` (bảng đo từng bản dựng).

## 7. Rà soát danh sách 20 repo motion/3D/âm thanh (18/11/2026)

Câu hỏi của chủ kênh: tool đã có các repo này chưa. Tiêu chí: tool dựng video offline, mỗi frame là hàm thuần theo số frame
(render song song, RESUME), không Node/không bước build lúc chạy, không thêm engine thứ năm.

| Repo | Kết luận |
|---|---|
| Three.js, FFmpeg | **Đã có** (r160 vendor; ffmpeg 9.0.2). Nâng three.js không đem lại gì rõ cho video, lại làm lệch golden QA. |
| GSAP, Anime.js, Motion (+ GSAP Skills, Motion AI Kit) | Không nhúng thư viện (chạy theo đồng hồ thật, trùng `lib/motion`; GSAP license độc quyền Webflow). **Đã lấy phần giá trị** (vòng 10b): bộ easing chuẩn cùng tên/hình (bounceOut, elastic, expoOut, circOut, sine, backIn, steps) viết lại trong `lib/motion` (JS = Python, test đối chiếu). Motion AI Kit: skill cho UI web, phần mạnh là gói Motion+ trả phí. |
| Remotion (+ Remotion Skills), Motion Canvas | Engine thứ năm cần Node + build; Remotion có license công ty (mục 1). |
| React Three Fiber, Drei | Bọc React cho three.js, cần build; cảnh của tool là dữ liệu storyboard. Không lấy. |
| **React Postprocessing → lấy lõi pmndrs/postprocessing** | **Đã lấy** (vòng 10b) bản 6.38.3 (mới nhất còn hợp three r160), không lớp React: `world.look3d.post` {smaa, ca, bloom} tuỳ chọn theo style; SMAA chờ nạp ảnh tra cứu trước khi render; bloom mặc định giữ nền #000. |
| **SVGO** | **Đã lấy** (bản browser 4.1.0): `studio.py svg` nhập icon SVG → `parts` có vai màu + lỗ (mọi look html, ép khối 3D). |
| Satori | Không lấy: Edge headless của tool đã dựng HTML/CSS thật (mạnh hơn Satori); thumbnail dựng bằng Pillow. |
| Howler.js, Mediabunny | Phát/ghi media trong trình duyệt; tool mix offline (`vidlib/mix.py`) và encode bằng ffmpeg (`vidlib/encode.py`). |
| **dotLottie, Rive** | **Đã lấy** (dotLottie 0.82.0, Rive canvas-advanced 2.49.0): actor `lottie`/`rive` của beat `scene`. Lệch palette: đổi màu Lottie JSON theo vai; Rive chạy lưới bước cố định từ 0 nên tất định (frame render lẻ = frame render liền, sai khác 0). Bản quyền theo từng file: linter nhắc khi thiếu ghi chú. |
| **React Three Rapier → lấy lõi Rapier** | **Đã lấy** (vòng này): engine three.js chưa có vật lý; kênh "thí nghiệm" cần rơi/va chạm thật. Bản tất định đa nền tảng, mô phỏng một lần lúc build, nên giữ được hàm thuần theo frame. Không dùng lớp React. Xem CHANGELOG 3.7.0. |
