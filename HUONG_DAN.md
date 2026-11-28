# HƯỚNG DẪN — làm video thí nghiệm bằng MỘT lệnh

> Kênh tiếng Anh (từ vòng 5): lời đọc, chữ trên hình, outro, thumbnail, tiêu đề/mô tả/hashtag (`publish.md`), phụ đề
> `.srt` đều tiếng Anh. Giao diện (`scripts.html`), log, báo cáo QA vẫn tiếng Việt.
> Vòng 6: thêm phong cách **Evidence Board** (engine `board`) và **đoạn chèn phim câm**. Xem mục 7.

```
/video "ý tưởng"  ──►  storyboard.json  ──►  scripts.html  ──►  [bạn tạo clip Flow cho shot Flow]
                                                                         │ thả vào projects/<slug>/clips/
/video <slug>     ──►  ingest → auto-trim → giọng ElevenLabs → dựng → chữ / bảng → âm thanh
                  ──►  qa/look/sheet.jpg (xem trước) ──► --look-ok ──► render
                       → out/final.mp4 + out/captions.srt + thumbnails/ + publish.md + qa/report.html
```

> **Không muốn gõ lệnh?** Nháy đúp `ui.bat` (hoặc `python studio.py ui`) → trình duyệt mở http://127.0.0.1:8765. Mọi
> bước dưới đây đều có nút bấm: *Tạo video* (xem kế hoạch rồi chạy), trang dự án (thanh tiến trình, log trực tiếp, kéo thả
> clip Flow vào từng shot, nút *Duyệt & render đầy đủ*, video + thumbnail + QA), *Style* (lọc 3D/2D/Flow, ảnh mẫu).
> Mục 7d.

Chỉ có **hai chỗ cần bạn**: tạo clip trong Google Flow, và duyệt contact sheet trước khi render đầy đủ. Trong Claude
Code, Claude tự viết storyboard, tự soi sheet và chạy tiếp; bạn chỉ cần làm clip Flow. Chạy lại bao nhiêu lần cũng được:
tool tự biết bước nào đã xong.

---

## 1. Cài đặt (1 lần)

1. **Python 3.10+** (Windows: tick "Add Python to PATH").
2. **ffmpeg**: Windows `winget install Gyan.FFmpeg` · macOS `brew install ffmpeg`.
3. Trong thư mục tool: `pip install -r requirements.txt` (gồm Playwright để điều khiển Microsoft Edge có sẵn trên Windows —
   không tải trình duyệt — và Manim cho style đồ thị vật lý).
4. **Tesseract** (OCR kiểm chữ): `winget install UB-Mannheim.TesseractOCR`.
5. **Key ElevenLabs**: file `.env` ở gốc repo, dòng `ELEVENLABS_API_KEY=...` (file này không bao giờ commit).
6. Kiểm tra: `python -m unittest discover -s tests -t .` phải ra `OK`.

---

## 2. Quy trình từ A đến Z (một video)

### Bước 0 — chọn ý tưởng (tuỳ chọn)
`python studio.py ideas "liquid nitrogen"` → Claude viết 10 ý tưởng có nhãn **True / Disputed / Hypothetical** →
`python studio.py ideas <slug-lô> --pick 3` (hoặc `--auto-pick` lấy điểm cao nhất). Lệnh này tạo dự án và chạy tiếp như
bước 1.

### Bước 1 — ra lệnh
Trong Claude Code gõ: `/video "What happens if you drop a hot coin into liquid nitrogen?"`

Claude đọc `projects/<slug>/brief.md`, kiểm chứng mọi con số bằng web search (ghi nguồn vào `sources`), rồi viết
`storyboard.json`: lời đọc tiếng Anh, từng shot, chữ trong cảnh, `beat_recipe` cho kiểu bảng, thumbnail, tiêu đề.

- Muốn ép phong cách: thêm vào câu lệnh, ví dụ "dùng style board-black". Không nói gì thì `style: "auto"` tự chọn style
  chưa dùng trong 3 video gần nhất (danh sách: `python studio.py styles`).
- Ngoài Claude Code: `python studio.py video "…"` rồi dán `brief.md` vào app Claude, lưu JSON trả về thành
  `storyboard.json`. Hoặc thêm `--ai claude` (cần `ANTHROPIC_API_KEY`).

### Bước 2 — tạo clip trong Google Flow
Tool mở **`projects/<slug>/scripts.html`** và dừng ở `waiting_clips`. Shot `mode: code` (three.js hoặc board) **không cần
Flow**. Với mỗi card shot Flow, làm theo thứ tự:

| | Việc | Ghi chú |
|---|---|---|
| 0 | Ingredients (nếu có): ảnh ref nhân vật/đạo cụ 1:1 → `refs/REF_….png` | Làm trước tất cả |
| ① | **Ảnh Start**: copy prompt, đính ảnh ref ghi trên card, tạo ảnh 9:16 → `frames/C01_start.png` | Cảnh nối tiếp: tool tự trích |
| ② | **Ảnh End** (chỉ khi card ghi Start+End) → `frames/C01_end.png` | Đính ảnh Start làm ref |
| ③ | **Video**: Flow → Video → Frames. Dán prompt, chọn **đúng độ dài ghi trên card**, 9:16 | |
| ④ | Tải về, đặt tên `C01.mp4` (hoặc để nguyên tên Flow) → thả vào `clips/` | Tiếng của Flow sẽ bị bỏ |

Phím tắt trong trang: `J`/`K` chuyển cảnh, `C` copy prompt video.

### Bước 3 — chạy lại
`/video <slug>`. Thiếu clip thì tool làm trước phần đã có rồi dừng chờ tiếp. Clip để nguyên tên Flow: tool map theo thứ
tự tải về và in bảng để bạn xác nhận (`--yes` nếu đúng).

### Bước 4 — duyệt contact sheet (look-check)
Đủ clip, tool tạo giọng ElevenLabs (có cache, chạy lại không tốn credit), dựng, rồi dừng ở **`look_check`** với
`qa/look/sheet.jpg`. Trong Claude Code, Claude tự xem và chạy tiếp. Tự làm thì mở ảnh, đạt thì:
`/video <slug> --look-ok`.

Video kiểu board in thêm bảng ✔/✖ ngay dưới dòng `▶ look`: dấu đỏ có đúng từ khoá không, nhãn có kịp đọc không, có ô
vuông không, màu có bị đảo không, có đứng hình không, OCR.

### Bước 5 — nhận kết quả
- `out/final.mp4` — video Shorts (CRF 17, −14 LUFS, −1 dBTP).
- `out/captions.srt` · `publish.md` (3 tiêu đề, mô tả, hashtag) · `thumbnails/` (+ `contact-sheet.png`).
- `qa/report.html` — mở trong trình duyệt. Phải thấy **ĐẠT**; "CẦN XEM" thì đọc các dòng ✗.
- `out/endscreen_16x9.mp4` — end screen cho video YouTube dài.

---

## 3. Các flag

| Flag | Dùng khi |
|---|---|
| `--dry-run` | Chưa có clip, muốn xem nhịp/chữ/bảng: tool sinh clip, giọng, nhạc **giả** cho phần thiếu |
| `--from <stage>` | Làm lại từ một bước (vd `--from text` sau khi sửa chữ/bảng, `--from render`) |
| `--only <stage>` | Chỉ làm một bước: `page`, `thumbnail`, `look`, `render`, `qa`… |
| `--look-ok` | Đã duyệt contact sheet → render đầy đủ |
| `--tts-force` | Tạo lại giọng ElevenLabs dù lời không đổi |
| `--model "<tên>"` | Đổi model Flow (`python studio.py models`) |
| `--yes` · `--no-open` | Tự xác nhận bảng map clip · không tự mở `scripts.html` |

Các stage: `python studio.py stages`. Trạng thái từng cảnh: `python studio.py status <slug>`.

---

## 4. Sửa nhanh trong `storyboard.json`

| Trường (shot) | Ý nghĩa |
|---|---|
| `vo` | Câu đọc (tiếng Anh) bắt đầu ở shot này; có thể mở bằng audio tag `[excited]`. Shot không có `vo` minh hoạ tiếp câu trước |
| `beat_recipe` + `board` | Ngữ pháp evidence board (mục 7) |
| `text_fx` | Chữ trong cảnh (style cắt cảnh), 1–4 từ: `text`, `anchor`, `layer`, `behavior`, `sync` (`vo_word:<từ>`) |
| `mode` + `code` | `"mode": "code", "code": {"scene": "stage", "params": {…}}` — shot three.js (xem đầu `engines/three/scenes/stage.js`) |
| `target_sec` | Thời lượng (1,5–2,5s; hook ≤ 1,5s; tối đa 3,5s) — lời đọc sẽ co/giãn lại |
| `transition_in` | `cut` · `flash` (lộ kết quả) · `whip` · `match` · `glitch` · `fade` |
| `hold` | `true` = cho phép đứng hình có chủ đích |
| `state_change`, `continues_from`, `refs`, `layout_free` | Điều khiển mode Flow |

Top-level: `style` (`auto` hoặc tên style) · `narrative` (dạng kịch bản, mục 7c) · `assembly` (`auto` | `board_spine` | `cuts`).
Sửa xong chạy lại `/video <slug>`. Không sửa trường do tool sinh (`video_prompt`, `mode_resolved`…); muốn ép prompt Flow
thì dùng `override.video_prompt`.

---

## 5. Tool viết prompt Flow thế nào
- `storyboard.json` chỉ chứa ý nghĩa; compiler ghép với block cố định trong `prompts/blocks/`.
- Mode tự chọn theo `config/flow-models.json`: mặc định Frames · Start; có biến đổi trước → sau thì Start+End; nối liền
  hành động thì ảnh Start trích từ clip trước; nhân vật lặp lại thì Ingredients. **Không bao giờ** text-to-video.
- Ingredients dùng ở bước tạo **ảnh**, Frames ở bước tạo **video**.
- Độ dài clip ≥ thời lượng dùng + 1,5s (tool cắt đầu tĩnh/đuôi giảm tốc), ưu tiên ≤ 10s.
- **Không bao giờ để Flow vẽ chữ.** Chữ/số nằm ở `text_fx`, chữ 3D trong shot three.js, hoặc nhãn/thẻ của engine board.

---

## 6. Âm thanh
- Tiếng Flow luôn bị bỏ. Âm thanh cuối = lời đọc + nhạc + SFX.
- Giọng ElevenLabs `eleven_v3` (đổi ở `config/voice.json`), tăng tốc 1,12× bằng atempo, mốc từng từ chính xác.
- SFX tự gắn: điểm cắt, chữ bật lên; kiểu board thêm tiếng gõ máy chữ cho nhãn, tiếng đóng dấu, bút dạ khoanh tròn,
  tiếng máy chiếu khi vào phim câm. Muốn tiếng "xịn" hơn: bỏ file CC0 vào `assets/sfx/<tên>.wav`.
- Mix khoá mức theo giọng (`config/mix.json`), nhạc dừng ở câu twist, master −14 LUFS / −1 dBTP.

---

## 7. Phong cách Evidence Board (vòng 6)

### Trông như thế nào
Một camera chạy liên tục trên một tấm bảng đen lớn. Clip Flow được **ghim như polaroid**; camera đẩy vào tới khi clip lấp
kín khung thì chiếu toàn màn hình, rồi kéo ra quay lại bảng. Vòng tròn đỏ vẽ tay hiện đúng lúc giọng đọc nói tới từ đó.
Dây đỏ nối nguyên nhân → kết quả. Nhãn băng dính đen chữ đánh máy. Con dấu đóng mạnh. Thẻ số lớn đếm lên. Câu twist là
một dòng "You'd think…" bị gạch đỏ rồi câu đúng hiện ra. Cuối video kéo ra thấy cả bảng, rồi tiêu đề "Next: …" glitch.

### Bốn style (đều nền đen, đỏ `#d0312d` chỉ dùng cho ý nghĩa)
| Style | Bề mặt |
|---|---|
| `board-black` | giấy đen nhám có lưới mờ, thẻ viền xám nhạt, ghim |
| `lab-notebook-black` | giấy ô li tông tối, chữ đánh máy, kẹp giấy, ghi chú viết tay |
| `chalk-case-black` | nhìn từ trên xuống, nền gần đen có vệt phấn, băng dính trắng |
| `silent-film-black` | đơn sắc bạc, grain/flicker/vết xước, chạy trên twos — cũng là style của mọi đoạn chèn phim câm |

Bốn style này tự dùng `assembly: board_spine`. Muốn dùng nét board nhưng vẫn cắt cứng: đặt `"assembly": "cuts"` (các thẻ
board thành shot riêng xen giữa clip).

### Các recipe (`beat_recipe` của từng shot)
| Recipe | Dùng cho | `board` |
|---|---|---|
| `REVEAL_PHOTO` | Shot có clip Flow / cảnh three.js (mặc định), hoặc ảnh bạn đưa vào | `fill: false` giữ là thẻ; `image: "assets/user/x.jpg"`, `gray` (xem `assets/user/README.md`) |
| `DOC_FOCUS` | Trang sổ thí nghiệm, khoanh đỏ cụm đang đọc | `lines`, `circle` (cụm từ có trong `lines`), `sync` |
| `NUMBER_CARD` | Con số lớn đếm lên | `number` ("1,000°C"), `from`, `caption`, `sync` |
| `NAME_TAG` | Nhãn băng dính + dây đỏ tới vật | `text` (≤ 18 ký tự), `at` [x, y] trên ảnh, `sync` |
| `CONNECT` | Dây đỏ nguyên nhân → kết quả | `from` (id shot), `to` ("self"), `sync` |
| `STAMP` | `CONFIRMED` / `MYTH` / `DON'T TRY THIS` (≤ 2/video) | `text`, `sync`, `at` |
| `HIGHLIGHT_LINE` | Nét cọ đỏ quét qua chữ trên trang | `on`, `phrase` |
| `THESIS` | **Twist**: dòng cũ bị gạch, câu đúng + chấm đỏ | `old`, `new`, `strike_sync`; shot sau `continue: true`, `new_sync` |
| `COUNTER` | Nhiệt kế / đồng hồ số | `label`, `from`, `to`, `unit`, `decimals`, `jitter` |
| `NETWORK_REVEAL` | Kéo ra thấy cả bảng, ngay trước outro | shot ngắn ~1,2s, beat `outro`, không lời |
| `SILENT_FILM` | Đoạn chèn phim câm 3–4s cho khoảnh khắc lịch sử | `film.panels`: `tableau` (nhân vật vẽ tay) + `intertitle` |

`board.marks` thêm nhãn / vòng tròn / con dấu / dây / nét cọ vào bất kỳ shot nào. Mẹo quan trọng: **gắn nhãn/con dấu vào
từ khoá SỚM trong câu**. Từ ở cuối câu thì camera đã rời đi trước khi kịp đọc; tool sẽ cảnh báo ⚠ nếu vậy.

Người thật (nhà khoa học…) chỉ được **vẽ** dạng hình bóng tối giản. Muốn dùng ảnh thật thì tự tải ảnh public domain
(Wikimedia Commons, Library of Congress) vào `assets/user/`. Không vẽ logo/masthead báo đài. Tai nạn/bạo lực chỉ thể hiện
bằng flash, khói, intertitle.

### Video mẫu
`projects/steel-ball-1000c-board/` — bản viên bi tiếng Anh dựng lại bằng `board-black`. Mở `storyboard.json` của nó để
xem cách viết từng recipe; `out/final.mp4` là kết quả, `out/insert_leidenfrost_1756.mp4` là đoạn phim câm đứng riêng.

### Lệnh riêng của engine board
- Đoạn phim câm đứng riêng (xem/duyệt):
  `python -m engines.board.render projects/<slug>/work/board/board.json insert C07 out.mp4 --sec 4`
- Vài frame xem nhanh: `python -m engines.board.render <board.json> stills 100,400,900 <thư mục>`
- Đo tốc độ: `python studio.py perf board` → `docs/PERF.md` (12 tiến trình ≈ 1 phút cho video 40s).
- Xuất 16:9 cho video YouTube dài: `config/channel.json → board.size = [1920, 1080]`.

---

## 7a. Mỗi video một style và một giọng khác nhau

Bạn không cần làm gì: chỉ gõ `/video "ý tưởng"`. Trước khi viết kịch bản, tool lập **kế hoạch** (`projects/<slug>/plan.json`):

- **Style theo chủ đề.** Mỗi style có nhãn chủ đề: lỗ đen/kích thước → `scale-zoom-black`; vũ trụ/phi hành gia →
  `hud-black`; sét/điện → `neon`; lửa/bếp/hoá học → `line-boil-black`… Không lặp style của 3 video gần nhất.
- **Có hôm dùng Flow, có hôm không.** Kịch bản được viết đúng loại ngày:
  - Ngày **có Flow**: phần lớn shot là clip Google Flow, bạn tạo clip như trước.
  - Ngày **toàn code**: mọi shot dựng bằng code, không phải chờ clip, làm một lệnh là xong.

  Tool tự cân hai loại: gần đây làm nhiều ngày Flow thì hôm nay nghiêng về code, và ngược lại (`config/channel.json →
  styles.flow_share`, mặc định 50%). Chủ đề khớp rõ một style thì chủ đề thắng.
- **Mỗi video một giọng.** Có 20 giọng ElevenLabs tự chọn (cả nam lẫn nữ, giọng Mỹ, Anh, Úc), cộng 2 giọng nhân vật chỉ
  dùng khi bạn chọn tay. Cách chọn:
  - Không lặp giọng của 5 video gần nhất.
  - Hợp tính cách style: spy-titles → giọng kể chuyện bí ẩn; HUD → giọng điều phối bình tĩnh.
  - Đổi nam/nữ so với video trước.

  Mỗi giọng nói nhanh chậm khác nhau, tool tự chỉnh tốc độ để giữ nhịp ~3.7 từ/giây.
- Đã chọn thì giữ nguyên: chạy lại video không đổi style hay giọng, và không tốn credit ElevenLabs lần nữa.

Muốn tự quyết thì thêm cờ:

| Cờ | Ý nghĩa |
|---|---|
| `--style hud-black` | dùng đúng style này |
| `--voice Brian` | dùng đúng giọng này (xem danh sách: `python studio.py voices`) |
| `--flow` | hôm nay tôi rảnh, làm clip Flow (chỉ chọn style có Flow) |
| `--no-flow` | hôm nay không làm Flow (chỉ chọn style dựng toàn bộ bằng code) |

| `--narrative countdown` | dùng đúng dạng kịch bản này (xem mục 7c) |

Xem trước tool sẽ chọn gì (style + giọng + dạng kịch bản):
`python studio.py styles --plan "What happens if you drop a phone into lava?"`.
Thêm giọng: thêm một dòng vào `config/voice.json → pools.en` (id lấy trong ElevenLabs, kèm vài nhãn như `calm`, `deep`).

Video làm trước bản này giữ nguyên giọng Liam và tốc độ cũ, không bị dựng lại.

## 7b. 14 style motion graphics nền đen (vòng 7) — không cần Flow

Các style này dựng **toàn bộ bằng code** (không phải tạo clip trong Flow): đặt `"style": "<id>"` trong `storyboard.json`
(hoặc để `"auto"` — tool chấm điểm theo chủ đề rồi mới xoay vòng) và chạy `/video` như thường.

| Style | Trông thế nào | Hợp với |
|---|---|---|
| `flat-vector-black` | khối màu phẳng, nảy đàn hồi | chủ đề đời thường, "nó hoạt động thế nào" |
| `line-boil-black` | nét vẽ tay rung, on twos | lửa, nhiệt, hoá học, bếp |
| `isometric-black` | khối 2.5D mọc trên sàn lưới | máy móc, hệ thống, năng lượng |
| `hud-black` | giao diện sci-fi nét cyan, khoá mục tiêu cam | không gian, công nghệ, cực hạn |
| `synthwave-black` | lưới hồng, mặt trời sọc, chữ crôm | retro, tốc độ, điện, game |
| `sticker-explainer-black` | sticker viền trắng, biểu đồ chính xác | số liệu, vật liệu, so sánh |
| `swiss-motion-black` | lưới + chữ căn trái + một màu đỏ | con số, quy tắc, đo lường |
| `spy-titles-black` | giấy cắt, dải chéo, chữ nghiêng | bí ẩn, lịch sử, chất độc |
| `pictogram-black` | pictogram + tiêu đề khổng lồ + "03 / 07" | danh sách, các bước, xếp hạng |
| `scale-zoom-black` | camera zoom qua các thang kích thước | "to/nhỏ cỡ nào", vũ trụ, nguyên tử |
| `flowchart-black` | băng hổ phách, huy hiệu số, mũi tên cong | quy trình, chuỗi nhân quả |
| `sketchnote-black` | sổ tay vẽ tay, hatching, một màu cam | sinh học, quan sát tự nhiên |
| `physics-diagram-black` | đồ thị/vector/phương trình kiểu bảng đen số (Manim) | nhiệt, lực, năng lượng, toán |
| `gallery-pointillist-black` | tranh chấm màu lồng khung trên tường đen | ánh sáng, màu sắc, cầu vồng, lăng kính, hoàng hôn, cực quang, đom đóm |

Thẻ đầy đủ từng style (bảng màu, luật nhịp, "nó KHÔNG phải là gì", nguồn): `styles/<id>.md`.

Mỗi shot là một **beat** viết bằng dữ liệu (không viết code):
```json
{"id": "C03", "beat": "escalate", "mode": "code", "target_sec": 2.4, "vo": "It hits, and the water flashes into steam.",
 "code": {"scene": "drop", "params": {"title": "Drop it in", "a": {"icon": "ball", "label": "1,000°C", "role": "hot"},
          "b": {"icon": "glass", "label": "ice water"}, "result": "Flash to steam", "hit": 0.4}}}
```
Beat có sẵn: `title` · `drop` (A rơi vào B) · `counter` (số chạy) · `compare` (hai cột) · `graph` (đường cong) · `process`
(các bước) · `scale` (thang kích thước) · `callout` (vật + nhãn) · `fact` (câu chốt) · `scene` (dàn cảnh tự do, mục 7c) ·
`outro`. Với `physics-diagram-black`
còn có `vectors` và `equation`. Thiếu tham số bắt buộc → tool báo ngay ở bước storyboard.

**Dùng cho mọi chủ đề, không riêng video mẫu.** Beat là "ngữ pháp" chung; đồ vật trong cảnh là `icon`:
- **Có sẵn 190 đạo cụ, chia theo các mảng của kênh** (brief cũng liệt kê theo nhóm này):

  | Nhóm | Ví dụ |
  |---|---|
  | A · chạy bộ & cơ thể | người chạy, giày, đồng hồ bấm giờ, điện tim, phổi, tim, ty thể, O₂, hồng cầu, đồng hồ thể thao, bồn nước đá, huy chương, cúp, cờ đích, đường chạy |
  | B · tập tạ | tạ đơn, tạ đòn, tạ ấm, người squat, bánh tạ, bình lắc protein, cánh tay gồng, lịch tập, mũi tên tăng/giảm, bia ngắm |
  | C · AI hình ảnh & motion | máy ảnh, máy quay, clapper, nút play, cuộn phim, ảnh, layer, bút bezier, keyframe, timeline, đũa phép, tia "AI", bảng màu, con trỏ, micro, sóng âm, khung hình, cọ |
  | D · công nghệ & dev | `</>`, terminal, con bug, database, server, phích cắm/API, khoá, chìa khoá, nhánh git, tài liệu, khung quét OCR, mạng nơ-ron, bàn phím, cửa sổ trình duyệt, thư mục, chip, robot |
  | Phòng thí nghiệm | nhà khoa học của kênh, bình tam giác, cốc becher, ống nghiệm, đèn Bunsen, đĩa petri, ống nhỏ giọt, kính hiển vi, kính bảo hộ, đồng hồ áp suất, chuông chân không, bình nitơ lỏng, cân đĩa, con lắc, đòn bẩy, bình cứu hoả, phóng xạ |
  | Vật chất & lực | bi thép, bóng bowling, lông vũ, đe, khói, sóng xung kích, vết nứt, đá, tinh thể… |
  | Thiên nhiên · vũ trụ · động vật · đồ ăn · xe cộ | mây mưa, gió, núi băng, xương rồng, Trái Đất, tiểu hành tinh, phi hành gia, voi, cá voi, cá mập, táo, chuối, pin mặt trời, tua-bin gió… |

  Xem hết, vẽ theo từng style: `python scripts/icon_sheet.py` → `qa/icons/<style>.jpg`.
- **Viết bằng chữ thường cũng được** (~830 từ khoá): "marathon" → người chạy, "bench press" → tạ đòn, "pull request" →
  nhánh git, "image to video" → ảnh, "vacuum chamber" → chuông chân không, "titanic" → tàu, "magnifying glass" → kính lúp.
- **Không có vật phù hợp thì tự ghép** từ hình tròn, chữ nhật, đa giác, đường. Ví dụ cái giường trong video demo
  `projects/_demo-no-sleep`:
  ```json
  "icon": {"parts": [{"k": "rect", "x": -0.9, "y": 0, "w": 1.8, "h": 0.32, "role": "cold"},
                     {"k": "rect", "x": -0.24, "y": -0.16, "w": 0.96, "h": 0.18, "rad": 0.08, "role": "hot"}]}
  ```
- **Tên đạo cụ lạ không bị lặng lẽ vẽ thành chấm tròn:** tool báo lỗi và gợi ý tên gần nghĩa.
- **Ngày có Flow vẫn dùng được các beat này** (đồ thị, bộ đếm, so sánh…). Chúng tự lấy màu và font của style hôm đó.

Lệnh xem nhanh:
- `python studio.py styles --gallery` → `qa/styles-gallery.png` (mỗi style một khung hình).
- `python studio.py styles --rank "chủ đề tiếng Anh"` → style nào hợp chủ đề nhất.
- `python scripts/style_compare.py --styles swiss-motion-black,hud-black` → dựng cùng một kịch bản bằng nhiều style, ghép
  cạnh nhau ở `qa/style-compare.mp4` để chọn.

Nguồn gốc các style, license và kết quả rà soát bảo mật: `docs/STYLE_AUDIT.md` · ghi công: `docs/CREDITS.md`.
Shot 3D "hero" bằng Blender (tuỳ chọn, ngoài pipeline): `docs/BLENDER_MCP.md`.

## 7c. Chống "video nào cũng như slide"

Năm cơ chế chạy tự động, bạn không phải làm gì. Muốn can thiệp thì xem cột cuối.

| Cơ chế | Làm gì | Can thiệp |
|---|---|---|
| **Dạng kịch bản xoay vòng** | 10 khung kể: `classic`, `countdown` (đếm ngược top 5), `timeline` (từng phút/giờ), `myth_fact`, `escalation` (×10 mỗi bước), `journey` (hành trình một vật), `versus` (A đấu B), `rewind` (mở bằng kết cục), `chain_reaction` (domino), `mystery`. Chọn theo chủ đề, không lặp 3 video gần nhất. Tiêu đề "5 things…" luôn ra `countdown`, "… vs …" luôn ra `versus` | `--narrative <id>` · `python studio.py narratives "<chủ đề>"` · sửa `config/narratives.json` |
| **Một cú máy liền** | Các shot html liền nhau nằm trên một canvas lớn. Camera bay từ ô này sang ô kia (lia, chéo, xoay 90°, lao vào vật, kéo ra), không cắt. Kiểu bay xáo theo video và hợp look (swiss chỉ lia thẳng, sketchnote cuộn dọc…) và dạng kịch bản (`timeline` lia phải như trục thời gian, `versus` lia qua lại) | tắt: `config/channel.json → code_render.html_spine: false` hoặc `styles/<id>.json → html.spine: false` |
| **Beat `scene`** | Dàn cảnh tự do: nhiều vật/nhân vật di chuyển theo keyframe, va chạm, bắn nước, sóng xung kích, nhãn bám vật. Brief yêu cầu 1–3 khoảnh khắc hành động mỗi video | xem ví dụ dưới |
| **Biến thể bố cục** | `title` (center/left/hero), `counter` (ring/giant/bar), `compare` (bars/split/balance), `fact` (center/stamp/left), `process` (list/path). Tool xoay theo video và theo thứ tự shot | ghi `"layout": "giant"` trong `params` |
| **Cổng QA chống slide** | Đo tỉ lệ khung hình có chuyển động nhanh trong `final.mp4`: dưới 3,5% là đỏ (như slide), dưới 6% là vàng | ngưỡng: `config/channel.json → qa.motion_red / motion_yellow` |

Ví dụ beat `scene` (video nước, shot C05: nước ùa vào tế bào làm nó phồng lên). Toạ độ `x`, `y` từ 0 đến 1 của khung,
thời gian `u` từ 0 đến 1 của shot:
```json
"code": {"scene": "scene", "params": {"title": "Water moves in",
  "actors": [{"id": "cell", "icon": "cell", "x": 0.5, "y": 0.56, "size": 380,
              "keys": [{"u": 0.42, "size": 380}, {"u": 0.88, "size": 660, "ease": "spring"}]},
             {"id": "w1", "icon": "drop", "x": 0.12, "y": 0.26, "size": 110, "role": "cold", "in": 0.04, "out": 0.44,
              "keys": [{"u": 0.42, "x": 0.44, "y": 0.5, "ease": "in"}]}],
  "labels": [{"text": "Cells swell", "of": "cell", "u": 0.72, "tag": true}],
  "fx": [{"kind": "splash", "at": "cell", "u": 0.44}, {"kind": "shockwave", "at": "cell", "u": 0.74}]}}
```

## 7d. Giao diện web (`ui/`)

| Màn hình | Làm gì |
|---|---|
| Tổng quan | số dự án, việc đang chờ bạn, job đang chạy, cân bằng ngày Flow/code, kiểm tra môi trường (ffmpeg, Edge, Manim, key) |
| Tạo video | nhập ý tưởng → **Xem kế hoạch** (style + giọng + dạng kịch bản tool chọn, có ảnh mẫu style) → ép lựa chọn nếu muốn → chạy |
| Dự án | thanh 19 bước, hộp "việc tiếp theo" theo trạng thái (cần storyboard / chờ clip / duyệt look), log trực tiếp, thanh **trộn engine** (mỗi shot một khúc màu theo engine), tab Shot (ảnh still, engine, lời đọc, **kéo thả clip Flow**, prompt Flow), Kết quả, QA, Style & prompt |
| Ý tưởng | tạo brief 10 ý tưởng, chọn ý tưởng → tạo dự án |
| Style / Giọng / Dạng kịch bản | thư viện, lọc + tìm, "Dùng cho video mới", dựng bảng đạo cụ 3D |
| Job | mọi lần chạy, log, huỷ (dừng cả worker render), lệnh dòng lệnh tương đương |
| Cài đặt | môi trường, cấu hình kênh (chỉ đọc), công cụ bảo trì (thẻ style, gallery, smoke test) |

Storyboard vẫn do Claude Code viết (gõ `/video <slug>`), hoặc bấm *Viết bằng Claude/Gemini API* nếu có key trong `.env`.
UI chỉ nghe `127.0.0.1`, không bao giờ hiện giá trị key.

## 7e. Trộn 3D + chart + sơ đồ trong MỘT video

Mỗi shot tự đi engine phù hợp — không cần đổi style giữa chừng. Style chỉ quyết định màu/font và engine mặc định.

| Khoảnh khắc | Dùng | Viết trong storyboard |
|---|---|---|
| Hook, va chạm, cơ thể/vật trong không gian, payoff | **3D** (three.js) | `"code": {"scene": "stage", "params": {"set": "track", "props": [{"type": "runner3d", "pose": "sprint"}], "fx": [{"kind": "shockwave"}]}}` |
| Con số, tốc độ, trước/sau | **chart 2D** (html) | `"scene": "counter"` · `"graph"` · `"compare"` · `"scale"` (cần `items`) |
| Cơ chế, các bước, chú thích bộ phận | **2D** (html) | `"scene": "scene"` (dàn cảnh) · `"process"` · `"callout"` |
| Lực, phương trình, đồ thị hàm | **Manim** | `"code": {"engine": "manim", "scene": "vectors", "params": {…}}` |
| Cảnh thật phức tạp | **Google Flow** | `"mode": "auto"` + `start_frame` + `action` |

Nguyên tắc (theo các studio làm explainer hybrid): 3D cho 2–4 khoảnh khắc cần chiều sâu/chuyển động vật lý; số liệu đặt
ở chart 2D (đọc nhanh hơn); đổi engine ở chỗ đổi nhịp kể (setup → escalate → payoff), không đổi mỗi shot. Brief cho LLM
đã có sẵn bảng này (danh sách cảnh lấy từ engine thật). Ví dụ đủ 13 shot: `projects/demo-hybrid-3d` (style toon) và
`projects/demo-hybrid-xray` (cùng kịch bản, style X-quang).

**9 look 3D** (`styles/<id>.json → world.look3d`): `toon` (toon3d-lab) · `clay` (clay3d-black) · `plastic`
(plastic-toy3d-black) · `glass` · `chrome` · `lowpoly` · `paper` (papercraft3d-black) · `holo` (hologram3d-black) · `xray`
(xray3d-black). Xem đạo cụ ở mọi look: `python scripts/props3d_sheet.py` → `qa/props3d/`.

### Vật lý thật cho cảnh 3D (Rapier, từ 18/11/2026)

Thả rơi, nảy, ném, va chạm, đổ tháp: thay vì tự đặt keyframe, gắn `body` cho đạo cụ và để máy mô phỏng. Mỗi cú chạm tự
có SFX + rung camera (+ bụi/tia nếu khai `fx`) đúng frame chạm. Mô phỏng chạy một lần lúc dựng cảnh, kết quả giống hệt
nhau ở mọi worker và mọi máy.

```json
"code": {"scene": "stage", "params": {
  "physics": {"slowmo": [{"u": [0.40, 0.66], "rate": 0.3}], "fx": "burst"},
  "props": [
    {"id": "k00", "type": "box", "size": [0.2, 0.2, 0.2], "at": [0.25, 0, 0], "body": {"material": "wood"}},
    {"id": "ball", "type": "bowling", "at": [-2.4, 0.11, 0], "frame": false,
     "body": {"material": "metal", "v": [5.5, 0, 0], "hit_u": 0.42}}]}}
```

- `material`: plastic · rubber · wood · metal · stone · glass · ice · foam · paper · feather (lông vũ/giấy rơi chậm, chao).
- `hit_u`: tool tự chọn lúc thả để **cú chạm đầu tiên rơi đúng u đó**, nên đặt `hit_u` đúng từ khoá trong lời đọc. Có
  slow-mo vẫn canh đúng.
- `release`: vật đi theo keyframe tới u đó rồi bay tiếp với đà của keyframe (kiểu ném). `kind: kinematic`: vật đi theo
  keyframe và đẩy được vật khác. `kind: fixed`: vật đứng yên làm chỗ va.
- `gravity` (-1.62 = Mặt Trăng, 0 = ngoài không gian) · `slowmo` · `settle` (giây cho chồng vật ổn định trước shot).
- Vật đặt sẵn ngoài khung để bay vào: thêm `"frame": false` (camera tự căn bỏ qua nó).
- Xem trước bản keyframe tay so với vật lý: `python scripts/physics_sheet.py` → `qa/physics/compare.mp4` + `sheet.jpg`.

### Icon SVG, animation Lottie / Rive của anh, hậu kỳ 3D, easing mới

- **Icon SVG**: `python studio.py svg duong-dan/rocket.svg --name rocket --license "Lucide, ISC"`. Sau đó viết
  `"icon": "svg:rocket"` ở bất kỳ chỗ nào nhận icon. Icon được vẽ bằng nét của style (sôi nét, phác thảo, đẳng trục…) và
  tự lấy màu style. Trong cảnh 3D, `{"type": "svg:rocket"}` thành khối nổi, lỗ thủng giữ nguyên.
- **Lottie / Rive**: chép file vào `assets/user/lottie/` hoặc `assets/user/rive/`, kèm `<tên>.license.txt` ghi nguồn. Trong
  beat `scene`, thay `icon` của actor bằng `"lottie": "<tên>"` hoặc `"rive": "<tên>"`. Lottie dạng `.json` tự đổi màu theo
  style (`"colors": "keep"` để giữ màu gốc). Chi tiết: `assets/user/README.md`.
- **Hậu kỳ 3D** (`world.look3d.post` của style): khử răng cưa nét viền (SMAA) đã BẬT sẵn cho mọi style 3D (`"post": false`
  để tắt) · thêm `"ca": 0.002` lệch màu ống kính ở mép khung · `"bloom": {}` quầng sáng mềm (nền vẫn đen tuyền).
- **Thumbnail**: video toàn code tự lấy frame thật của shot nhiều hình làm nền; muốn chọn tay thì thêm vào biến thể
  `"frame": {"shot": "C05", "u": 0.6}` (u = vị trí trong shot).
- **Easing mới** cho `ease` của keyframe (2D lẫn 3D): `bounceOut` (rơi nảy 3 lần), `elastic` (lò xo), `expoOut` (phóng rồi
  phanh gắt), `circOut`, `sine` (êm nhất), `backIn` (lùi lấy đà), `steps` (nhảy bậc như đồng hồ).

## 7f. Zoom xuyên bộ phận · nhân vật có bộ phận sống · dữ kiện có nguồn · SEO (vòng 21)

**Zoom xuyên bộ phận** (kiểu kênh giải thích lớn: lao vào mắt → thấy võng mạc, vào màn hình → thấy mạch điện):
- Shot trước (2D `scene`): camera `{"u": 1, "at": "hero.eye", "zoom": 12}` — camera bám đúng con mắt rồi phóng vào.
- Shot sau: `"transition_in": "zoom_through", "through": "hero.eye"` → cảnh sau mở ra từ bên trong con mắt (lỗ tròn
  nở ra). Hai shot html liền nhau: engine vẽ lại vector nên nét ở mọi độ phóng. Shot 3D: `"frame": {"dive": {"of":
  "hero", "part": "head"}}`.
- Bộ phận có sẵn: head, eye, brain, mouth, ear, nose, neck, chest, heart, lungs, belly, stomach, hand, foot, back, tail,
  wing, center, top (icon thường: center, top, bottom, left, right, screen, window, core).

**Nhân vật có bộ phận sống** (trong `actors` của `scene`): `"xray": 1` + `"organs": ["brain", "heart", "lungs"]` (thân
trong suốt, tim đập theo `bpm`), `"focus": "brain"` (vầng sáng nhịp), `"hold": "phone"` (cầm đồ vật), `"talk": true`
(miệng nói), `"look_at": "cup"` (mắt nhìn theo); nhãn `"bubble": "thought"` = bong bóng suy nghĩ. Đi bộ tự khớp chân với
quãng đường (không trượt). Xem mẫu: `python scripts/parts_sheet.py` → `qa/round21/`.

**Dữ kiện có nguồn**: storyboard có `sources` (có `publisher`, `year`, `url`) + `claims`; shot ghi `"claims": ["K1"]` →
góc dưới hiện chip nhỏ "Source: NASA (2024)". `python studio.py facts <slug>` in bảng claim/nguồn/hạng nguồn và lỗi
(nguồn yếu, số không nguồn, giả định nói như thật, tỉ lệ người–vật sai thực tế) → `qa/facts.md`.

**SEO Shorts**: ghi `publish.primary_keyword`; tool kiểm từ khoá ở tiêu đề/mô tả/lời đọc, hashtag, tag, dòng nguồn;
`out/publish.md` có mục **SEO check**. Upload YouTube tự đặt category, nhãn "nội dung tổng hợp" (video toàn hoạt hình code
= No; có clip Flow trông như thật → anh quyết trong `publish.youtube_shorts.altered_content`). **Không bao giờ** ghi tên
kênh khác (Kurzgesagt, TED-Ed…) vào tiêu đề/tag/mô tả — tool chặn.

## 7g. Hình nhận ra được · người tả thực · bối cảnh đêm · kính lúp · rủi ro YouTube (vòng 22)

**Vật thể chi tiết** (tự thay bản đơn giản cùng tên): laptop, phone, chip, keyboard, server, gpu, film (khung phim có hình
vẽ), reel, drawing, pencil, brain (có thuỳ + nếp), neuron, rbc / bloodcell, macrophage + chomper (đớp liên tục khi `p` >
0.5), fatcell / fat, glycogen, glucose, bread, pasta, vertebra, spine (`p` = đĩa đệm bị nén), disc, muscle, musclefiber,
fiber (`p` = vết rách nhỏ), mitochondria, heart, lungs, liver, capillary (`p` = bị ép), vesselwall, peptide, lipidchain,
caffeine, adenosine, receptor, cup, coffeebean, bed, shoe, paper, bits, bike, denoise (`p` 0 = nhiễu → 1 = cảnh sạch).
Xem: `python scripts/icon_sheet.py cosmic-flat-black --detail` → `qa/icons/`.

**Người tả thực**: `rig:athlete`, `rig:marathoner`, `rig:runnerf`, `rig:lifter`, `rig:casual`, `rig:casualf` với hành động
idle, walk, run, sit, sleep, point, wave, cheer, jump, tired, curl, squat, **cycle** (có xe đạp thật). Bộ phận thêm: knee,
thigh, calf, heel, ankle, sole, elbow, shoulder, arm, liver, spine, hip. X-ray thêm: liver, spine, muscles, vessels,
fuel (kho glycogen sáng theo `p`).

**Bối cảnh đêm** (thay nền đen trơn): trong `params` của `scene` ghi `"backdrop": "gym"` (hoặc city, road, bedroom,
track, office, studio, lab) hoặc `{"kind": "gym", "floor": 0.66}` — `floor` ≈ vạch chân nhân vật. 3D: `"set": "gym"` hoặc
`"bedroom"` (phòng đêm có cửa sổ, đèn treo, vũng sáng).

**Kính lúp** thay cho "zoom vào bộ phận đang chạy": `"lenses": [{"of": "r.sole", "x": 0.64, "y": 0.34, "r": 0.3,
"title": "CAPILLARY IN YOUR SOLE", "actors": [{"icon": "capillary", "size": 1000}]}]` + `"freeze": 0.12` trên nhân vật
(đứng hình trước khi soi).

**Nhịp explainer**: `"length_profile": "explainer"` — 34–56 giây, mỗi shot 4–6.5 giây một ý, không tự chèn punch-in,
camera bay êm giữa các shot. Nhãn tự né nhau và tự kẹp trong vùng an toàn.

**Rủi ro YouTube**: `python studio.py policy <slug>` (hoặc `--all`) → `qa/policy.md`. Cổng QA đỏ khi ≥ 40% shot lặp khung
của 10 video gần nhất (YouTube "inauthentic content"). Video sức khoẻ tự có dòng "Educational content, not medical
advice." trong mô tả. Chi tiết + nguồn: `docs/YOUTUBE_RISK.md`.

## 7h. Đầu ra gọn · QA tự chặn · người nhiều góc · giọng + tông (vòng 23)

**Mỗi video xong chỉ còn 4 file trong `projects/<slug>/out/`:**

| File | Dùng để |
|---|---|
| `final.mp4` | video 9:16 — đăng chung cho YouTube Shorts, TikTok, Instagram/Facebook Reels |
| `post.md` | copy-dán theo từng nền tảng: tiêu đề (chọn 1), mô tả + nguồn, hashtag, tag YouTube, bình luận ghim, caption TikTok/Reels, cài đặt đăng (Made for kids = No…) |
| `cover-16x9.jpg` | ảnh bìa 16:9 |
| `captions.srt` | phụ đề (nếu muốn tải lên) |

Không còn version cũ, gói nền tảng trùng lặp hay báo cáo QA — tool tự xoá sau khi video **qua cổng QA**. Muốn giữ như cũ:
`config/channel.json → output.lean: false`. Dọn dự án render trước vòng 23: `python studio.py clean --all --lean`.

**QA không cần đọc:** lỗi thấy được bằng mắt đều chặn (video không được xuất): chữ đè hình, video đứng như slide, chữ
khó đọc, số liệu không nguồn, hook yếu (> 16 từ / không gây tò mò / mở đầu chậm), thiếu câu nối lại giữa video, câu độn
hay xin like trong lời đọc, người chỉ một góc nghiêng, người chính trùng video trước.

**Người:** `view` side | front | back (đổi giữa shot bằng key), 15 kiểu người (thêm coach, lifterf, bigguy, elder,
student, office, cyclist, medic, trailrunner), `outfit`, `hair`, `beard`, `glasses`; động tác `deadlift`. Tập tạ nên để
`front` (đòn tạ ngang vai/trước đùi), đạp xe để `side`.

**Giọng:** 27 giọng khác nhau (Edge Neural), mỗi giọng một tông; hook đọc nhanh/sáng hơn, câu chốt chậm/trầm lại.

**Kiếm tiền với giọng TTS:** YouTube không cấm giọng TTS/AI trong video bật kiếm tiền — điều kiện là nội dung tự làm,
không lặp khuôn mẫu, có giá trị (chính sách "inauthentic content"). Điểm cần lưu ý là **giấy phép** của chính dịch vụ
TTS: Edge TTS (thư viện `edge-tts` gọi tính năng đọc to của trình duyệt Edge) không có điều khoản thương mại công khai;
ElevenLabs gói trả phí / Azure Speech thì có. An toàn nhất trước khi bật kiếm tiền: lồng lại bằng ElevenLabs
(`--tts-force`).

## 8. Outro & thumbnail
- Style cắt cảnh: outro Shorts 2,2s ("Next: …" + follow), frame cuối whip về frame đầu để loop. Style board: outro là
  tiêu đề đỏ glitch trên bảng rồi về đen.
- Thumbnail: 3 biến thể theo 5 archetype; ảnh nền không chữ tạo trong Flow (prompt trong `scripts.html`) → 
  `thumbnails/bg_T1.png` (16:9) và `bg_T1_v.png` (9:16). Chưa có thì tool lấy frame từ clip.

## 9. Lỗi thường gặp
| Hiện tượng | Cách xử lý |
|---|---|
| `::stage=lint_failed` / `storyboard_invalid` | Đọc lỗi in ra, sửa trường do người viết trong `storyboard.json` |
| `⚠ board: nhãn … chỉ còn 0.3s để đọc` | Đổi `sync` sang từ xuất hiện sớm hơn trong câu, hoặc rút ngắn nhãn |
| `⚠ board: không tìm thấy từ khoá` | Từ trong `sync` phải có trong câu `vo` của chính shot đó (viết đúng như lời đọc) |
| `::stage=confirm_map` | Kiểm tra bảng map; đúng thì chạy lại với `--yes`, sai thì đổi tên file thành `C01.mp4`… |
| QA "CẦN XEM" | Đọc các dòng ✗ trong `qa/report.html`; ảnh cắt OCR ở `qa/board/`, frame quanh điểm cắt ở `qa/cuts/` |
| Không tìm thấy ffmpeg | Cài như mục 1, hoặc đặt biến `FFMPEG_DIR` trỏ tới thư mục chứa `ffmpeg.exe` |

Font: Be Vietnam Pro, Montserrat, Anton, Patrick Hand… (SIL OFL); FreeMono/FreeSerif Bold (GPL + font exception);
Caladea Bold (Apache 2.0). Chi tiết: `docs/CREDITS.md`.
