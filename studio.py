"""STUDIO — pipeline short thí nghiệm "what happens if…" (kênh tiếng Anh, 2D nền đen) với Google Flow + engine code.

MỘT LỆNH:
  python studio.py video "<ý tưởng>"          tạo dự án → storyboard → scripts.html → (chờ clip) → final.mp4
  python studio.py video <slug>               chạy tiếp dự án (tự nhận biết stage)
  Flags: --dry-run  --from <stage>  --only <stage>  --model "<model Flow>"  --ai claude|gemini  --yes  --no-open
         --look-ok (đã xem contact sheet, render đầy đủ)  --tts-force (tạo lại giọng ElevenLabs)

Ý tưởng:
  python studio.py ideas "<chủ đề>"           10 ý tưởng (title/hook/twist/visual/True-Disputed-Hypothetical)
  python studio.py ideas <slug> --pick 3      tạo dự án cho ý tưởng 3 rồi chạy video   (--auto-pick: điểm cao nhất)

Giao diện web (không cần gõ lệnh):
  python studio.py ui [--port 8765] [--no-open]   mở http://127.0.0.1:8765 — tạo video, tải clip, duyệt look, xem QA

Khác:
  python studio.py status <slug>     trạng thái từng cảnh
  python studio.py models            bảng capability Flow (config/flow-models.json)
  python studio.py stages            danh sách stage
  python studio.py styles            thư viện style + 3 video gần nhất (chống lặp)
  python studio.py narratives ["<chủ đề>"]   10 dạng kịch bản (đếm ngược, theo đồng hồ, myth vs fact…) + điểm hợp chủ đề
  python studio.py svg <file.svg> [--name n] [--role auto|ink|hot|cold|accent] [--license "…"]
                                     nhập icon SVG (SVGO) → assets/user/svg/<n>.json; dùng "icon": "svg:<n>"
  python studio.py assets [search <từ> [--svg] | fetch [svg] | sheet [gói…] | check]
                                     kho thư viện: mô hình 3D CC0 ("type": "model:<tên>") + icon SVG ("svg:<tên>")
  python studio.py sb check|import|patch|history|restore|preview <slug> …   sửa storyboard.json CÓ KIỂM (không mở
                                     file tay): dán JSON của AI, --set code.params.to=157, hoàn tác, xem trước 1 frame
  python studio.py ideas import <lô> <file|->   dán 10 ý tưởng (kiểm trước khi ghi ideas/<lô>/ideas.json)
  python studio.py charsheet [style] character test sheet → docs/charsheet_<style>.jpg
  python studio.py perf [frames]     benchmark engine three.js (s/frame theo số worker) → docs/PERF.md
  python studio.py perf board [board.json]   benchmark engine board (1/4/8/12 tiến trình) → docs/PERF.md
  python -m engines.board.render <board.json> insert <id> <out.mp4> [--sec 4]   đoạn phim câm đứng riêng

Lệnh cũ (wrapper mỏng gọi pipeline mới): new, prompts, preview, build, cover.
Trong Claude Code: /video "<ý tưởng>".
"""
import argparse
import os
import sys

if sys.platform == "win32":  # in tiếng Việt trên Windows
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

from vidlib import pipeline  # noqa: E402
from vidlib.common import StudioError, ffbin  # noqa: E402

LEGACY = {  # lệnh cũ → tham số của `video`
    "new": [],
    "prompts": ["--only", "page"],
    "preview": ["--only", "preview"],
    "build": [],
    "cover": ["--only", "thumbnails"],
}


def video_parser(prog="video"):
    ap = argparse.ArgumentParser(prog=f"studio.py {prog}", description="Pipeline một lệnh")
    ap.add_argument("target", help="ý tưởng (dự án mới) hoặc slug dự án có sẵn")
    ap.add_argument("--from", dest="frm", metavar="STAGE", help="làm lại từ stage này")
    ap.add_argument("--only", metavar="STAGE", help="chỉ chạy stage này (vd thumbnail, page, preview, render)")
    ap.add_argument("--dry-run", action="store_true", help="dùng clip/lời đọc/nhạc GIẢ cho phần còn thiếu")
    ap.add_argument("--model", help='model video Flow, vd "Veo 3.1 Lite" (xem: studio.py models)')
    ap.add_argument("--ai", choices=["claude", "gemini"], help="nhờ API viết storyboard (cần API key)")
    ap.add_argument("--yes", action="store_true", help="tự xác nhận bảng map clip")
    ap.add_argument("--no-open", action="store_true", help="không tự mở scripts.html")
    ap.add_argument("--look-ok", action="store_true", help="đã xem contact sheet (look-check) → render đầy đủ")
    ap.add_argument("--tts-force", action="store_true", help="gọi lại ElevenLabs dù lời không đổi")
    ap.add_argument("--style", help="ép style cho video này (xem: studio.py styles); mặc định auto = theo chủ đề")
    ap.add_argument("--voice", help="ép giọng (tên như Brian, hoặc id ElevenLabs; xem: studio.py voices); mặc định auto")
    ap.add_argument("--accept-qa", action="store_true", help="duyệt tay video bị cổng QA chặn (ghi vào manifest)")
    ap.add_argument("--platforms", help="preset xuất (config/delivery.json): youtube_shorts,instagram_reels,tiktok,"
                                        "youtube_16x9 | all | default")
    ap.add_argument("--narrative", help="ép dạng kịch bản (countdown, timeline, myth_fact, versus…; xem: studio.py "
                                        "narratives); mặc định auto = xoay vòng theo chủ đề")
    ap.add_argument("--captions",
                    choices=["studio_clean", "capcut_pop", "capcut_pill", "capcut_box", "vox_highlight", "off"],
                    help="phụ đề burn-in kiểu Studio/CapCut (studio_clean|capcut_pop|capcut_pill|capcut_box|"
                         "vox_highlight|off)")
    fl = ap.add_mutually_exclusive_group()
    fl.add_argument("--flow", dest="flow", action="store_const", const=True,
                    help="hôm nay dùng clip Flow (chỉ chọn style có Flow)")
    fl.add_argument("--no-flow", dest="flow", action="store_const", const=False,
                    help="hôm nay KHÔNG dùng Flow (chỉ chọn style dựng toàn bộ bằng code)")
    return ap


def run_video(argv, prog="video"):
    a = video_parser(prog).parse_args(argv)
    r = pipeline.Run(a.target, frm=a.frm, only=a.only, dry=a.dry_run, model=a.model, ai=a.ai, yes=a.yes,
                     no_open=a.no_open or a.dry_run, look_ok=a.look_ok, tts_force=a.tts_force, style=a.style,
                     voice=a.voice, flow=a.flow, narrative=a.narrative, accept_qa=a.accept_qa, platforms=a.platforms,
                     captions=a.captions)
    return r.run()


def run_review(argv):
    """python studio.py review <slug> [--model gemini-4-hydrogen] — chấm video out/final.mp4 bằng Gemini đa phương thức."""
    from vidlib import aireview  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="studio.py review")
    ap.add_argument("target", help="slug dự án đã có out/final.mp4")
    ap.add_argument("--model", help="model Gemini (mặc định gemini-4-hydrogen)")
    a = ap.parse_args(argv)
    proj, _, new = pipeline.project_for(a.target)
    if new:
        print(f"✖ Không có dự án '{a.target}'.")
        return 1
    res = aireview.review_video(proj, model=a.model)
    return 0 if res.get("verdict") != "REDO" else 12


def run_deliver(argv):
    """python studio.py deliver <slug> [--platforms a,b|all] — xuất lại gói nền tảng từ out/final.mp4 có sẵn."""
    from vidlib import deliver, qagate  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="studio.py deliver")
    ap.add_argument("target")
    ap.add_argument("--platforms")
    a = ap.parse_args(argv)
    proj = pipeline.project_for(a.target)[0]
    res = deliver.build(proj, a.platforms)
    for r in res.values():
        bad = [f"{x['label']}: {x['value']}" for x in r["rows"] if x["level"] != "green"]
        print(f"  {r['label']:<16} {r['verdict']:<6} {r['video']}")
        for b in bad:
            print(f"      · {b}")
    return 1 if any(qagate.verdict(r["rows"]) == "red" for r in res.values()) else 0


def run_project_tool(cmd, argv):
    """versions <slug> · cost <slug> · clean <slug> [--yes] (xoá file trung gian sinh lại được, giữ out/ + nguồn)."""
    import json  # noqa: PLC0415

    from vidlib import cost, manifest  # noqa: PLC0415
    if not argv:
        print(f"Cách dùng: python studio.py {cmd} <slug>")
        return 1
    proj = pipeline.project_for(argv[0])[0]
    if cmd == "versions":
        for v in sorted(os.listdir(manifest.versions_dir(proj))) if os.path.isdir(manifest.versions_dir(proj)) else []:
            m = json.load(open(os.path.join(manifest.versions_dir(proj), v, "manifest.json"), encoding="utf-8"))
            print(f"  {v}  {m['created']}  {m.get('style')}  QA {m.get('qa', {}).get('verdict')}  "
                  f"git {str(m['git'].get('commit'))[:8]}{'*' if m['git'].get('dirty') else ''}")
        return 0
    if cmd == "cost":
        print(json.dumps(cost.summary(proj), ensure_ascii=False, indent=2))
        return 0
    from vidlib import cleanup  # noqa: PLC0415
    if "--all" in argv:
        return cleanup.run_all(apply="--yes" in argv)
    return cleanup.run(proj, apply="--yes" in argv)


def run_rerender(argv):
    """rerender <slug> <SID> [--dry-run] — chỉ dựng lại MỘT shot: xoá frame/clip ingest của shot đó rồi chạy từ stage
    code (RESUME giữ frame các shot khác) → ghép lại video, QA, gói, version mới."""
    import json  # noqa: PLC0415
    import shutil  # noqa: PLC0415

    from vidlib import codeshot, ingest  # noqa: PLC0415
    if len(argv) < 2:
        print("Cách dùng: python studio.py rerender <slug> <C03> [--dry-run]")
        return 1
    proj, _, new = pipeline.project_for(argv[0])
    sid = argv[1].upper()
    if new:
        print(f"✖ Không có dự án '{argv[0]}'.")
        return 1
    gone = []
    for d in (codeshot.frames_dir(proj, sid),):
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
            gone.append(os.path.relpath(d, proj))
    pats = (os.path.join(codeshot.code_dir(proj, sid), "*.mp4"), os.path.join(ingest.ingest_dir(proj), f"{sid}.*"))
    for f in glob_many(*pats):
        os.remove(f)
        gone.append(os.path.relpath(f, proj))
    tp = os.path.join(proj, "work", "trim.json")
    if os.path.exists(tp):
        t = json.load(open(tp, encoding="utf-8"))
        if t.pop(sid, None) is not None:
            from vidlib.common import save_json  # noqa: PLC0415
            save_json(tp, t)
            gone.append(f"work/trim.json → {sid}")
    print(f"▶ rerender · {sid} · xoá {len(gone)} mục: " + ", ".join(gone) if gone
          else f"▶ rerender · {sid} · chưa có gì để xoá")
    r = pipeline.Run(argv[0], frm="code", dry="--dry-run" in argv, yes=True, no_open=True)
    return r.run()


def glob_many(*pats):
    import glob  # noqa: PLC0415
    return [f for p in pats for f in glob.glob(p)]


def run_trim(argv):
    """trim <slug> <SID> --in 0.4 --out 2.1 [--dry-run] | --auto — ghi điểm vào/ra tay (giây trong clip Flow) vào
    storyboard.json → shot.trim rồi dựng lại từ stage trim. --auto bỏ trim tay (về auto-trim)."""
    import argparse  # noqa: PLC0415

    from vidlib import storyboard as sbm  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="studio.py trim")
    ap.add_argument("target")
    ap.add_argument("sid")
    ap.add_argument("--in", dest="t_in", type=float)
    ap.add_argument("--out", dest="t_out", type=float)
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    proj, _, new = pipeline.project_for(a.target)
    if new:
        print(f"✖ Không có dự án '{a.target}'.")
        return 1
    sb = sbm.load(proj)
    shot = next((x for x in sb.get("shots") or [] if x["id"] == a.sid.upper()), None)
    if not shot:
        print(f"✖ Không có shot {a.sid}.")
        return 1
    tr = dict(shot.get("trim") or {})
    if a.auto:
        tr.pop("in", None)
        tr.pop("out", None)
    else:
        if a.t_in is None or a.t_out is None or not 0 <= a.t_in < a.t_out <= 60:
            print("✖ Cần --in < --out (giây trong clip, 0–60).")
            return 1
        tr.update({"in": round(a.t_in, 3), "out": round(a.t_out, 3)})
    shot["trim"] = tr
    sbm.save(proj, sb)
    print(f"▶ trim · {shot['id']} · " + (f"{tr['in']}–{tr['out']}s" if "in" in tr else "auto-trim"))
    return pipeline.Run(a.target, frm="trim", dry=a.dry_run, yes=True, no_open=True).run()


def run_shots(argv):
    """shots <slug> --order C02,C01,… — đổi thứ tự shot trong storyboard.json (nguồn sự thật), giữ nguyên id."""
    from vidlib import storyboard as sbm  # noqa: PLC0415
    if len(argv) < 3 or argv[1] != "--order":
        print("Cách dùng: python studio.py shots <slug> --order C02,C01,C03")
        return 1
    proj, _, new = pipeline.project_for(argv[0])
    if new:
        print(f"✖ Không có dự án '{argv[0]}'.")
        return 1
    sb = sbm.load(proj)
    order = [x.strip().upper() for x in argv[2].split(",") if x.strip()]
    ids = [s["id"] for s in sb.get("shots") or []]
    if sorted(order) != sorted(ids):
        print(f"✖ Thứ tự phải gồm đúng các shot: {', '.join(ids)}")
        return 1
    by = {s["id"]: s for s in sb["shots"]}
    sb["shots"] = [by[i] for i in order]
    sbm.save(proj, sb)
    print(f"✔ storyboard.json · thứ tự mới: {', '.join(order)} — chạy lại video để dựng theo thứ tự này")
    return 0


def run_ideas(argv):
    from vidlib import ideas  # noqa: PLC0415
    if argv and argv[0] == "import":              # ideas import <lô> <file|-> — kiểm rồi ghi ideas.json (vidlib/sbedit)
        from vidlib import sbedit  # noqa: PLC0415
        return sbedit.ideas_cli(argv[1:])
    ap = argparse.ArgumentParser(prog="studio.py ideas", description="10 ý tưởng → chọn → chạy video")
    ap.add_argument("theme", help="chủ đề (lần đầu) hoặc slug lô ý tưởng trong ideas/")
    ap.add_argument("--pick", help="số thứ tự ý tưởng, vd 3 hoặc 3,7")
    ap.add_argument("--auto-pick", action="store_true", help="tự chọn ý tưởng điểm cao nhất")
    a = ap.parse_args(argv)
    return ideas.run(a.theme, a.pick, a.auto_pick, run_video=run_video)


def run_svg(argv):
    """python studio.py svg <file.svg> [--name tên] [--role auto|ink|hot|cold|accent|dim] [--license "nguồn, giấy phép"]"""
    import argparse  # noqa: PLC0415

    from vidlib import userassets  # noqa: PLC0415

    ap = argparse.ArgumentParser(prog="python studio.py svg")
    ap.add_argument("file")
    ap.add_argument("--name")
    ap.add_argument("--role", default="auto")
    ap.add_argument("--license", default="")
    a = ap.parse_args(argv)
    userassets.import_svg(a.file, a.name, a.role, a.license)
    return 0


def run_assets(argv):
    """python studio.py assets [search <từ> [--svg] [--tag t] | fetch [svg] [--discover] | sheet [gói…] | check]"""
    import subprocess  # noqa: PLC0415

    from vidlib import assets3d  # noqa: PLC0415

    sub, rest = (argv[0], argv[1:]) if argv else ("", [])
    if sub == "search":
        svg = "--svg" in rest
        tag = rest[rest.index("--tag") + 1] if "--tag" in rest else None
        q = " ".join(w for i, w in enumerate(rest) if not w.startswith("--") and (i == 0 or rest[i - 1] != "--tag"))
        hits = assets3d.search(q, limit=25, tag=tag, kind="svg" if svg else "3d")
        if not svg:
            n, _ = assets3d.lookup(q)
            print(f'"model:{q}" → {n or "(không có)"}')
        for sc, n, e in hits:
            extra = "" if svg else f"{e['group']:<9} h {e['h']:<6} " + (f"anim {len(e['anims'])}" if e.get("anims") else "")
            print(f"  {sc:>5}  {('svg:' if svg else 'model:') + n:<34} {extra}  [{e['pack']}]")
        return 0
    if sub == "fetch":
        args = ["svg"] + [a for a in rest if a != "svg"] if "svg" in rest else rest
        return subprocess.call([sys.executable, os.path.join("scripts", "assets_fetch.py"), *args])
    if sub == "sheet":
        return subprocess.call([sys.executable, os.path.join("scripts", "assets_sheet.py"), *rest])
    if sub == "check":
        probs = assets3d.check()
        for lv, msg in probs:
            print(("✖ " if lv == "err" else "⚠ ") + msg)
        s = assets3d.summary()
        bad = sum(1 for lv, _ in probs if lv == "err")
        print(
            f"{'✖' if bad else '✔'} kho: {s['models']} mô hình 3D ({s['animated']} có animation, "
            f"{s['bytes'] / 1e6:.1f} MB) · {s['svg']} icon SVG · nhóm: "
            + ", ".join(f"{k} {v}" for k, v in s["groups"].items())
        )
        return 1 if bad else 0
    print(run_assets.__doc__)
    s = assets3d.summary()
    print(f"kho: {s['models']} mô hình 3D ({s['animated']} có animation) · {s['svg']} icon SVG")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "doctor":
            from vidlib import doctor  # noqa: PLC0415
            return doctor.run(browser="--no-browser" not in rest)
        if cmd == "ui":
            from ui.server.__main__ import main as ui_main  # noqa: PLC0415
            return ui_main(rest)
        ffbin("ffmpeg")
        if cmd == "deliver":
            return run_deliver(rest)
        if cmd == "review":
            return run_review(rest)
        if cmd in ("versions", "cost", "clean"):
            return run_project_tool(cmd, rest)
        if cmd == "rerender":
            return run_rerender(rest)
        if cmd == "shots":
            return run_shots(rest)
        if cmd == "trim":
            return run_trim(rest)
        if cmd == "video":
            return run_video(rest)
        if cmd == "status":
            pipeline.status(rest[0] if rest else "")
            return 0
        if cmd == "models":
            pipeline.list_models()
            return 0
        if cmd == "svg":
            return run_svg(rest)
        if cmd == "assets":
            return run_assets(rest)
        if cmd == "stages":
            print(" → ".join(pipeline.STAGES))
            return 0
        if cmd == "ideas":
            return run_ideas(rest)
        if cmd == "sb":                            # sửa storyboard có kiểm (UI gọi qua danh sách trắng job)
            from vidlib import sbedit  # noqa: PLC0415
            return sbedit.cli(rest)
        if cmd == "voices":
            from vidlib import voices  # noqa: PLC0415
            style = rest[1] if len(rest) > 1 and rest[0] == "--for" else None
            used = {vid: slug for _, slug, vid in reversed(voices.history())}
            print("  Kho giọng (config/voice.json → pools.en)" + (f" · xếp theo style {style}" if style else "") + ":")
            rows = voices.ranked(style) if style else [(v, 0, "") for v in voices.pool(include_manual=True)]
            for v, sc, _why in rows:
                tag = "" if v.get("auto", True) else " [chỉ chọn tay]"
                tags = ", ".join(v.get("tags", []))[:52]
                print(f"  {voices.short(v):<8} {v.get('gender', ''):<7} {v.get('accent', ''):<10} {tags:<52}{tag}"
                      + (f"  · dùng gần nhất: {used[v['id']]}" if v["id"] in used else "")
                      + (f"  · {sc:g} điểm" if style else ""))
            print("  Video gần nhất:", ", ".join(f"{slug} ({voices.short(voices.find(vid) or {'id': vid})})"
                                                for _, slug, vid in voices.history()[:5]) or "—")
            return 0
        if cmd == "styles":
            from vidlib import styles  # noqa: PLC0415
            if rest and rest[0] == "--plan":
                import json  # noqa: PLC0415

                from vidlib import voices  # noqa: PLC0415
                flow = True if "--flow" in rest else False if "--no-flow" in rest else None
                topic = " ".join(x for x in rest[1:] if not x.startswith("--"))
                pl = styles.plan(topic, flow=flow)
                v, why = voices.resolve({"voice": "auto", "style_resolved": pl["style"], "language": "en"}, None)
                pl["voice"] = voices.short(v) if v else None
                pl["voice_reason"] = why
                from vidlib import narratives  # noqa: PLC0415
                pl.update(narratives.plan(topic))
                print(json.dumps(pl, ensure_ascii=False, indent=2))
                return 0
            if rest and rest[0] == "--cards":
                for p in styles.write_cards():
                    print("  " + os.path.relpath(p))
                return 0
            if rest and rest[0] == "--gallery":
                from vidlib import enginebench  # noqa: PLC0415
                print(enginebench.styles_gallery())
                return 0
            if rest and rest[0] == "--rank":
                for s, sc in styles.ranked({"topic": " ".join(rest[1:])}):
                    print(f"  {sc:>2}  {s}")
                return 0
            for s in styles.available():
                i = styles.info(s)
                tag = f"[{i['engine']}] "
                print(f"  {s:<19} {tag}{i['description'][:90]}")
            print("  3 video gần nhất:", ", ".join(f"{slug} ({st})" for _, slug, st in styles.history()[:3]) or "—")
            return 0
        if cmd == "narratives":
            from vidlib import narratives  # noqa: PLC0415
            topic = " ".join(rest)
            used = {}
            for _, slug, nid in reversed(narratives.history()):
                used[nid] = slug
            rows = {r[0]: r for r in narratives.ranked(topic)} if topic else {}
            print("  Dạng kịch bản (config/narratives.json)" + (f" · xếp theo: {topic}" if topic else "") + ":")
            for nid in ([r[0] for r in narratives.ranked(topic)] if topic else narratives.ids()):
                d = narratives.get(nid)
                print(f"  {nid:<15} {d['name']:<45}"
                      + (f" {rows[nid][1]:4.1f} điểm" if nid in rows else "")
                      + (f"  · dùng gần nhất: {used[nid]}" if nid in used else ""))
            rec = narratives.recent()
            print("  Tránh lặp (gần nhất):", ", ".join(rec) or "—")
            return 0
        if cmd == "charsheet":
            from vidlib import tools  # noqa: PLC0415
            print(tools.charsheet(rest[0] if rest else "forward"))
            return 0
        if cmd == "perf":
            from vidlib import tools  # noqa: PLC0415
            if rest and rest[0] == "engines":
                from vidlib import enginebench  # noqa: PLC0415
                print(enginebench.perf_engines(int(rest[1]) if len(rest) > 1 else 90))
            elif rest and rest[0] == "board":
                print(tools.perf_board(rest[1] if len(rest) > 1 else None))
            else:
                print(tools.perf(int(rest[0]) if rest else 48))
            return 0
        if cmd in LEGACY:
            if not rest:
                print(f"Cách dùng: python studio.py {cmd} <ý tưởng|slug>  (= video … {' '.join(LEGACY[cmd])})")
                return 1
            print(f"(lệnh cũ '{cmd}' → video {' '.join(LEGACY[cmd])})")
            return run_video([rest[0], *LEGACY[cmd], *rest[1:]], cmd)
        # cho phép gõ thẳng ý tưởng: python studio.py "What happens if…" — nhưng MỘT từ không dấu cách mà không phải
        # dự án có sẵn thì là lệnh gõ sai (vd "stauts") → báo lỗi, không tạo dự án rác (AUD-112)
        if len(argv) == 1 and " " not in cmd and pipeline.project_for(cmd)[2]:
            import difflib  # noqa: PLC0415
            cmds = ["video", "ui", "doctor", "deliver", "versions", "cost", "clean", "status", "models", "stages", "ideas",
                    "voices", "styles", "narratives", "charsheet", "perf", "sb", *LEGACY]
            near = difflib.get_close_matches(cmd, cmds, n=3)
            print(f"✖ Không có lệnh '{cmd}'" + (f" — ý anh là: {', '.join(near)}?" if near else "")
                  + " · Ý tưởng video cần có dấu cách (vd \"What happens if…\"). Xem: python studio.py help")
            return 2
        return run_video(argv)
    except StudioError as ex:
        print(f"✖ {ex}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
