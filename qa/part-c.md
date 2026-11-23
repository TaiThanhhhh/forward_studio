# Phần C — kiểm chứng gói xuất + tái lập (đo độc lập, 2026-11-16 01:42)

## e2e-classic-flat-vector

| Preset | Kết quả | khung | fps CFR | codec | pix_fmt | màu | faststart | audio | loudness | true peak | thời lượng | dung lượng |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| instagram_reels | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 255 kb/s | -14.0 LUFS | -1.8 dBTP | 19.3s | 6.3 MB |
| tiktok | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 255 kb/s | -14.0 LUFS | -1.8 dBTP | 19.3s | 6.3 MB | 2622 kb/s |
| youtube_shorts | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 255 kb/s | -14.0 LUFS | -1.8 dBTP | 19.3s | 6.3 MB |

## atlas-glass-test-what-happens-if-you-drop-a-1

| Preset | Kết quả | khung | fps CFR | codec | pix_fmt | màu | faststart | audio | loudness | true peak | thời lượng | dung lượng |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| instagram_reels | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 243 kb/s | -13.8 LUFS | -3.2 dBTP | 17.3s | 11.8 MB |
| tiktok | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 243 kb/s | -13.8 LUFS | -3.2 dBTP | 17.3s | 11.8 MB | 5461 kb/s |
| youtube_shorts | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 243 kb/s | -13.8 LUFS | -3.2 dBTP | 17.3s | 11.8 MB |

## atlas-xray-test-what-happens-if-you-drop-a-1

| Preset | Kết quả | khung | fps CFR | codec | pix_fmt | màu | faststart | audio | loudness | true peak | thời lượng | dung lượng |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| instagram_reels | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 244 kb/s | -13.8 LUFS | -2.8 dBTP | 17.3s | 16.7 MB |
| tiktok | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 244 kb/s | -13.8 LUFS | -2.8 dBTP | 17.3s | 16.7 MB | 7695 kb/s |
| youtube_shorts | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 244 kb/s | -13.8 LUFS | -2.8 dBTP | 17.3s | 16.7 MB |

## atlas-swarm-test-what-happens-if-you-drop-a-1

| Preset | Kết quả | khung | fps CFR | codec | pix_fmt | màu | faststart | audio | loudness | true peak | thời lượng | dung lượng |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| instagram_reels | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 257 kb/s | -13.9 LUFS | -1.7 dBTP | 16.9s | 7.0 MB |
| tiktok | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 257 kb/s | -13.9 LUFS | -1.7 dBTP | 16.9s | 7.0 MB | 3305 kb/s |
| youtube_shorts | ĐẠT | 1080x1920 | 30/1 / 30/1 | h264 High L42 + aac | yuv420p | bt709/bt709/bt709 tv | moov đầu | 48000 Hz 257 kb/s | -13.9 LUFS | -1.7 dBTP | 16.9s | 7.0 MB |

## Tái lập (cùng đầu vào, dựng lại 2 lần)

- dự án `atlas-swarm-test-what-happens-if-you-drop-a-1` · exit [0, 0] · [26, 31] s
- sha256 final.mp4 giống hệt: **True** · pHash lệch tối đa 0 bit trên 17 mốc 1 s (0 = giống hệt)

## Ngắt giữa lúc render → chạy lại (RESUME)

- shot `C02` (55 frame): xoá frame → bắt đầu `rerender` → ngắt cả cây tiến trình khi đã có 3 frame (3 sau 2 s)
- chạy lại `video --from code`: chỉ dựng **52** frame còn thiếu (= 55 − 3) · đủ 55/55 · exit 0 · 33 s → **ĐẠT**

_Ghi chú: 2 lần đo RESUME trước đó (01:36, 01:39) không hợp lệ — đếm phải frame cũ trước khi `rerender` kịp xoá, rồi ngắt khi shot đã dựng xong (~50 frame/giây ở chế độ chạy thử). Script đã sửa: tự xoá frame trước, ngắt ngay khi có frame đầu tiên, đo lại 2 s sau để chắc không còn worker sót._

