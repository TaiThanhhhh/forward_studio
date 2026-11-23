"""Visual regression: python scripts/visual_regression.py [--update] [--cases=a,b] → qa/visreg/report.md.

Chi tiết: vidlib/visreg.py."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from vidlib import visreg  # noqa: E402

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cases = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--cases=")), None)
    rows = visreg.run(update="--update" in sys.argv, cases=cases)
    sys.exit(0 if all(r["ok"] for r in rows) else 1)
