# Mảng 4: chuẩn âm thanh (AUD-4xx)

Ngày audit: 15/11/2026 · nhánh `upgrade/atlas-and-audit` @ 5589dc2 · chỉ đọc (không sửa repo, không gọi ElevenLabs).
Công cụ đo: ffmpeg/ffprobe 9.0.2 (`ebur128=peak=true`, `loudnorm=print_format=json`). Mô phỏng `mix.lock()` chạy trong RAM bằng `python -B`, không ghi file nào vào repo.
Script đo và dữ liệu thô nằm trong `C:\Users\lp\AppData\Local\Temp\claude\5969f80ef3cd6de4\626147d2-8970-453a-b069-9f26523574e4\scratchpad\audit\tmp\` (`measure.py` → `finals.json`, `stems.py` → `stems.json`, `extra.py`).

## Điểm: 7.0 / 10 hiện tại → 9.5 / 10 mục tiêu

**Điểm mạnh:** kiến trúc stems → khoá mức → master tách bạch. Master dùng **một gain tuyến tính** cộng limiter, không dùng loudnorm động. Không dùng `-shortest`. Mọi stem đều 48 kHz. Đồng bộ tiếng và hình gần như tuyệt đối. Integrated loudness trúng −14 ±0.4 LU trên cả 21 file.

**Điểm trừ:**
- True peak nằm sát trần −1 dBTP.
- Limiter phải nén tới 4.5 dB.
- SFX không có fade, VO nối và nhạc lặp không có crossfade.
- Nguồn VO là MP3 128k, AAC xuất ra chỉ 192k.
- Khoá mức theo RMS không trọng số K.
- QA thiếu kiểm tra LRA, đồng bộ và clip.
- Có cấu hình chết.

## Số đo thật trên `projects/*/out/final.mp4` (21 file)

Mọi file đều là AAC-LC, 48000 Hz, stereo, khoảng 191 kbps. `start_time` audio = video = 0.000. `initial_padding` = 1024, được edit list bù.

| dự án | VO | I (ebur128) | I (loudnorm) | TP dBTP | LRA ebur128 / loudnorm | lệch dài audio−video |
|---|---|---|---|---|---|---|
| steel-ball-1000c-ice-water | ElevenLabs | −14.2 | −14.38 | **−1.1** | 4.8 / 8.7 | 0.0 ms |
| steel-ball-1000c-board | ElevenLabs | −14.2 | −14.28 | **−1.1** | 4.3 / 6.5 | 0.0 ms |
| feather-vs-bowling-ball-vacuum | ElevenLabs | −14.2 | −14.38 | **−1.1** | 3.7 / 9.3 | 0.0 ms |
| the-marathon-danger-… | ElevenLabs | −14.0 | −14.11 | **−1.1** | 2.6 / 3.1 | 0.0 ms |
| cmp-flat-vector-black | ElevenLabs | −14.0 | −14.24 | **−1.1** | 4.4 / 8.8 | 0.0 ms |
| cmp-hud-black | ElevenLabs | −14.0 | −14.23 | −1.2 | 4.1 / 7.9 | 0.0 ms |
| cmp-line-boil-black | ElevenLabs | −14.1 | −14.26 | **−1.1** | 4.1 / 7.9 | 0.0 ms |
| cmp-physics-diagram-black | ElevenLabs | −14.1 | −14.25 | **−1.1** | 3.8 / 6.8 | 0.0 ms |
| cmp-swiss-motion-black | ElevenLabs | −14.1 | −14.25 | **−1.0** | 4.3 / 8.2 | 0.0 ms |
| dieu-gi-…-bi-sat-nong (VN cũ) | mp3 cũ | −13.9 | −14.00 | −2.3 | 2.4 / 2.9 | −17.3 ms (0.52 frame) |
| dieu-gi-…-marathon-voi-cai (VN cũ) | giả | −13.9 | −14.02 | −4.3 | 0.5 / 3.7 | −8.0 ms (0.24 frame) |
| demo-hybrid-3d / -xray | giả | −13.9 | −14.03 | −3.5 / −2.7 | 0.8–1.0 | 0.0 ms |
| _smoke-html | giả | **−13.4** | −14.00 | −2.1 | 4.0 / 7.0 | 0.0 ms |
| _smoke-three / -manim / -board / -flowday | giả | −13.5…−13.7 | −13.96…−14.05 | −2.8…−4.5 | 2.9–4.2 | 0.0 ms |
| _demo-no-sleep / _dryrun-* (3) | giả | −13.8…−13.9 | −14.02 | −2.1…−3.6 | 0.4–1.5 | 0.0 ms |

Tỉ lệ stem sau khi khoá mức (mô phỏng `mix.lock` trên stems thật, đo bằng ebur128):

| dự án | VO (LUFS) | nhạc sau khoá + duck (LUFS) | SFX (LUFS / TP) | nhạc so với VO khi có lời (RMS) | nhạc ở khe lặng (dBFS RMS) | mix.wav TP |
|---|---|---|---|---|---|---|
| steel-ball-1000c-ice-water | −18.2 | −31.4 (−13.2 LU) | −26.3 / −6.7 | −11.9 dB | −28.9 | — |
| steel-ball-1000c-board | −18.2 | −31.4 | −23.5 / −4.9 | −11.9 dB | −28.9 | −1.0 |
| the-marathon-… | −15.8 | −29.3 (−13.5 LU) | −21.4 / −6.6 | −11.8 dB | −27.9 | −0.9 |
| feather-vs-bowling-ball | −19.3 | −32.4 (−13.1 LU) | −26.4 / −10.1 | −11.9 dB | −33.2 | −2.4 |
| cmp-hud-black | −19.6 | −32.5 (−12.9 LU) | −24.3 / −10.3 | −12.2 dB | −29.1 | −3.0 |

Limiter khi master (mix.wav × gain so với ngưỡng `limit` = −1.3 dBFS):

| dự án | gain | vượt ngưỡng tối đa | số cửa sổ 10 ms vượt | vượt > 3 dB |
|---|---|---|---|---|
| steel-ball-1000c-ice-water | +3.95 dB | **4.5 dB** | 149/4133 (3.6 %) | 8 |
| feather-vs-bowling-ball | +5.23 dB | **4.1 dB** | 81/2146 (3.8 %) | 9 |
| cmp-hud-black | +5.07 dB | 3.4 dB | 46/2120 (2.2 %) | 2 |
| the-marathon-… | +1.37 dB | 1.8 dB | 65/4633 (1.4 %) | 0 |

Tái hiện:

```
ffmpeg -hide_banner -nostats -i projects/steel-ball-1000c-ice-water/out/final.mp4 -vn -af ebur128=peak=true:framelog=quiet -f null -
ffmpeg -hide_banner -nostats -i projects/steel-ball-1000c-ice-water/out/final.mp4 -vn -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
ffprobe -v error -show_streams -of json projects/steel-ball-1000c-ice-water/out/final.mp4
```

---

## Phát hiện

### AUD-401: True peak sát trần −1 dBTP, cổng QA còn nới lên −0.7 dBTP (High)
- **Vị trí:** `config/mix.json:26` (`true_peak_db: -1.0`, `limiter_margin_db: 0.3`), `vidlib/mix.py:138-145`, `vidlib/pipeline.py:752-754` (`true_peak <= true_peak_db + 0.3`).
- **Mô tả và số đo:** cả 9 video ElevenLabs ra TP **−1.0 đến −1.2 dBTP** (ebur128, oversample ×4). cmp-swiss-motion-black đạt −1.03 dBTP. Limiter đặt trần −1.3 dBFS sample-peak ở 192 kHz, sau đó encode AAC lại vọt thêm khoảng 0.2–0.3 dB. Upload lên YouTube/TikTok/IG còn bị transcode thêm lần nữa (Opus/AAC). Spotify khuyến nghị **< −2 dBTP** cho master ≥ −14 LUFS. Video của kênh nằm đúng mức −14 nên không còn đệm. QA cho qua tới −0.7 dBTP, tức là cho phép vượt chính chuẩn của tool.
- **Tái hiện:** lệnh ebur128 ở trên → dòng `Peak:` ra −1.0/−1.1.
- **Sửa:** `true_peak_db: -1.5` (hoặc −2.0) và `limiter_margin_db: 0.5`. QA kiểm `true_peak <= true_peak_db` (bỏ `+0.3`), đo bằng ebur128.
- **Công sức:** S.

### AUD-402: Limiter làm việc của compressor: nén tới 4.5 dB, release 60 ms, gain tính trước limiter nên lệch target (High)
- **Vị trí:** `vidlib/mix.py:148-160` (gain = target − đo trước limiter, đo một lượt), `config/mix.json:26` (`attack_ms 3`, `release_ms 60`). Không có tầng nén hay leveler cho VO ở bất kỳ đâu (`vidlib/vo.py`, `vidlib/mix.py`).
- **Số đo:** steel-ball cần +3.95 dB, đỉnh vượt ngưỡng tới **4.5 dB** trên 3.6 % cửa sổ 10 ms. feather vượt 4.1 dB. Vì gain tính trước khi limiter cắt, đầu ra hụt target: loudnorm đo **−14.38 LUFS** (report.md ghi "→ −14.38 LUFS"), feather −14.38, mọi video thật nằm trong −14.1…−14.4. Release 60 ms với 3 ms attack trên VO cộng `sting_low` (sine 41 Hz, chu kỳ 24 ms) có nguy cơ méo điều biến biên độ và "bơm".
- **Tái hiện:** `extra.py` (mục "limiter GR"), hoặc tính `mix.measure(mix.wav)` rồi `20·log10(peak·10^(gain/20)/0.861)`.
- **Sửa:**
  - Thêm tầng nén VO nhẹ trước `lock()`, ví dụ `acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=…`, hoặc leveler RMS 400 ms. Mục tiêu là limiter chỉ còn cắt ≤ 1.5 dB.
  - Đổi release limiter sang 100–200 ms.
  - Master hai lượt: sau limiter đo lại và bù phần dư (≤ 0.5 dB) rồi limit lần nữa, hoặc dùng `loudnorm` hai lượt với `linear=true`.
- **Công sức:** M.

### AUD-403: mix.wav trung gian là int16 có `np.clip`, không có đệm headroom trước master (Medium)
- **Vị trí:** `vidlib/fakes.py:109-117` (`np.clip(stereo,-1,1)*32767 → int16`), `vidlib/mix.py:114-120`, `vidlib/audio.py:125,152,162`.
- **Mô tả:** VO, nhạc và SFX được cộng ở float32 rồi ghi ra 16-bit có kẹp. Báo cáo `pre_master_peak_dbfs` có ghi lại nhưng không ai xử lý. Hiện chưa clip: mẫu tối đa −0.64 dBFS (demo-hybrid-3d), −0.92 (marathon), 0 mẫu chạm 32767. Nhưng VO ElevenLabs đã có đỉnh −0.9 dBFS, chỉ một SFX lớn trùng đỉnh VO cũng đủ cắt cứng **trước** limiter, không gỡ lại được. Thêm nữa, master còn tăng tới +5.2 dB trên dữ liệu 16-bit.
- **Tái hiện:** đọc mix.wav của marathon: sample peak −0.92 dBFS, chỉ còn chưa tới 1 dB đệm.
- **Sửa:** ghi stems và mix ở WAV float32 (`format=3`, sampwidth 4) hoặc qua ffmpeg `-c:a pcm_f32le`. Nếu giữ int16 thì chuẩn hoá mix về đỉnh −6 dBFS và cộng phần chênh vào gain master. Thêm cảnh báo khi `pre_master_peak_dbfs > -1`.
- **Công sức:** S.

### AUD-404: Chuỗi nguồn VO bị nén mất dữ liệu hai lần và resample (Medium)
- **Vị trí:** `config/voice.json:28` (`"output_format": "mp3_44100_128"`), `vidlib/sfx.py:15` (`GEN_SR = 44100`), `vidlib/mix.py:160` (AAC).
- **Số đo:** cả 9 `audio/vo.mp3` đều là 44100 Hz, 128 kbps. Đường đi là MP3 128k → decode, resample 48 kHz (`sfx.decode`) → AAC 192k → nền tảng transcode lần nữa: **3 thế hệ codec mất dữ liệu** cho giọng, thứ mà khán giả nghe nhiều nhất. SFX tổng hợp ở 44.1 kHz rồi resample lên 48 kHz (không lỗi, chỉ thừa một bước). Mọi stem và mix.wav đều đo được 48000 Hz, nhất quán.
- **Sửa:**
  - VO dùng `pcm_44100` (gói Pro) hoặc tối thiểu `mp3_44100_192` (gói Creator) theo tài liệu ElevenLabs. Khi đổi sang PCM thì `tts.synthesize` phải ghi `vo.wav`, và `load_alignment` (so `mp3_size`) phải cập nhật theo.
  - `GEN_SR` lấy từ `channel.audio.sample_rate`, xoá cache `_builtin` khi đổi.
- **Công sức:** S.

### AUD-405: AAC 192 kbps bằng một nửa khuyến nghị upload của YouTube (Low)
- **Vị trí:** `vidlib/mix.py:159-160` (`-c:a aac -b:a 192k`).
- **Mô tả:** đo được khoảng 191 kbps. YouTube chính thức khuyến nghị AAC-LC stereo **384 kbps**, 48 kHz. Encoder `aac` gốc của ffmpeg ở 192k vẫn ổn, nhưng nguồn đã là MP3 128k và sẽ bị transcode thêm. Với video 60 s, 384 kbps chỉ khoảng 2.9 MB.
- **Sửa:** `-b:a 320k` hoặc `384k`, đặt trong `mix.json → master.aac_kbps`.
- **Công sức:** S.

### AUD-406: SFX không có fade-in/out, nhiều file kết thúc giữa sóng ở mức lớn (Medium)
- **Vị trí:** `vidlib/sfx.py:314-322` (`_write` chỉ chuẩn hoá đỉnh), `vidlib/audio.py:155-159` (`s[i0:i0+len(a)] += a·gain`, không fade, cắt cứng ở cuối stem), `vidlib/sfx.py:204-209` (riser), `:219-224` (glitch), `:148-156` (projector).
- **Số đo** (`assets/sfx/_builtin`, mẫu đầu/cuối so với đỉnh):

  | file | 5 ms cuối | mẫu cuối | mẫu đầu |
  |---|---|---|---|
  | `riser` | **−1.2 dB** | — | — |
  | `glitch` | −2.3 dB | −4.7 dB | −6 dB |
  | `projector_2.8` | — | −10 dB | −4.6 dB |
  | `projector_3.3/3.4` | — | khoảng −18…−19 dB | — |
  | `scrape` | −25.9 dB | — | — |
  | `sting_low` | −27 dB | — | — |
  | `pop` | — | −33.8 dB | — |
  | `typing_*` | — | khoảng −38 dB | — |

  Tiếng "tách" khi cắt ở mức −1…−20 dB nghe rõ, nhất là riser (luôn dẫn vào reveal) và projector (vào/ra phim câm). Các transient cố ý như click/hit/thunk có mẫu đầu khác 0, chấp nhận được.
- **Tái hiện:** `extra.py` (mục "builtin SFX").
- **Sửa:** trong `load()` áp fade-out 5–10 ms (raised-cosine) cho mọi SFX. Áp fade-in 2–3 ms cho SFX không phải transient (`riser`, `projector`, `scratch`, `typing`, `sizzle`, `rumble`). Khi `a` bị cắt bởi `n − i0` cũng fade đoạn cuối. Sau đó xoá `_builtin` để sinh lại.
- **Công sức:** S.

### AUD-407: Nối VO sau khi rút lặng không có crossfade (Low)
- **Vị trí:** `vidlib/vo.py:232-250` (`compress`: nối `mono[pos:a]`, `mono[a:a+h]`, `mono[b-h:b]` trực tiếp), `vidlib/vo.py:350-361` (file từng câu: nối cùng mảng `zeros`, không fade), `vidlib/vo.py:255-263` (atempo).
- **Mô tả:** điểm cắt nằm trong vùng "lặng" (< −38 dB so với cửa sổ 10 ms to nhất), nên bước nhảy tối đa khoảng −38 dB so với đỉnh. Thường không nghe thấy với TTS sạch, nhưng giọng có hơi thở hoặc nền ồn (người dùng tự thu `audio/vo.*`) sẽ ra tiếng tích nhẹ ở mỗi chỗ rút lặng.
- **Sửa:** cắt ở điểm qua 0 gần nhất, hoặc crossfade equal-power 5 ms ở mỗi mối nối. Với file từng câu thì fade 3 ms ở đầu/cuối mỗi câu.
- **Công sức:** S.

### AUD-408: Nhạc người dùng lặp bằng `np.tile` không crossfade; "dừng ở twist" thực chất fade dài vài giây và thay đổi theo từng video (Medium)
- **Vị trí:** `vidlib/audio.py:131` (`np.tile`), `vidlib/audio.py:132-134` và `vidlib/musicgen.py:93-94` (`linspace(1,0,n−i0)**8`).
- **Mô tả:**
  - (a) Nhạc ngắn hơn video sẽ lặp ở đúng mẫu cuối → click, nhảy pha, lệch nhịp ở mối nối.
  - (b) Độ dài fade "dừng" tỉ lệ với **thời gian còn lại** của video, chứ không cố định. Steel-ball: twist 26.67 s, còn 14.6 s, nên nhạc chỉ xuống −20 dB sau **≈ 3.65 s** và −40 dB sau ≈ 6.4 s. Đây không phải cú "DỪNG" như preset payoff mô tả (`config/mix.json:17-19`). Với nhạc tổng hợp, vấn đề nhẹ hơn vì sau twist không đặt nốt mới.
  - musicgen còn cắt cứng đuôi snare (−25.7 dB) và pluck cao (−30.3 dB) ở mỗi nhịp, nhưng mức thấp và bị nốt kế tiếp che.
- **Sửa:** lặp nhạc ở biên ô nhịp (dùng `detect_beats`) với crossfade 50–100 ms. Stop = fade cố định 80–150 ms (`mix.json → payoff.stop_ms`), tuỳ chọn giữ đuôi reverb.
- **Công sức:** S/M.

### AUD-409: Cân bằng VO/nhạc khoá theo RMS không trọng số K; nhạc chỉ thấp hơn lời khoảng 12 dB; duck không có look-ahead (Medium)
- **Vị trí:** `vidlib/mix.py:28-44` (`gated_rms`, cửa sổ 50 ms, không K-weighting), `vidlib/mix.py:88-98`, `vidlib/mix.py:47-62` (`envelope`: attack 40 ms, không nhìn trước), `config/mix.json:5-14`.
- **Số đo:** khi có lời, nhạc thấp hơn VO **−11.8 đến −12.2 dB RMS** (khoá −6 cộng duck −6). Tính bằng LUFS thì nhạc thấp hơn VO 12.9–13.5 LU. Ở khe lặng nhạc bật lên −28…−33 dBFS RMS. Khung thường gặp cho thoại có nhạc nền là thấp hơn 15–20 dB. Ở mức −12 dB, nghe trên loa điện thoại (dải trầm bị cắt, nhạc synth nhiều trung tần) dễ lấn phụ âm. RMS không trọng số K làm nhạc nhiều bass (kick 50–140 Hz) bị đo "to" hơn cảm nhận, nên tỉ lệ thay đổi theo bài. Duck không nhìn trước, nên âm tiết đầu mỗi câu bị nhạc che khoảng 40–80 ms.
- **Sửa:**
  - Khoá mức theo LUFS ngắn hạn hoặc tích hợp của từng stem (lọc K của BS.1770 làm bằng numpy với 2 biquad, hoặc gọi `ebur128` trên từng stem).
  - Đặt `music_db_vs_voice` ≈ −10 và duck 8 dB, để tổng thể khi có lời là −16…−18 LU.
  - Dịch `env` sớm hơn 20–30 ms (look-ahead).
  - Lưu `music_lu_vs_voice_speech` vào QA.
- **Công sức:** M.

### AUD-410: Cấu hình âm thanh trùng hoặc chết, tài liệu sai (Low)
- **Vị trí:** `config/channel.json → audio.music_db, duck_db, duck_attack_ms, duck_release_ms, lufs, true_peak` (khoảng dòng 120-150). Không mô-đun nào dùng các khoá này ngoài `scripts/style_compare.py:230`, nơi in ngưỡng QA từ **channel.json** thay vì mix.json. `config/mix.json:21` `hit_db_vs_voice_peak: -3` không được đọc ở đâu (grep `vidlib/` không thấy). `_doc` của `channel.audio` ghi "Không có VO thì tham chiếu −6 dBFS" trong khi `mix.json:15` là `no_voice_ref_dbfs: -20`.
- **Hệ quả:** người dùng sửa `channel.json → audio.lufs` sẽ không thấy gì thay đổi, còn `style_compare` lại báo ngưỡng sai.
- **Sửa:** xoá các khoá chết, cho `style_compare` đọc `mix.cfg()["master"]`. Hoặc nối `hit_db_vs_voice_peak` vào `sfx.level_db` cho cú hit payoff, hoặc xoá nó.
- **Công sức:** S.

### AUD-411: Đo loudness bằng `loudnorm` (không phải máy đo chuẩn); LRA không được kiểm (Low)
- **Vị trí:** `vidlib/mix.py:124-135`, `vidlib/pipeline.py:750-754`.
- **Số đo:** trên cùng một file, `loudnorm` và `ebur128` (bộ đo BS.1770 tham chiếu của ffmpeg) lệch nhau: _smoke-html **−14.00 và −13.4 LUFS** (0.6 LU), steel-ball −14.38 và −14.2. LRA lệch còn lớn hơn: 8.7 và 4.8 LU (steel-ball), 9.3 và 3.7 (feather). QA không kiểm LRA. `mix.measure` có trả `lra` nhưng không ai dùng.
- **Sửa:** QA đo bằng `ebur128=peak=true` (I, LRA, TP). Thêm check LRA 3–8 LU cho short nói (vàng nếu > 8, đỏ nếu > 11). Giữ loudnorm nếu cần cho đường hai lượt.
- **Công sức:** S.

### AUD-412: Đồng bộ tiếng–hình tốt nhưng chưa được QA tự động (Low, ghi nhận)
- **Vị trí:** `vidlib/qa.py:71-77` (`check_final` chỉ kiểm số audio track), `vidlib/mix.py:156-160`.
- **Số đo:**
  - 19/21 file có độ dài audio bằng video ±0.04 ms. `start_time` của cả hai = 0. Priming AAC 1024 mẫu được edit list bù.
  - Hai video tiếng Việt cũ lệch −8 ms và −17.3 ms (≤ 0.52 frame ở 30 fps), do code cũ sinh ra, không cần render lại.
  - `vo.mp3` của ElevenLabs có header Xing/Info (`start_time 0.025057`), nên ffmpeg đã bỏ encoder delay 1105 mẫu và timestamp từng ký tự khớp audio đã decode.
- **Sửa:** thêm check `|a_dur − v_dur| ≤ 1/30 s`, `a.start_time == v.start_time`, sample rate 48000, codec AAC-LC, số kênh 2.
- **Công sức:** S.

### AUD-413: Sample rate 48000 hard-code ở nhiều chỗ thay vì đọc `channel.audio.sample_rate` (Low)
- **Vị trí:** `vidlib/musicgen.py:8` (`SR = 48000`), `vidlib/mix.py:114` (mặc định), `vidlib/mix.py:141` (`sr = 48000` trong `master_filter`), `vidlib/mix.py:159` (`-ar 48000`), `vidlib/outro.py:152` (`anullsrc=r=48000`).
- **Hệ quả:** nếu sau này đổi sang 44.1 hoặc 96 kHz, `build_stems` sẽ coi bed 48 kHz là mảng ở sample rate mới, làm nhạc lệch cao độ hoặc tốc độ, còn master resample sai. Hiện chưa gây lỗi vì config đang là 48000.
- **Sửa:** truyền `sr` từ config vào `musicgen.bed()` và `master_filter()`.
- **Công sức:** S.

---

## Tổng hợp theo mức

| mức | số lượng | ID |
|---|---|---|
| Critical | 0 | — |
| High | 2 | AUD-401, AUD-402 |
| Medium | 5 | AUD-403, AUD-404, AUD-406, AUD-408, AUD-409 |
| Low | 6 | AUD-405, AUD-407, AUD-410, AUD-411, AUD-412, AUD-413 |

## Bảng chuẩn loudness đã xác minh (web search 15/11/2026)

| nền tảng / chuẩn | giá trị | mức xác minh | nguồn (truy cập 15/11/2026) |
|---|---|---|---|
| YouTube: thông số upload | AAC-LC hoặc Opus; stereo; **48 kHz**; stereo **384 kbps** (mono 128, 5.1 512) | **Chính thức**. Trang này không nói gì về loudness | https://support.google.com/youtube/answer/1722171?hl=en |
| YouTube: chuẩn hoá loudness | khoảng **−14 LUFS** tích hợp, chỉ giảm nội dung to hơn, không tăng nội dung nhỏ | Chỉ có nguồn thứ cấp và đồng thuận cộng đồng (một nguồn nói −13). Không có tài liệu chính thức của YouTube | https://www.meterplugs.com/blog/2019/09/18/youtube-changes-loudness-reference-to-14-lufs.html · https://www.soundbridge.io/mastering-for-streaming-your-2026-platform-guide · https://loststoriesacademy.com/blogs-and-tutorials/why-mastering-for-streaming-is-different-in-2025 (−13) |
| Instagram Reels | khoảng −14 LUFS, TP −1 dBTP (một số nguồn khuyên −15) | **Không có spec chính thức**, chỉ có nguồn thứ cấp | https://dev.to/arthurvalle1_a2586dd2b4bc/mastering-for-reels-tiktok-and-youtube-shorts-the-lufs-14-standard-2ck5 · https://wubble.ai/docs/studio-tools/brand-kit/technical-standards |
| TikTok | khoảng −14 LUFS, TP −1 dBTP; một nguồn nói −16 | **Không có spec chính thức**, các nguồn mâu thuẫn nhau | https://dev.to/arthurvalle1_a2586dd2b4bc/mastering-for-reels-tiktok-and-youtube-shorts-the-lufs-14-standard-2ck5 · https://d1lex0gkhzvix9.cloudfront.net/tiktok-instagram-reels-loudness (−16) |
| Spotify (tham chiếu cho codec mất dữ liệu) | −14 LUFS (ITU 1770); TP **< −1 dBTP** cho Ogg/AAC; **< −2 dBTP nếu master to hơn −14 LUFS** | **Chính thức** | https://support.spotify.com/artists/article/loudness-normalization/ |
| AES TD1008 (streaming) | lời nói **−18 LUFS**, hỗn hợp lời + nhạc −17, nhạc −16; TP −1 dBTP ở đầu vào codec | Nguồn thứ cấp tóm tắt TD1008; chưa mở được bản PDF gốc | https://productionadvice.co.uk/td1008/ · https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026 |
| AES TD1004 (cũ) | target không vượt −16 LUFS và không dưới −20 LUFS | Nguồn thứ cấp | https://www.scribd.com/document/440898812/AESTD1004-1-15-10-pdf |
| LRA cho short nói | không nền tảng nào công bố. Khuyến nghị kỹ thuật: **3–8 LU** (ebur128); kênh hiện đo được 2.6–4.8 LU | Suy luận kỹ thuật, **không phải spec nền tảng** | — |
| ElevenLabs output | `mp3_44100_192` cần gói Creator trở lên; PCM 44.1 kHz cần gói Pro trở lên | Nguồn thứ cấp và tài liệu cũ; cần kiểm lại trang pricing | https://elevenlabs.io/docs/capabilities/text-to-speech · https://docs.getbifrost.ai/providers/supported-providers/elevenlabs |

Ghi chú: tính năng "Stable volume" của YouTube trên mobile chưa xác minh được, vì lượt tìm kiếm bị giới hạn API.

## Target thống nhất đề xuất cho tool

| thông số | hiện tại | đề xuất |
|---|---|---|
| Integrated | −14 LUFS (loudnorm), thực tế −14.0…−14.4 | **−14.0 LUFS ±0.5**, đo bằng `ebur128`, master hai lượt |
| True peak | trần −1.3 dBFS, đo được −1.0…−1.2 dBTP, QA ≤ −0.7 | **≤ −1.5 dBTP** (trần limiter khoảng −2.0 dBFS ở 4×). QA đỏ nếu > −1.0, vàng nếu > −1.5 |
| LRA | không kiểm | **3–8 LU** (ebur128), vàng nếu > 8 |
| Gain reduction của limiter | tới 4.5 dB | **≤ 1.5 dB** (thêm compressor/leveler cho VO) |
| Sample rate | 48 kHz ở stem/mix/final (hard-code một số chỗ) | 48 kHz ở mọi nơi, đọc từ config; trung gian float32 |
| Nguồn VO | MP3 44.1k 128k | PCM 44.1k (Pro) hoặc MP3 192k (Creator) |
| Codec xuất | AAC-LC 192k | **AAC-LC 320–384 kbps** stereo 48 kHz |
| Nhạc so với VO khi có lời | khoảng −12 dB RMS (−13 LU) | **−16…−18 LU** (K-weighted), duck có look-ahead 20–30 ms |
| Mối nối | không fade | fade/crossfade **5–10 ms** ở mọi SFX, mối nối VO, vòng lặp nhạc |
| Đồng bộ | đạt (0 ms) | QA tự động: lệch ≤ 1 frame, start_time bằng nhau |

Lý do giữ −14 LUFS cho Shorts: YouTube, IG và TikTok đều chỉ giảm nội dung to hơn mức chuẩn, không tăng nội dung nhỏ. −14 là mức thấp nhất mà vẫn không bị nhỏ hơn các video khác trong feed. Mức −16/−18 của AES dành cho podcast và radio, không áp cho feed short.
