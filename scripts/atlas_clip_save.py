"""Lưu một style 3D Style Atlas từ clipboard Windows → vendor/3d-style-atlas/raw/NN-<slug>.json.

Hook trong trang (`scripts/atlas_capture.js`) gói prompt mà nút "Copy prompt" của trang chép ra thành một bản ghi JSON
{"__atlas": 1, number, name, category, tag, description, shown_here, good_for, prompt_full, …} rồi mới ghi vào
clipboard. Lệnh này đọc clipboard (CF_UNICODETEXT, không qua mã hoá của PowerShell), kiểm tra, ghi file.

  python scripts/atlas_clip_save.py [--expect 7]
In một dòng tóm tắt (không in nội dung prompt).
"""
import argparse
import ctypes
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from atlas_receiver import save  # noqa: E402

CF_UNICODETEXT = 13


def read_clipboard():
    u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
    u32.GetClipboardData.restype = ctypes.c_void_p
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [ctypes.c_void_p]
    k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    if not u32.OpenClipboard(None):
        raise RuntimeError("không mở được clipboard")
    try:
        h = u32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return ""
        p = k32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p)
        finally:
            k32.GlobalUnlock(h)
    finally:
        u32.CloseClipboard()


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect", type=int)
    ap.add_argument("--meta", help="JSON metadata của style (khi clipboard chỉ có prompt thô, không có bản ghi __atlas)")
    a = ap.parse_args(argv)
    txt = read_clipboard()
    if a.meta:
        with open(a.meta, encoding="utf-8") as fh:
            rec = json.load(fh)
        if f'"{rec["name"]}"' not in txt[:400]:
            print(f"LỖI: prompt trong clipboard không phải của '{rec['name']}'")
            return 3
        rec.update({"__atlas": 1, "prompt_full": txt})
        txt = json.dumps(rec, ensure_ascii=False)
    try:
        rec = json.loads(txt)
    except ValueError:
        print(f"LỖI: clipboard không phải bản ghi atlas ({len(txt)} ký tự)")
        return 2
    if isinstance(rec, dict) and rec.get("__atlas_list") == 1:       # cả danh sách một lần (4–5 MB)
        n = 0
        for r in rec.get("items") or []:
            if r.get("number") and r.get("name") and r.get("prompt_full"):
                save(r)
                n += 1
        print(f"OK danh sách: {n}/{len(rec.get('items') or [])} style · "
              f"{sum(len(r.get('prompt_full') or '') for r in rec.get('items') or [])} ký tự prompt")
        return 0 if n == len(rec.get("items") or []) else 3
    if not isinstance(rec, dict) or rec.get("__atlas") != 1:
        print("LỖI: thiếu dấu __atlas")
        return 2
    if a.expect and int(rec.get("number") or 0) != a.expect:
        print(f"LỖI: clipboard là #{rec.get('number')} nhưng chờ #{a.expect}")
        return 3
    p, out = save(rec)
    print(f"OK #{out['number']:02d} {out['name']} · {out['category']} · {out['tag']} · prompt {out['prompt_chars']} ký tự"
          f"{' · INCOMPLETE' if out['incomplete'] else ''} → {os.path.basename(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
