"""Bảng soát VẬT LÝ của cảnh `stage` (engine three.js + Rapier): mỗi thí nghiệm mẫu dựng HAI lần trên cùng style —
keyframe tay (cách cũ) và `body` vật lý (engines/three/physics.js) — rồi ghép cạnh nhau để so.

  python scripts/physics_sheet.py [--style toon3d-lab] [--scenes drop,topple] [--sec 4]
→ qa/physics/<cảnh>-keyframe.mp4 · <cảnh>-physics.mp4 (1080×1920, SFX đặt theo cue của cảnh)
  · compare.mp4 (hai bản cạnh nhau, tiếng của bản vật lý) · sheet.jpg (6 thời điểm × mỗi bản) · report.md
Dữ liệu thí nghiệm nằm ngay dưới đây (giống storyboard thật: props + keys + body), không có mã riêng cho từng cảnh.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from engines import adapter  # noqa: E402
from vidlib import sfx as sfxlib  # noqa: E402
from vidlib.common import db2amp, ffbin  # noqa: E402
from vidlib.fakes import write_wav  # noqa: E402

OUT = os.path.join(ROOT, "qa", "physics")
WORK = os.path.join(OUT, "_work")
FONT = os.path.join(ROOT, "assets", "fonts", "Inter-Bold.otf")
SR = 48000
SHEET_U = (0.1, 0.3, 0.42, 0.5, 0.62, 0.9)


def scene_drop():
    """Thả cùng lúc bi bowling (thép), hộp gỗ nghiêng, lông vũ."""
    rel = 0.15
    ball = {"id": "ball", "type": "bowling", "r": 0.11, "at": [-0.5, 1.55, 0]}
    box = {"id": "box", "type": "box", "size": [0.24, 0.24, 0.24], "at": [0, 1.45, 0], "rot": [18, 0, 32]}
    fea = {"id": "feather", "type": "feather", "at": [0.5, 1.5, 0], "rot": [0, 0, 60]}
    physics = {"physics": {"fx": "smoke"}, "props": [
        {**ball, "body": {"material": "metal", "release": rel}},
        {**box, "body": {"material": "wood", "release": rel}},
        {**fea, "body": {"material": "feather", "release": rel}},
    ]}
    keyframe = {"props": [
        {**ball, "keys": [{"u": rel, "at": ball["at"]}, {"u": 0.30, "at": [-0.5, 0.11, 0], "ease": "easeIn"},
                          {"u": 0.36, "at": [-0.5, 0.2, 0], "ease": "easeOut"},
                          {"u": 0.42, "at": [-0.5, 0.11, 0], "ease": "easeIn"}]},
        {**box, "keys": [{"u": rel, "at": box["at"], "rot": box["rot"]},
                         {"u": 0.30, "at": [0, 0, 0], "rot": [0, 0, 0], "ease": "easeIn"}]},
        {**fea, "keys": [{"u": rel, "at": fea["at"], "rot": fea["rot"]},
                         {"u": 0.95, "at": [0.5, 0.02, 0], "rot": [0, 0, 90], "ease": "linear"}]},
    ], "kicks": [{"u": 0.30, "a": 0.07}], "cues": [{"u": 0.30, "sfx": "thud"}, {"u": 0.42, "sfx": "thud"}]}
    return keyframe, physics


def scene_topple():
    """Bi thép lăn vào tháp 10 hộp gỗ; cú chạm canh đúng u = 0.42 (hit_u) + slow-motion quanh cú chạm."""
    s, hit = 0.2, 0.42
    tower = [{"id": f"k{r}{c}", "type": "box", "size": [s, s, s], "at": [0.25 + (c - 0.5) * (s + 0.004), r * s, 0]}
             for r in range(5) for c in range(2)]
    ball = {"id": "ball", "type": "bowling", "r": 0.11, "at": [-2.4, 0.11, 0], "frame": False}
    physics = {"physics": {"slowmo": [{"u": [0.40, 0.66], "rate": 0.3}], "fx": "burst"}, "props": [
        *[{**b, "body": {"material": "wood"}} for b in tower],
        {**ball, "body": {"material": "metal", "v": [5.5, 0, 0], "hit_u": hit}},
    ]}
    keys_tower = []
    for b in tower:
        r = int(b["id"][1])
        x, y, z = b["at"]
        keys_tower.append({**b, "keys": [{"u": hit, "at": b["at"], "rot": [0, 0, 0]},
                                         {"u": 0.75, "at": [x + 0.25 + 0.12 * r, 0, z + (0.1 if r % 2 else -0.1)],
                                          "rot": [0, 0, -90 if r > 1 else -20], "ease": "easeOut"}]})
    ball_keys = [{"u": 0, "at": ball["at"]},
                 {"u": hit, "at": [0.02, 0.11, 0], "rot": [0, 0, -700], "ease": "linear"},
                 {"u": 0.6, "at": [0.25, 0.11, 0], "rot": [0, 0, -820], "ease": "easeOut"}]
    keyframe = {"props": [*keys_tower, {**ball, "keys": ball_keys}],
                "kicks": [{"u": hit, "a": 0.07}], "cues": [{"u": hit, "sfx": "impact"}, {"u": 0.75, "sfx": "thud"}]}
    return keyframe, physics


SCENES = {"drop": scene_drop, "topple": scene_topple}


def render(name, version, params, style, n):
    work = os.path.join(WORK, f"{name}-{version}")
    spec = adapter.ShotSpec(sid=f"{name}-{version}", engine="three", scene="stage", params=params, frames=n, fps=30,
                            style=style, work=work)
    t0 = time.time()
    clip = adapter.render_clip(spec, mp4=True, log=lambda *a: None)
    sec = time.time() - t0
    meta = adapter.get("three").meta(os.path.join(work, "job.json"))
    return clip, meta, sec


def sfx_track(cues, n, fps=30):
    """Cue của cảnh → WAV stereo 48 kHz đúng độ dài shot (mức theo channel.json → audio.sfx_db)."""
    out = np.zeros((int(np.ceil(n / fps * SR)) + SR // 10, 2), np.float32)
    for c in cues:
        a = sfxlib.load(c["name"], SR) * db2amp(sfxlib.level_db(c["name"]))
        i = int(round(c["f"] / fps * SR))
        j = min(len(out), i + len(a))
        if 0 <= i < len(out):
            out[i:j] += a[: j - i]
    return np.clip(out, -1, 1)


def mux(video, wav, out):
    subprocess.run([ffbin("ffmpeg"), "-y", "-v", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)


def label(img, text, sub=""):
    d = ImageDraw.Draw(img)
    f1, f2 = ImageFont.truetype(FONT, 34), ImageFont.truetype(FONT, 22)
    d.rectangle([0, 0, img.width, 74 if sub else 50], fill=(0, 0, 0))
    d.text((16, 8), text, font=f1, fill=(255, 255, 255))
    if sub:
        d.text((16, 46), sub, font=f2, fill=(170, 170, 170))
    return img


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python scripts/physics_sheet.py")
    ap.add_argument("--style", default="toon3d-lab")
    ap.add_argument("--scenes", default=",".join(SCENES))
    ap.add_argument("--sec", type=float, default=4.0)
    a = ap.parse_args(argv)
    n = int(round(a.sec * 30))
    os.makedirs(WORK, exist_ok=True)
    rows, report, cmp_frames, cmp_audio = [], [], [], []
    for name in [s.strip() for s in a.scenes.split(",") if s.strip()]:
        keyframe, physics = SCENES[name]()
        res = {}
        for version, params in (("keyframe", keyframe), ("physics", physics)):
            errs = adapter.validate_three("stage", params)
            if errs:
                raise SystemExit("\n".join(errs))
            clip, meta, sec = render(name, version, params, a.style, n)
            wav = os.path.join(WORK, f"{name}-{version}.wav")
            write_wav(wav, sfx_track(meta.get("cues") or [], n), SR)
            mux(clip.mp4, wav, os.path.join(OUT, f"{name}-{version}.mp4"))
            res[version] = (clip, meta, sec, wav)
            print(f"  ✓ {name}/{version}: {n} frame trong {sec:.1f} s · {len(meta.get('cues') or [])} cue")
        # bảng soát: hàng keyframe + hàng vật lý, 6 thời điểm
        for version in ("keyframe", "physics"):
            clip = res[version][0]
            tiles = []
            for u in SHEET_U:
                f = int(round(u * (n - 1)))
                im = Image.open(os.path.join(clip.frames_dir, f"f{f:04d}.jpg")).convert("RGB").resize((270, 480))
                tiles.append(label(im, f"u {u:.2f}"))
            row = Image.new("RGB", (270 * len(tiles), 480 + 44), (12, 12, 12))
            for i, t in enumerate(tiles):
                row.paste(t, (i * 270, 44))
            ImageDraw.Draw(row).text((12, 6), f"{name} · {version.upper()}", font=ImageFont.truetype(FONT, 28),
                                     fill=(255, 255, 255) if version == "physics" else (150, 150, 150))
            rows.append(row)
        # video so sánh: trái keyframe, phải vật lý (tiếng của bản vật lý)
        for f in range(n):
            pair = Image.new("RGB", (1080, 960), (0, 0, 0))
            for i, version in enumerate(("keyframe", "physics")):
                im = Image.open(os.path.join(res[version][0].frames_dir, f"f{f:04d}.jpg")).convert("RGB").resize((540, 960))
                pair.paste(label(im, "KEYFRAME (old)" if i == 0 else "PHYSICS (Rapier)", name), (i * 540, 0))
            cmp_frames.append(pair)
        cmp_audio.append(res["physics"][3])
        m = res["physics"][1].get("physics") or {}
        report.append(f"## {name}\n\n"
                      f"| bản | thời gian dựng | cue |\n|---|---|---|\n"
                      + "".join(f"| {v} | {res[v][2]:.1f} s | "
                                + ", ".join(f"{c['name']}@{c['f']}" for c in (res[v][1].get('cues') or [])) + " |\n"
                                for v in ("keyframe", "physics"))
                      + "\nVật lý: " + ", ".join(f"{b['id']} ({b['material']}, {b['shape']}, {b['mass']} kg)"
                                                  for b in m.get("bodies", []))
                      + "\n\nVa chạm (frame): " + (", ".join(f"{h['id']}@{h['f']} ({h['speed']} m/s)"
                                                             for h in m.get("impacts", [])) or "—")
                      + "\n\nCanh hit_u: " + (", ".join(f"{x['id']}: muốn frame {x['want']}, chạm frame {x['got']} "
                                                       f"(thả ở frame {x['release']})" for x in m.get("aligned", [])) or "—")
                      + ("\n\n⚠ " + "; ".join(m["warn"]) if m.get("warn") else "") + "\n")
    sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), (0, 0, 0))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(os.path.join(OUT, "sheet.jpg"), quality=90)
    cdir = os.path.join(WORK, "compare")
    shutil.rmtree(cdir, ignore_errors=True)
    os.makedirs(cdir)
    for i, im in enumerate(cmp_frames):
        im.save(os.path.join(cdir, f"f{i:04d}.jpg"), quality=92)
    video = adapter.encode(cdir, len(cmp_frames), 30, os.path.join(WORK, "compare.mp4"))
    wavs = [sfxlib.decode(w, SR) for w in cmp_audio]
    audio = np.concatenate([w[: n * SR // 30] if len(w) >= n * SR // 30 else np.pad(w, ((0, n * SR // 30 - len(w)), (0, 0)))
                            for w in wavs])
    cwav = os.path.join(WORK, "compare.wav")
    write_wav(cwav, audio, SR)
    mux(video, cwav, os.path.join(OUT, "compare.mp4"))
    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# Vật lý cảnh stage — keyframe tay vs Rapier\n\nStyle `{a.style}` · {n} frame/bản · "
                 "dựng bằng `python scripts/physics_sheet.py`\n\n" + "\n".join(report))
    print(f"✔ {os.path.relpath(OUT, ROOT)}: compare.mp4 · sheet.jpg · report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
