"""Theo dõi chi phí mỗi video (AUD-801): work/cost.json = danh sách sự kiện + tổng hợp.

Sự kiện: tts (ký tự ElevenLabs, có/không cache), llm (token vào/ra), render (giây theo engine), flow (lượt tạo, nhập tay
qua UI/CLI). Giá ở config/costs.json — đơn giá ElevenLabs phụ thuộc gói (chưa xác nhận → null: chỉ hiện ký tự/credit).
"""
import datetime
import os

from .common import CONFIG_DIR, load_json, save_json


def prices():
    return load_json(os.path.join(CONFIG_DIR, "costs.json"), {})


def path(proj):
    return os.path.join(proj, "work", "cost.json")


def record(proj, kind, **fields):
    if not proj:
        return
    os.makedirs(os.path.join(proj, "work"), exist_ok=True)
    d = load_json(path(proj), {"events": []})
    d.setdefault("events", []).append({"t": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                                       "kind": kind, **fields})
    d["summary"] = summarize(d["events"])
    save_json(path(proj), d)


def summarize(events):
    p = prices()
    el = p.get("elevenlabs") or {}
    llm = p.get("llm") or {}
    s = {"tts_chars": 0, "tts_calls": 0, "tts_cached": 0, "llm_in": 0, "llm_out": 0, "render_sec": {}, "flow_gens": 0}
    usd, unknown = 0.0, []
    for e in events:
        k = e.get("kind")
        if k == "tts":
            if e.get("cached"):
                s["tts_cached"] += 1
                continue
            s["tts_calls"] += 1
            s["tts_chars"] += int(e.get("chars") or 0)
        elif k == "llm":
            s["llm_in"] += int(e.get("tokens_in") or 0)
            s["llm_out"] += int(e.get("tokens_out") or 0)
            m = llm.get(e.get("model") or "", {})
            if m:
                usd += s_llm(e, m)
            else:
                unknown.append(f"giá model {e.get('model')}")
        elif k == "render":
            eng = e.get("engine", "?")
            s["render_sec"][eng] = round(s["render_sec"].get(eng, 0) + float(e.get("sec") or 0), 1)
        elif k == "flow":
            s["flow_gens"] += int(e.get("gens") or 0)
    if s["tts_chars"]:
        per1k = el.get("usd_per_1k_chars")
        if per1k is None:
            unknown.append("đơn giá ElevenLabs (theo gói — rights/ledger.json → decisions.elevenlabs_plan)")
        else:
            usd += s["tts_chars"] / 1000 * float(per1k)
    s["credits_elevenlabs"] = s["tts_chars"] * float(el.get("credits_per_char", 1))
    s["usd_known"] = round(usd, 4)
    s["usd_unknown"] = sorted(set(unknown))
    return s


def s_llm(e, m):
    return (int(e.get("tokens_in") or 0) * float(m.get("in_per_m", 0)) + int(e.get("tokens_out") or 0)
            * float(m.get("out_per_m", 0))) / 1e6


def summary(proj):
    return load_json(path(proj), {}).get("summary") or summarize([])
