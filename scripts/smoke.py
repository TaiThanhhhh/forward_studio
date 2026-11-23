"""Kiểm tra khói (smoke test) toàn pipeline — mọi đường dựng, chế độ --dry-run (clip/giọng/nhạc giả, không tốn credit).

  python scripts/smoke.py [tên …]       (mặc định: tất cả)   → qa/smoke.md

Mỗi ca là một dự án `projects/_smoke-<tên>/` dựng từ một storyboard nhỏ (nằm trong mã dưới đây, không phải video thật):
  flowday  — style Flow (chalk): shot Flow + cảnh three.js `stage` + beat motion html (graph, counter) theo look của chalk
  board    — evidence board (board-black, board_spine): thẻ Flow + DOC_FOCUS + NUMBER_CARD + thẻ motion html được ghim
  three    — style toàn code three.js (toon3d-lab)
  manim    — physics-diagram-black: graph/vectors/equation (Manim) + drop (beat html dự phòng)
  html     — một style motion html (hud-black) với đạo cụ tự ghép (parts)
Ghi kết quả từng ca: exit code, stage cuối, QA (ĐẠT/CẦN XEM), thời lượng, engine đã dùng.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vidlib.common import save_json  # noqa: E402

T = "What happens if you test every part of this tool at once?"


def shot(sid, beat, sec, vo, **kw):
    return {"id": sid, "beat": beat, "target_sec": sec, "vo": vo, **kw}


def code(scene, **params):
    return {"mode": "code", "code": {"scene": scene, "params": params}}


FLOW = {
    "start_frame": {"desc": "a glass of ice water on a lab bench, a red-hot steel ball hanging above it"},
    "subject": "steel ball",
    "action": [{"t": [0, 2], "do": "the steel ball drops into the glass"}],
}

CASES = {
    "flowday": {
        "style": "chalk",
        "shots": [
            shot("C01", "hook", 2.4, "[excited] A red-hot ball drops into ice water, and nothing touches it.", **FLOW),
            shot(
                "C02",
                "setup",
                2.6,
                "Here's how fast it cools down in the first ten seconds.",
                **code(
                    "graph",
                    title="Cooling curve",
                    x_label="seconds",
                    y_unit="°C",
                    points=[[0, 1000], [3, 300], [10, 40]],
                    y_min=0,
                ),
            ),
            shot(
                "C03",
                "escalate",
                2.4,
                "The surface reaches a thousand degrees.",
                **code("counter", title="Surface", to=1000, suffix="°C", icon="thermometer"),
            ),
            shot("C04", "twist", 2.4, "[dramatically] The twist: the water barely warms up.", **FLOW),
        ],
    },
    "board": {
        "style": "board-black",
        "assembly": "auto",
        "shots": [
            shot(
                "C01", "hook", 2.6, "[excited] A teenager stayed awake for eleven days.", beat_recipe="REVEAL_PHOTO", **FLOW
            ),
            shot(
                "C02",
                "setup",
                2.6,
                "Doctors wrote down every symptom.",
                beat_recipe="DOC_FOCUS",
                board={
                    "lines": ["CASE FILE — 1964", "Day 4: hallucinations", "Day 11: blank stare"],
                    "circle": "hallucinations",
                },
            ),
            shot(
                "C03",
                "escalate",
                2.4,
                "Two hundred sixty-four hours in total.",
                beat_recipe="NUMBER_CARD",
                board={"number": "264 h", "from": 0, "caption": "HOURS AWAKE"},
            ),
            shot(
                "C04",
                "payoff",
                2.6,
                "His brain kept taking tiny naps.",
                **code(
                    "callout", title="Microsleeps", icon="brain", labels=[{"text": "Seconds long"}, {"text": "Eyes open"}]
                ),
            ),
            shot(
                "C05",
                "twist",
                2.6,
                "[dramatically] Then he slept fourteen hours and was fine.",
                beat_recipe="THESIS",
                board={"old": "No sleep breaks you forever.", "new": "He recovered in one night"},
            ),
        ],
    },
    "three": {
        "style": "toon3d-lab",
        "shots": [
            shot(
                "C01",
                "hook",
                2.6,
                "[excited] In a vacuum, a feather falls like a bowling ball.",
                **code("vacuum", beat="air"),
            ),
            shot(
                "C02", "escalate", 2.6, "Pump the air out, and both hit the floor together.", **code("vacuum", beat="pump")
            ),
            shot(
                "C03",
                "twist",
                2.4,
                "[dramatically] The twist: gravity never cared about weight.",
                **code("counter", title="Fall time", to=1.4, decimals=1, suffix=" s", icon="clock"),
            ),
        ],
    },
    "manim": {
        "style": "physics-diagram-black",
        "shots": [
            shot(
                "C01",
                "hook",
                2.6,
                "[excited] A steel ball loses most of its heat in seconds.",
                **code(
                    "graph",
                    title="Cooling",
                    x_label="seconds",
                    y_label="°C",
                    y_unit="°C",
                    points=[[0, 1000], [2, 330], [10, 20]],
                    marks=[{"x": 2, "label": "steam collapses"}],
                ),
            ),
            shot(
                "C02",
                "setup",
                2.6,
                "Two forces fight over it: weight and the steam cushion.",
                **code(
                    "vectors",
                    title="Forces",
                    object={"label": "ball", "role": "hot"},
                    vectors=[
                        {"label": "weight", "dir": [0, -1], "mag": 1, "role": "hot"},
                        {"label": "steam", "dir": [0, 1], "mag": 0.8, "role": "cold"},
                    ],
                ),
            ),
            shot(
                "C03",
                "escalate",
                2.6,
                "Heat lost equals mass times heat capacity times the drop.",
                **code(
                    "equation",
                    title="Heat",
                    lines=[{"text": "Q = m·c·ΔT"}, {"text": "Q ≈ 0.1 × 450 × 980"}],
                    result="Q ≈ 44 kJ",
                ),
            ),
            shot(
                "C04",
                "twist",
                2.4,
                "[dramatically] And the ice still stays at zero.",
                **code(
                    "drop",
                    title="Drop",
                    a={"icon": "ball", "role": "hot"},
                    b={"icon": "glass", "label": "ice water"},
                    result="Still 0°C",
                ),
            ),
        ],
    },
    "html": {
        "style": "hud-black",
        "shots": [
            shot(
                "C01",
                "hook",
                2.4,
                "[excited] An astronaut's heart changes shape in space.",
                **code("title", title="Heart in orbit", icon="heart", icon_role="hot", sub="It gets rounder"),
            ),
            shot(
                "C02",
                "escalate",
                2.6,
                "Six months on the station made it nine percent rounder.",
                **code(
                    "compare",
                    title="Heart shape",
                    left={"icon": "earth", "label": "On Earth", "value": 100, "unit": "%"},
                    right={
                        "icon": {
                            "parts": [
                                {"k": "circle", "x": 0, "y": 0, "r": 0.7, "role": "hot"},
                                {"k": "rect", "x": -0.1, "y": -0.95, "w": 0.2, "h": 0.3, "role": "ink"},
                            ]
                        },
                        "label": "In orbit",
                        "value": 109,
                        "unit": "%",
                    },
                ),
            ),
            shot(
                "C03",
                "twist",
                2.4,
                "[dramatically] Back on Earth, it slowly returns to normal.",
                **code("fact", kicker="the twist", text="It changes back", em="In months", icon="satellite"),
            ),
        ],
    },
}


def make(name, case):
    proj = os.path.join(ROOT, "projects", f"_smoke-{name}")
    shutil.rmtree(proj, ignore_errors=True)
    os.makedirs(proj)
    with open(os.path.join(proj, "idea.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(T + "\n")
    sb = {
        "topic": T,
        "title": T,
        "hook": "test",
        "truth": "True",
        "language": "en",
        "voice": "auto",
        "outro": {"teaser": "Next test?", "enabled": True},
        "thumbnail": {"variants": [{"id": "T1", "archetype": "vs", "text": "TEST?!", "scene": "a lab bench"}]},
        **{k: v for k, v in case.items()},
    }
    save_json(os.path.join(proj, "storyboard.json"), sb)
    return proj


def run(name, proj):
    t0 = time.time()
    pr = subprocess.run(
        [sys.executable, "studio.py", "video", proj, "--dry-run", "--yes", "--look-ok"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    out = pr.stdout + pr.stderr
    stage = (re.findall(r"::stage=(\w+)", out) or ["?"])[-1]
    rep = os.path.join(proj, "qa", "report.md")
    verdict = dur = "—"
    if os.path.exists(rep):
        head = open(rep, encoding="utf-8").read()
        m = re.search(r"(?:Kết quả|Cổng QA): \*\*([^*]+)\*\*.*?thời lượng ([\d.]+)s", head)  # báo cáo vòng 9 đổi nhãn
        if m:
            verdict, dur = m.group(1), m.group(2)
    engines = set()
    cd = os.path.join(proj, "work", "code")
    if os.path.isdir(cd):
        for sid in os.listdir(cd):
            jp = os.path.join(cd, sid, "job.json")
            if os.path.exists(jp):
                with open(jp, encoding="utf-8") as fh:
                    engines.add(json.load(fh).get("engine") or "three")
    if os.path.isdir(os.path.join(proj, "work", "board")):
        engines.add("board")
    tail = [ln for ln in out.splitlines() if ln.strip().startswith(("✖", "⚠", "Traceback")) or "Error" in ln][-6:]
    return {
        "case": name,
        "exit": pr.returncode,
        "stage": stage,
        "qa": verdict,
        "sec": dur,
        "engines": sorted(engines),
        "wall": round(time.time() - t0, 1),
        "notes": tail,
    }


def main(argv):
    names = argv or list(CASES)
    rows = []
    for n in names:
        proj = make(n, CASES[n])
        r = run(n, proj)
        rows.append(r)
        print(
            f"{n:<8} exit {r['exit']} · {r['stage']} · QA {r['qa']} · {r['sec']}s · {'+'.join(r['engines'])} · {r['wall']}s",
            flush=True,
        )
    L = [
        "# Smoke test — mọi đường dựng (dry-run)",
        "",
        "| Ca | Exit | Stage cuối | QA | Dài (s) | Engine | Thời gian chạy (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    L += [
        f"| {r['case']} | {r['exit']} | {r['stage']} | {r['qa']} | {r['sec']} | {'+'.join(r['engines'])} | {r['wall']} |"
        for r in rows
    ]
    for r in rows:
        if r["notes"]:
            L += ["", f"**{r['case']}**:"] + [f"- `{x.strip()[:200]}`" for x in r["notes"]]
    with open(os.path.join(ROOT, "qa", "smoke.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    return 0 if all(r["exit"] == 0 and r["stage"] == "done" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
