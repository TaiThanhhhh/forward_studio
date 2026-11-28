"""Kiểm bằng hình chuyển cảnh `zoom_through` (vòng 21) — hai đường dựng:

  python scripts/portal_check.py [style] [--out qa/round21]

1) html → html trong cú máy liền: kiểu bay `portal` (engine vẽ lại vector) — render đuôi shot A + đầu shot B như pipeline
   (mỗi shot render riêng, ô hàng xóm vẽ trong chính shot đó) → ghép thành dải frame; frame cuối A phải trùng frame đầu B.
2) hậu kỳ (mọi cặp engine khác): `vidlib/partzoom.py` trên chính các frame đó, điểm đích đọc từ anchors_end của A.
Ra <out>/portal_<style>.jpg (2 hàng) + in độ lệch điểm ảnh tại điểm cắt (≈ 0 là khớp)."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from engines import adapter  # noqa: E402
from vidlib import partzoom, spine  # noqa: E402
from vidlib.common import font, load_json  # noqa: E402

A = {"id": "C01", "beat": "hook", "code": {"engine": "html", "scene": "scene", "params": {
    "kicker": "YOUR EYE", "title": "A camera made of jelly",
    "actors": [{"id": "hero", "icon": "rig:adult:idle:shock", "x": 0.5, "y": 0.6, "size": 640}],
    "camera": [{"u": 0.0, "x": 0.5, "y": 0.56}, {"u": 1.0, "at": "hero.head", "zoom": 1.5}],
    "labels": [{"text": "retina", "of": "hero.eye", "u": 0.3, "tag": True}]}}}
B = {"id": "C02", "beat": "setup", "transition_in": "zoom_through", "through": "hero.eye",
     "code": {"engine": "html", "scene": "scene", "params": {
    "kicker": "INSIDE THE EYE", "title": "120 million rods",
    "actors": [{"id": "rod", "icon": "cell", "x": 0.35, "y": 0.6, "size": 260, "role": "cold"},
               {"id": "cone", "icon": "cell", "x": 0.68, "y": 0.62, "size": 220, "role": "hot"}],
    "labels": [{"text": "rods", "of": "rod", "u": 0.1}, {"text": "cones", "of": "cone", "u": 0.2}]}}}


def main(argv):
    style = argv[0] if argv and not argv[0].startswith("--") else "cosmic-flat-black"
    out_dir = os.path.join(ROOT, argv[argv.index("--out") + 1]) if "--out" in argv else os.path.join(ROOT, "qa", "round21")
    n = 60
    segs = [{"sid": "C01", "n": n, "start_f": 0}, {"sid": "C02", "n": n, "start_f": n}]
    shots = {"C01": A, "C02": B}

    def entry(sh):
        return {"scene": "scene", "params": dict(sh["code"]["params"])}

    ctx = spine.context(segs, shots, style, "portal-check", lambda sh: True, entry)
    print("kiểu bay:", ctx["C01"]["move_out"], "→ tile", ctx["C01"]["next"]["tile"])
    eng = adapter.get("html")
    frames = {}
    for sh, idx in ((A, 1), (B, 2)):
        work = os.path.join(ROOT, "qa", "round21", "_work", style, "portal_" + sh["id"])
        spec = adapter.ShotSpec(sid=sh["id"], engine="html", scene="scene", params=sh["code"]["params"], frames=n,
                                style=style, work=work, index=[idx, 2], spine=ctx[sh["id"]])
        job = eng.job(spec)
        if sh is A:                                   # điểm đích cho đường hậu kỳ
            jd = load_json(job)
            jd["anchors_out"] = True
            from vidlib.common import save_json  # noqa: PLC0415
            save_json(job, jd)
            meta = eng.meta(job)
            save_json(os.path.join(work, "meta.json"), meta)
            eye = (meta.get("anchors_end") or {}).get("hero.eye")
            print("portal (A):", meta.get("portal"), "· anchors_end hero.eye:", eye)
        fr = list(range(n - 10, n)) if sh is A else list(range(0, 10))
        eng.render(job, os.path.join(work, "frames"), fr, log=lambda m: None, workers=2)
        frames[sh["id"]] = [Image.open(os.path.join(work, "frames", f"f{f:04d}.jpg")).convert("RGB") for f in fr]
    clean = {}
    for sh, idx in ((A, 1), (B, 2)):                  # bản không spine (cắt thường) cho đường hậu kỳ
        work = os.path.join(ROOT, "qa", "round21", "_work", style, "clean_" + sh["id"])
        spec = adapter.ShotSpec(sid=sh["id"], engine="html", scene="scene", params=sh["code"]["params"], frames=n,
                                style=style, work=work, index=[idx, 2])
        job = eng.job(spec)
        fr = list(range(n - 10, n)) if sh is A else list(range(0, 10))
        eng.render(job, os.path.join(work, "frames"), fr, log=lambda m: None, workers=2)
        clean[sh["id"]] = [Image.open(os.path.join(work, "frames", f"f{f:04d}.jpg")).convert("RGB") for f in fr]
    a_last, b_first = np.asarray(frames["C01"][-1], np.float32), np.asarray(frames["C02"][0], np.float32)
    print(f"lệch tại điểm cắt (spine portal): {np.abs(a_last - b_first).mean():.2f} / 255")
    # đường hậu kỳ trên khung A "sạch" (không spine) — dùng điểm đích từ meta
    an = (load_json(os.path.join(ROOT, "qa", "round21", "_work", style, "portal_C01", "meta.json")).get("anchors_end") or {})
    hit = an.get("hero.eye")
    tgt = (hit[0], hit[1], hit[2]) if hit else (540, 960, 60)
    post_a = [partzoom.apply_out(clean["C01"][k], n - 10 + k, n, tgt) for k in range(10)]
    post_b = [partzoom.apply_in(clean["C02"][k], clean["C01"][-1], k, tgt) for k in range(10)]
    rows = [frames["C01"][::2] + frames["C02"][::2], post_a[::2] + post_b[::2]]
    cw, ch = 216, 384
    sheet = Image.new("RGB", (cw * 10, ch * 2), (10, 10, 12))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            cell = im.resize((cw, ch))
            tag = ("spine " if r == 0 else "post ") + ("A" if c < 5 else "B")
            ImageDraw.Draw(cell).text((6, 4), tag, font=font(18, "bold"), fill=(255, 255, 0))
            sheet.paste(cell, (c * cw, r * ch))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"portal_{style}.jpg")
    sheet.save(path, quality=88)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
