"""Test suite. Windows: in tiếng Việt/ký hiệu ra console UTF-8 (như studio.py)."""
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
