"""Cảnh Manim của engine `manim` — một lớp `Shot`, mỗi beat là một phương thức b_<tên>.

Ngữ pháp (style physics-diagram-black): nền đen, chỉ đặt thứ đang được nói; đối tượng xuất hiện trước, chữ đến sau;
màu = tên khái niệm (hot/cold/accent); cùng lúc ≤ 2 ý; khi giữ hình chỉ còn camera trôi rất nhẹ (không frame nào đứng yên).
Thời lượng: tổng đúng frames/fps — mỗi beat chia thời gian theo TỈ LỆ của T, không có mốc tuyệt đối nào trong mã.
"""

import os

import manimpango
import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Axes,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    GrowArrow,
    GrowFromEdge,
    Line,
    MoveAlongPath,
    MovingCameraScene,
    Rectangle,
    Succession,
    SurroundingRectangle,
    Text,
    ValueTracker,
    VGroup,
    VMobject,
    Wait,
    Write,
    config,
    linear,
    smooth,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOP, BOTTOM = 8 - 2.2, -8 + 3.4  # vùng an toàn 9:16 (đơn vị Manim): trên 220 px, dưới 384 px


class Shot(MovingCameraScene):
    def __init__(self, job, **kw):
        super().__init__(**kw)
        self.job, self.P, self.tok = job, job.get("params") or {}, job["tokens"]
        self.pal = self.tok["palette"]
        self.T = (job["frames"] + job.get("preroll", 0)) / job["fps"]
        self.elapsed = 0.0
        self.boxes = []
        manimpango.register_font(os.path.join(ROOT, job["font"]["file"]))
        self.family = job["font"]["family"]

    # ---------- tiện ích ----------
    def col(self, role):
        return self.pal.get(role or "ink", self.pal["ink"]) if not str(role).startswith("#") else role

    def txt(self, s, size=0.9, role="ink", weight="BOLD", max_w=8.0):
        t = Text(str(s), font=self.family, weight=weight, color=self.col(role), line_spacing=0.8)
        t.scale_to_fit_height(size * max(1, str(s).count("\n") + 1))
        if t.width > max_w:
            t.scale_to_fit_width(max_w)
        t._src = str(s)
        return t

    def fmt(self, v, dec=0):
        return f"{v:,.{dec}f}"

    def go(self, *anims, t):
        """Chơi hoạt cảnh trong t giây (cộng dồn thời gian)."""
        t = max(1 / self.job["fps"], t)
        self.play(*anims, run_time=t)
        self.elapsed = float(self.renderer.time)  # thời gian thật Manim đã dựng (làm tròn theo frame)

    def mark(self, mob):
        """Ghi khung bao pixel của một dòng chữ đã hiện đủ (cho QA OCR)."""
        fr = self.camera.frame
        sx, sy = config.pixel_width / fr.width, config.pixel_height / fr.height
        c = fr.get_center()
        x0, x1 = (
            (mob.get_left()[0] - c[0]) * sx + config.pixel_width / 2,
            (mob.get_right()[0] - c[0]) * sx + config.pixel_width / 2,
        )
        y0, y1 = (
            config.pixel_height / 2 - (mob.get_top()[1] - c[1]) * sy,
            config.pixel_height / 2 - (mob.get_bottom()[1] - c[1]) * sy,
        )
        self.boxes.append(
            {
                "text": getattr(mob, "_src", ""),
                "box": [x0, y0, x1, y1],
                "from_f": int(round(self.elapsed * self.job["fps"])) + 1,
            }
        )

    def header(self, frac=0.16):
        y = TOP - 0.5
        out = []
        if self.P.get("kicker"):
            k = self.txt(self.P["kicker"], 0.42, "dim", "MEDIUM").move_to([0, y, 0])
            out.append(k)
            y -= 0.9
        if self.P.get("title"):
            t = self.txt(self.P["title"], 0.95).move_to([0, y - 0.3, 0])
            out.append(t)
        if out:
            self.go(*[Write(m) for m in out], t=min(0.34, self.T * frac))
            for m in out:
                self.mark(m)
        return out

    def hold(self):
        rest = self.T - self.elapsed
        if rest > 1e-6:
            self.wait(rest, frozen_frame=False)
            self.elapsed += rest

    def construct(self):
        fr = self.camera.frame
        self.add(fr)
        creep = float(self.tok.get("creep", 0.03))
        fr.add_updater(lambda m, dt: m.scale(1 - creep * dt / max(0.1, self.T)))  # trôi vào rất nhẹ suốt shot
        getattr(self, "b_" + self.job["scene"])()
        self.hold()

    # ---------- beat ----------
    def b_title(self):
        self.header(0.3)
        ln = Line([-3.4, 0.6, 0], [3.4, 0.6, 0], color=self.col("hot"), stroke_width=self.tok["stroke"])
        self.go(Create(ln), t=self.T * 0.15)
        if self.P.get("sub"):
            s = self.txt(self.P["sub"], 0.7, "accent").move_to([0, -0.6, 0])
            self.go(Write(s), t=self.T * 0.2)
            self.mark(s)

    b_outro = None  # gán bên dưới

    def b_graph(self):
        P = self.P
        self.header(0.14)
        pts = [(float(a), float(b)) for a, b in P["points"]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        y0, y1 = min(ys + [P.get("y_min", min(ys))]), max(ys + [P.get("y_max", max(ys))])
        ax = Axes(
            x_range=[min(xs), max(xs), (max(xs) - min(xs)) / 5 or 1],
            y_range=[y0, y1, (y1 - y0) / 4 or 1],
            x_length=6.4,
            y_length=6.2,
            axis_config={"include_tip": False, "color": self.col("dim"), "stroke_width": 4, "include_numbers": False},
            tips=False,
        ).move_to([0.25, -0.4, 0])
        labs = []
        if P.get("y_label"):
            labs.append(self.txt(P["y_label"], 0.4, "dim", "MEDIUM").next_to(ax.y_axis, UP, buff=0.2))
        if P.get("x_label"):
            labs.append(self.txt(P["x_label"], 0.4, "dim", "MEDIUM").next_to(ax.x_axis, DOWN, buff=0.25).align_to(ax, RIGHT))
        self.go(Create(ax), *[FadeIn(m) for m in labs], t=self.T * 0.12)
        for m in labs:
            self.mark(m)
        curve = VMobject(color=self.col(P.get("role", "hot")), stroke_width=self.tok["stroke"] + 2)
        curve.set_points_smoothly([ax.c2p(a, b) for a, b in pts])
        dot = Dot(ax.c2p(*pts[0]), radius=0.16, color=self.col("accent"))
        dec = int(P.get("decimals", 0))
        unit = P.get("y_unit", "")
        read = self.txt(self.fmt(pts[0][1], dec) + unit, 0.62, "accent")

        def upd(m):
            v = ax.p2c(dot.get_center())[1]
            new = self.txt(self.fmt(v, dec) + unit, 0.62, "accent")
            new.next_to(dot, UP + RIGHT, buff=0.15)
            if new.get_right()[0] > 4.0:
                new.next_to(dot, UP + LEFT, buff=0.15)
            m.become(new)

        read.add_updater(upd)
        self.add(dot, read)
        D = self.T * 0.5
        extra = []
        for mk in P.get("marks") or []:
            fx = (float(mk["x"]) - min(xs)) / max(1e-9, max(xs) - min(xs))
            ln = DashedLine(ax.c2p(mk["x"], y0), ax.c2p(mk["x"], y1), color=self.col("dim"), stroke_width=3)
            lb = self.txt(mk["label"], 0.42, "ink", "MEDIUM", max_w=4.2).next_to(
                ax.c2p(mk["x"], y0 + 0.66 * (y1 - y0)), RIGHT, buff=0.2
            )
            lb.shift(RIGHT * max(0, -3.9 - lb.get_left()[0]) + LEFT * max(0, lb.get_right()[0] - 3.9))
            extra.append(
                Succession(
                    Wait(run_time=max(0.01, D * fx)),
                    Create(ln, run_time=min(0.3, D * 0.2)),
                    FadeIn(lb, run_time=min(0.3, D * 0.2)),
                )
            )
            self._marks = getattr(self, "_marks", []) + [lb]
        self.play(
            Create(curve, rate_func=linear, run_time=D), MoveAlongPath(dot, curve, rate_func=linear, run_time=D), *extra
        )
        self.elapsed = float(self.renderer.time)
        read.clear_updaters()
        fin = self.txt(self.fmt(pts[-1][1], dec) + unit, 0.62, "accent").move_to(read)
        self.remove(read)
        self.add(fin)
        self.mark(fin)
        for lb in getattr(self, "_marks", []):
            self.mark(lb)

    def b_vectors(self):
        P = self.P
        ob = P.get("object") or {}
        c = (
            Circle(radius=1.1, color=self.col(ob.get("role", "hot")), stroke_width=self.tok["stroke"])
            .set_fill(self.col(ob.get("role", "hot")), 0.25)
            .move_to([0, -0.6, 0])
        )
        self.go(Create(c), t=min(0.30, self.T * 0.12))
        if ob.get("label"):
            ol = self.txt(ob["label"], 0.45, "ink", "MEDIUM", max_w=1.9).move_to(c)   # nhãn vật nằm gọn trong vòng
            self.go(FadeIn(ol), t=min(0.15, self.T * 0.06))
            self.mark(ol)
        self.header(0.14)
        vs = P["vectors"]
        mmax = max(float(v.get("mag", 1)) for v in vs) or 1
        for v in vs:
            d = np.array([float(v["dir"][0]), float(v["dir"][1]), 0.0])
            d = d / (np.linalg.norm(d) or 1)
            ln = 1.2 + 2.0 * float(v.get("mag", 1)) / mmax
            a = Arrow(
                c.get_center() + d * 1.15,
                c.get_center() + d * (1.15 + ln),
                buff=0,
                color=self.col(v.get("role", "accent")),
                stroke_width=self.tok["stroke"] + 2,
                max_tip_length_to_length_ratio=0.18,
            )
            lb = self.txt(v["label"], 0.45, v.get("role", "accent"), max_w=3.6)
            if abs(d[0]) > 2 * abs(d[1]):
                # mũi tên gần nằm ngang: nhãn nằm TRÊN thân/mũi tên (trên điểm cao nhất của mũi tên để không đè thân nghiêng)
                lo, hi = (c.get_right()[0] + 0.15, 4.0) if d[0] > 0 else (-4.0, c.get_left()[0] - 0.15)
                if lb.width > hi - lo:
                    lb.scale_to_fit_width(hi - lo)
                y_top = max(a.get_start()[1], a.get_end()[1])
                lb.move_to([min(max(a.get_center()[0], lo + lb.width / 2), hi - lb.width / 2), y_top + 0.42, 0])
            else:
                lb.move_to(a.get_end() + d * 0.5)
            lb.shift(RIGHT * max(0, -4.0 - lb.get_left()[0]) + LEFT * max(0, lb.get_right()[0] - 4.0))
            self.go(GrowArrow(a), FadeIn(lb), t=self.T * 0.5 / len(vs))
            self.mark(lb)

    def b_equation(self):
        P = self.P
        self.header(0.16)
        lines = P["lines"]
        y = 1.6
        last = None
        for ln in lines:
            t = self.txt(
                ln["text"] if isinstance(ln, dict) else ln, 0.8, (ln.get("role") if isinstance(ln, dict) else None) or "ink"
            ).move_to([0, y, 0])
            self.go(Write(t), t=self.T * 0.45 / len(lines))
            self.mark(t)
            y -= 1.5
            last = t
        if P.get("result"):
            r = self.txt(P["result"], 0.95, "accent").move_to([0, y - 0.3, 0])
            self.go(Write(r), t=self.T * 0.12)
            self.mark(r)
            last = r
        if last is not None:
            self.go(
                Create(SurroundingRectangle(last, color=self.col("accent"), buff=0.3, stroke_width=self.tok["stroke"])),
                t=self.T * 0.08,
            )

    def b_counter(self):
        P = self.P
        self.header(0.16)
        a, b, dec = float(P.get("from", 0)), float(P["to"]), int(P.get("decimals", 0))
        pre, suf = P.get("prefix", ""), P.get("suffix", "")
        vt = ValueTracker(a)
        num = self.txt(pre + self.fmt(a, dec) + suf, 2.0, "ink").move_to([0, -0.2, 0])
        num.add_updater(
            lambda m: m.become(self.txt(pre + self.fmt(vt.get_value(), dec) + suf, 2.0, "ink").move_to([0, -0.2, 0]))
        )
        bar_bg = Line([-3.2, -2.2, 0], [3.2, -2.2, 0], color=self.col("dim"), stroke_width=8)
        bar = Line([-3.2, -2.2, 0], [-3.19, -2.2, 0], color=self.col("hot"), stroke_width=12)
        bar.add_updater(
            lambda m: m.put_start_and_end_on(
                [-3.2, -2.2, 0], [-3.2 + 6.4 * max(0.002, (vt.get_value() - a) / ((b - a) or 1)), -2.2, 0]
            )
        )
        self.add(num, bar_bg, bar)
        self.go(vt.animate(rate_func=smooth).set_value(b), t=self.T * 0.42)
        num.clear_updaters()
        bar.clear_updaters()
        fin = self.txt(pre + self.fmt(b, dec) + suf, 2.0, "ink").move_to([0, -0.2, 0])
        self.remove(num)
        self.add(fin)
        self.mark(fin)
        for key, yy, role, sz in (("unit", -3.2, "accent", 0.7), ("label", -4.4, "ink", 0.6)):
            if P.get(key):
                t = self.txt(P[key], sz, role).move_to([0, yy, 0])
                self.go(Write(t), t=self.T * 0.1)
                self.mark(t)

    def b_compare(self):
        P = self.P
        self.header(0.16)
        cols = [(P["left"], -2.0), (P["right"], 2.0)]
        vmax = max(float(c.get("value", 0) or 0) for c, _ in cols) or 1
        base = -3.6
        self.go(Create(Line([-3.8, base, 0], [3.8, base, 0], color=self.col("dim"), stroke_width=4)), t=self.T * 0.06)
        for c, x in cols:
            v = float(c.get("value", 0) or 0)
            h = max(0.08, 5.0 * v / vmax)
            role = c.get("role") or ("hot" if v >= vmax else "cold")
            r = (
                Rectangle(width=1.7, height=h, color=self.col(role), stroke_width=self.tok["stroke"])
                .set_fill(self.col(role), 0.35)
                .move_to([x, base + h / 2, 0])
            )
            val = self.txt(
                self.fmt(v, int(c.get("decimals", 0))) + (" " + c["unit"] if c.get("unit") else ""), 0.6, "accent"
            ).next_to(r, UP, buff=0.25)
            self.go(GrowFromEdge(r, DOWN), t=self.T * 0.16)
            self.go(FadeIn(val), t=self.T * 0.05)
            self.mark(val)
            if c.get("label"):
                lb = self.txt(c["label"], 0.45, "ink", "MEDIUM", max_w=3.6).move_to([x, base - 0.6, 0])
                self.go(FadeIn(lb), t=self.T * 0.05)
                self.mark(lb)

    def b_fact(self):
        P = self.P
        if P.get("kicker"):
            k = self.txt(P["kicker"], 0.42, "dim", "MEDIUM").move_to([0, TOP - 0.6, 0])
            self.go(Write(k), t=self.T * 0.03)
            self.mark(k)
        words, lines, cur = str(P["text"]).split(), [], ""
        for w in words:  # ngắt dòng ~16 ký tự
            if cur and len(cur) + len(w) + 1 > 16:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        lines.append(cur)
        grp = VGroup(*[self.txt(ln, 1.0) for ln in lines]).arrange(DOWN, buff=0.35).move_to([0, 1.2, 0])
        self.go(*[Write(m) for m in grp], t=self.T * 0.3)
        for m in grp:
            self.mark(m)
        if P.get("em"):
            e = self.txt(P["em"], 1.0, "accent").next_to(grp, DOWN, buff=1.0)
            self.go(Write(e), t=self.T * 0.14)
            self.mark(e)
            self.go(
                Create(SurroundingRectangle(e, color=self.col("accent"), buff=0.3, stroke_width=self.tok["stroke"])),
                t=self.T * 0.08,
            )


def _outro(self):
    P = self.P
    self.P = {"kicker": P.get("next_prefix"), "title": P.get("teaser"), "sub": P.get("follow")}
    self.b_title()


Shot.b_outro = _outro
