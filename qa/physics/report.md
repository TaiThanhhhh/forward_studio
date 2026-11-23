# Vật lý cảnh stage — keyframe tay vs Rapier

Style `toon3d-lab` · 120 frame/bản · dựng bằng `python scripts/physics_sheet.py`

## drop

| bản | thời gian dựng | cue |
|---|---|---|
| keyframe | 7.1 s | thud@36, thud@50 |
| physics | 6.5 s | impact@34 |

Vật lý: ball (metal, ball, 43.521 kg), box (wood, box, 8.294 kg), feather (feather, box, 0.008 kg)

Va chạm (frame): ball@34 (5.31 m/s)

Canh hit_u: —

## topple

| bản | thời gian dựng | cue |
|---|---|---|
| keyframe | 6.6 s | impact@50, thud@89 |
| physics | 6.5 s | impact@50, impact@88, thud@105 |

Vật lý: k00 (wood, box, 4.8 kg), k01 (wood, box, 4.8 kg), k10 (wood, box, 4.8 kg), k11 (wood, box, 4.8 kg), k20 (wood, box, 4.8 kg), k21 (wood, box, 4.8 kg), k30 (wood, box, 4.8 kg), k31 (wood, box, 4.8 kg), k40 (wood, box, 4.8 kg), k41 (wood, box, 4.8 kg), ball (metal, ball, 43.521 kg)

Va chạm (frame): ball@50 (3.9 m/s), k40@88 (3.64 m/s), k21@105 (2.08 m/s)

Canh hit_u: ball: muốn frame 50, chạm frame 50 (thả ở frame 31)
