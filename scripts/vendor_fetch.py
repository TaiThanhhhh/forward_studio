"""Dựng lại các repo tham khảo trong vendor/ đúng commit đã ghim ở vendor/SOURCES.json (vòng 7).

  python scripts/vendor_fetch.py [tên-repo …]        (không tên = tất cả)

- clone shallow đúng SHA, GIT_LFS_SKIP_SMUDGE=1 (không kéo file LFS nặng);
- sparse-checkout LOẠI các thư mục tự kích hoạt agent (SOURCES.json → stripped: .claude/, .claude-plugin/, .agents/…)
  để không skill bên ngoài nào tranh quyền với pipeline /video;
- không chạy script nào của repo nguồn (không npm install, không setup.sh).
Các thư mục này chỉ để tham khảo/đối chiếu và không nằm trong git của tool (.gitignore).
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "vendor")


def git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True, env={**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"})


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_files(name, grp):
    for item in grp.get("items") or []:
        dst = os.path.join(ROOT, item["path"])
        if os.path.isfile(dst) and sha256_file(dst) == item["sha256"]:
            print(f"  = {item['path']} (sha256 khớp)")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with urllib.request.urlopen(item["url"], timeout=60) as r:
            data = r.read()
        got = hashlib.sha256(data).hexdigest()
        if got != item["sha256"]:
            raise RuntimeError(f"{item['path']}: sha256 {got} != {item['sha256']}")
        with open(dst, "wb") as fh:
            fh.write(data)
        print(f"  ✓ {item['path']} ({name})")


def fetch(name, src, stripped):
    dst = os.path.join(VENDOR, name)
    if os.path.isdir(os.path.join(dst, ".git")):
        head = subprocess.run(["git", "-C", dst, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        if head == src["sha"]:
            print(f"  = {name} đã ở {head[:12]}")
            return
    os.makedirs(dst, exist_ok=True)
    if not os.path.isdir(os.path.join(dst, ".git")):
        git("init", "-q", cwd=dst)
        git("remote", "add", "origin", src["url"], cwd=dst)
    git("sparse-checkout", "init", "--no-cone", cwd=dst)
    with open(os.path.join(dst, ".git", "info", "sparse-checkout"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("/*\n" + "".join(f"!{d}\n" for d in stripped))  # không neo "/": loại ở mọi độ sâu
    git("fetch", "-q", "--depth", "1", "origin", src["sha"], cwd=dst)
    git("checkout", "-q", "FETCH_HEAD", cwd=dst)
    print(f"  ✓ {name} @ {src['sha'][:12]} ({src['license']})")


def main(argv):
    with open(os.path.join(VENDOR, "SOURCES.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    for name, grp in (cfg.get("files") or {}).items():
        if not argv or name in argv:
            fetch_files(name, grp)
    for name, src in cfg["sources"].items():
        if not argv or name in argv:
            fetch(name, src, cfg.get("stripped", []))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
