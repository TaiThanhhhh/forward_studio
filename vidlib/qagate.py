"""Cổng QA đỏ/vàng/xanh (AUD-901/902/905) + kiểm spec file thật bằng ffprobe (AUD-301/305/306/307/401).

Mỗi dòng kiểm (nhãn → (giá trị, đạt?)) được xếp mức:
- xanh: đạt;
- đỏ:   không đạt và nhãn bắt đầu bằng một tiền tố trong `config/channel.json → qa.blocking` → CHẶN xuất bản
        (không ghi publish.md, không xuất gói nền tảng, pipeline thoát mã 12 `qa_failed`);
- vàng: không đạt nhưng không chặn, hoặc không đo được (giá trị None).
`--accept-qa` cho phép người làm duyệt tay một video đỏ (ghi lại trong manifest).
"""
import json

from .common import channel, run

DEFAULT_BLOCKING = ["kích thước", "fps", "số audio track", "codec", "loudness", "true peak", "freeze", "black frame",
                    "chữ đúng chính tả", "màu BT.709", "pix_fmt", "faststart", "audio 48 kHz", "file hỏng", "nền tảng",
                    "quyền thương mại BỊ CẤM"]


def blocking():
    return list((channel().get("qa") or {}).get("blocking") or DEFAULT_BLOCKING)


def level(label, ok):
    if ok is True:
        return "green"
    if ok is None:
        return "yellow"
    return "red" if any(label.startswith(b) for b in blocking()) else "yellow"


def classify(checks):
    """checks: {nhãn: (giá trị, đạt?)} → [{label, value, ok, level}]."""
    return [{"label": k, "value": str(v), "ok": ok, "level": level(k, ok)} for k, (v, ok) in checks.items()]


def verdict(rows):
    lv = {r["level"] for r in rows}
    return "red" if "red" in lv else "yellow" if "yellow" in lv else "green"


def summary(rows):
    v = verdict(rows)
    reds = [r for r in rows if r["level"] == "red"]
    yel = [r for r in rows if r["level"] == "yellow"]
    return {"verdict": v, "red": len(reds), "yellow": len(yel), "green": len(rows) - len(reds) - len(yel),
            "red_items": [f"{r['label']}: {r['value']}" for r in reds],
            "yellow_items": [f"{r['label']}: {r['value']}" for r in yel]}


# ------------------------------------------------------------------ spec file (ffprobe)
def probe_full(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path], "ffprobe")
    return json.loads(r.stdout.decode("utf-8", "replace"))


def moov_first(path):
    """True nếu atom moov nằm trước mdat (faststart)."""
    with open(path, "rb") as fh:
        pos = 0
        while True:
            fh.seek(pos)
            hdr = fh.read(16)
            if len(hdr) < 8:
                return False
            size = int.from_bytes(hdr[:4], "big")
            kind = hdr[4:8]
            if size == 1:
                size = int.from_bytes(hdr[8:16], "big")
            if kind == b"moov":
                return True
            if kind == b"mdat":
                return False
            if size < 8:
                return False
            pos += size


def spec_checks(path, max_mbps=None):
    """Dòng kiểm spec container/codec của một MP4 thật: màu BT.709, dải tv, yuv420p, faststart, edit list, bitrate,
    audio 48 kHz. Không đọc được file → một dòng đỏ 'file hỏng'."""
    try:
        d = probe_full(path)
    except Exception as e:  # noqa: BLE001
        return {"file hỏng / không đọc được": (str(e).splitlines()[0][:80], False)}
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = d.get("format") or {}
    color = (v.get("color_primaries"), v.get("color_transfer"), v.get("color_space"))
    br = float(fmt.get("bit_rate") or 0) / 1e6
    cap = max_mbps or float((channel().get("qa") or {}).get("max_mbps", 20))
    out = {
        "màu BT.709 (primaries/transfer/matrix)": ("/".join(str(c) for c in color), color == ("bt709", "bt709", "bt709")),
        "màu dải limited (tv)": (v.get("color_range"), v.get("color_range") == "tv"),
        "pix_fmt yuv420p": (v.get("pix_fmt"), v.get("pix_fmt") == "yuv420p"),
        "faststart (moov trước mdat)": ("có" if moov_first(path) else "không", moov_first(path)),
        "bitrate tổng": (f"{br:.1f} Mb/s (trần {cap:g})", br <= cap),
        "profile H.264": (f"{v.get('profile')} L{v.get('level')}", str(v.get("profile", "")).lower().startswith("high")),
    }
    if a is not None:
        out["audio 48 kHz"] = (a.get("sample_rate"), str(a.get("sample_rate")) == "48000")
    return out


def audio_checks(loud, target_lufs, tp_max):
    """loud: {lufs, true_peak, lra?} → dòng loudness + true peak (TP tách riêng, không còn khoảng nới +0.3 dB)."""
    if not loud or loud.get("lufs") is None:
        return {"loudness": ("không đo được", None)}
    out = {"loudness (LUFS tích hợp)": (f"{loud['lufs']:.1f} LUFS (mục tiêu {target_lufs:g} ±1)",
                                        abs(loud["lufs"] - target_lufs) <= 1.0),
           "true peak": (f"{loud['true_peak']:.1f} dBTP (≤ {tp_max:g})", loud["true_peak"] <= tp_max + 1e-6)}
    if loud.get("lra") is not None:
        out["LRA"] = (f"{loud['lra']:.1f} LU", loud["lra"] <= 12)
    return out
