"""Dựng kho tài sản thư viện (vòng 10, WP-A) từ NGUỒN CHÍNH CHỦ, chỉ giấy phép thoáng — index: vidlib/assets3d.py.

  python scripts/assets_fetch.py                     tải file còn thiếu theo index (config/assets3d.json), kiểm SHA-256
  python scripts/assets_fetch.py --discover [gói…]   liệt kê lại từ nguồn (GitHub tree @commit, Poly Haven API), chọn file
                                                     theo luật của gói, đo mô hình, ghi lại `models` của index
  python scripts/assets_fetch.py --local <file.zip> --pack <id> [--title …] [--author …] [--page URL] [--unit 1]
                                                     nhập gói anh TỰ TẢI (Kenney/Quaternius: trang chặn tải tự động) —
                                                     zip phải có văn bản giấy phép CC0/MIT/… bên trong (đọc và lưu lại)
  python scripts/assets_fetch.py svg [--discover]    kho icon SVG thư viện (assets/lib/svg/index.json) → parts

Tài liệu tải về là dữ liệu KHÔNG tin cậy: chỉ ghi vào assets/lib/…, không chạy gì trong đó, đường dẫn được lọc (không
'..', không tuyệt đối). User-Agent nêu tên công cụ (Poly Haven yêu cầu). Không dùng nguồn mà robots.txt cấm tác tử tự động
(kenney.nl, opengameart.org, drive.google.com) — xem docs/round10/A.md.
"""

import argparse
import concurrent.futures as cf
import hashlib
import html
import io
import json
import os
import posixpath
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vidlib import assets3d as A  # noqa: E402
from vidlib.common import StudioError, save_json  # noqa: E402

UA = "forward-studio-assets-fetch/1.0 (local video tool; one-time download of CC0/MIT assets)"
TODAY = time.strftime("%Y-%m-%d")


# ------------------------------------------------------------------------------------------------------------- mạng
def get(url, tries=3):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as ex:  # noqa: BLE001
            last = ex
            time.sleep(1.5 * (k + 1))
    raise StudioError(f"tải không được {url}: {last}")


def get_json(url):
    return json.loads(get(url).decode("utf-8"))


def safe_rel(p):
    """Đường dẫn tương đối an toàn (dữ liệu tải về không được thoát khỏi thư mục gói)."""
    p = posixpath.normpath(str(p).replace("\\", "/"))
    if p.startswith(("/", "../")) or p == ".." or re.match(r"^[a-zA-Z]:", p):
        raise StudioError(f"đường dẫn không an toàn trong dữ liệu tải về: {p}")
    return p


_LOCKS, _LOCK = {}, threading.Lock()


def path_lock(path):
    """Khoá theo file: texture dùng chung (atlas của cả gói) chỉ tải một lần dù nhiều luồng cùng cần."""
    with _LOCK:
        return _LOCKS.setdefault(os.path.normcase(os.path.abspath(path)), threading.Lock())


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{threading.get_ident()}.part"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw_url(repo, commit, path):
    return f"https://raw.githubusercontent.com/{repo}/{commit}/{urllib.parse.quote(path)}"


# ------------------------------------------------------------------------------------------------------- giấy phép
def save_license(pid, name, data, must):
    """Lưu văn bản giấy phép (bằng chứng lúc tải) → assets/lib/licenses/<gói>__<tên>; phải chứa mọi cụm `must`."""
    txt = data.decode("utf-8", "replace")
    for m in must or []:
        if m.lower() not in txt.lower():
            raise StudioError(f"gói {pid}: văn bản giấy phép {name} KHÔNG có '{m}' — dừng, không dùng gói này.")
    dst = os.path.join(A.LICENSES, f"{pid}__{re.sub(r'[^A-Za-z0-9._-]+', '_', name)}")
    write(dst, txt.replace("\r\n", "\n").encode("utf-8"))
    return {"path": A.rel(dst), "sha256": A.sha256_file(dst), "from": name}


def html_text(b):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", b.decode("utf-8", "replace"))
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", html.unescape(t))).strip().encode("utf-8")


# --------------------------------------------------------------------------------------------- tên / tag / cỡ thật
def model_name(p, base):
    s = os.path.splitext(os.path.splitext(base)[0])[0]          # "x.gltf.glb" → "x"
    s = re.sub(r"([a-z])([A-Z])", r"\1-\2", s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    for pat, rep in p.get("rename") or []:
        s = re.sub(pat, rep, s)
    return s.strip("-")


def tags_for(vocab, p, name, extra=()):
    toks = {A.stem(t) for t in A.tokens(name)} | {A.stem(t) for x in extra for t in A.tokens(x)}
    out = list(p.get("tags") or [])
    for tag, words in (vocab.get("tags") or {}).items():
        if tag.startswith("_"):
            continue
        if any(A.stem(w) in toks for w in words) and tag not in out:
            out.append(tag)
    for pat, tg in (p.get("tag_rules") or {}).items():
        if re.search(pat, name):
            out += [t for t in tg if t not in out]
    return out


def group_of(vocab, tags):
    for g in vocab.get("groups") or []:
        if g in tags:
            return g
    return tags[0] if tags else "prop"


def keywords_for(vocab, p, name, tags, extra=()):
    syn = vocab.get("synonyms") or {}
    kw = []
    for t in A.tokens(name) + [x for e in extra for x in A.tokens(e)]:
        for w in [t] + syn.get(A.stem(t), []) + syn.get(t, []):
            if w not in kw:
                kw.append(w)
    for t in tags + list(p.get("keywords") or []):
        if t not in kw:
            kw.append(t)
    for pat, ws in (p.get("keyword_rules") or {}).items():
        if re.search(pat, name):
            kw += [w for w in ws if w not in kw]
    return kw


def height_for(vocab, p, name, group, meta):
    """Chiều cao thật (m): heights[regex] cố định → unit_rules[regex] → unit_by_group[nhóm] → unit của gói; kẹp theo
    sizes[nhóm]. (Gói game hay phóng to đồ ăn/đồ nhỏ so với nhân vật — luật riêng đưa về cỡ thật.)"""
    lo, hi = meta["bbox"]
    h_src = max(1e-6, hi[1] - lo[1])
    for pat, h in (p.get("heights") or {}).items():
        if re.search(pat, name):
            return float(h), h_src
    unit = next((u for pat, u in (p.get("unit_rules") or {}).items() if re.search(pat, name)), None)
    unit = unit or (p.get("unit_by_group") or {}).get(group) or p.get("unit") or 1.0
    h = h_src * float(unit)
    rng = (vocab.get("sizes") or {}).get(group)
    if rng:
        h = min(max(h, rng[0]), rng[1])
    return round(h, 3), h_src


def make_entry(vocab, pid, p, name, file_abs, files, meta, extra_kw=(), src=""):
    hide = [h for h in p.get("hide") or [] if meta["skinned"] and any(h.lower() in n.lower() for n in meta["mesh_nodes"])]
    if hide:
        meta = A.gltf_meta(file_abs, hide)
    tags = tags_for(vocab, p, name, extra_kw)
    group = group_of(vocab, tags)
    h, h_src = height_for(vocab, p, name, group, meta)
    lo, hi = meta["bbox"]
    k = h / h_src
    e = {"pack": pid, "file": A.rel(file_abs), "files": files, "src": src, "group": group, "tags": tags,
         "keywords": keywords_for(vocab, p, name, tags, extra_kw), "h": h,
         "dims": [round((hi[i] - lo[i]) * k, 3) for i in range(3)], "bbox_src": meta["bbox"], "tris": meta["tris"],
         "skinned": meta["skinned"], "morph": meta["morph"], "textured": meta["textured"],
         "materials": meta["materials"][:12], "anims": meta["anims"]}
    if hide:
        e["hide"] = hide
    ad = p.get("anim_default")
    if ad and meta["anims"]:
        hit = A.anim_match([a["name"] for a in meta["anims"]], ad)
        if hit:
            e["anim_default"] = hit
    if p.get("render"):
        e["render"] = p["render"]
    return e


# ------------------------------------------------------------------------------------------------------ nguồn GitHub
def gh_tree(repo, commit):
    d = get_json(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1")
    if d.get("truncated"):
        print(f"  ⚠ cây {repo} bị cắt (quá lớn) — có thể thiếu file")
    return [x["path"] for x in d.get("tree") or [] if x.get("type") == "blob"]


def fetch_gltf_set(src_url_of, dst_dir, rel_main):
    """Tải file chính + mọi URI tương đối nó cần (bin, ảnh). → {đường dẫn tương đối theo thư mục mô hình: {sha256, url}}."""
    rel_main = safe_rel(rel_main)
    main_abs = os.path.join(dst_dir, rel_main)
    data = get(src_url_of(rel_main))
    write(main_abs, data)
    files = {os.path.basename(rel_main): {"sha256": sha(data), "url": src_url_of(rel_main)}}
    j, _ = A.read_gltf(main_abs)
    mdir = posixpath.dirname(rel_main)
    for u in A.external_uris(j):
        ru = safe_rel(posixpath.join(mdir, urllib.parse.unquote(u)))
        dst = os.path.join(dst_dir, ru)
        with path_lock(dst):
            if not os.path.isfile(dst):
                write(dst, get(src_url_of(ru)))
        with open(dst, "rb") as fh:
            files[safe_rel(posixpath.relpath(ru, mdir or "."))] = {"sha256": sha(fh.read()), "url": src_url_of(ru)}
    return main_abs, files


def licenses_of(pid, p, url_of):
    out = []
    for lf in (p.get("source") or {}).get("license_files") or []:
        lf = lf if isinstance(lf, dict) else {"path": lf}
        out.append(save_license(pid, posixpath.basename(lf["path"]) if not lf.get("name") else lf["name"],
                                get(url_of(lf["path"])), lf.get("must", p.get("license_must"))))
    return out


def discover_github(vocab, pid, p):
    s = p["source"]
    repo, commit, base = s["repo"], s["commit"], s.get("dir", "").strip("/")
    paths = gh_tree(repo, commit)
    lic = licenses_of(pid, p, lambda path: raw_url(repo, commit, path))
    subs = s.get("dirs")                      # chỉ các thư mục con này (vd 1 biến thể màu của gói nhà)
    cands = [x for x in paths if x.lower().endswith((".gltf", ".glb")) and (not base or x.startswith(base + "/"))
             and (subs is None or posixpath.dirname(x[len(base) + 1:] if base else x) in subs)]
    pick = A.pack_select(p, cands)
    dst_dir = os.path.join(A.LIB3D, pid)
    out = {}

    def one(path):
        relp = path[len(base) + 1:] if base else path
        f_abs, files = fetch_gltf_set(lambda r: raw_url(repo, commit, f"{base}/{r}" if base else r), dst_dir, relp)
        return path, f_abs, files

    with cf.ThreadPoolExecutor(8) as ex:
        for path, f_abs, files in ex.map(one, pick):
            out[path] = (f_abs, files)
    return lic, out


# --------------------------------------------------------------------------------------------------- nguồn Poly Haven
def discover_polyhaven(vocab, pid, p):
    s = p["source"]
    lic = [save_license(pid, "polyhaven.com-license.txt", html_text(get(s["license_page"])), p.get("license_must"))]
    res, dst_dir, out = s.get("res", "1k"), os.path.join(A.LIB3D, pid), {}

    def one(slug):
        info = get_json(f"https://api.polyhaven.com/info/{slug}")
        g = get_json(f"https://api.polyhaven.com/files/{slug}")["gltf"][res]["gltf"]
        raw = get(g["url"])
        if g.get("md5") and hashlib.md5(raw).hexdigest() != g["md5"]:
            raise StudioError(f"{slug}: md5 gltf không khớp API")
        gj = json.loads(raw.decode("utf-8"))
        # chỉ giữ ảnh màu (baseColorTexture): look 3D của tool thay chất liệu → normal/ARM không dùng, đỡ ~55% dung lượng
        keep_tex = set()
        for m in gj.get("materials") or []:
            pbr = m.get("pbrMetallicRoughness") or {}
            if "baseColorTexture" in pbr:
                keep_tex.add(pbr["baseColorTexture"]["index"])
            for k in ("normalTexture", "occlusionTexture", "emissiveTexture"):
                m.pop(k, None)
            pbr.pop("metallicRoughnessTexture", None)
            m.pop("extensions", None)
        tex = gj.get("textures") or []
        keep_img = sorted({tex[i]["source"] for i in keep_tex})
        img_map = {old: new for new, old in enumerate(keep_img)}
        tex_map, new_tex = {}, []
        for i, t in enumerate(tex):
            if i in keep_tex:
                tex_map[i] = len(new_tex)
                new_tex.append({**t, "source": img_map[t["source"]]})
        for m in gj.get("materials") or []:
            pbr = m.get("pbrMetallicRoughness") or {}
            if "baseColorTexture" in pbr:
                pbr["baseColorTexture"]["index"] = tex_map[pbr["baseColorTexture"]["index"]]
        gj["images"] = [gj["images"][i] for i in keep_img]
        gj["textures"] = new_tex
        gj.pop("extensionsUsed", None)
        gj.pop("extensionsRequired", None)
        need = {u for u in A.external_uris(gj)}
        files = {}
        for k, inc in (g.get("include") or {}).items():
            if k not in need:
                continue
            b = get(inc["url"])
            if inc.get("md5") and hashlib.md5(b).hexdigest() != inc["md5"]:
                raise StudioError(f"{slug}: md5 {k} không khớp API")
            write(os.path.join(dst_dir, safe_rel(k)), b)
            files[safe_rel(k)] = {"sha256": sha(b), "url": inc["url"]}
        data = (json.dumps(gj, indent=1) + "\n").encode("utf-8")
        main = os.path.join(dst_dir, f"{slug}.gltf")
        write(main, data)
        files[f"{slug}.gltf"] = {"sha256": sha(data), "url": g["url"], "patch": "chỉ giữ baseColorTexture",
                                 "src_md5": g.get("md5")}
        return slug, main, files, info

    with cf.ThreadPoolExecutor(6) as ex:
        for slug, main, files, info in ex.map(one, s["assets"]):
            out[slug] = (main, files, info)
    return lic, out


# -------------------------------------------------------------------------------------------------- nguồn file lẻ
def discover_files(vocab, pid, p):
    s = p["source"]
    lic = licenses_of(pid, p, lambda path: s["base"] + path)
    dst_dir, out = os.path.join(A.LIB3D, pid), {}
    for path in s["files"]:
        pdir = posixpath.dirname(path)
        f_abs, files = fetch_gltf_set(lambda r, d=pdir: s["base"] + posixpath.join(d, r), dst_dir,
                                      posixpath.basename(path))
        out[path] = (f_abs, files)
    return lic, out


# ---------------------------------------------------------------------------------------------- gói anh tự tải (zip)
LICENSE_HINTS = ("license", "licence", "readme")


def import_local(zpath, pid, title, author, page, unit, tags):
    """Zip tải tay (Kenney/Quaternius…) → assets/lib/3d/<pid>/. Giấy phép đọc TỪ CHÍNH zip; không CC0/MIT/… → từ chối."""
    idx = A.require()
    with open(zpath, "rb") as fh:
        zdata = fh.read()
    zf = zipfile.ZipFile(io.BytesIO(zdata))
    names = [n for n in zf.namelist() if not n.endswith("/")]
    lic_names = [n for n in names if any(h in posixpath.basename(n).lower() for h in LICENSE_HINTS)
                 and n.lower().endswith((".txt", ".md", ""))]
    found, lic = None, []
    for n in lic_names:
        txt = zf.read(n).decode("utf-8", "replace")
        for spdx, pats in (("CC0-1.0", ("cc0", "publicdomain/zero")), ("MIT", ("mit license",)),
                           ("Apache-2.0", ("apache license",)), ("ISC", ("isc license",))):
            if any(x in txt.lower() for x in pats) and not re.search(r"non-?commercial|\bnc\b|no derivatives", txt, re.I):
                found = found or spdx
                lic.append(save_license(pid, posixpath.basename(n), txt.encode("utf-8"), []))
    if not found:
        raise StudioError(f"{zpath}: không thấy văn bản giấy phép CC0/MIT/Apache/ISC trong zip — không nhập.")
    p = (idx.get("packs") or {}).get(pid) or {}
    p.update({"title": title or p.get("title") or pid, "author": author or p.get("author") or "?",
              "page": page or p.get("page"), "license": found, "license_files": lic, "checked": TODAY,
              "unit": unit or p.get("unit") or 1.0,
              "source": {"kind": "local", "zip": os.path.basename(zpath), "zip_sha256": sha(zdata),
                         "url": page or ""},
              "checked_note": "giấy phép đọc từ văn bản trong zip anh tự tải (xem license_files)"})
    if tags:
        p["tags"] = tags
    dst_dir = os.path.join(A.LIB3D, pid)
    out = {}
    models = [n for n in names if n.lower().endswith((".glb", ".gltf"))]
    for n in A.pack_select(p, models):
        rn = safe_rel(n)
        write(os.path.join(dst_dir, rn), zf.read(n))
        files = {posixpath.basename(rn): {"sha256": sha(zf.read(n)), "url": f"zip:{os.path.basename(zpath)}:{n}"}}
        j, _ = A.read_gltf(os.path.join(dst_dir, rn))
        for u in A.external_uris(j):
            ru = safe_rel(posixpath.join(posixpath.dirname(rn), urllib.parse.unquote(u)))
            if ru in zf.namelist():
                b = zf.read(ru)
                write(os.path.join(dst_dir, ru), b)
                files[safe_rel(posixpath.relpath(ru, posixpath.dirname(rn) or "."))] = {"sha256": sha(b), "url": f"zip:{ru}"}
        out[n] = (os.path.join(dst_dir, rn), files)
    idx.setdefault("packs", {})[pid] = p
    build_models(idx, {pid: (p, out, "zip")})
    print(f"✔ gói {pid}: {len(out)} mô hình · giấy phép {found} (đọc từ zip)")
    return 0


# ---------------------------------------------------------------------------------------------- ghép index models
def build_models(idx, results):
    """results: {pid: (pack, {src: (file_abs, files[, info])}, kind)} → cập nhật idx['models'] (thứ tự gói = ưu tiên tên)."""
    vocab, rejected = idx.get("vocab") or {}, idx.get("rejected") or {}
    # đặt tên lại cho MỌI gói theo thứ tự ưu tiên (tên trùng → hậu tố gói), gói không tải lần này lấy từ index cũ
    results = {**found_from_index(idx, [k for k in idx["packs"] if k not in results]), **results}
    models, taken = {}, set()
    order = [k for k in idx["packs"] if k in results]
    for pid in order:
        p, found, kind = results[pid]
        nbytes, seen = 0, set()
        cnt = 0
        for src in sorted(found):
            v = found[src]
            f_abs, files = v[0], v[1]
            info = v[2] if len(v) > 2 else None
            base = os.path.basename(src) if kind != "polyhaven" else src
            name = model_name(p, base)
            if name in taken:
                name = f"{name}-{p.get('short', pid)}"
            if name in rejected or f"{pid}:{name}" in rejected:
                continue
            meta = A.gltf_meta(f_abs)
            extra = []
            if info:
                extra = list(info.get("tags") or []) + list(info.get("categories") or []) + [info.get("name", "")]
            e = make_entry(vocab, pid, p, name, f_abs, files, meta, extra, src)
            if info:
                e["title"] = info.get("name")
                e["authors"] = list((info.get("authors") or {}).keys())
                e["src_tags"] = sorted({str(t).lower() for t in extra if t and t != info.get("name")})
            models[name] = e
            taken.add(name)
            cnt += 1
            for fn in files:
                fp = os.path.normpath(os.path.join(os.path.dirname(f_abs), fn))
                if fp not in seen and os.path.isfile(fp):
                    seen.add(fp)
                    nbytes += os.path.getsize(fp)
        p["models"], p["bytes"], p["fetched"] = cnt, nbytes, TODAY
    idx["models"] = dict(sorted(models.items()))
    idx["totals"] = {"models": len(idx["models"]), "animated": sum(1 for e in idx["models"].values() if e.get("anims")),
                     "bytes": sum(p.get("bytes") or 0 for k, p in idx["packs"].items() if not k.startswith("_"))}
    save_json(A.INDEX, idx)
    return idx


def discover(only):
    idx = A.require()
    results = {}
    for pid, p in idx["packs"].items():
        if pid.startswith("_") or (only and pid not in only):
            continue
        kind = (p.get("source") or {}).get("kind")
        t0 = time.time()
        if kind == "github":
            lic, found = discover_github(idx["vocab"], pid, p)
        elif kind == "polyhaven":
            lic, found = discover_polyhaven(idx["vocab"], pid, p)
        elif kind == "files":
            lic, found = discover_files(idx["vocab"], pid, p)
        else:
            print(f"  – {pid}: nguồn '{kind}' không tự tải được (gói nhập tay bằng --local)")
            continue
        p["license_files"] = lic
        p["checked"] = TODAY
        results[pid] = (p, found, kind)
        print(f"  ✓ {pid}: {len(found)} mô hình · {time.time() - t0:.1f}s")
    build_models(idx, results)
    t = idx["totals"]
    print(f"✔ index: {t['models']} mô hình ({t['animated']} có animation) · {t['bytes'] / 1e6:.1f} MB → "
          "config/assets3d.json")
    return 0


def found_from_index(idx, only=None):
    """{pid: (pack, {src: (file, files[, info])}, kind)} dựng lại từ models đang có trong index (file đã ở trên máy)."""
    results = {}
    for n, e in (idx.get("models") or {}).items():
        pid = e["pack"]
        if (only and pid not in only) or pid not in idx["packs"]:
            continue
        p = idx["packs"][pid]
        kind = (p.get("source") or {}).get("kind")
        info = ({"name": e.get("title"), "tags": e.get("src_tags") or [], "categories": [],
                 "authors": {a: 1 for a in e.get("authors") or []}} if kind == "polyhaven" else None)
        found = results.setdefault(pid, (p, {}, kind))[1]
        found[e.get("src") or n] = (A.model_path(e), e["files"], info) if info else (A.model_path(e), e["files"])
    return results


def reindex(only):
    """Đo/gắn tag/cỡ lại từ file ĐÃ có trên máy (không tải) — dùng khi sửa luật vocab/unit của gói."""
    idx = A.require()
    build_models(idx, found_from_index(idx, only))
    t = idx["totals"]
    print(f"✔ đo lại: {t['models']} mô hình ({t['animated']} có animation) → config/assets3d.json")
    return 0


def rebuild():
    """Theo index: tải lại file thiếu/sai SHA từ URL đã ghi (gói zip: báo cần zip)."""
    idx = A.require()
    todo = []
    for n, e in A.models().items():
        base = os.path.dirname(A.model_path(e))
        for fn, m in (e.get("files") or {}).items():
            fp = os.path.join(base, safe_rel(fn))
            if os.path.isfile(fp) and A.sha256_file(fp) == m["sha256"]:
                continue
            todo.append((n, e, fn, fp, m))
    if not todo:
        print("✔ kho 3D đủ file, SHA-256 khớp index.")
        return 0
    print(f"… tải {len(todo)} file thiếu/sai")
    bad = []
    redo_ph = set()

    def one(t):
        n, e, fn, fp, m = t
        if str(m.get("url", "")).startswith("zip:"):
            return f"{n}: {fn} thuộc gói nhập tay — chạy lại --local <zip> --pack {e['pack']}"
        if m.get("patch"):
            redo_ph.add(e["pack"])
            return None
        b = get(m["url"])
        if sha(b) != m["sha256"]:
            return f"{n}: {fn} tải về khác SHA-256 (nguồn đã đổi?)"
        write(fp, b)
        return None

    with cf.ThreadPoolExecutor(8) as ex:
        bad = [r for r in ex.map(one, todo) if r]
    for pid in sorted(redo_ph):        # gltf đã vá (Poly Haven): tải + vá lại cả gói, rồi so SHA
        print(f"  … vá lại gói {pid}")
        discover_polyhaven(idx["vocab"], pid, idx["packs"][pid])
    for b in bad:
        print("  ✖", b)
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------- kho SVG 2D
def svg_main(argv):
    from vidlib import userassets  # noqa: PLC0415
    si = A.svg_index()
    if not si:
        raise StudioError("thiếu assets/lib/svg/index.json (định nghĩa gói SVG)")
    disc = "--discover" in argv
    icons = dict(si.get("icons") or {}) if not disc else {}
    for pid, p in (si.get("packs") or {}).items():
        s = p["source"]
        repo, commit = s["repo"], s["commit"]
        lic = save_license(pid, s["license_file"], get(raw_url(repo, commit, s["license_file"])), p.get("license_must"))
        p["license_file"], p["checked"] = lic, TODAY
        if disc:
            meta = get(raw_url(repo, commit, s["meta"])).decode("utf-8")
            ents = []
            for m in re.finditer(r'\{\s*name: "([^"]+)",(.*?)\n  \}', meta, re.S):
                body = m.group(2)
                cats = re.findall(r"IconCategory\.(\w+)", body.split("figma_category", 1)[0])
                fig = (re.findall(r"FigmaCategory\.(\w+)", body) or [""])[0]
                tg = re.findall(r'"([^"]+)"', (re.search(r"tags: \[(.*?)\]", body, re.S) or [None, ""])[1] or "")
                ents.append((m.group(1), cats, fig, [t for t in tg if not t.startswith("*")]))
            inc, exc = set(p["categories"]), set(p.get("exclude_categories") or [])
            pick = [e for e in ents if (set(e[1]) & inc or e[2] in inc) and not (set(e[1]) & exc or e[2] in exc)
                    and not any(re.search(x, e[0]) for x in p.get("exclude_names") or [])]
            for name, cats, fig, tg in pick:
                nm = name if name not in icons else f"{name}-{p.get('short', pid)}"
                icons[nm] = {"pack": pid, "src": s["pattern"].format(name=name),
                             "file": A.rel(os.path.join(A.LIBSVG, pid, f"{nm}.json")),
                             "tags": sorted({c.lower() for c in cats} | ({fig.lower()} if fig else set())),
                             "keywords": list(dict.fromkeys(A.tokens(name) + [t.lower() for t in tg]))}
        todo = []
        for nm, e in icons.items():
            if e["pack"] != pid:
                continue
            svgp = os.path.join(A.LIBSVG, pid, f"{nm}.svg")
            if not os.path.isfile(svgp) or (e.get("svg_sha256") and A.sha256_file(svgp) != e["svg_sha256"]):
                todo.append((nm, raw_url(repo, commit, e["src"]), svgp))
        with cf.ThreadPoolExecutor(8) as ex:
            datas = list(ex.map(lambda t: (t[0], get(t[1]), t[2]), todo))
        for nm, b, svgp in datas:
            if icons[nm].get("svg_sha256") and sha(b) != icons[nm]["svg_sha256"]:
                raise StudioError(f"icon {nm}: SVG tải về khác SHA-256 trong index")
            write(svgp, b)
        need = [nm for nm, e in icons.items() if e["pack"] == pid and (not os.path.isfile(os.path.join(ROOT, e["file"]))
                                                                     or nm in {t[0] for t in todo})]
        print(f"  {pid}: {sum(1 for e in icons.values() if e['pack'] == pid)} icon · nhập {len(need)} (một trình duyệt)")
        texts = []
        for nm in need:
            with open(os.path.join(A.LIBSVG, pid, f"{nm}.svg"), encoding="utf-8") as fh:
                texts.append((nm, fh.read()))
        res = userassets.svg_batch(texts, role=p.get("role", "auto"), budget=p.get("budget", 700))
        note = f"{p['title']} — {p['license']} ({s['url']})"
        for nm, r in res.items():
            if r.get("error") or not r.get("parts"):
                print(f"   ✖ {nm}: {r.get('error') or 'không có hình'} — bỏ")
                icons.pop(nm, None)
                continue
            with open(os.path.join(A.LIBSVG, pid, f"{nm}.svg"), "rb") as fh:
                svg_sha = sha(fh.read())
            out = os.path.join(ROOT, icons[nm]["file"])
            save_json(out, {"name": nm, "source": icons[nm]["src"], "license": note, "sha256": svg_sha,
                            "role": p.get("role", "auto"), "stats": r["stats"], "parts": r["parts"]})
            icons[nm].update({"svg_sha256": svg_sha, "parts_sha256": A.sha256_file(out), "n_parts": len(r["parts"])})
        p["icons"] = sum(1 for e in icons.values() if e["pack"] == pid)
        p["fetched"] = TODAY
    si["icons"] = dict(sorted(icons.items()))
    save_json(A.SVG_INDEX, si)
    print(f"✔ kho SVG: {len(icons)} icon → {A.rel(A.SVG_INDEX)}")
    return 0


def main(argv):
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    if argv and argv[0] == "svg":
        return svg_main(argv[1:])
    ap = argparse.ArgumentParser(prog="python scripts/assets_fetch.py")
    ap.add_argument("packs", nargs="*")
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--reindex", action="store_true")
    ap.add_argument("--local")
    ap.add_argument("--pack")
    ap.add_argument("--title")
    ap.add_argument("--author")
    ap.add_argument("--page")
    ap.add_argument("--unit", type=float)
    ap.add_argument("--tags")
    a = ap.parse_args(argv)
    try:
        if a.local:
            if not a.pack:
                raise StudioError("--local cần --pack <id>")
            return import_local(a.local, a.pack, a.title, a.author, a.page, a.unit,
                                [t.strip() for t in (a.tags or "").split(",") if t.strip()])
        if a.reindex:
            return reindex(set(a.packs))
        return discover(set(a.packs)) if a.discover else rebuild()
    except StudioError as ex:
        print(f"✖ {ex}")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
