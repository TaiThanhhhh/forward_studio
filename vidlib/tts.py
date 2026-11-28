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

EDGE_VOICE_MAP = {
    "george": "en-GB-RyanNeural",
    "daniel": "en-GB-RyanNeural",
    "brian": "en-US-BrianMultilingualNeural",
    "eric": "en-US-BrianMultilingualNeural",
    "bill": "en-US-BrianMultilingualNeural",
    "roger": "en-US-BrianMultilingualNeural",
    "adam": "en-US-AndrewMultilingualNeural",
    "chris": "en-US-AndrewMultilingualNeural",
    "will": "en-US-AndrewMultilingualNeural",
    "john": "en-US-AndrewMultilingualNeural",
    "liam": "en-US-ChristopherNeural",
    "charlie": "en-US-ChristopherNeural",
    "sarah": "en-US-AvaMultilingualNeural",
    "alice": "en-GB-SoniaNeural",
    "bella": "en-US-AvaMultilingualNeural",
    "matilda": "en-US-AvaMultilingualNeural",
    "lily": "en-GB-SoniaNeural",
    "laura": "en-US-EmmaMultilingualNeural",
    "jessica": "en-US-EmmaMultilingualNeural",
    "river": "en-US-AndrewMultilingualNeural",
}


def _edge_voice_for(voice_name):
    """Map tên giọng ElevenLabs sang giọng Microsoft Neural tương đương (miễn phí, không giới hạn)."""
    raw = str(voice_name or "").strip()
    if raw.lower().startswith("edge:"):
        return raw.split(":", 1)[1].strip()
    if raw.endswith("Neural"):
        return raw
    first = raw.split()[0].lower() if raw else ""
    return EDGE_VOICE_MAP.get(first, "en-US-AndrewMultilingualNeural")


def _align_boundary_words(spoken_text, words, boundaries):
    """Khớp danh sách WordBoundary từ edge-tts về từng từ hiển thị `{w, line, start, end}`."""
    def _norm(s):
        return re.sub(r"[^a-z0-9]", "", str(s or "").lower())

    b_idx = 0
    nb = len(boundaries)
    out = []
    last_t = 0.0
    for w in words:
        target = _norm(spoken_text[w["a"]:w["b"]]) or _norm(w["w"])
        if b_idx >= nb:
            out.append({"w": w["w"], "line": w["line"], "start": round(last_t, 3), "end": round(last_t + 0.15, 3)})
            last_t += 0.15
            continue
        start = boundaries[b_idx][1]
        end = boundaries[b_idx][2]
        acc = _norm(boundaries[b_idx][0])
        b_idx += 1
        while target and acc and len(acc) < len(target) and target.startswith(acc) and b_idx < nb:
            nxt = _norm(boundaries[b_idx][0])
            if not target.startswith(acc + nxt):
                break
            acc += nxt
            end = boundaries[b_idx][2]
            b_idx += 1
        last_t = max(last_t, end)
        out.append({"w": w["w"], "line": w["line"], "start": round(start, 3), "end": round(max(end, start + 0.04), 3)})
    return out


def edge_spec(cfg, voice=None):
    """Giọng Neural + tông gốc {voice, rate %, pitch Hz} của giọng đang dùng (vòng 23: mỗi giọng trong kho một giọng
    riêng — trước đây 22 tên dồn vào 5 giọng). Thứ tự: voice['edge'] → mục trong kho cùng id → bảng tên cũ."""
    v = voice or cfg.get("voice") or {}
    spec = v.get("edge")
    if not spec and v.get("id"):
        for p in (cfg.get("pools") or {}).values():
            for x in p if isinstance(p, list) else []:
                if isinstance(x, dict) and x.get("id") == v["id"] and x.get("edge"):
                    spec = x["edge"]
    if not spec:
        vid = str(v.get("id") or "")
        name = vid.split(":", 1)[1] if vid.startswith("edge:") else _edge_voice_for(v.get("name"))
        spec = {"voice": name, "rate": 0, "pitch": 0}
    return {"voice": spec["voice"], "rate": int(spec.get("rate", 0)), "pitch": int(spec.get("pitch", 0))}


def _tone_segments(lines, cfg):
    """Câu liền nhau cùng vai (beat) → một đoạn đọc cùng tông. [(chỉ số câu đầu, [câu], beat)]."""
    segs = []
    for i, ln in enumerate(lines):
        b = ln.get("beat") or "setup"
        if segs and segs[-1][2] == b:
            segs[-1][1].append(ln)
        else:
            segs.append((i, [ln], b))
    return segs


def _synth_edge(lines, cfg, log=print, voice=None):
    """Tổng hợp giọng Neural miễn phí qua `edge-tts` kèm mốc từng từ (`WordBoundary`). Vòng 23: tông theo vai câu
    (`voice.json → edge_tone`: hook nhanh/sáng hơn, payoff chậm/trầm lại) — đọc từng đoạn cùng vai rồi nối."""
    import asyncio  # noqa: PLC0415
    import shutil  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    try:
        import edge_tts  # noqa: PLC0415
    except ImportError as ex:
        raise StudioError("Chưa cài edge-tts cho giọng Neural dự phòng. Chạy: pip install edge-tts") from ex

    clean_cfg = {**cfg, "audio_tags": {"enabled": False}}
    spec = edge_spec(cfg, voice)
    tones = cfg.get("edge_tone") or {}
    segs = _tone_segments(lines, cfg)
    total_chars = len(build_text(lines, clean_cfg)[0])
    log(f"  · Edge Neural TTS: {spec['voice']} (tông {spec['rate']:+d}% / {spec['pitch']:+d}Hz) · "
        f"{len(segs)} đoạn theo vai · {total_chars} ký tự")

    async def _one(text, rate, pitch):
        comm = edge_tts.Communicate(text, spec["voice"], rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz", boundary="WordBoundary")
        buf, bounds = bytearray(), []
        async for ch in comm.stream():
            if ch["type"] == "audio":
                buf.extend(ch["data"])
            elif ch["type"] == "WordBoundary":
                bounds.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
        return bytes(buf), bounds

    tmp = tempfile.mkdtemp(prefix="edge_tts_")
    try:
        parts, wt_all, offset = [], [], 0.0
        for k, (start, sub, beat) in enumerate(segs):
            t = tones.get(beat) or {}
            rate = max(-30, min(30, spec["rate"] + int(t.get("rate", 0))))
            pitch = max(-20, min(20, spec["pitch"] + int(t.get("pitch", 0))))
            text, words = build_text(sub, clean_cfg)
            audio, bounds = asyncio.run(_one(text, rate, pitch))
            if not audio:
                raise StudioError("Edge Neural TTS không trả về dữ liệu âm thanh.")
            pth = os.path.join(tmp, f"seg_{k:02d}.mp3")
            with open(pth, "wb") as fh:
                fh.write(audio)
            parts.append(pth)
            for w in _align_boundary_words(text, words, bounds):
                wt_all.append({**w, "line": w["line"] + start, "start": round(w["start"] + offset, 3),
                               "end": round(w["end"] + offset, 3)})
            try:
                offset += float(probe(pth)["duration"])
            except Exception:  # noqa: BLE001
                offset += bounds[-1][2] if bounds else 0.0
        if len(parts) == 1:
            with open(parts[0], "rb") as fh:
                audio = fh.read()
        else:
            lst = os.path.join(tmp, "list.txt")
            with open(lst, "w", encoding="utf-8", newline=chr(10)) as fh:
                fh.writelines(f"file '{os.path.abspath(q).replace(chr(92), '/')}'" + chr(10) for q in parts)
            merged = os.path.join(tmp, "merged.mp3")
            run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", merged],
                "ffmpeg (edge tts concat)")
            with open(merged, "rb") as fh:
                audio = fh.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    dur = wt_all[-1]["end"] if wt_all else 0.0
    return audio, wt_all, round(dur, 3), spec["voice"]


def _is_elevenlabs_quota_err(ex):
    msg = str(ex).lower()
    return any(k in msg for k in ("quota", "http 401", "http 402", "http 429", "character_limit", "credits"))


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
    provider_pref = (env("TTS_PROVIDER") or os.environ.get("TTS_PROVIDER") or "elevenlabs").strip().lower()
    if str((voice or {}).get("id", "")).startswith("edge:"):
        provider_pref = "edge"                     # giọng chỉ có trên Edge (vòng 23)
    key = cache_key(text, cfg)
    if provider_pref == "edge":                    # đổi giọng/tông Edge → đọc lại (khoá cache gồm cả tông theo vai)
        key = hashlib.sha1(json.dumps({"k": key, "edge": edge_spec(cfg, voice), "tone": cfg.get("edge_tone")},
                                      sort_keys=True).encode()).hexdigest()[:16]
    adir = os.path.join(proj, "audio")
    os.makedirs(adir, exist_ok=True)
    mp3, ap = os.path.join(adir, "vo.mp3"), os.path.join(adir, "vo_alignment.json")
    old = load_json(ap, {})
    if not force and old.get("key") == key and os.path.exists(mp3):
        from . import cost  # noqa: PLC0415
        cost.record(proj, "tts", provider="elevenlabs", chars=len(text), cached=True, model=cfg["model_id"])
        return ap
    api_key = env(cfg.get("api_key_env", "ELEVENLABS_API_KEY"))
    used_provider = "elevenlabs"
    used_model = cfg["model_id"]
    used_voice_name = cfg["voice"].get("name")

    def _run_elevenlabs():
        chunks = _split_chunks(lines, cfg)
        if len(chunks) > 1:
            return _synth_chunked(adir, chunks, cfg, api_key, log=log)
        log(f"  · ElevenLabs: {cfg['voice']['name']} · {cfg['model_id']} · {len(text)} ký tự")
        r = _post(f"/text-to-speech/{cfg['voice']['id']}/with-timestamps?output_format={cfg['output_format']}",
                  {"text": text, "model_id": cfg["model_id"], "voice_settings": cfg["voice_settings"]}, api_key)
        raw_audio = base64.b64decode(r["audio_base64"])
        align = r.get("alignment") or r.get("normalized_alignment")
        if not align or len(align.get("characters", [])) != len(text):
            align = r.get("normalized_alignment") or align
        raw_wt = word_times(words, align)
        raw_dur = align["character_end_times_seconds"][-1] if align.get("character_end_times_seconds") else 0
        return raw_audio, raw_wt, raw_dur

    if provider_pref == "edge":
        audio, wt, dur, ev = _synth_edge(lines, cfg, log=log, voice=voice)
        used_provider, used_model, used_voice_name = "edge_tts", ev, ev
    elif not api_key:
        if provider_pref == "elevenlabs":
            raise StudioError("Chưa có ELEVENLABS_API_KEY (biến môi trường hoặc file .env ở gốc repo).")
        log("  ⚠ Không có ELEVENLABS_API_KEY → chuyển tự động sang Edge Neural TTS (miễn phí).")
        audio, wt, dur, ev = _synth_edge(lines, cfg, log=log, voice=voice)
        used_provider, used_model, used_voice_name = "edge_tts", ev, ev
    else:
        try:
            audio, wt, dur = _run_elevenlabs()
        except StudioError as ex:
            if provider_pref != "elevenlabs" and _is_elevenlabs_quota_err(ex):
                log(f"  ⚠ ElevenLabs hết quota/giới hạn ({ex}) → chuyển tự động sang Edge Neural TTS (miễn phí).")
                audio, wt, dur, ev = _synth_edge(lines, cfg, log=log, voice=voice)
                used_provider, used_model, used_voice_name = "edge_tts", ev, ev
            else:
                raise
    from . import cost  # noqa: PLC0415
    cost.record(proj, "tts", provider=used_provider, chars=len(text), cached=False, model=used_model,
                voice=used_voice_name)
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
                   "speed_at_synth": sp, "mp3_size": len(audio),
                   "provider": used_provider, "provider_model": used_model, "provider_voice": used_voice_name})
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
