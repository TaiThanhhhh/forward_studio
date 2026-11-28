# Vòng 21 — Prompt cho Claude Opus 5.5 (effort xhigh)
## "Explainer 2D/3D cấp studio": zoom xuyên bộ phận · nhân vật có bộ phận sống · dữ kiện có nguồn · SEO Shorts chuẩn

> Prompt này viết cho **Claude Opus 5.5 (xhigh)** chạy trong Claude Code ở repo `forward_studio` (kênh **forward.**).
> Agent đọc trọn file, làm tuần tự WP-0 → WP-7, tự kiểm sau mỗi WP (test + lint + render thật), cuối cùng báo cáo.
> **Nguyên tắc:** nâng cấp ở tầng tool/engine/brief/QA (mọi video sau tự hưởng), không vá riêng một video;
> tương thích ngược 100% (dự án cũ chạy lại không lỗi); tất định 100% (không `Math.random`, không đồng hồ thật).

---

## 0. Bối cảnh & đọc bắt buộc

Chủ kênh muốn tool đi theo hướng **explainer hoạt hình 2D đẹp** (tham chiếu thể loại: vector phẳng khoa học/vũ trụ;
essay tâm lý tối giản; infographic nhịp nhanh; sketch khoa học; nhân vật dẫn chuyện) và thấy các kênh lớn dùng
**zoom vào từng bộ phận của nhân vật/bối cảnh để chuyển cảnh**, đồng thời muốn **thông tin xác thực hơn** và
**SEO YouTube Shorts / đa nền tảng chuẩn hiện đại**.

Đọc trước khi sửa: `CLAUDE.md` · `engines/html/{core.js,beats.js,rig2d.js,looks.js,__init__.py}` · `vidlib/{spine.py,
render.py,storyboard.py,linter.py,brief.py,qareport.py,ytupload.py,viralscore.py,styles.py}` ·
`engines/three/scenes/stage.js` · `prompts/storyboard_brief.md` · `.claude/commands/video.md` ·
`.claude/skills/black-lab-toon/SKILL.md` · `brand/DIRECTOR_SKILL.md`.

---

## 1. Kiểm định công việc vòng 19–20 (Gemini) — kết quả phải xử lý

| # | Phát hiện | Mức | Việc |
|---|---|---|---|
| A1 | Style/look đặt tên theo **kênh có thật** (`kurzgesagt-black`, `school-of-life-black`, `infographics-show-black`, look `kurzgesagt`…; bí danh rig `kurzbird`; regex chủ đề chứa `kurzgesagt`). Tên style đi vào brief → LLM viết tên thương hiệu vào **metadata khán giả**: dự án `how-ai-turns-static-noise-into-video` có YouTube tag `"kurzgesagt tech explainer"` và mô tả thumbnail "Split Kurzgesagt 2D visual…". Gắn tên kênh khác vào tag/tiêu đề = rủi ro chính sách spam/metadata gây hiểu lầm của YouTube. | **Cao** | Đổi sang tên thể loại + bí danh tương thích ngược; thêm cổng **brand-safety** chặn tên kênh tham chiếu trong mọi trường khán giả thấy. |
| A2 | Brief bảo "verify every number with a web search" nhưng `brief.ask("claude")` **không bật công cụ web search** → nguồn có thể bịa; `sources` chỉ là chuỗi tự do (vd "Latent Diffusion Models & DiT Papers"). | **Cao** | Sổ dữ kiện có cấu trúc + lint + bật `web_search_20260209`/`web_fetch_20260209` cho đường API + đối chiếu URL đã thật sự tìm thấy. |
| A3 | Rig `duck`/`owl`/`scientist` chỉ đổi tỉ lệ thân của `bird`/`biped` — nhìn không ra cú/vịt/nhà khoa học. | Vừa | Thêm đặc điểm hình: cú (túm lông tai, đĩa mặt, mắt to, dáng đứng), vịt (mỏ dẹt, chân màng), nhà khoa học (áo blouse, kính). |
| A4 | `iris_match` chỉ phóng **tâm khung** (1.0→1.42×) — không thể "lao vào mắt/não/cửa sổ" ở lệch tâm; nhân vật không có điểm neo bộ phận. | Vừa | WP-1/WP-2/WP-3. |
| A5 | Đúng/đủ: 3 look mới chạy được (easing `bounce`/`snap` có thật trong `core.js`), Director Skill + `learn`, Poster QA, Edge TTS tuỳ chọn, `story_hud` headroom — **giữ**. Edge TTS dùng endpoint không chính thức của Microsoft → chỉ là phương án dự phòng, ghi rõ trong tài liệu. | — | Không đổi. |

---

## 2. Gói việc

### WP-0 — Trung lập thương hiệu (A1, A3)
- `styles/`: `cosmic-flat-black` (look `cosmic`), `essay-ink-black` (look `essay`), `bold-infographic-black` (look `bold`).
  Mô tả/tag/`flow.look` chỉ dùng từ ngữ thể loại. Bí danh cũ → mới trong `vidlib/textstyle.py` (`STYLE_ALIASES`) và
  `engines/html/looks.js` (`LOOK_ALIASES`) để storyboard/job cũ vẫn chạy.
- Cập nhật `config/formats.json`, `vidlib/styles.py`, `vidlib/viralscore.py`, `brand/DIRECTOR_SKILL.md`, test vòng 19.
- Bỏ bí danh `kurzbird`. Rig: `owl`, `duck`, `scientist` có đặc điểm riêng (A3).
- **Nghiệm thu:** `grep -ri kurzgesagt styles engines vidlib config` = 0 (trừ bảng bí danh + danh sách chặn); style cũ load được.

### WP-1 — Điểm neo bộ phận & nhân vật "có bộ phận sống" (engine html)
- `rig2d.js`: `export const PARTS` (head, eye, brain, mouth, ear, nose, neck, chest, heart, lungs, belly, stomach, hand,
  hand_far, foot, foot_far, back, tail, wing, center, top) + `rigAnchors(name, o)` — tính bằng **chính dáng của frame**
  (marker đi qua cùng phép xoay/nghiêng/lật) → neo không lệch khỏi hình vẽ.
- Bộ phận sống: `xray` 0..1 (thân mờ đi, lộ cơ quan) + `organs` [brain|heart|lungs|stomach|skeleton] (tim đập theo
  `bpm`, phổi thở, não có nếp) · `focus` (vầng sáng nhịp quanh một bộ phận) · `hold` (đạo cụ gắn bàn tay/miệng) ·
  `talk` (miệng nói, bool hoặc khoảng u) · `look_at` (mắt nhìn theo vật khác) · **chống trượt chân** (chu kỳ bước
  tính từ quãng đường đi thật, không theo đồng hồ).
- `scene`: mọi tham chiếu nhận `"actor.part"` — `labels[].of`, `arrows[].from/to`, `fx[].at`, `camera[].at`;
  `camera[].zoom` (0.5–40, phóng 2D về điểm neo, vẫn là vector sắc nét); nhãn `bubble: speech|thought` có đuôi chỉ về
  miệng/đầu.
- Python (`engines/html/__init__.py`): kiểm id actor/part, `zoom`, `xray`, `organs`, `talk`, `bubble`… — lỗi tiếng Việt.

### WP-2 — Chuyển cảnh `zoom_through` ("lao xuyên bộ phận")
- `storyboard`: `transition_in: "zoom_through"` + `through`: `"hero.eye"` | `"hero"` | `[x, y]` | `{x, y, r}`
  (toạ độ 0..1 của khung shot TRƯỚC). Kiểm `through` có thật ở shot trước (nếu shot trước là html `scene`).
- html → html trong cú máy liền (`spine`): kiểu bay `portal` — ô sau nằm **bên trong** bộ phận của shot trước,
  camera lao vào, cảnh sau lộ qua **lỗ tròn** đúng cỡ bộ phận rồi nở ra lấp khung (vẽ lại vector, không vỡ hạt).
  Điểm neo tính trong JS bằng "dry draw" tất định ở frame cuối shot trước → hai shot render riêng vẫn khớp từng pixel.
- Mọi cặp khác (three.js, Flow, board…): hậu kỳ `render.py` — đuôi shot trước phóng về điểm neo (đọc `meta.json →
  anchors_end` của engine html, hoặc toạ độ `through`), đầu shot sau mở qua lỗ tròn nở ra. SFX `swish_match` tự thêm.
- Không hai cú đổi cỡ liền nhau (giữ luật `spine.ZOOMS`).

### WP-3 — 3D: camera lao vào bộ phận
- `stage`: `frame.dive: {of, part: head|eye|chest|belly|feet|center|top, u, dist, fov}` — camera tự căn khung rồi từ
  `u` lao vào bộ phận (tính từ hộp bao thật của prop ở frame cuối, mặt hướng camera) → nối `zoom_through` sang shot sau.
- Python kiểm `of` có trong `props`, `part` hợp lệ.

### WP-4 — Sổ dữ kiện có nguồn (A2)
- `vidlib/facts.py`: `sources` (chuỗi cũ hoặc `{id, title, publisher, year, url, kind}`), `claims`
  (`{id, text, value, unit, source, status: established|estimate|disputed|hypothetical}`), shot `claims: [ids]`.
- Lint (cảnh báo, không chặn): con số trên màn/VO không có claim · claim thiếu nguồn/URL · nguồn yếu (blog, wiki mở,
  mạng xã hội, content farm) · claim `disputed/hypothetical` mà VO không có từ rào đón · từ tuyệt đối/"studies show"
  không có claim · số trên màn ≠ `value` của claim · URL nguồn không có trong kết quả tìm kiếm thật (`work/research.json`)
  · **tỉ lệ thực tế** (người ≈ 1.7 m, cửa ≈ 2 m, chó ≈ 0.6 m…: hai vật lệch > 2.5× so với ngoài đời → nhắc, tắt bằng
  `scale_free: true`).
- Chip nguồn trên màn (hậu kỳ, mọi engine): "Source: NASA (2023)" giữa sân khấu và phụ đề, chỉ ở shot có claim có nguồn.
- `brief.ask("claude")`: bật web search/fetch (xử lý `pause_turn`), lưu URL đã thấy → `work/research.json`.
- `studio.py facts <slug>` → `qa/facts.md` (bảng claim · nguồn · hạng nguồn · vấn đề).

### WP-5 — SEO YouTube Shorts + đa nền tảng
- `vidlib/seo.py`: `publish.primary_keyword` (tự suy nếu thiếu) phải nằm trong 40 ký tự đầu của tiêu đề, câu đầu mô
  tả, **lời đọc 1–2 shot đầu** (YouTube đọc transcript) · 3 hashtag (3 cái đầu hiện trên tiêu đề) · tag ≤ 500 ký tự ·
  không tên kênh khác · nguồn trong mô tả (link Shorts không bấm được — ghi tên nguồn).
- `ytupload`: `status.containsSyntheticMedia` theo quyết định nhãn AI, `localizations` tuỳ chọn, category theo chủ đề
  (27 Education / 28 Science & Tech) hoặc `publish.youtube_shorts.category`.
- `publish.md` có mục **SEO check** (điểm + việc cần sửa) và **Sources**; `caption.txt` của YouTube có khối nguồn.

### WP-6 — Brief, skill, tài liệu
- Brief: khối **PART ZOOM & LIVING PARTS** (khi nào dùng, cú pháp), **FACT DISCIPLINE** (sổ dữ kiện, rào đón, làm
  tròn, đơn vị, hình đúng tỉ lệ), **SEARCH-FIRST SEO**. Schema có `claims`, `sources` dạng object, `through`.
- `.claude/commands/video.md` + `SKILL.md`: quy trình kiểm chứng bằng WebSearch + WebFetch (mở trang, đối chiếu số).
- `CLAUDE.md`, `HUONG_DAN.md`, `docs/CHANGELOG.md`, `brand/DIRECTOR_SKILL.md` (bài học mới).

### WP-7 — Kiểm định
- `tests/test_round21_*.py`: từ vựng PARTS/ORGANS (Python đọc từ JS), validate scene/part/camera, storyboard
  `zoom_through`, spine `portal`, hậu kỳ `zoom_through` (khung cuối A phóng đúng điểm, khung đầu B có lỗ tròn), facts
  lint, SEO lint, brand-safety, bí danh style, payload web search (mock), payload YouTube.
- Render thật một cảnh demo (Edge headless): nhân vật x-ray + zoom vào mắt + portal sang shot sau → contact sheet
  `qa/round21/`. Xem ảnh bằng mắt trước khi báo xong.
- `python -m unittest discover -s tests -t .` + `python -m ruff check .` sạch.

---

## 3. Bất biến (không được phá)
- Grid 3 tầng (header 250–370 · stage 390–1240 · captions 1340–1460), `overlapPairs() == []`, vùng an toàn 9:16.
- Kênh tiếng Anh cho mọi thứ khán giả thấy/nghe; giao diện/log/báo cáo cho người làm bằng tiếng Việt.
- Không thêm engine thứ năm; không cài skill/plugin trong `vendor/`; không vẽ logo/nhân vật của kênh khác.
- Key API chỉ trong `.env`. Không push/commit khi chủ kênh chưa yêu cầu.
