# Smoke test — mọi đường dựng (dry-run)

| Ca | Exit | Stage cuối | QA | Dài (s) | Engine | Thời gian chạy (s) |
|---|---|---|---|---|---|---|
| flowday | 0 | done | XANH | 11.67 | html+three | 134.2 |
| board | 0 | done | XANH | 11.60 | board+html | 124.6 |
| three | 0 | done | XANH | 9.27 | html+three | 132.7 |
| manim | 0 | done | XANH | 11.67 | html+manim | 150.1 |
| html | 0 | done | XANH | 8.90 | html | 146.4 |

**flowday**:
- `⚠ [nhịp] Lời 36 từ ≈ 10s ở 3.7 từ/giây — ngắn hơn 30s (20s ≈ 75 từ, 30s ≈ 110, 45s ≈ 165).`
- `⚠ [kịch bản] Thiếu beat 'payoff'.`
- `⚠ [thumbnail] Có 1 biến thể — nên 3–5.`
- `⚠ [T1] Chữ thumbnail lặp lại tiêu đề — nên bổ sung, không lặp.`
- `⚠ KHÔNG có timestamp ElevenLabs/whisper → đang chạy chế độ CĂN THEO KHOẢNG LẶNG (sai số ~1–3 frame mỗi từ). Nên tạo VO bằng ElevenLabs (có timestamp) hoặc cài faster-whisper.`
- `⚠ publish: cần 3 phương án tiêu đề (có 1).`

**board**:
- `⚠ [C04] Lời thưa 2.3 từ/giây trên 2.6s hình — VO sẽ co các shot lại.`
- `⚠ [nhịp] Lời 33 từ ≈ 9s ở 3.7 từ/giây — ngắn hơn 30s (20s ≈ 75 từ, 30s ≈ 110, 45s ≈ 165).`
- `⚠ [thumbnail] Có 1 biến thể — nên 3–5.`
- `⚠ [T1] Chữ thumbnail lặp lại tiêu đề — nên bổ sung, không lặp.`
- `⚠ KHÔNG có timestamp ElevenLabs/whisper → đang chạy chế độ CĂN THEO KHOẢNG LẶNG (sai số ~1–3 frame mỗi từ). Nên tạo VO bằng ElevenLabs (có timestamp) hoặc cài faster-whisper.`
- `⚠ publish: cần 3 phương án tiêu đề (có 1).`

**three**:
- `⚠ [nhịp] Lời 27 từ ≈ 7s ở 3.7 từ/giây — ngắn hơn 30s (20s ≈ 75 từ, 30s ≈ 110, 45s ≈ 165).`
- `⚠ [kịch bản] Thiếu beat 'payoff'.`
- `⚠ [thumbnail] Có 1 biến thể — nên 3–5.`
- `⚠ [T1] Chữ thumbnail lặp lại tiêu đề — nên bổ sung, không lặp.`
- `⚠ KHÔNG có timestamp ElevenLabs/whisper → đang chạy chế độ CĂN THEO KHOẢNG LẶNG (sai số ~1–3 frame mỗi từ). Nên tạo VO bằng ElevenLabs (có timestamp) hoặc cài faster-whisper.`
- `⚠ publish: cần 3 phương án tiêu đề (có 1).`

**manim**:
- `⚠ [nhịp] Lời 37 từ ≈ 10s ở 3.7 từ/giây — ngắn hơn 30s (20s ≈ 75 từ, 30s ≈ 110, 45s ≈ 165).`
- `⚠ [kịch bản] Thiếu beat 'payoff'.`
- `⚠ [thumbnail] Có 1 biến thể — nên 3–5.`
- `⚠ [T1] Chữ thumbnail lặp lại tiêu đề — nên bổ sung, không lặp.`
- `⚠ KHÔNG có timestamp ElevenLabs/whisper → đang chạy chế độ CĂN THEO KHOẢNG LẶNG (sai số ~1–3 frame mỗi từ). Nên tạo VO bằng ElevenLabs (có timestamp) hoặc cài faster-whisper.`
- `⚠ publish: cần 3 phương án tiêu đề (có 1).`

**html**:
- `⚠ [nhịp] Lời 25 từ ≈ 7s ở 3.7 từ/giây — ngắn hơn 30s (20s ≈ 75 từ, 30s ≈ 110, 45s ≈ 165).`
- `⚠ [kịch bản] Thiếu beat 'payoff'.`
- `⚠ [thumbnail] Có 1 biến thể — nên 3–5.`
- `⚠ [T1] Chữ thumbnail lặp lại tiêu đề — nên bổ sung, không lặp.`
- `⚠ KHÔNG có timestamp ElevenLabs/whisper → đang chạy chế độ CĂN THEO KHOẢNG LẶNG (sai số ~1–3 frame mỗi từ). Nên tạo VO bằng ElevenLabs (có timestamp) hoặc cài faster-whisper.`
- `⚠ publish: cần 3 phương án tiêu đề (có 1).`
