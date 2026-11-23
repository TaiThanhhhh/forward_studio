# CREDITS — mã và tài nguyên bên thứ ba (đã vendor, không cần mạng lúc chạy)

| Thư mục | Nguồn | Phiên bản | Giấy phép |
|---|---|---|---|
| `vendor/three/three.module.js` | three.js — npm `three@0.160.0` (`build/three.module.js`) | r160, sha256 `76dea815…` | MIT (`vendor/three/LICENSE`) |
| `vendor/three/addons/loaders/GLTFLoader.js`, `utils/SkeletonUtils.js`, `utils/BufferGeometryUtils.js` | three.js addons — github.com/mrdoob/three.js tag `r160` (`d04539a7`, `examples/jsm/…`) | r160, sha256 `d073b438…` / `83748c50…` / `9be041e9…` | MIT (`vendor/three/LICENSE`) |
| `vendor/svgo/svgo.browser.js` | SVGO — npm `svgo@4.1.0` (`dist/svgo.browser.js`), chỉ chạy lúc nhập SVG (`studio.py svg`) | 4.1.0, sha256 `76a415be…` | MIT (`vendor/svgo/LICENSE`) |
| `vendor/dotlottie/dotlottie-web.js`, `dotlottie-player.wasm` | dotLottie web (LottieFiles) — npm `@lottiefiles/dotlottie-web@0.82.0` (`dist/index.js` + WASM; URL WASM đặt về máy, không CDN) | 0.82.0, sha256 `8ede12eb…` / `d6307420…` | MIT (`vendor/dotlottie/LICENSE`) |
| `vendor/rive/canvas_advanced_single.mjs` | Rive web runtime — npm `@rive-app/canvas-advanced-single@2.49.0` (WASM nhúng) | 2.49.0, sha256 `653ed947…` | MIT (`vendor/rive/LICENSE`, từ github.com/rive-app/rive-wasm) |
| `vendor/postprocessing/postprocessing.js` | pmndrs/postprocessing — npm `postprocessing@6.38.3` (`build/index.js`; bản mới nhất còn hợp three r160) | 6.38.3, sha256 `44bd51d2…` | Zlib (`vendor/postprocessing/LICENSE.md`) |
| `tests/fixtures/rive/truck.riv` | file ví dụ trong github.com/rive-app/rive-wasm (`js/examples/_frameworks/parcel_example_canvas/truck.riv`) — CHỈ cho test, không dùng trong video | — | MIT (repo rive-wasm) |
| `vendor/rapier/rapier.mjs` | Rapier 3D (dimforge) — npm `@dimforge/rapier3d-deterministic-compat@0.21.0` (`dist/rapier.mjs`, WASM nhúng base64; tarball khớp integrity sha512 của npm, không chạy script cài) | 0.21.0, sha256 `9f0c4ea9…` | Apache-2.0 (`vendor/rapier/LICENSE`) |
| `vendor/claude-animated-shorts/toon.ts` | github.com/mromidev/claude-animated-shorts `templates/bridge/toon.ts` | commit `e3b817b6` (01/11/2026), sha256 `524f6dfa…` | MIT (`vendor/claude-animated-shorts/LICENSE`) |
| `vendor/claude-animated-shorts/toonbase.js` | sinh từ `toon.ts` bằng `node module.stripTypeScriptTypes` (Node 22.16) | — | MIT (như trên) |
| `vendor/cartoon-short-kit/` | `cartoon-short-kit.zip` do người dùng cung cấp (+ `SKILL.md` của kit) — tài liệu tham khảo, không chạy trực tiếp | — | của người dùng; phần dựa trên claude-animated-shorts theo MIT |
| `assets/fonts/Anton-Regular.ttf` | Google Fonts (github.com/google/fonts `ofl/anton`) | — | OFL (`OFL-anton.txt`) |
| `assets/fonts/LuckiestGuy-Regular.ttf` | Google Fonts `apache/luckiestguy` | — | Apache 2.0 (`LICENSE-luckiestguy.txt`) |
| `vendor/kaz-documentary/` | `kaz-documentary.plugin` (zip) do người dùng cung cấp — tài liệu tham khảo, không chạy trực tiếp | 0.1.0 | của tác giả plugin (Kaz) |
| `assets/fonts/FreeMonoBold.ttf`, `FreeSerifBold.ttf` | GNU FreeFont (ftp.gnu.org/gnu/freefont, `freefont-ttf-20120503.zip`) | 20120503 | GPL v3+ kèm font exception (`LICENSE-freefont.txt`) |
| `assets/fonts/Caladea-Bold.ttf` | Caladea, Huerta Tipografia (github.com/huertatipografica/Caladea; bản 1.002 có trong Windows Fonts) | 1.002 | Apache 2.0 (`LICENSE-caladea.txt`) |
| `assets/fonts/PressStart2P-Regular.ttf` | Press Start 2P — CodeMan38 (Google Fonts `ofl/pressstart2p`) | — | OFL 1.1 (`OFL-pressstart2p.txt`) |
| `assets/fonts/PixelifySans-Variable.ttf` | Pixelify Sans — Stefie Justprince (github.com/eifetx/Pixelify-Sans, Google Fonts `ofl/pixelifysans`) | — | OFL 1.1 (`OFL-pixelifysans.txt`) |

Phần lấy ý tưởng/port từ kit (viết lại trong repo): `lib/motion/motion.js` (+ bản Python), `engines/three/main.js` (toon material,
ink pass normal/depth, DOF, grade, flash, cơ chế card), `engines/three/paint.js` (rng/tex/radial), SFX tổng hợp trong
`vidlib/sfx.py`, nhạc nền `vidlib/musicgen.py`, căn từ theo khoảng lặng `vidlib/timing.py`, QA freeze/black/qa_sheet.

Phần lấy ý tưởng/port từ kaz-documentary (viết lại trong repo, tách máy vẽ khỏi dữ liệu): camera keys (ease, zoom log),
thẻ có bóng đổ, giấy ghi chép, nhãn băng dính, dây đỏ, vòng tròn rung tay, con dấu, thẻ số, thẻ luận điểm, tiêu đề glitch,
grain/vignette/flicker (`engines/board/`); máy vẽ phim câm — twos, nét rung, iris, intertitle, xử lý phim
(`engines/board/vintage.py`, đổi sepia → bạc trên nền gần đen); SFX typing/thud/scratch/projector (`vidlib/sfx.py`).

## Vòng 7 — nguồn style và engine (tham khảo trong `vendor/`, ghim ở `vendor/SOURCES.json`)

Các repo dưới đây được clone shallow vào `vendor/<repo>/` (không nằm trong git của tool; dựng lại bằng
`python scripts/vendor_fetch.py`). Không có tệp nào của chúng được chép nguyên vào tool; không dùng phim demo, ảnh, nhạc, giọng,
font hay nhân vật của bất kỳ nguồn nào. Rà soát license + bảo mật: `docs/STYLE_AUDIT.md`.

| Nguồn | Commit | Giấy phép | Dùng vào đâu | Cách dùng |
|---|---|---|---|---|
| Lemo-Opuscar by Lemomo (LemoLab) — github.com/lemomo-ai/lemo-opuscar | `3a7132b996be` | mã MIT · tài liệu `*.md` CC BY-NC 4.0 (creativecommons.org/licenses/by-nc/4.0/) · phim/ảnh CC BY 4.0 | style `swiss-motion-black`, `spy-titles-black`, `pictogram-black`, `scale-zoom-black` | Chỉ đọc STYLE.md để hiểu ngữ pháp; thẻ style và mã look được **viết lại bằng lời và mã của tool**, đảo sang nền đen 9:16 (đã thay đổi so với bản gốc). Không chép tài liệu NC. |
| 15 Motion Design Styles — github.com/Vincentwei1021/mg-styles-15 | `269f6ed788cf` | MIT (font không kèm) | style `flat-vector-black`, `line-boil-black`, `isometric-black`, `hud-black`, `synthwave-black`, `sticker-explainer-black` | Port ý tưởng kỹ thuật (overshoot so le, boil on twos, lăng trụ đẳng trục, ngoặc khoá HUD, lưới phối cảnh + glow hai lớp, viền sticker) thành look của `engines/html/`. |
| huashu-art-motion — github.com/alchaincyf/huashu-art-motion | `1468196505a5` | MIT (ảnh nhân vật Huashu, frame library, clip Clawd KHÔNG thuộc MIT — không dùng) | `physics-diagram-black` (grammar t1: màu = khái niệm, ≤ 2 ý trên màn hình), luật camera của `scale-zoom-black` (grammar y1), `gallery-pointillist-black` (ý tưởng "cảnh → lớp chất liệu hội hoạ"), cổng QA kiểu film_gate (đo tỉ lệ nền đen/đứng hình trong `scripts/style_compare.py`) | Chỉ lấy luật; mã viết mới. |
| dashi-animationstyle — github.com/chuspeeism/dashi-animationstyle | `aa620f3b859a` | MIT (file giọng mẫu không thuộc license — không dùng) | style `flowchart-black`, `sketchnote-black` | Port ngữ pháp thẻ style (băng tiêu đề, huy hiệu số, mũi tên vòng cung; khung nét đứt, nhãn @, hatching) sang nền đen 9:16, bỏ xử lý chữ Trung. |
| Manim Community Edition — github.com/ManimCommunity/manim | pip `manim==0.22.1` | MIT | engine `engines/manim/` | Dùng làm thư viện (không vendor). |
| HyperFrames — github.com/heygen-com/hyperframes | `ff9c3b7619c6` (npm 0.9.45) | Apache-2.0 | chỉ benchmark (`docs/PERF.md` mục 4) | Không đưa vào pipeline. |
| anything2explainer — github.com/Vincentwei1021/anything2explainer | `0b85f6c7bfc4` | PolyForm Noncommercial 1.0.0 | — | Cấm thương mại → chỉ xem, không lấy mã, không lấy tài liệu. |
| claude-animation-skills (zach-d-films) — github.com/artemnovitckii/claude-animation-skills | `5dbea55c23aa` | MIT | — | Chỉ tham khảo (slow-motion lúc va chạm, caption 1–3 từ). |
| awesome-claude-video-skills — github.com/zhuyansen/awesome-claude-video-skills | `d51e496fa8c6` | CC0 1.0 (danh sách) | — | Chỉ tra cứu. |

Font cho 14 style mới đều đã có sẵn trong `assets/fonts/` (Montserrat, Baloo 2, Anton, Roboto Mono, Patrick Hand, Caladea) — không
tải thêm font nào.

## Vòng 8 — 3D Style Atlas (ý tưởng thị giác, không lấy chữ hay mã)

| Nguồn | Ngày lấy | Điều khoản | Dùng vào đâu | Cách dùng |
|---|---|---|---|---|
| 3D Style Atlas — Futurepedia / HubSpot Media, https://www.futurepedia.io/resources/3d-style-atlas/view | 15/11/2026 | HubSpot Website Terms of Use (sửa 14/04/2026): cá nhân, phi thương mại | 37 preset `styles/atlas-*.json` (biến thể dark-stage) | Chỉ lấy ý tưởng thị giác (chất liệu, ánh sáng, cú máy, vai trò accent). Mọi block prompt + thẻ style viết lại bằng lời của tool, kiểm tự động không trùng cụm 6 từ; dựng bằng engine three.js + look 3D sẵn có của tool, không dùng mã nguồn trong prompt atlas. Bản gốc lưu cục bộ (gitignore). Dùng cho kênh thương mại: chờ chủ kênh quyết định. |

## Vòng 10 — Kho tài sản 3D glTF/GLB (CC0) & Icon SVG (MIT)

File nhị phân đặt trong `assets/lib/3d/` và `assets/lib/svg/` (gitignore; dựng lại bằng `python studio.py assets fetch` và `python studio.py assets fetch svg`). Văn bản giấy phép gốc lưu tại `assets/lib/licenses/`; chỉ mục và SHA-256 lưu tại `config/assets3d.json` và `assets/lib/svg/index.json`.

| Gói / Nguồn | Tác giả / Repo chính chủ | Giấy phép | Số lượng / Dùng vào đâu |
|---|---|---|---|
| Kenney Starter Kits (`kenney-platformer`, `kenney-city`, `kenney-racing`, `kenney-arena`) | Kenney (+ Tony Schär cho Mini Arena) — github.com/KenneyNL (`Starter-Kit-3D-Platformer`, `Starter-Kit-City-Builder`, `Starter-Kit-Racing`, `Starter-Kit-Basic-Scene`) | CC0 1.0 (`assets/lib/licenses/kenney-*`) | 49 mô hình glTF/GLB trong `assets/lib/3d/kenney-*/` (`model:<tên>` trong cảnh `stage`) |
| KayKit Game Assets (`kaykit-adventurers`, `kaykit-skeletons`, `kaykit-restaurant`, `kaykit-furniture`, `kaykit-city`, `kaykit-prototype`, `kaykit-space`, `kaykit-halloween`, `kaykit-hexagon`, `kaykit-dungeon`) | Kay Lousberg — github.com/KayKit-Game-Assets | CC0 1.0 (`assets/lib/licenses/kaykit-*`) | 392 mô hình glTF/GLB (9 nhân vật có animation) trong `assets/lib/3d/kaykit-*/` |
| RobotExpressive (`threejs-robot`) | Tomás Laulhé (Quaternius), sửa bởi Don McCurdy — github.com/mrdoob/three.js (`r160/examples/models/gltf/RobotExpressive`) | CC0 1.0 (`assets/lib/licenses/threejs-robot__*`) | 1 mô hình robot có 14 animation clip trong `assets/lib/3d/threejs-robot/` |
| Poly Haven Models (`polyhaven`) | Poly Haven (nhiều tác giả, ghi nhận trong `config/assets3d.json → models.*.authors`) — https://polyhaven.com/models | CC0 1.0 (`assets/lib/licenses/polyhaven__*`) | 37 mô hình 3D glTF chọn lọc (đồ ăn, công nghệ, đạo cụ) trong `assets/lib/3d/polyhaven/` |
| Phosphor Icons (`phosphor`, kiểu fill) | Phosphor Icons (Helena Zhang, Tobias Fried) — github.com/phosphor-icons/core (`2b75f3ad12b4`) | MIT (`assets/lib/licenses/phosphor__LICENSE`) | 926 icon SVG đã chuyển thành `parts` trong `assets/lib/svg/phosphor/` (`svg:<tên>` ở engine html & three) |
