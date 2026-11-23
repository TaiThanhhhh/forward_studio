"""Dựng CÙNG một storyboard bằng nhiều style rồi ghép lưới để chọn (vòng 7, mục verification).

  python scripts/style_compare.py [storyboard.json] --styles a,b,c [--out qa/style-compare.mp4] [--skip-render]

Mỗi style → một dự án `projects/cmp-<style>/` chạy qua pipeline thật (`studio.py video … --yes --look-ok`): VO (cache
theo nội dung nên chỉ tốn một lần gọi TTS), shot code, mix/master, QA. Sau đó:
  - qa/style-compare.mp4  — lưới các bản dựng cạnh nhau, có tên style; tiếng của bản đầu tiên;
  - qa/style-compare.md   — bảng đo từng bản: thời lượng, tỉ lệ nền đen (so với black_min của style), đứng hình dài nhất,
                            LUFS / true peak, OCR, engine đã dùng.
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from vidlib import textstyle  # noqa: E402
from vidlib.common import PROJECTS, channel, ffbin, load_json, save_json  # noqa: E402


def run_style(sb_path, style, log=print):
    slug = f"cmp-{style}"
    proj = os.path.join(PROJECTS, slug)
    os.makedirs(proj, exist_ok=True)
    sb = load_json(sb_path)
    sb.pop("_doc", None)
    sb["style"], sb["slug"] = style, slug
    cur = load_json(os.path.join(proj, "storyboard.json"), {})
    keep = ("topic", "shots", "outro", "style")
    if not cur or any(_strip(cur.get(k)) != _strip(sb.get(k)) for k in keep):
        save_json(os.path.join(proj, "storyboard.json"), sb)
    with open(os.path.join(proj, "idea.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sb["topic"])
    # MỘT bản giọng đọc cho mọi style (các ô cùng nhịp, không gọi TTS lại): <thư mục storyboard>/vo/
    shared, adir = os.path.join(os.path.dirname(os.path.abspath(sb_path)), "vo"), os.path.join(proj, "audio")
    if os.path.exists(os.path.join(shared, "vo_alignment.json")):
        os.makedirs(adir, exist_ok=True)
        for f in ("vo.mp3", "vo_alignment.json"):
            shutil.copyfile(os.path.join(shared, f), os.path.join(adir, f))
    pr = subprocess.run(
        [sys.executable, "studio.py", "video", slug, "--yes", "--look-ok", "--no-open"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    tail = "\n".join((pr.stdout + pr.stderr).strip().splitlines()[-14:])
    log(f"── {style}: exit {pr.returncode}\n{tail}")
    if pr.returncode == 0 and not os.path.exists(os.path.join(shared, "vo_alignment.json")):
        os.makedirs(shared, exist_ok=True)
        for f in ("vo.mp3", "vo_alignment.json"):
            shutil.copyfile(os.path.join(adir, f), os.path.join(shared, f))
    return proj, pr.returncode


def _strip(x):
    """So sánh phần người viết (bỏ trường tool sinh) để không ghi đè storyboard đã chạy."""
    if isinstance(x, dict):
        return {
            k: _strip(v)
            for k, v in x.items()
            if k in ("id", "beat", "mode", "target_sec", "vo", "code", "scene", "params", "teaser", "follow_text", "enabled")
            or isinstance(v, (dict, list))
        }
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def frames_of(path, fps=6, w=180):
    h = w * 16 // 9
    raw = subprocess.run(
        [
            ffbin("ffmpeg"),
            "-v",
            "error",
            "-i",
            path,
            "-vf",
            f"fps={fps},scale={w}:{h}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def measure(final, style):
    """Đo trên file cuối: tỉ lệ nền đen trung bình/thấp nhất, đoạn đứng hình dài nhất (30 fps), loudness."""
    fr = frames_of(final)
    lum = fr.astype(np.float32).mean(axis=3)
    black = (lum < 26).mean(axis=(1, 2))  # điểm ảnh gần đen (≤ ~10% sáng)
    full = frames_of(final, fps=30, w=96).astype(np.int16)
    diff = np.abs(np.diff(full, axis=0)).mean(axis=(1, 2, 3))
    run = best = 0
    for d in diff:
        run = run + 1 if d < 0.02 else 0
        best = max(best, run)
    pr = subprocess.run(
        [ffbin("ffmpeg"), "-hide_banner", "-i", final, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    tail = pr.stderr[pr.stderr.rfind("Summary:") :]
    num = lambda key: float(tail.split(key)[1].split()[0]) if key in tail else None  # noqa: E731
    need = float(textstyle.load_style(style).get("black_min", 0.5))
    return {
        "sec": round(len(full) / 30, 2),
        "black_mean": round(float(black.mean()), 3),
        "black_min_frame": round(float(black.min()), 3),
        "black_need": need,
        "black_ok": bool(black.mean() >= need),
        "freeze_max_sec": round((best + 1) / 30 if best else 0.0, 2),
        "lufs": num("I:"),
        "true_peak": num("Peak:"),
    }


def label(style, w, h=64):
    im = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "RobotoMono-Variable.ttf"), 24)
    eng = textstyle.load_style(style).get("code_engine", "")
    d.text((w // 2, h // 2), f"{style} · {eng}", font=f, fill=(236, 236, 236), anchor="mm")
    return im


def grid(finals, out, cell_w=432):
    """Các bản dựng xếp hàng ngang, nhãn tên style phía dưới; tiếng lấy từ bản đầu."""
    cell_h = cell_w * 16 // 9
    tmp = os.path.join(os.path.dirname(out), "_labels")
    os.makedirs(tmp, exist_ok=True)
    cmd, flt = [ffbin("ffmpeg"), "-y", "-v", "error"], []
    for i, (style, f) in enumerate(finals):
        lp = os.path.join(tmp, f"{i}.png")
        label(style, cell_w).save(lp)
        cmd += ["-i", f, "-loop", "1", "-i", lp]
        flt.append(f"[{2 * i}:v]scale={cell_w}:{cell_h},setsar=1[v{i}];[v{i}][{2 * i + 1}:v]vstack=shortest=1[c{i}]")
    n = len(finals)
    flt.append("".join(f"[c{i}]" for i in range(n)) + (f"hstack=inputs={n}:shortest=1[v]" if n > 1 else "null[v]"))
    cmd += [
        "-filter_complex",
        ";".join(flt),
        "-map",
        "[v]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        out,
    ]
    subprocess.run(cmd, check=True)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard", nargs="?", default=os.path.join(ROOT, "qa", "style-compare", "storyboard.json"))
    ap.add_argument("--styles", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "qa", "style-compare.mp4"))
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args(argv)
    styles = [s for s in a.styles.split(",") if s]
    rows, finals = [], []
    for st in styles:
        proj = os.path.join(PROJECTS, f"cmp-{st}")
        rc = 0
        if not a.skip_render:
            proj, rc = run_style(a.storyboard, st)
        final = os.path.join(proj, "out", "final.mp4")
        if not os.path.exists(final):
            rows.append({"style": st, "error": f"không có final.mp4 (exit {rc})"})
            continue
        m = measure(final, st)
        csb = load_json(os.path.join(proj, "storyboard.json"), {})
        engines = sorted(
            {
                load_json(os.path.join(proj, "work", "code", d, "job.json"), {}).get("engine", "three")
                for d in os.listdir(os.path.join(proj, "work", "code"))
            }
        )
        qa = load_json(os.path.join(proj, "qa", "report.json"), {}) or {}
        rows.append(
            {
                "style": st,
                "exit": rc,
                "engines": engines,
                "shots": len(csb.get("shots", [])),
                **m,
                "ocr": qa.get("ocr_summary"),
                "qa_verdict": qa.get("verdict"),
            }
        )
        finals.append((st, final))
    if finals:
        grid(finals, a.out)
    q = channel().get("qa", {})
    aud = channel().get("audio", {})
    L = [
        "# So sánh style — cùng một ý tưởng",
        "",
        f"Storyboard: `{os.path.relpath(a.storyboard, ROOT)}` · lưới: `{os.path.relpath(a.out, ROOT)}`",
        "",
        f"Ngưỡng: đứng hình < {q.get('freeze_max_sec', 0.4)} s · {aud.get('lufs', -14)} LUFS ±1 · true peak ≤ {aud.get('true_peak', -1.0)} dBTP · "
        "nền đen ≥ `black_min` của style.",
        "",
        "| Style | Engine | Dài (s) | Nền đen TB | cần | Đứng hình dài nhất (s) | LUFS | TP (dBTP) | Pipeline |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r.get("error"):
            L.append(f"| {r['style']} | — | — | — | — | — | — | — | ✖ {r['error']} |")
            continue
        L.append(
            f"| {r['style']} | {'+'.join(r['engines'])} | {r['sec']} | {r['black_mean']:.0%} {'✓' if r['black_ok'] else '✖'} | "
            f"{r['black_need']:.0%} | {r['freeze_max_sec']} {'✓' if r['freeze_max_sec'] < q.get('freeze_max_sec', 0.4) else '✖'} | "
            f"{r['lufs']} | {r['true_peak']} | exit {r['exit']} |"
        )
    md = os.path.splitext(a.out)[0] + ".md"
    with open(md, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    save_json(os.path.splitext(a.out)[0] + ".json", rows)
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
