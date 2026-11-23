"""Tiến trình con dựng MỘT shot bằng Manim:  python -m engines.manim.run <job.json> <out.mp4>

Khung dọc 1080×1920 = 9 × 16 đơn vị Manim. Ghi thêm boxes.json (khung bao chữ theo pixel) cạnh job.json cho QA OCR.
"""

import json
import os
import shutil
import sys


def main(argv):
    job_path, out = argv[0], argv[1]
    with open(job_path, encoding="utf-8") as fh:
        job = json.load(fh)
    work = os.path.dirname(os.path.abspath(job_path))
    media = os.path.join(work, "manim_media")
    shutil.rmtree(media, ignore_errors=True)
    from manim import tempconfig  # noqa: PLC0415

    cfg = {
        "pixel_width": int(job["width"]),
        "pixel_height": int(job["height"]),
        "frame_rate": int(job["fps"]),
        "frame_height": 16.0,
        "frame_width": 16.0 * job["width"] / job["height"],
        "background_color": job["tokens"]["palette"]["bg"],
        "media_dir": media,
        "output_file": "shot",
        "disable_caching": True,
        "verbosity": "ERROR",
        "progress_bar": "none",
        "write_to_movie": True,
        "format": "mp4",
    }
    with tempconfig(cfg):
        from engines.manim import scenes  # noqa: PLC0415

        sc = scenes.Shot(job)
        sc.render()
        src = str(sc.renderer.file_writer.movie_file_path)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    shutil.copyfile(src, out)
    with open(os.path.join(work, "boxes.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sc.boxes, fh, ensure_ascii=False, indent=1)
    shutil.rmtree(media, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
