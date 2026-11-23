"""Kiểm chứng Phần C (C3 + C4) cho các dự án thử → qa/part-c.md + qa/part-c.json.

  python scripts/verify_partc.py <slug> [<slug> …] [--repro <slug>] [--resume <slug>]

C3: đo độc lập mọi out/deliver/<preset>/video.mp4 bằng ffprobe + ebur128 (không dùng lại kết quả của deliver.py) so với
    config/delivery.json → bảng ĐẠT/KHÔNG từng mục.
C4: --repro: dựng lại từ render (dry-run) 2 lần → so sha256 + pHash từng giây của final.mp4.
    --resume: bắt đầu dựng lại một shot code, ngắt sau khi có frame mới, chạy lại → kiểm log RESUME + thời gian.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vidlib.common import PROJECTS, ffbin, load_json  # noqa: E402


def ffprobe(p):
    r = subprocess.run([ffbin("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", p], capture_output=True, text=True)
    return json.loads(r.stdout)


def ebur128(p):
    r = subprocess.run([ffbin("ffmpeg"), "-hide_banner", "-nostats", "-i", p, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    t = r.stderr
    tail = t[t.rfind("Summary:"):]
    get = lambda k: float(re.search(rf"{k}:\s*(-?[\d.]+)", tail).group(1)) if re.search(rf"{k}:\s*(-?[\d.]+)", tail) else None  # noqa: E731
    return {"I": get("I"), "LRA": get("LRA"), "TP": get("Peak")}


def moov_first(p):
    from vidlib.qagate import moov_first as mf  # noqa: PLC0415
    return mf(p)


def check_preset(video, p):
    d = ffprobe(video)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), {})
    f = d["format"]
    loud = ebur128(video)
    mb = os.path.getsize(video) / 1e6
    rows = [
        ("khung", f"{v['width']}x{v['height']}", (v["width"], v["height"]) == tuple(p["size"])),
        ("fps CFR", f"{v['r_frame_rate']} / {v['avg_frame_rate']}", v["r_frame_rate"] == v["avg_frame_rate"] == f"{p['fps']}/1"),
        ("codec", f"{v['codec_name']} {v.get('profile')} L{v.get('level')} + {a.get('codec_name')}", v["codec_name"] == "h264" and a.get("codec_name") == "aac"),
        ("pix_fmt", v.get("pix_fmt"), v.get("pix_fmt") == "yuv420p"),
        ("màu", f"{v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')} {v.get('color_range')}",
         (v.get("color_primaries"), v.get("color_transfer"), v.get("color_space"), v.get("color_range")) == ("bt709", "bt709", "bt709", "tv")),
        ("faststart", "moov đầu" if moov_first(video) else "moov cuối", moov_first(video)),
        ("audio", f"{a.get('sample_rate')} Hz {int(float(a.get('bit_rate') or 0) / 1000)} kb/s", str(a.get("sample_rate")) == "48000"),
        ("loudness", f"{loud['I']} LUFS", loud["I"] is not None and abs(loud["I"] - p.get("lufs", -14)) <= 1.0),
        ("true peak", f"{loud['TP']} dBTP", loud["TP"] is not None and loud["TP"] <= p.get("tp_max", -1.0)),
        ("thời lượng", f"{float(f['duration']):.1f}s", not p.get("max_sec") or float(f["duration"]) <= p["max_sec"]),
        ("dung lượng", f"{mb:.1f} MB", not p.get("max_mb") or mb <= p["max_mb"]),
    ]
    if p.get("min_kbps"):
        rows.append(("bitrate tối thiểu", f"{float(f['bit_rate']) / 1000:.0f} kb/s", float(f["bit_rate"]) / 1000 >= p["min_kbps"]))
    return rows, loud


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frame_hashes(video, every=1.0):
    import cv2  # noqa: PLC0415

    from vidlib.visreg import phash  # noqa: PLC0415
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    out, i = [], 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % int(fps * every) == 0:
            out.append(phash(cv2.resize(fr, (270, 480))))
        i += 1
    cap.release()
    return out


def run(argv):
    return subprocess.run([sys.executable, "studio.py", *argv], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--repro")
    ap.add_argument("--resume")
    a = ap.parse_args(argv)
    cfg = load_json(os.path.join(ROOT, "config", "delivery.json"))
    out = load_json(os.path.join(ROOT, "qa", "part-c.json"), {}) or {}
    L = ["# Phần C — kiểm chứng gói xuất + tái lập (đo độc lập, " + time.strftime("%Y-%m-%d %H:%M") + ")", ""]
    for slug in a.slugs:
        res = {}
        for vid in sorted(glob.glob(os.path.join(PROJECTS, slug, "out", "deliver", "*", "video.mp4"))):
            preset = os.path.basename(os.path.dirname(vid))
            rows, loud = check_preset(vid, cfg["presets"][preset])
            res[preset] = {"rows": rows, "pass": all(r[2] for r in rows)}
        out.setdefault("c3", {})[slug] = res
        L += [f"## {slug}", "", "| Preset | Kết quả | " + " | ".join(r[0] for r in next(iter(res.values()))["rows"]) + " |" if res else "_(chưa có gói)_"]
        if res:
            L.append("|---|---|" + "---|" * len(next(iter(res.values()))["rows"]))
            for k, r in res.items():
                L.append(f"| {k} | {'ĐẠT' if r['pass'] else 'KHÔNG'} | " + " | ".join(f"{x[1]}{'' if x[2] else ' ✗'}" for x in r["rows"]) + " |")
        L.append("")
    if a.repro:
        fin = os.path.join(PROJECTS, a.repro, "out", "final.mp4")
        runs = []
        for _ in range(2):
            t0 = time.time()
            r = run(["video", a.repro, "--from", "render", "--dry-run", "--no-open", "--yes"])
            runs.append({"rc": r.returncode, "sec": round(time.time() - t0), "sha": sha(fin), "ph": frame_hashes(fin)})
        same_sha = runs[0]["sha"] == runs[1]["sha"]
        dist = [int((x != y).sum()) for x, y in zip(runs[0]["ph"], runs[1]["ph"])]
        out["c4_repro"] = {"slug": a.repro, "rc": [x["rc"] for x in runs], "sec": [x["sec"] for x in runs], "same_sha256": same_sha,
                           "phash_max_dist": max(dist) if dist else None, "frames_compared": len(dist)}
        L += ["## Tái lập (cùng đầu vào, dựng lại 2 lần)", "", f"- dự án `{a.repro}` · exit {out['c4_repro']['rc']} · {out['c4_repro']['sec']} s",
              f"- sha256 final.mp4 giống hệt: **{same_sha}** · pHash lệch tối đa {out['c4_repro']['phash_max_dist']} bit trên "
              f"{len(dist)} mốc 1 s (0 = giống hệt)", ""]
    if a.resume:
        import shutil  # noqa: PLC0415

        from vidlib import codeshot  # noqa: PLC0415
        proj = os.path.join(PROJECTS, a.resume)
        ids = sorted(s for s in os.listdir(os.path.join(proj, "work", "code")) if s.startswith("C"))
        # shot dry-run dựng ~50 frame/giây → ngắt ngay khi thấy frame đầu (poll 50 ms); shot nào xong trước khi ngắt kịp → thử shot khác
        for sid in ids[1:4] + ids[:1]:
            fdir = codeshot.frames_dir(proj, sid)
            total = len(glob.glob(os.path.join(fdir, "f*.jpg")))
            shutil.rmtree(fdir, ignore_errors=True)
            p = subprocess.Popen([sys.executable, "studio.py", "rerender", a.resume, sid, "--dry-run"], cwd=ROOT, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            t0 = time.time()
            while time.time() - t0 < 300:
                if os.path.isdir(fdir) and glob.glob(os.path.join(fdir, "f*.jpg")):
                    break
                time.sleep(0.05)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True) if os.name == "nt" else p.kill()
            at_kill = len(glob.glob(os.path.join(fdir, "f*.jpg")))
            time.sleep(2)
            have = len(glob.glob(os.path.join(fdir, "f*.jpg")))
            if 0 < have < total:
                break
        t1 = time.time()
        r = run(["video", a.resume, "--from", "code", "--dry-run", "--no-open", "--yes"])
        st = (load_json(os.path.join(proj, "work", "code_stats.json"), {}) or {}).get(sid, {})
        after = len(glob.glob(os.path.join(fdir, "f*.jpg")))
        ok = r.returncode == 0 and 0 < have < total and st.get("rendered") == total - have and after == total
        out["c4_resume"] = {"slug": a.resume, "shot": sid, "frames_total": total, "frames_at_kill": at_kill, "frames_before_kill": have,
                            "rendered_after": st.get("rendered"), "frames_after": after, "rc": r.returncode,
                            "sec": round(time.time() - t1), "pass": ok}
        L += ["## Ngắt giữa lúc render → chạy lại (RESUME)", "",
              f"- shot `{sid}` ({total} frame): xoá frame → bắt đầu `rerender` → ngắt cả cây tiến trình khi đã có {at_kill} frame ({have} sau 2 s)",
              f"- chạy lại `video --from code`: chỉ dựng **{st.get('rendered')}** frame còn thiếu (= {total} − {have}) · đủ {after}/{total} · "
              f"exit {r.returncode} · {out['c4_resume']['sec']} s → **{'ĐẠT' if ok else 'KHÔNG'}**", ""]
    with open(os.path.join(ROOT, "qa", "part-c.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(ROOT, "qa", "part-c.md"), "a" if not a.slugs else "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
