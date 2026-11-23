"""python -m ui.server [--port 8765] [--no-open]  ·  hoặc: python studio.py ui"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if sys.platform == "win32":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass


def main(argv=None):
    ap = argparse.ArgumentParser(prog="studio.py ui", description="Giao diện web cục bộ cho Studio")
    ap.add_argument("--port", type=int, default=int(os.environ.get("STUDIO_UI_PORT", 8765)))
    ap.add_argument("--no-open", action="store_true", help="không tự mở trình duyệt")
    a = ap.parse_args(argv)
    os.chdir(ROOT)
    from ui.server.app import serve  # noqa: PLC0415
    serve(a.port, open_browser=not a.no_open)
    return 0


if __name__ == "__main__":
    sys.exit(main())
