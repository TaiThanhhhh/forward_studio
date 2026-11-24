"""Lời đọc bằng ElevenLabs (config/voice.json) — kèm timestamp TỪNG KÝ TỰ để căn hình theo giọng.

- Ghép các câu `vo` của storyboard thành MỘT lần gọi (ngữ điệu liền mạch), số/ký hiệu đổi sang chữ (lang.spoken),
  thuật ngữ đổi theo bảng phát âm, audio tag [excited]… giữ nguyên cho model v3.
- Kết quả: audio/vo.mp3 + audio/vo_alignment.json (mốc từng TỪ hiển thị, đã map ngược từ ký tự).
- Cache theo nội dung: chạy lại pipeline không gọi API lần nữa nếu lời/giọng/cài đặt không đổi (không tốn credit).
"""
import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.request

from . import lang
from .common import CONFIG_DIR, StudioError, env, load_json, probe, run, save_json

TAG_RE = re.compile(r"\[([a-zA-Z ]{2,24})\]")
API = "https://api.elevenlabs.io/v1"
CHUNK_MAX_CHARS = 1400


def voice_cfg():
    return load_json(os.path.join(CONFIG_DIR, "voice.json"))


def strip_tags(text):
    """Bỏ audio tag — chữ hiển thị, .srt, đếm từ đều dùng bản này."""
    return re.sub(r"\s{2,}", " ", TAG_RE.sub("", text or "")).strip()


def tags_in(text):
    return [m.group(1).strip().lower() for m in TAG_RE.finditer(text or "")]


def _alias(token, pron):
    core = re.sub(r"^[^\w]+|[^\w]+$", "", token)
    for k, v in pron.items():
        if k.startswith("_"):
            continue
        if core.lower() == k.lower():
            return token.replace(core, v)
    return token


def build_text(lines, cfg=None):
    """lines = [{text, beat}] → (chuỗi gửi TTS, words=[{w, line, a, b}] với [a, b) là vị trí ký tự trong chuỗi)."""
    cfg = cfg or voice_cfg()
    tags_cfg = cfg.get("audio_tags", {})
    pron = cfg.get("pronunciation", {})
    items = []  # (chuỗi gửi đi, từ hiển thị hoặc None nếu là tag, số câu)
    for k, ln in enumerate(lines):
        raw = ln["text"].strip()
        if tags_cfg.get("enabled") and not tags_in(raw):
            dflt = tags_cfg.get("default_by_beat", {}).get(ln.get("beat"))
            if dflt:
                items.append((f"[{dflt}]", None, k))
        for piece in re.split(r"(\[[a-zA-Z ]{2,24}\])", raw):
            piece = piece.strip()
            if not piece:
                continue
            if TAG_RE.fullmatch(piece):
                if tags_cfg.get("enabled"):
                    items.append((piece, None, k))
                continue
            for tok in piece.split():
                items.append((_alias(lang.spoken(tok), pron), tok, k))
    text, words, pos = [], [], 0
    for s, disp, k in items:
        if pos:
            text.append(" ")
            pos += 1
        if disp is not None:
            words.append({"w": disp, "line": k, "a": pos, "b": pos + len(s)})
        text.append(s)
        pos += len(s)
    return "".join(text), words


def cache_key(text, cfg):
    blob = json.dumps({"t": text, "v": cfg["voice"]["id"], "m": cfg["model_id"], "s": cfg["voice_settings"],
                       "f": cfg["output_format"]}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def _post(path, body, key, tries=3, backoff=4.0):
    """POST JSON; tự thử lại khi 429/5xx/lỗi mạng (AUD-205) — 4xx khác (sai key, hết quota) báo ngay."""
    import time  # noqa: PLC0415

    last = None
    for k in range(tries):
        req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                                     headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            last = StudioError(f"ElevenLabs trả lỗi HTTP {e.code}: {detail}")
            if e.code != 429 and e.code < 500:
                raise last from e
        except urllib.error.URLError as e:
            last = StudioError(f"Không gọi được ElevenLabs ({e.reason}). Kiểm tra mạng.")
        if k < tries - 1:
            time.sleep(backoff * (2 ** k))
    raise last


def word_times(words, align):
    """Map mốc ký tự → mốc từng từ hiển thị."""
    st, en = align["character_start_times_seconds"], align["character_end_times_seconds"]
    out = []
    for w in words:
        a, b = w["a"], min(w["b"], len(st))
        if a >= b:
            continue
        idx = [i for i in range(a, b) if not align["characters"][i].isspace()] or list(range(a, b))
        out.append({"w": w["w"], "line": w["line"], "start": round(st[idx[0]], 3), "end": round(en[idx[-1]], 3)})
    return out


def _split_chunks(lines, cfg=None, max_chars=CHUNK_MAX_CHARS):
    """Chia danh sách câu `lines` thành các đoạn ≤ max_chars (tách tại ranh giới câu) cho video 65–180s.
    Trả về list[(start_line_idx, sub_lines)]. Video ngắn (≤ max_chars) luôn trả về đúng 1 đoạn."""
    full_text, _ = build_text(lines, cfg)
    if len(full_text) <= max_chars or len(lines) <= 1:
        return [(0, list(lines))]
    chunks, cur, cur_start = [], [], 0
    for idx, ln in enumerate(lines):
        cand = cur + [ln]
        cand_text, _ = build_text(cand, cfg)
        if cur and len(cand_text) > max_chars:
            chunks.append((cur_start, cur))
            cur = [ln]
            cur_start = idx
        else:
            cur = cand
    if cur:
        chunks.append((cur_start, cur))
    return chunks


def _synth_chunked(adir, chunks, cfg, api_key, log=print):
    """Gọi ElevenLabs theo từng đoạn (giữ ngữ điệu bằng previous_text/next_text), nối MP3 và cộng dồn mốc từ."""
    import tempfile  # noqa: PLC0415

    built = [(start_idx, *build_text(sub, cfg)) for start_idx, sub in chunks]
    log(f"  · ElevenLabs (chia {len(built)} đoạn cho kịch bản dài): {cfg['voice']['name']} · {cfg['model_id']}")
    part_paths, wt_all, offset = [], [], 0.0
    tmp_dir = tempfile.mkdtemp(prefix="tts_chunks_", dir=adir)
    try:
        for i, (start_idx, ctext, cwords) in enumerate(built):
            body = {"text": ctext, "model_id": cfg["model_id"], "voice_settings": cfg["voice_settings"]}
            if i > 0:
                body["previous_text"] = built[i - 1][1][-300:]
            if i + 1 < len(built):
                body["next_text"] = built[i + 1][1][:300]
            r = _post(
                f"/text-to-speech/{cfg['voice']['id']}/with-timestamps?output_format={cfg['output_format']}",
                body,
                api_key,
            )
            part_mp3 = os.path.join(tmp_dir, f"part_{i:02d}.mp3")
            with open(part_mp3, "wb") as pf:
                pf.write(base64.b64decode(r["audio_base64"]))
            part_paths.append(part_mp3)
            align = r.get("alignment") or r.get("normalized_alignment")
            if not align or len(align.get("characters", [])) != len(ctext):
                align = r.get("normalized_alignment") or align
            cwt = word_times(cwords, align)
            for w in cwt:
                wt_all.append({
                    "w": w["w"],
                    "line": w["line"] + start_idx,
                    "start": round(w["start"] + offset, 3),
                    "end": round(w["end"] + offset, 3),
                })
            try:
                cdur = float(probe(part_mp3)["duration"])
            except Exception:  # noqa: BLE001
                cdur = align["character_end_times_seconds"][-1] if align.get("character_end_times_seconds") else 0.0
            offset += cdur

        lst_path = os.path.join(tmp_dir, "concat.txt")
        with open(lst_path, "w", encoding="utf-8", newline="\n") as lf:
            for p in part_paths:
                lf.write(f"file '{os.path.abspath(p).replace(chr(92), '/')}'\n")
        merged = os.path.join(tmp_dir, "merged.mp3")
        run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst_path, "-c", "copy", merged],
            "ffmpeg (tts chunk concat)",
        )
        with open(merged, "rb") as mf:
            audio = mf.read()
        return audio, wt_all, round(offset, 3)
    finally:
        import shutil  # noqa: PLC0415
        shutil.rmtree(tmp_dir, ignore_errors=True)


def synthesize(proj, lines, log=print, force=False, voice=None):
    """Tạo audio/vo.mp3 + audio/vo_alignment.json nếu chưa có hoặc lời/giọng đã đổi. Trả về đường dẫn alignment.
    voice: giọng của video này (storyboard.voice_resolved, vidlib/voices.py); None = giọng mặc định trong voice.json."""
    cfg = voice_cfg()
    if voice and voice.get("id"):
        cfg = {**cfg, "voice": {"id": voice["id"], "name": voice.get("name", "")}}
        if voice.get("settings"):
            cfg["voice_settings"] = {**cfg["voice_settings"], **voice["settings"]}
    text, words = build_text(lines, cfg)
    key = cache_key(text, cfg)
    adir = os.path.join(proj, "audio")
    os.makedirs(adir, exist_ok=True)
    mp3, ap = os.path.join(adir, "vo.mp3"), os.path.join(adir, "vo_alignment.json")
    old = load_json(ap, {})
    if not force and old.get("key") == key and os.path.exists(mp3):
        from . import cost  # noqa: PLC0415
        cost.record(proj, "tts", provider="elevenlabs", chars=len(text), cached=True, model=cfg["model_id"])
        return ap
    api_key = env(cfg.get("api_key_env", "ELEVENLABS_API_KEY"))
    if not api_key:
        raise StudioError("Chưa có ELEVENLABS_API_KEY (biến môi trường hoặc file .env ở gốc repo).")
    chunks = _split_chunks(lines, cfg)
    if len(chunks) > 1:
        audio, wt, dur = _synth_chunked(adir, chunks, cfg, api_key, log=log)
    else:
        log(f"  · ElevenLabs: {cfg['voice']['name']} · {cfg['model_id']} · {len(text)} ký tự")
        r = _post(f"/text-to-speech/{cfg['voice']['id']}/with-timestamps?output_format={cfg['output_format']}",
                  {"text": text, "model_id": cfg["model_id"], "voice_settings": cfg["voice_settings"]}, api_key)
        audio = base64.b64decode(r["audio_base64"])
        align = r.get("alignment") or r.get("normalized_alignment")
        if not align or len(align.get("characters", [])) != len(text):
            align = r.get("normalized_alignment") or align
        wt = word_times(words, align)
        dur = align["character_end_times_seconds"][-1] if align.get("character_end_times_seconds") else 0
    from . import cost  # noqa: PLC0415
    cost.record(proj, "tts", provider="elevenlabs", chars=len(text), cached=False, model=cfg["model_id"],
                voice=cfg["voice"].get("name"))
    tmp = mp3 + ".part"                         # ghi nguyên tử (AUD-208): bị ngắt không để lại vo.mp3 cụt
    with open(tmp, "wb") as f:
        f.write(audio)
    if old and os.path.exists(mp3):  # giữ bản cũ để so sánh, không ghi đè mất
        os.replace(mp3, os.path.join(adir, f"vo.prev-{old.get('key', 'x')}.mp3"))
    os.replace(tmp, mp3)
    n_words = len(wt)
    # nhịp NÓI: tổng thời gian từng câu (bỏ khoảng ngừng giữa câu — hậu kỳ cắt lặng), nhân atempo vo.speed
    speak = sum(max(w["end"] for w in wt if w["line"] == k) - min(w["start"] for w in wt if w["line"] == k)
                for k in {w["line"] for w in wt}) or dur
    from .common import channel  # noqa: PLC0415
    from .voices import adaptive_speed  # noqa: PLC0415
    raw = n_words / max(speak, 1e-6)
    sp = adaptive_speed(raw) if voice and not voice.get("legacy") else float(channel()["vo"].get("speed") or 1.0)
    rate = raw * sp
    save_json(ap, {"key": key, "voice": cfg["voice"], "model_id": cfg["model_id"],
                   "voice_settings": cfg["voice_settings"], "text": text, "words": wt,
                   "duration": dur, "words_per_sec": round(rate, 2), "raw_words_per_sec": round(raw, 3),
                   "speed_at_synth": sp, "mp3_size": len(audio)})
    log(f"  ✔ audio/vo.mp3 · {dur:.1f}s · {n_words} từ · nhịp nói {rate:.2f} từ/giây (sau atempo, bỏ khoảng ngừng)")
    lo, hi = cfg.get("min_words_per_sec", 3.2), cfg.get("max_words_per_sec", 4.3)
    if not lo <= rate <= hi:
        log(f"  ⚠ nhịp nói {rate:.2f} từ/giây ngoài {lo}–{hi} — eleven_v3 bỏ qua voice_settings.speed: chỉnh "
            "channel.json → vo.speed (atempo ≤ 1.15) hoặc đổi voice/model trong config/voice.json.")
    return ap


def load_alignment(proj, vo_path):
    """Alignment còn khớp với file vo đang dùng? (cùng kích thước file mp3) → dict, ngược lại None."""
    ap = os.path.join(proj, "audio", "vo_alignment.json")
    a = load_json(ap, {})
    if not a or not vo_path or not os.path.exists(vo_path):
        return None
    if a.get("mp3_size") and os.path.getsize(vo_path) != a["mp3_size"]:
        return None
    return a
