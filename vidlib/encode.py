"""Tham số encode H.264 dùng chung (AUD-107/301/302/304/305/306): một nơi cho mọi chỗ ghi MP4.

- Màu: chuyển RGB→YUV bằng ma trận BT.709, dải limited (tv), gắn tag bt709 cả trong VUI của x264 lẫn container.
- Khung: yuv420p, High profile, level khoá tường minh, GOP đóng = ½ fps, 2 B-frame (khuyến nghị upload của YouTube).
- Bitrate: CRF + trần maxrate/bufsize (engine board từng ra 40–81 Mb/s).
- Container: +faststart, không edit list.
Cấu hình: config/channel.json → "encode" (mặc định ở DEFAULTS bên dưới).
"""
from .common import channel

DEFAULTS = {
    "master": {"preset": "veryfast", "crf": 18, "maxrate": "16M", "bufsize": "32M", "level": "4.2"},
    "intermediate": {"preset": "veryfast", "crf": 14, "maxrate": None, "bufsize": None, "level": "5.1"},
    "preview": {"preset": "veryfast", "crf": 23, "maxrate": "6M", "bufsize": "12M", "level": "4.2"},
    "audio": {"codec": "aac", "bitrate": "320k", "sample_rate": 48000},
    "gop_sec": 0.5,
    "bframes": 2,
}
VUI = "colorprim=bt709:transfer=bt709:colormatrix=bt709"
TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
RGB_TO_YUV = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"            # rawvideo rgb24/bgr24 → yuv 709
JPEG_TO_YUV = "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p"  # chuỗi JPEG (JFIF full range)
TO_YUV = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"                # nguồn video bất kỳ (tag tự đọc)


def cfg():
    c = (channel().get("encode") or {}) if _has_channel() else {}
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULTS.items()}
    for k, v in c.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def _has_channel():
    try:
        channel()
        return True
    except Exception:  # noqa: BLE001 — engine chạy độc lập (tiến trình con) vẫn có mặc định
        return False


def video_args(kind="master", fps=30, crf=None):
    """Đối số ffmpeg cho luồng video H.264 (đặt sau -i …, trước tên file)."""
    c = cfg()
    k = c[kind]
    gop = max(1, round(fps * float(c.get("gop_sec", 0.5))))
    args = ["-c:v", "libx264", "-preset", k["preset"], "-crf", str(crf if crf is not None else k["crf"]),
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level:v", str(k["level"]),
            "-g", str(gop), "-keyint_min", str(gop), "-bf", str(c.get("bframes", 2)), "-sc_threshold", "0",
            "-x264-params", VUI, *TAGS]
    if k.get("maxrate"):
        args += ["-maxrate", k["maxrate"], "-bufsize", k.get("bufsize") or k["maxrate"]]
    return args


def audio_args():
    a = cfg()["audio"]
    return ["-c:a", a["codec"], "-b:a", a["bitrate"], "-ar", str(a["sample_rate"])]


def mux_args():
    """Container MP4: moov ở đầu (+faststart), không edit list (YouTube: "No Edit Lists")."""
    return ["-movflags", "+faststart", "-use_editlist", "0"]
