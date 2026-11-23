"""Ingest clip Flow: map tên file → shot, BỎ AUDIO (-an), chuẩn hoá 1080x1920 @30fps CFR.

Quy tắc map (ưu tiên từ trên xuống):
  1. Tên đúng id shot: C01.mp4 / c1.mov / C01_v2.mp4 → C01.
  2. Map đã xác nhận trong clips/_map.json ({"<tên file>": "C03"}).
  3. Tên mặc định của Flow (bất kỳ): sắp theo thời gian tải về (mtime) và gán lần lượt cho các shot CÒN THIẾU clip,
     theo thứ tự shot. Bảng map được in ra để xác nhận và lưu vào clips/_map.json.
"""
import os
import re

from .common import H, VIDEO_EXT, W, FPS, StudioError, load_json, probe, run, save_json

ID_IN_NAME = re.compile(r"^c0*(\d{1,3})(?:[_\-\s.].*)?$", re.I)


def clips_dir(proj):
    return os.path.join(proj, "clips")


def map_path(proj):
    return os.path.join(clips_dir(proj), "_map.json")


def ingest_dir(proj):
    return os.path.join(proj, "work", "ingest")


def ingested(proj, sid):
    return os.path.join(ingest_dir(proj), f"{sid}.mp4")


def _videos(folder):
    if not os.path.isdir(folder):
        return []
    out = []
    for n in os.listdir(folder):
        p = os.path.join(folder, n)
        if os.path.isfile(p) and n.lower().endswith(VIDEO_EXT) and not n.startswith((".", "_")):
            out.append(p)
    return out


def shot_id_from_name(name):
    m = ID_IN_NAME.match(os.path.splitext(os.path.basename(name))[0])
    return f"C{int(m.group(1)):02d}" if m else None


def scan(proj, sb, extra_dirs=()):
    """Trả về list dict {sid, path, how} cho các clip tìm thấy (mỗi shot tối đa 1 clip)."""
    need = [s["id"] for s in sb["shots"] if s.get("mode_resolved", s.get("mode")) != "code" and not s.get("code")]
    files = _videos(clips_dir(proj))
    for d in extra_dirs:
        files += _videos(d)
    saved = load_json(map_path(proj), {})
    taken, rows, loose = set(), [], []
    # 1. tên đúng id — bản tải sau cùng thắng nếu trùng
    for p in sorted(files, key=os.path.getmtime):
        sid = shot_id_from_name(p)
        if sid in need:
            rows = [r for r in rows if r["sid"] != sid]
            rows.append({"sid": sid, "path": p, "how": "tên file"})
            taken.add(sid)
    named = {r["path"] for r in rows}
    # 2. map đã lưu
    for p in files:
        if p in named:
            continue
        sid = saved.get(os.path.basename(p))
        if sid in need and sid not in taken:
            rows.append({"sid": sid, "path": p, "how": "đã xác nhận"})
            taken.add(sid)
        elif shot_id_from_name(p) is None:
            loose.append(p)
    # 3. tên mặc định của Flow → theo thời gian tải về
    loose = [p for p in loose if os.path.basename(p) not in saved]
    missing = [sid for sid in need if sid not in taken]
    for p, sid in zip(sorted(loose, key=os.path.getmtime), missing):
        rows.append({"sid": sid, "path": p, "how": "thời gian tải về"})
    order = {sid: i for i, sid in enumerate(need)}
    return sorted(rows, key=lambda r: order[r["sid"]])


def table(rows):
    if not rows:
        return "  (chưa có clip nào)"
    w = max(len(os.path.basename(r["path"])) for r in rows)
    lines = [f"  {'Shot':<5} {'File':<{w}}  Map theo"]
    lines += [f"  {r['sid']:<5} {os.path.basename(r['path']):<{w}}  {r['how']}" for r in rows]
    return "\n".join(lines)


def needs_confirm(rows):
    return any(r["how"] == "thời gian tải về" for r in rows)


def save_map(proj, rows):
    data = load_json(map_path(proj), {})
    for r in rows:
        if r["how"] == "thời gian tải về" and os.path.dirname(r["path"]) == clips_dir(proj):
            data[os.path.basename(r["path"])] = r["sid"]
    if data:
        save_json(map_path(proj), data)


def as_dict(rows):
    return {r["sid"]: r["path"] for r in rows}


def normalize_clip(src, dst):
    """Bỏ audio + chuẩn hoá khung/fps. Đảm bảo 100% không còn audio stream."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    info = probe(src)
    if info["width"] and info["height"] and info["width"] > info["height"]:
        print(f"  ⚠ {os.path.basename(src)} là video NGANG {info['width']}x{info['height']} — sẽ cắt giữa về 9:16. "
              f"Nên tạo dọc 9:16 trong Flow.")
    from . import encode  # noqa: PLC0415
    vf = (f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
          f"{encode.TO_YUV}")
    tmp = dst + ".part.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", vf,
         *encode.video_args("intermediate", FPS), *encode.mux_args(), tmp],
        "ffmpeg (ingest)")
    out = probe(tmp)
    if out["audio_streams"]:
        raise StudioError(f"Ingest {src}: vẫn còn audio stream (không thể xảy ra với -an).")
    os.replace(tmp, dst)
    return {"src": os.path.basename(src), "src_audio_streams": info["audio_streams"], "src_fps": info["fps"],
            "src_size": [info["width"], info["height"]], "duration": out["duration"]}


def ingest(proj, rows, log=print):
    """Chuẩn hoá các clip đã map (bỏ qua nếu bản ingest mới hơn file gốc). Trả về {sid: info}."""
    report = load_json(os.path.join(ingest_dir(proj), "_ingest.json"), {})
    for r in rows:
        dst = ingested(proj, r["sid"])
        prev = report.get(r["sid"], {})
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(r["path"]) \
                and prev.get("src") == os.path.basename(r["path"]):
            continue
        info = normalize_clip(r["path"], dst)
        report[r["sid"]] = info
        log(f"  ✔ {r['sid']} ← {info['src']} ({info['duration']:.1f}s, bỏ {info['src_audio_streams']} track tiếng)")
    if rows:
        save_json(os.path.join(ingest_dir(proj), "_ingest.json"), report)
    return report
