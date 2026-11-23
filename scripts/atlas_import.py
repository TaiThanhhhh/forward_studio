"""3D Style Atlas → preset của tool (một lệnh).

  python scripts/atlas_import.py                      # sinh lại styles/atlas-*.json + .md, INDEX.md, bảng phân tích
  python scripts/atlas_import.py --from atlas-capture.json   # trước đó: tách file chụp (scripts/atlas_capture.js) → raw/
  python scripts/atlas_import.py --check              # chỉ kiểm (không ghi), exit 1 nếu có lỗi

Bảng phân tích + bản chuyển nằm ở config/atlas.json; bản gốc ở vendor/3d-style-atlas/raw/ (cục bộ, gitignore).
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from vidlib import atlas, styles, textstyle  # noqa: E402

DOC = os.path.join(ROOT, "docs", "3D_ATLAS_ANALYSIS.md")
BEGIN, END = "<!-- atlas-table:begin -->", "<!-- atlas-table:end -->"


def split_capture(path):
    from atlas_receiver import save  # noqa: PLC0415
    with open(path, encoding="utf-8") as fh:
        recs = json.load(fh)
    n = 0
    for r in recs:
        if r.get("number") and r.get("name"):
            save(r)
            n += 1
    return n


def write_doc_table():
    if not os.path.exists(DOC):
        return False
    with open(DOC, encoding="utf-8") as fh:
        s = fh.read()
    if BEGIN not in s:
        return False
    s = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), BEGIN + "\n" + atlas.analysis_table() + "\n" + END, s, flags=re.S)
    with open(DOC, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s)
    return True


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.src:
        print(f"[atlas] tách {split_capture(a.src)} style từ {a.src} → {atlas.RAW_DIR}")
    res = atlas.build(write=not a.check)
    bad = [(sid, errs) for sid, _, errs in res if errs]
    for sid, errs in bad:
        print(f"[atlas] LỖI {sid}: {'; '.join(errs)}")
    if a.check:
        return 1 if bad else 0
    textstyle.load_style.cache_clear()
    cards = styles.write_cards([sid for sid, _, errs in res if not errs])
    with open(os.path.join(ROOT, "vendor", "3d-style-atlas", "INDEX.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(atlas.index_md())
    write_doc_table()
    t1 = atlas.ids(tiers=[1], include_off_brand=False)
    off = [atlas.style_id(e) for e in atlas.entries() if e["brand_fit"] == "off-brand"]
    print(f"[atlas] {len(res) - len(bad)}/{len(res)} preset · {len(cards)} thẻ .md · tier 1: {len(t1)} · "
          f"off-brand: {len(off)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
