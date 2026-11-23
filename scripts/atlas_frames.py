"""Style frame 9:16 do tool tự render cho preset 3D Style Atlas + contact sheet.

  python scripts/atlas_frames.py [--ids atlas-neon-sign,…] [--force]
→ qa/styles/<id>.jpg (engine three.js thật, đạo cụ kênh) · qa/atlas-style-compare.png (tier 1) · qa/atlas-all.png (37).
Không dùng ảnh chụp từ Futurepedia làm thumbnail.
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from vidlib import atlas, enginebench, textstyle  # noqa: E402


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    ids = a.ids.split(",") if a.ids else [atlas.style_id(e) for e in atlas.entries()]
    for sid in ids:
        out = os.path.join(ROOT, "qa", "styles", f"{sid}.jpg")
        if os.path.exists(out) and not a.force:
            continue
        t = time.time()
        enginebench.style_frame(sid, out)
        print(f"[frame] {sid} {time.time() - t:.1f}s", flush=True)

    def lab(n):
        st = textstyle.load_style(n)
        return f"#{st['atlas']['number']:02d} t{st['tier']} {st['brand_fit']} · {st['category']}"

    t1 = atlas.ids(tiers=[1], include_off_brand=False)
    print(enginebench.contact_sheet(t1, os.path.join(ROOT, "qa", "atlas-style-compare.png"), cols=7, label=lab))
    print(enginebench.contact_sheet([atlas.style_id(e) for e in atlas.entries()], os.path.join(ROOT, "qa", "atlas-all.png"),
                                    cols=8, label=lab))
    return 0


if __name__ == "__main__":
    sys.exit(main())
