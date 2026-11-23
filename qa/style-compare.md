# So sánh style — cùng một ý tưởng

Storyboard: `qa\style-compare\storyboard.json` · lưới: `qa\style-compare.mp4`

Ngưỡng: đứng hình < 0.4 s · -14 LUFS ±1 · true peak ≤ -1.0 dBTP · nền đen ≥ `black_min` của style.

| Style | Engine | Dài (s) | Nền đen TB | cần | Đứng hình dài nhất (s) | LUFS | TP (dBTP) | Pipeline |
|---|---|---|---|---|---|---|---|---|
| swiss-motion-black | html | 21.1 | 92% ✓ | 70% | 0.0 ✓ | -14.1 | -1.0 | exit 0 |
| hud-black | html | 21.1 | 94% ✓ | 60% | 0.0 ✓ | -14.0 | -1.2 | exit 0 |
| line-boil-black | html | 21.1 | 95% ✓ | 70% | 0.07 ✓ | -14.1 | -1.1 | exit 0 |
| flat-vector-black | html | 21.1 | 93% ✓ | 60% | 0.0 ✓ | -14.0 | -1.1 | exit 0 |
| physics-diagram-black | html+manim | 21.1 | 95% ✓ | 80% | 0.0 ✓ | -14.1 | -1.1 | exit 0 |
