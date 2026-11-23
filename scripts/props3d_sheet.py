"""Bảng xem đạo cụ 3D của cảnh `stage` (engine three.js) theo từng style/look 3D — soát chất lượng khi thêm đạo cụ
hoặc thêm look 3D (styles/<id>.json → world.look3d) — và bảng soát vòng 10 (look thời 90 + nhân vật con vật 3D).

  python scripts/props3d_sheet.py [style1,style2,…] [--props a,b,c]
→ qa/props3d/<style>.jpg (mỗi trang 12 đạo cụ, ghép ngang) + qa/props3d/_all.jpg (trang 1 của mọi style, cạnh nhau).
Mặc định: mọi style có world.look3d + toon3d-lab.

  python scripts/props3d_sheet.py --retro       cùng cảnh ở lowpoly · retro90 · psx → qa/retro90/compare.jpg (+ từng look)
  python scripts/props3d_sheet.py --meadow      cảnh "dachshund hít hoa trên meadow" (retro90): frame mẫu, % nền đen,
                                                tất định 2 worker (đổi thứ tự frame → so md5), s/frame, clip mp4
                                                → qa/retro90/meadow_*.jpg · meadow.mp4 · report.json/.md
  python scripts/props3d_sheet.py --creatures [loài,…] [--looks retro90,toon]
                                                mọi loài × 3 hành động (walk · sniff · sit) × mỗi look, 1080×1920
                                                → qa/creatures/<look>/<loài>.jpg + qa/creatures/<look>_sheet.jpg
  python scripts/props3d_sheet.py --faces [loài,…]   9 biểu cảm/loài → qa/creatures/faces_<loài>.jpg
"""

import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from engines import adapter  # noqa: E402
from vidlib import coderender, textstyle  # noqa: E402

SKIP = {"character", "glow", "parts", "fx", "track", "sign", "text", "box", "sphere", "cylinder", "cone", "torus",
        "human3d", "scientist3d", "runner", "lifter", "terminal", "code", "frame", "cpu", "fire", "earth", "bloodcell",
        "grass"}
PER_PAGE = 12
COLS = 3
# look → (style, ghi đè world.look3d) — psx dùng style retro90 với look3d = "psx"
LOOKS = {"lowpoly": ("lowpoly3d-black", None), "retro90": ("retro90-lowpoly-black", None),
         "psx": ("retro90-lowpoly-black", "psx"), "toon": ("toon3d-lab", None), "clay": ("clay3d-black", None)}
FONT = os.path.join(ROOT, "assets", "fonts", "Inter-Bold.otf")
ACTIONS = (("walk", "neutral"), ("sniff", None), ("sit", "happy"))


def prop_types():
    """Kiểu đạo cụ khai trong `const mk = {…}` của engines/three/scenes/stage.js (một nguồn sự thật)."""
    with open(os.path.join(ROOT, "engines", "three", "scenes", "stage.js"), encoding="utf-8") as fh:
        src = fh.read()
    body = src.split("const mk = {", 1)[1].split("\n  };", 1)[0]
    names = re.findall(r"^\s{4}(\w+):", body, re.M)
    return [n for n in dict.fromkeys(names) if n not in SKIP]


def styles_3d():
    out = [s for s in textstyle.list_styles() if (textstyle.load_style(s).get("world") or {}).get("look3d")]
    return (["toon3d-lab"] if "toon3d-lab" not in out else []) + out


def page(style, types, k):
    props = []
    for i, t in enumerate(types):
        col, row = i % COLS, i // COLS
        p = {"id": f"p{i}", "type": t, "at": [(col - 1) * 0.95, (3 - row) * 0.95, 0]}
        if t in ("mannequin", "runner3d", "lifter3d"):
            p["scale"] = 0.5
        if t in ("battery", "hourglass", "syringe", "stopwatch", "clock", "pendulum"):
            p["value"] = 0.6
        props.append(p)
    work = os.path.join(ROOT, "qa", "props3d", "_work", style, f"p{k}")
    spec = adapter.ShotSpec(sid=f"PROPS{k}", engine="three", scene="stage",
                            params={"props": props, "frame": {"orbit": 0, "push": 0, "headroom": 0.06, "margin": 1.08}},
                            frames=24, fps=30, width=1080, height=1920, style=style, work=work)
    job = adapter.get("three").job(spec)
    fdir = os.path.join(work, "frames")
    coderender.render(job, fdir, frames=[12], workers=1, log=lambda *_: None)
    im = Image.open(os.path.join(fdir, "f0012.jpg")).convert("RGB")
    return im


def sheet(style, types):
    pages = [types[i:i + PER_PAGE] for i in range(0, len(types), PER_PAGE)]
    ims = [page(style, chunk, k) for k, chunk in enumerate(pages)]
    w, h = 540, 960
    out = Image.new("RGB", (w * len(ims), h))
    for i, im in enumerate(ims):
        out.paste(im.resize((w, h)), (i * w, 0))
    d = os.path.join(ROOT, "qa", "props3d")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{style}.jpg")
    out.save(path, quality=86)
    return path, ims[0]


# ---------------------------------------------------------------------------------------------------------------------
# vòng 10 — look thời 90 + nhân vật 3D
# ---------------------------------------------------------------------------------------------------------------------
def render_job(tag, look, params, frames, n=60, workers=1, base="retro90"):
    """Một job cảnh `stage` theo look (LOOKS) → (danh sách ảnh PIL, thống kê render, thư mục frame)."""
    style, override = LOOKS[look]
    work = os.path.join(ROOT, "qa", base, "_work", tag)
    spec = adapter.ShotSpec(sid=tag, engine="three", scene="stage", params=params, frames=n, fps=30, width=1080,
                            height=1920, style=style, work=work)
    job = adapter.get("three").job(spec)
    if override:
        from vidlib.common import save_json  # noqa: PLC0415
        j = adapter.load_job(job)
        j["world"] = {**j["world"], "look3d": override}
        save_json(job, j)
    fdir = os.path.join(work, "frames")
    st = coderender.render(job, fdir, frames=frames, workers=workers, log=lambda *_: None)
    return [Image.open(os.path.join(fdir, f"f{f:04d}.jpg")).convert("RGB") for f in frames], st, fdir


def label(im, text, size=34):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, size)
    d.rectangle((0, 0, im.width, size + 16), fill=(0, 0, 0))
    d.text((12, 6), text, fill=(255, 244, 220), font=f)
    return im


def black_frac(im):
    import numpy as np  # noqa: PLC0415
    a = (lambda x: x.astype("float32").mean(axis=2))(np.asarray(im))
    return round(float((a < 26).mean()), 3)


def meadow_scene(seed=4):
    """Cảnh mẫu theo ảnh tham chiếu #10: chó dachshund cam hít bông hoa vàng trên đảo cỏ nổi, rồi quay ra vẫy đuôi."""
    return {"set": "meadow", "set_opts": {"seed": seed},
            "props": [{"id": "dog", "type": "dachshund", "at": [-0.13, 0, -0.08], "rot": [0, 22, 0], "gait": "sniff",
                       "expr": "neutral", "look": [0.15, 0.14, 0.2],
                       "keys": [{"u": 0.62, "gait": "wag", "expr": "happy", "look": "camera"}]},
                      {"id": "fl", "type": "flower", "at": [0.15, 0, 0.2], "h": 0.15}],
            "frame": {"azim": 14, "margin": 1.06}}


def do_retro():
    out = os.path.join(ROOT, "qa", "retro90")
    os.makedirs(out, exist_ok=True)
    panels, info = [], {}
    for look in ("lowpoly", "retro90", "psx"):
        ims, st, _ = render_job(f"cmp_{look}", look, meadow_scene(), [24], n=90)
        ims[0].save(os.path.join(out, f"look_{look}.jpg"), quality=90)
        panels.append(label(ims[0].resize((540, 960)), look))
        info[look] = {"black": black_frac(ims[0]), "sec_per_frame": st.get("sec_per_frame")}
        print(f"  {look:<8} nền đen {info[look]['black']:.0%}")
    sheet_im = Image.new("RGB", (540 * len(panels), 960))
    for i, p in enumerate(panels):
        sheet_im.paste(p, (540 * i, 0))
    sheet_im.save(os.path.join(out, "compare.jpg"), quality=88)
    return info


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def do_meadow(video=True):
    out = os.path.join(ROOT, "qa", "retro90")
    os.makedirs(out, exist_ok=True)
    params, n = meadow_scene(), 90
    need = float(textstyle.load_style("retro90-lowpoly-black").get("black_min", 0.5))
    rep = {"scene": params, "frames": n, "black_min": need}
    samples = [0, 30, 50, 75]
    ims, _, _ = render_job("meadow_samples", "retro90", params, samples, n=n)
    rep["black"] = {}
    for f, im in zip(samples, ims):
        im.save(os.path.join(out, f"meadow_f{f:02d}.jpg"), quality=92)
        rep["black"][f] = black_frac(im)
    # tất định: cùng job, 2 worker, thứ tự frame đảo ngược → mỗi frame do worker khác dựng → phải giống từng byte
    _, _, da = render_job("det_a", "retro90", params, [12, 61], n=n, workers=2)
    _, _, db = render_job("det_b", "retro90", params, [61, 12], n=n, workers=2)
    rep["deterministic"] = {f: md5(os.path.join(da, f"f{f:04d}.jpg")) == md5(os.path.join(db, f"f{f:04d}.jpg"))
                            for f in (12, 61)}
    # s/frame: cả clip, 2 worker
    t0 = time.time()
    _, st, fdir = render_job("meadow_full", "retro90", params, list(range(n)), n=n, workers=2)
    rep["render"] = {**st, "wall_sec": round(time.time() - t0, 1)}
    if video:
        rep["mp4"] = os.path.relpath(adapter.encode(fdir, n, 30, os.path.join(out, "meadow.mp4")), ROOT)
    full = [Image.open(os.path.join(fdir, f"f{f:04d}.jpg")).convert("RGB") for f in range(0, n, 6)]
    rep["black_clip_mean"] = round(sum(black_frac(im) for im in full) / len(full), 3)
    rep["black_ok"] = rep["black_clip_mean"] >= need
    from vidlib.common import save_json  # noqa: PLC0415
    save_json(os.path.join(out, "report.json"), rep)
    print(json.dumps({k: rep[k] for k in ("black", "black_clip_mean", "black_ok", "deterministic")}, ensure_ascii=False))
    print(f"  s/frame (2 worker): {st.get('sec_per_frame')} · s/frame/worker: {st.get('sec_per_frame_per_worker')}")
    return rep


def species_list():
    return list(adapter.creature_vocab()["species"])


def do_creatures(only=None, looks=("retro90", "toon")):
    res = {}
    for look in looks:
        d = os.path.join(ROOT, "qa", "creatures", look)
        os.makedirs(d, exist_ok=True)
        thumbs = []
        for sp in only or species_list():
            keys = [{"u": 0.34, "gait": ACTIONS[1][0], "expr": "sniff"},
                    {"u": 0.67, "gait": ACTIONS[2][0], "expr": ACTIONS[2][1]}]
            params = {"props": [{"id": "c", "type": "creature", "species": sp, "rot": [0, 35, 0], "gait": ACTIONS[0][0],
                                 "expr": ACTIONS[0][1], "keys": keys}],
                      "frame": {"azim": 8, "elev": 12, "headroom": 0.12, "margin": 1.25, "orbit": 0, "push": 0}}
            t0 = time.time()
            ims, st, _ = render_job(f"cr_{look}_{sp}", look, params, [15, 36, 57], n=60, base="creatures")
            strip = Image.new("RGB", (1080, 1920))
            for i, im in enumerate(ims):              # 3 hành động xếp dọc, mỗi ô 1080×640 (cắt giữa khung)
                strip.paste(im.crop((0, 380, 1080, 1020)), (0, 640 * i))
                label(strip.crop((0, 640 * i, 1080, 640 * i + 50)), "")
            dr = ImageDraw.Draw(strip)
            f = ImageFont.truetype(FONT, 40)
            for i, (g, e) in enumerate(ACTIONS):
                dr.text((20, 640 * i + 14), f"{sp} · {g} · {e or 'sniff'}", fill=(255, 244, 220), font=f)
            strip.save(os.path.join(d, f"{sp}.jpg"), quality=86)
            thumbs.append(strip.resize((270, 480)))
            res[f"{look}:{sp}"] = round(time.time() - t0, 1)
            print(f"  {look:<8} {sp:<10} {res[f'{look}:{sp}']} s")
        cols = 6
        rows = (len(thumbs) + cols - 1) // cols
        sh = Image.new("RGB", (270 * cols, 480 * rows))
        for i, t in enumerate(thumbs):
            sh.paste(t, (270 * (i % cols), 480 * (i // cols)))
        sh.save(os.path.join(ROOT, "qa", "creatures", f"{look}_sheet.jpg"), quality=86)
    return res


def do_faces(only=None, look="retro90"):
    exprs = list(adapter.creature_vocab()["exprs"])
    d = os.path.join(ROOT, "qa", "creatures")
    os.makedirs(d, exist_ok=True)
    for sp in only or ["dachshund", "dog", "cat", "kid", "frog", "pig"]:
        n = 9 * 10
        keys = [{"u": i * 10 / (n - 1), "expr": e} for i, e in enumerate(exprs)]
        params = {"props": [{"id": "c", "type": "creature", "species": sp, "gait": "idle", "expr": exprs[0], "keys": keys,
                             "look": "camera"}],
                  "frame": {"elev": 6, "headroom": 0.05, "margin": 1.1, "orbit": 0, "push": 0}}
        frames = [i * 10 + 5 for i in range(len(exprs))]
        ims, _, _ = render_job(f"face_{look}_{sp}", look, params, frames, n=n, base="creatures")
        grid = Image.new("RGB", (1080, 1920))
        f = ImageFont.truetype(FONT, 30)
        for i, (im, e) in enumerate(zip(ims, exprs)):
            t = im.resize((360, 640))
            ImageDraw.Draw(t).text((10, 10), e, fill=(255, 244, 220), font=f)
            grid.paste(t, (360 * (i % 3), 640 * (i // 3)))
        grid.save(os.path.join(d, f"faces_{sp}.jpg"), quality=88)
        print(f"  faces {sp}")


def main(argv):
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    pos = [a for a in argv if not a.startswith("--")]
    if "--retro" in argv:
        print(json.dumps(do_retro(), ensure_ascii=False))
        return 0
    if "--meadow" in argv:
        do_meadow(video="--no-video" not in argv)
        return 0
    if "--creatures" in argv:
        looks = argv[argv.index("--looks") + 1].split(",") if "--looks" in argv else ("retro90", "toon")
        only = [p for p in pos if p not in looks]
        do_creatures(only[0].split(",") if only else None, looks)
        return 0
    if "--faces" in argv:
        do_faces(pos[0].split(",") if pos else None)
        return 0
    styles = pos[0].split(",") if pos else styles_3d()
    types = prop_types()
    if "--props" in argv:
        types = argv[argv.index("--props") + 1].split(",")
    firsts = []
    for st in styles:
        path, first = sheet(st, types)
        firsts.append(first)
        print(f"  {st:<22} → {os.path.relpath(path, ROOT)}")
    if len(firsts) > 1:
        w, h = 270, 480
        allim = Image.new("RGB", (w * len(firsts), h))
        for i, im in enumerate(firsts):
            allim.paste(im.resize((w, h)), (i * w, 0))
        allim.save(os.path.join(ROOT, "qa", "props3d", "_all.jpg"), quality=86)
    print(json.dumps({"styles": len(styles), "props": len(types)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
