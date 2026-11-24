"""Gói xuất theo nền tảng (AUD-501/502/504/505, stage `deliver`).

  out/deliver/<preset>/video.mp4 · cover.jpg · captions.srt · deliver.json   +   out/deliver/deliver.json (tổng)

- 9:16 (Shorts / Reels / TikTok): remux master `out/final.mp4` (video + audio copy → không nén lại lần nữa), gắn
  metadata nguồn gốc; kiểm lại bằng ffprobe + đo loudness so với spec của preset (`config/delivery.json`).
- 16:9 (YouTube): pillarbox nền đen 1920×1080 (+ endscreen 16:9 nối cuối nếu có), encode bằng tham số chung.
- Bìa: từ thumbnail 9:16 / 16:9 của dự án, đúng kích thước preset, JPEG sRGB, ép dưới trần dung lượng.
- Safe zone: so bố cục chữ của kênh (`channel.json → safe_zone`) với vùng an toàn của từng preset → dòng vàng nếu lấn.
"""
import glob
import os
import shutil

from . import encode, mix, qagate
from .common import CONFIG_DIR, StudioError, channel, load_json, probe, replace_retry, run, save_json


def cfg():
    return load_json(os.path.join(CONFIG_DIR, "delivery.json"), {})


def preset_names(names=None):
    c = cfg()
    if names in (None, "", "default"):
        return list(c.get("default") or [])
    if names == "all":
        return list(c["presets"])
    names = names.split(",") if isinstance(names, str) else list(names)
    bad = [n for n in names if n not in c["presets"]]
    if bad:
        raise StudioError(f"Không có preset {bad} (có: {', '.join(c['presets'])}).")
    return names


def _meta_args(meta):
    out = []
    for k, v in (meta or {}).items():
        if v:
            out += ["-metadata", f"{k}={v}"]
    return out


def _remux(src, dst, meta):
    tmp = dst + ".part.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-map", "0", "-c", "copy", *_meta_args(meta), *encode.mux_args(), tmp],
        "ffmpeg (deliver remux)")
    replace_retry(tmp, dst)


def _pillarbox(src, dst, p, endscreen, meta):
    w, h = p["size"]
    fps = p.get("fps", 30)
    pad = (f"scale=-2:{h}:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={fps}")
    tmp = dst + ".part.mp4"
    if endscreen and os.path.exists(endscreen) and os.path.getsize(endscreen) > 1024:
        fc = (f"[0:v]{pad}[v0];[1:v]scale={w}:{h}:flags=lanczos,setsar=1,fps={fps}[v1];"
              f"[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];[1:a]aresample=48000,aformat=channel_layouts=stereo[a1];"
              f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[vc][a];[vc]{encode.TO_YUV}[v]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-i", endscreen, "-filter_complex", fc,
               "-map", "[v]", "-map", "[a]"]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", f"{pad},{encode.TO_YUV}", "-map", "0:v:0", "-map", "0:a:0?"]
    run(cmd + [*encode.video_args("master", fps), "-fps_mode", "cfr", "-r", str(fps), *encode.audio_args(),
               *_meta_args(meta), *encode.mux_args(), tmp],
        "ffmpeg (deliver 16:9)")
    replace_retry(tmp, dst)


def _thumb_source(proj, aspect):
    tag = "9x16" if aspect == "9:16" else "16x9"
    for pat in (f"T1_{tag}.png", f"T1_{tag}.jpg", f"*_{tag}.png", f"*_{tag}.jpg", "T1*.png"):
        hits = sorted(glob.glob(os.path.join(proj, "thumbnails", pat)))
        if hits:
            return hits[0]
    return None


def cover(proj, p, dst):
    """Ảnh bìa đúng kích thước preset (cắt giữa theo tỉ lệ), JPEG sRGB, giảm chất lượng tới khi ≤ max_kb."""
    from PIL import Image, ImageOps  # noqa: PLC0415

    src = _thumb_source(proj, p["aspect"])
    if not src:
        return None, "không có thumbnail nguồn"
    w, h = p["cover"]["size"]
    im = ImageOps.fit(Image.open(src).convert("RGB"), (w, h), Image.LANCZOS)
    lim = int(p["cover"].get("max_kb") or 2048) * 1024
    for q in (92, 88, 84, 80, 75, 70):
        im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
        if os.path.getsize(dst) <= lim:
            break
    return dst, f"{w}x{h} · {os.path.getsize(dst) // 1024} KB (≤ {lim // 1024})"


def safe_zone_checks(p):
    """Bố cục chữ của master (channel.safe_zone) có nằm trong vùng an toàn của preset không (chỉ cảnh báo vàng)."""
    sz = {k: v for k, v in (channel().get("safe_zone") or {}).items() if not k.startswith("_")}
    ps = p.get("safe") or {}
    if p["aspect"] != "9:16" or not sz:
        return {}
    H = p["size"][1]
    band = sz.get("caption_band") or [0, 0]
    low = H - int(ps.get("bottom", 0))
    rows = {
        f"safe zone {p['label']} — đỉnh": (f"chữ từ y={sz.get('top')} (preset ≥ {ps.get('top')})",
                                          int(sz.get("top", 0)) >= int(ps.get("top", 0)) or None),
        f"safe zone {p['label']} — đáy": (f"dải chữ tới y={band[1]} (preset ≤ {low})", int(band[1]) <= low or None),
        f"safe zone {p['label']} — cạnh": (f"lề {sz.get('left')} px (preset ≥ {ps.get('left')})",
                                          int(sz.get("left", 0)) >= int(ps.get("left", 0)) or None),
    }
    return rows                     # None = vàng (lấn vùng UI của nền tảng), không chặn


def verify(video, p):
    """Đo file đã xuất so với spec preset → {nhãn: (giá trị, đạt?)} (nhãn bắt đầu 'nền tảng' → chặn khi đỏ)."""
    lab = f"nền tảng {p['label']}"
    if not os.path.exists(video) or os.path.getsize(video) < 1024:
        return {f"{lab}: file": ("thiếu / hỏng", False)}
    info = probe(video)
    d = qagate.probe_full(video)
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), {})
    a = next((s for s in d["streams"] if s.get("codec_type") == "audio"), {})
    mb = os.path.getsize(video) / 1e6
    kbps = float(d["format"].get("bit_rate") or 0) / 1000
    w, h = p["size"]
    cfr = v.get("r_frame_rate") == v.get("avg_frame_rate")
    out = {
        f"{lab}: khung {w}x{h}": (f"{info['width']}x{info['height']}", (info["width"], info["height"]) == (w, h)),
        f"{lab}: {p['fps']} fps CFR": (f"{v.get('avg_frame_rate')} ({'CFR' if cfr else 'VFR'})",
                                      cfr and abs(info["fps"] - p["fps"]) < 0.01),
        f"{lab}: codec H.264 + AAC": (f"{v.get('codec_name')} + {a.get('codec_name')}",
                                     v.get("codec_name") == "h264" and a.get("codec_name") == "aac"),
        f"{lab}: audio {p.get('audio_rate', 48000)} Hz ≥ {p.get('audio_min_kbps', 128)} kb/s":
            (f"{a.get('sample_rate')} Hz · {int(float(a.get('bit_rate') or 0) / 1000)} kb/s"
             + (" (endscreen im lặng kéo trung bình xuống; encoder đặt " + encode.cfg()["audio"]["bitrate"] + ")"
                if p.get("append_endscreen") else ""),
             str(a.get("sample_rate")) == str(p.get("audio_rate", 48000))
             and (p.get("append_endscreen") or float(a.get("bit_rate") or 0) / 1000 >= p.get("audio_min_kbps", 128) - 1)),
    }
    if p.get("max_sec"):
        out[f"{lab}: thời lượng ≤ {p['max_sec']} s"] = (f"{info['duration']:.1f} s", info["duration"] <= p["max_sec"])
    if p.get("max_mb"):
        out[f"{lab}: dung lượng ≤ {p['max_mb']} MB"] = (f"{mb:.1f} MB", mb <= p["max_mb"])
    if p.get("min_kbps"):
        out[f"{lab}: bitrate ≥ {p['min_kbps']} kb/s"] = (f"{kbps:.0f} kb/s", kbps >= p["min_kbps"])
    for k, val in qagate.spec_checks(video, p.get("max_mbps")).items():
        out[f"{lab}: {k}"] = val
    loud = mix.measure(video) or {}
    for k, val in qagate.audio_checks(loud, p.get("lufs", -14), p.get("tp_max", -1.0)).items():
        out[f"{'gói ' + p['label'] if k == 'LRA' else lab}: {k}"] = val      # LRA chỉ để tham khảo (không chặn)
    return out


def _link_or_remux(src, dst, meta, prev_9x16=None):
    """Dùng hard-link giữa các gói 9:16 cùng metadata để tiết kiệm 3× dung lượng ổ cứng; lỗi thì remux như cũ."""
    if prev_9x16 and os.path.exists(prev_9x16):
        try:
            if os.path.exists(dst):
                os.remove(dst)
            os.link(prev_9x16, dst)
            return
        except OSError:
            pass
    _remux(src, dst, meta)


def build(proj, names=None, meta=None, log=print, sb=None):
    """Xuất mọi preset → {preset: {"dir", "video", "cover", "srt", "caption", "checks": {...}, "ok"}}; ghi deliver.json."""
    from . import qareport  # noqa: PLC0415
    from . import storyboard as sbm  # noqa: PLC0415
    from .common import slugify  # noqa: PLC0415
    final = os.path.join(proj, "out", "final.mp4")
    if not os.path.exists(final):
        raise StudioError("Chưa có out/final.mp4 để xuất.")
    if sb is None:
        sb = sbm.load(proj) or {}
    slug = slugify(sb.get("slug") or os.path.basename(os.path.abspath(proj))) or "video"
    fname = f"{slug}.mp4"
    srt = os.path.join(proj, "out", "captions.srt")
    endscreen = os.path.join(proj, "out", "endscreen_16x9.mp4")
    c = cfg()
    res = {}
    first_9x16 = None
    for name in preset_names(names):
        p = c["presets"][name]
        d = os.path.join(proj, "out", "deliver", name)
        os.makedirs(d, exist_ok=True)
        video = os.path.join(d, fname)
        legacy = os.path.join(d, "video.mp4")
        if legacy != video and os.path.exists(legacy):
            os.remove(legacy)
        if p["aspect"] == "9:16":
            _link_or_remux(final, video, meta, prev_9x16=first_9x16)
            if first_9x16 is None and os.path.exists(video):
                first_9x16 = video
        else:
            _pillarbox(final, video, p, endscreen if p.get("append_endscreen") else None, meta)
        cov, cov_note = cover(proj, p, os.path.join(d, "cover.jpg"))
        has_srt = os.path.exists(srt)
        if has_srt and p.get("srt"):
            shutil.copyfile(srt, os.path.join(d, "captions.srt"))
        cap_path = os.path.join(d, "caption.txt")
        with open(cap_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(qareport.render_platform_caption(sb, name))
        checks = verify(video, p)
        checks[f"gói {p['label']}: bìa"] = (cov_note, cov is not None or None)
        checks.update(safe_zone_checks(p))
        rows = qagate.classify(checks)
        res[name] = {"label": p["label"], "dir": os.path.relpath(d, proj), "video": os.path.relpath(video, proj),
                     "cover": os.path.relpath(cov, proj) if cov else None, "srt": has_srt and bool(p.get("srt")),
                     "caption": os.path.relpath(cap_path, proj), "ai_label": p.get("ai_label", ""),
                     "rows": rows, "verdict": qagate.verdict(rows)}
        save_json(os.path.join(d, "deliver.json"), res[name])
        log(f"  · {p['label']}: {qagate.verdict(rows)} · {os.path.getsize(video) / 1e6:.1f} MB")
    save_json(os.path.join(proj, "out", "deliver", "deliver.json"), res)
    return res


def checks_of(res):
    """Gộp dòng kiểm của mọi preset để đưa vào cổng QA."""
    out = {}
    for r in res.values():
        for row in r["rows"]:
            out[row["label"]] = (row["value"], row["ok"])
    return out
