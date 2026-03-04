"""
External Merge Sort Visualizer
================================
Ứng dụng sắp xếp tập tin nhị phân số thực (float64 – 8 bytes/số)
bằng giải thuật External Merge Sort, kèm minh hoạ từng bước.

Sinh viên: Cáp Kim Hải Anh - MSSV: 23520036
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
import os
import shutil
import tempfile
import random
import threading
import math
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (Light theme)
# ══════════════════════════════════════════════════════════════════════════════
BG       = "#f0f2f5"   # page background
SURFACE0 = "#ffffff"   # card / panel background
SURFACE1 = "#e4e8ee"   # separator / secondary surface
OVERLAY  = "#9ba3af"   # muted text / icons
TEXT     = "#1a1d23"   # primary text
SUBTEXT  = "#4b5563"   # secondary text
BLUE     = "#1971c2"   # accent blue
GREEN    = "#2b8a3e"   # accent green
RED      = "#c92a2a"   # accent red
YELLOW   = "#e67700"   # accent amber
PEACH    = "#d9480f"   # accent orange
MAUVE    = "#6741d9"   # accent violet
TEAL     = "#0c7a79"   # accent teal
PINK     = "#a61e4d"   # accent pink
SAPPHIRE = "#1864ab"   # accent sapphire

RUN_PALETTE = [BLUE, GREEN, YELLOW, PEACH, MAUVE, TEAL, PINK, RED, SAPPHIRE]

FLOAT_SIZE = 8   # bytes per float64


# ══════════════════════════════════════════════════════════════════════════════
#  SORT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class SortEngine:
    """
    External Merge Sort implementation.
    Records every significant step as a snapshot for the visualiser.

    Step dict format:
        {
            'title':       str,
            'description': str,
            'runs':        list[list[float]],  # all current runs
            'highlighted': list[int],          # run indices being processed
            'merged_into': list[int] | None,   # run indices that are *sources*
        }
    """

    def __init__(self, chunk_size: int = 4):
        self.chunk_size = chunk_size
        self.steps: list[dict] = []

    # ── public ───────────────────────────────────────────────────────────────
    def sort(self, source_path: str, output_path: str) -> list[dict]:
        """Sort *source_path* → *output_path*; return recorded step list."""
        self.steps = []
        tmp = tempfile.mkdtemp(prefix="ems_")

        try:
            numbers = self._read_floats(source_path)
            if not numbers:
                raise ValueError("Tập tin rỗng hoặc không có dữ liệu hợp lệ!")

            n = len(numbers)

            cs = self.chunk_size
            nr = math.ceil(n / cs)

            # ── Step 0 : original data ────────────────────────────────────
            self._snap(
                "Bước 0 – Dữ liệu gốc (chưa sắp xếp)",
                [numbers],
                [],
                f"File chứa {n} số thực (mỗi số 8 bytes).  "
                f"Chunk size = {cs}  →  sẽ tạo {nr} run ban đầu."
            )

            # ── Phase 1 : build initial sorted runs ───────────────────────
            runs: list[list[float]] = []
            for i in range(0, n, cs):
                chunk = sorted(numbers[i: i + cs])
                runs.append(chunk)

            run_preview = "   ".join(
                f"R{k}:{self._fmt_list(r, 4)}" for k, r in enumerate(runs)
            )
            self._snap(
                "Phase 1 – Tạo các run ban đầu",
                [r[:] for r in runs],
                list(range(len(runs))),
                f"Chia {n} phần tử thành {len(runs)} nhóm ({cs} pt/nhóm), "
                f"sắp xếp từng nhóm tăng dần trong bộ nhớ.\n{run_preview}"
            )

            # ── Phase 2+ : merge passes ───────────────────────────────────
            pass_num = 1
            while len(runs) > 1:
                new_runs: list[list[float]] = []
                i = 0
                while i < len(runs):
                    if i + 1 < len(runs):
                        a_str = self._fmt_list(runs[i])
                        b_str = self._fmt_list(runs[i + 1])
                        # build a step-by-step merge trace (first few steps)
                        trace = self._merge_trace(runs[i], runs[i + 1], max_shown=4)
                        # Highlight the two runs about to be merged
                        self._snap(
                            f"Pass {pass_num} – Chuẩn bị gộp R{i} và R{i+1}",
                            [r[:] for r in runs],
                            [i, i + 1],
                            f"R{i}: {a_str}\nR{i+1}: {b_str}\n\n"
                            f"So sánh từng cặp phần tử (bắt đầu từ vị trí 0):\n{trace}"
                        )
                        merged = self._merge(runs[i], runs[i + 1])
                        new_runs.append(merged)

                        # Show intermediate result after this pair is merged
                        partial = new_runs[:] + runs[i + 2:]
                        self._snap(
                            f"Pass {pass_num} – Sau khi gộp R{i} ⊕ R{i+1}",
                            [r[:] for r in partial],
                            [len(new_runs) - 1],
                            f"Gộp hoàn tất → R{len(new_runs)-1}: {self._fmt_list(merged)} "
                            f"({len(merged)} phần tử, tăng dần)."
                        )
                        i += 2
                    else:
                        # Odd run passes through unchanged
                        new_runs.append(runs[i])
                        self._snap(
                            f"Pass {pass_num} – R{i} giữ nguyên (không có cặp)",
                            [r[:] for r in new_runs[:] + runs[i + 1:]],
                            [len(new_runs) - 1],
                            f"Số run lẻ → R{i} đi thẳng sang pass tiếp theo: "
                            f"{self._fmt_list(new_runs[-1])}."
                        )
                        i += 1

                runs = new_runs
                pass_num += 1

            # ── Final snapshot ────────────────────────────────────────────
            final = runs[0]
            self._snap(
                "✔  Hoàn tất sắp xếp!",
                [final],
                [0],
                f"Tất cả {len(final)} phần tử đã sắp xếp tăng dần.  "
                f"Min = {final[0]:.6g}   Max = {final[-1]:.6g}"
            )

            self._write_floats(output_path, runs[0])
            return self.steps

        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _read_floats(path: str) -> list[float]:
        result = []
        with open(path, "rb") as f:
            while True:
                raw = f.read(FLOAT_SIZE)
                if len(raw) < FLOAT_SIZE:
                    break
                result.append(struct.unpack("d", raw)[0])
        return result

    @staticmethod
    def _write_floats(path: str, numbers: list[float]) -> None:
        with open(path, "wb") as f:
            for v in numbers:
                f.write(struct.pack("d", v))

    @staticmethod
    def _merge(a: list[float], b: list[float]) -> list[float]:
        out, i, j = [], 0, 0
        while i < len(a) and j < len(b):
            if a[i] <= b[j]:
                out.append(a[i]); i += 1
            else:
                out.append(b[j]); j += 1
        out.extend(a[i:])
        out.extend(b[j:])
        return out

    def _snap(self, title, runs, highlighted, description):
        self.steps.append({
            "title":       title,
            "description": description,
            "runs":        runs,
            "highlighted": highlighted,
        })

    @staticmethod
    def _merge_trace(a: list[float], b: list[float], max_shown: int = 4) -> str:
        """
        Simulate the merge and build a human-readable step-by-step trace.
        Shows up to *max_shown* comparison steps, then summarises the rest.
        """
        lines  = []
        result = []
        ia, ib = 0, 0
        step   = 0

        while ia < len(a) and ib < len(b):
            av, bv = a[ia], b[ib]
            taken  = av if av <= bv else bv
            op     = "≤" if av <= bv else ">"
            if step < max_shown:
                chosen = f"{av:.4g}" if av <= bv else f"{bv:.4g}"
                src    = "R trái" if av <= bv else "R phải"
                so_far = result[:] + [taken]
                so_far_str = "[" + ", ".join(f"{v:.4g}" for v in so_far[:6])
                if len(so_far) > 6:
                    so_far_str += ", …"
                so_far_str += "]"
                lines.append(
                    f"  Bước {step+1}: {av:.4g} {op} {bv:.4g}  →  lấy {chosen} ({src})  →  kết quả: {so_far_str}"
                )
            result.append(taken)
            if av <= bv:
                ia += 1
            else:
                ib += 1
            step += 1

        remaining_a = a[ia:]
        remaining_b = b[ib:]
        result.extend(remaining_a)
        result.extend(remaining_b)

        if step > max_shown:
            lines.append(f"  … (tương tự, tiếp tục so sánh và lấy phần tử nhỏ hơn cho đến hết)")

        if remaining_a:
            lines.append(
                f"  R trái còn lại: {SortEngine._fmt_list(remaining_a)}  →  nối thẳng vào cuối"
            )
        if remaining_b:
            lines.append(
                f"  R phải còn lại: {SortEngine._fmt_list(remaining_b)}  →  nối thẳng vào cuối"
            )

        final_str = "[" + ", ".join(f"{v:.4g}" for v in result[:8])
        if len(result) > 8:
            final_str += ", …"
        final_str += "]"
        lines.append(f"  ⇒ Kết quả sau gộp: {final_str}")
        return "\n".join(lines)

    @staticmethod
    def _fmt_list(lst: list[float], max_items: int = 6) -> str:
        items = [f"{v:.2g}" for v in lst[:max_items]]
        if len(lst) > max_items:
            items.append("…")
        return "[" + ", ".join(items) + "]"


# ══════════════════════════════════════════════════════════════════════════════
#  CANVAS VISUALISER
# ══════════════════════════════════════════════════════════════════════════════
class Visualiser:
    """Draws the current sort step onto a tk.Canvas."""

    CELL_W  = 68
    CELL_H  = 46
    PAD_X   = 24
    PAD_Y   = 20
    GAP_Y   = 52          # vertical spacing between runs
    LABEL_W = 90          # width reserved for run label
    ARROW_W = 14          # width of the → between cells

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas

    def render(self, step: dict) -> None:
        c = self.canvas
        c.delete("all")

        runs        = step["runs"]
        highlighted = set(step["highlighted"])

        if not runs:
            return

        cw  = max(c.winfo_width(), 700)
        y   = self.PAD_Y

        for ridx, run in enumerate(runs):
            hi    = ridx in highlighted
            color = RUN_PALETTE[ridx % len(RUN_PALETTE)]
            dim   = self._dim(color)

            # ── run label ────────────────────────────────────────────────
            lbl = f"Run {ridx}"
            c.create_text(
                self.PAD_X, y + self.CELL_H // 2,
                text=lbl, anchor="w",
                font=("Consolas", 10, "bold" if hi else "normal"),
                fill=color if hi else OVERLAY
            )

            # ── indicator bar if highlighted ─────────────────────────────
            if hi:
                c.create_rectangle(
                    self.PAD_X - 6, y - 4,
                    self.PAD_X - 2, y + self.CELL_H + 4,
                    fill=color, outline=""
                )

            # ── cells ─────────────────────────────────────────────────────
            x0 = self.PAD_X + self.LABEL_W
            for ci, val in enumerate(run):
                x = x0 + ci * (self.CELL_W + self.ARROW_W)

                # arrow between cells
                if ci > 0:
                    ax = x - self.ARROW_W
                    c.create_text(
                        ax + self.ARROW_W // 2,
                        y + self.CELL_H // 2,
                        text="→", fill=OVERLAY,
                        font=("Segoe UI", 8)
                    )

                fill_col    = color if hi else dim
                outline_col = color
                lw          = 2 if hi else 1

                c.create_rectangle(
                    x, y, x + self.CELL_W, y + self.CELL_H,
                    fill=fill_col, outline=outline_col, width=lw
                )

                txt = self._fmt_val(val)
                c.create_text(
                    x + self.CELL_W // 2, y + self.CELL_H // 2,
                    text=txt,
                    fill="#ffffff" if hi else TEXT,
                    font=("Consolas", 10, "bold")
                )

            y += self.CELL_H + self.GAP_Y

        # scroll region
        total_w = self.PAD_X + self.LABEL_W + \
                  max(len(r) for r in runs) * (self.CELL_W + self.ARROW_W) + 40
        c.configure(scrollregion=(0, 0, max(cw, total_w), y + self.PAD_Y))

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _fmt_val(v: float) -> str:
        if v == int(v) and abs(v) < 1e9:
            return str(int(v))
        s = f"{v:.3g}"
        return s[:8]          # cap width

    @staticmethod
    def _dim(hex_color: str) -> str:
        """Return a very-light pastel version of *hex_color* for non-highlighted cells (light theme)."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        # blend 15 % colour into white
        factor = 0.15
        r = int(r * factor + 255 * (1 - factor))
        g = int(g * factor + 255 * (1 - factor))
        b = int(b * factor + 255 * (1 - factor))
        return f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class App:
    """Main GUI application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("External Merge Sort  –  Visualizer")
        self.root.geometry("1360x860")
        self.root.minsize(960, 640)
        self.root.configure(bg=BG)
        self.root.option_add("*Font", "SegoeUI 10")

        # state
        self.source_file: str | None = None
        self.output_file: str | None = None
        self.steps:       list[dict] = []
        self.cur_step:    int        = 0
        self.is_playing:  bool       = False

        self.chunk_size = tk.IntVar(value=4)
        self.speed_ms   = tk.IntVar(value=5000)  # ms between auto-play steps

        self.engine     = SortEngine()
        self.vis        = None   # set after canvas is built

        self._setup_ttk_styles()
        self._build_ui()

    # ── TTK styles ────────────────────────────────────────────────────────────
    def _setup_ttk_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TScrollbar", background=SURFACE1, troughcolor=SURFACE0,
                     arrowcolor=SUBTEXT, bordercolor=SURFACE0)
        s.configure("Header.TFrame", background=SURFACE0)
        s.configure("Sidebar.TFrame", background=SURFACE0)

    # ══ UI CONSTRUCTION ═══════════════════════════════════════════════════════
    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._build_sidebar(body)
        self._build_main_panel(body)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=SURFACE0, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="  ⬡  External Merge Sort  –  Visualizer",
                 font=("Segoe UI", 14, "bold"),
                 bg=SURFACE0, fg=TEXT).pack(side=tk.LEFT, padx=18, pady=10)

        tk.Label(hdr, text="Sắp xếp tập tin nhị phân số thực (float64 · 8 bytes/số)",
                 font=("Segoe UI", 9),
                 bg=SURFACE0, fg=SUBTEXT).pack(side=tk.LEFT, padx=4, pady=16)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        # outer frame (fixed width)
        sb_outer = tk.Frame(parent, bg=SURFACE0, width=310)
        sb_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sb_outer.pack_propagate(False)

        # scrollable canvas inside the sidebar
        sb_canvas = tk.Canvas(sb_outer, bg=SURFACE0, highlightthickness=0)
        sb_vsb    = ttk.Scrollbar(sb_outer, orient=tk.VERTICAL, command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_vsb.set)
        sb_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        sb_canvas.pack(fill=tk.BOTH, expand=True)

        # inner frame holds all widgets
        sb = tk.Frame(sb_canvas, bg=SURFACE0)
        sb_win = sb_canvas.create_window((0, 0), window=sb, anchor="nw")

        def _on_inner_configure(e):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))
            sb_canvas.itemconfig(sb_win, width=sb_canvas.winfo_width())

        def _on_canvas_resize(e):
            sb_canvas.itemconfig(sb_win, width=e.width)

        sb.bind("<Configure>", _on_inner_configure)
        sb_canvas.bind("<Configure>", _on_canvas_resize)
        sb_canvas.bind("<MouseWheel>",
                       lambda e: sb_canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        sb.bind("<MouseWheel>",
                lambda e: sb_canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # ── File ──────────────────────────────────────────────────────────
        self._sec(sb, "📁  Tập Tin Nguồn")

        self.lbl_file = tk.Label(sb, text="(chưa chọn)",
                                  font=("Segoe UI", 10), bg=SURFACE0,
                                  fg=SUBTEXT, wraplength=266, justify="left")
        self.lbl_file.pack(padx=14, pady=(0, 6), anchor="w")

        self._btn(sb, "Chọn Tập Tin  (.bin)",   self._open_file,          BLUE)
        self._btn(sb, "Tạo Tập Tin Thử Nghiệm", self._generate_test_dlg,  GREEN)

        # ── Settings ──────────────────────────────────────────────────────
        self._sec(sb, "⚙  Cài Đặt Sắp Xếp")

        tk.Label(sb, text="Chunk size  (số phần tử mỗi run):",
                 font=("Segoe UI", 10), bg=SURFACE0, fg=SUBTEXT).pack(padx=14, anchor="w")

        rf = tk.Frame(sb, bg=SURFACE0)
        rf.pack(padx=14, pady=(3, 4), anchor="w")
        for v in [2, 3, 4, 6, 8, 10]:
            tk.Radiobutton(rf, text=str(v), variable=self.chunk_size, value=v,
                           bg=SURFACE0, fg=TEXT, selectcolor=SURFACE1,
                           activebackground=SURFACE0, activeforeground=TEXT,
                           font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=3)

        # custom value row
        cf2 = tk.Frame(sb, bg=SURFACE0)
        cf2.pack(padx=14, pady=(2, 8), anchor="w")
        tk.Label(cf2, text="Tuỳ chọn:",
                 font=("Segoe UI", 9), bg=SURFACE0, fg=OVERLAY).pack(side=tk.LEFT, padx=(0, 6))
        tk.Spinbox(cf2, from_=2, to=999, textvariable=self.chunk_size,
                   bg=SURFACE1, fg=TEXT, font=("Segoe UI", 10),
                   buttonbackground=SURFACE1, insertbackground=TEXT,
                   width=5, relief="flat").pack(side=tk.LEFT)

        tk.Label(sb, text="Tốc độ phát tự động (giây/bước):",
                 font=("Segoe UI", 10), bg=SURFACE0, fg=SUBTEXT).pack(padx=14, anchor="w")

        tk.Scale(sb, from_=5000, to=20000, resolution=1000,
                 variable=self.speed_ms, orient=tk.HORIZONTAL,
                 bg=SURFACE0, fg=TEXT, troughcolor=SURFACE1,
                 highlightthickness=0, font=("Segoe UI", 9),
                 length=260, showvalue=True,
                 label="").pack(padx=14, pady=(3, 4))
        tk.Label(sb, text="(giá trị hiển thị theo mili-giây, 5000 = 5 giây)",
                 font=("Segoe UI", 8), bg=SURFACE0, fg=OVERLAY,
                 wraplength=266).pack(padx=14, pady=(0, 8), anchor="w")

        # ── Sort & Playback ───────────────────────────────────────────────
        self._sec(sb, "▶  Điều Khiển")
        self._btn(sb, "🔀  Bắt Đầu Sắp Xếp", self._start_sort, MAUVE)

        pb = tk.Frame(sb, bg=SURFACE0)
        pb.pack(padx=14, pady=4, fill=tk.X)
        for txt, cmd in [("◀◀", self._first_step),
                         ("◀",  self._prev_step),
                         ("▶",  self._toggle_play),
                         ("▶▶", self._next_step),
                         ("▶|", self._last_step)]:
            b = tk.Button(pb, text=txt, command=cmd,
                          bg=SURFACE1, fg=TEXT, font=("Segoe UI", 10, "bold"),
                          relief="flat", cursor="hand2", padx=8, pady=5,
                          activebackground=OVERLAY, activeforeground="#ffffff")
            b.pack(side=tk.LEFT, padx=2, pady=2)
            if txt == "▶":
                self.play_btn = b

        self.lbl_step = tk.Label(sb, text="Bước:  – / –",
                                  font=("Segoe UI", 11, "bold"),
                                  bg=SURFACE0, fg=YELLOW)
        self.lbl_step.pack(padx=14, pady=4, anchor="w")

        # ── Output ────────────────────────────────────────────────────────
        self._sec(sb, "💾  Kết Quả")
        self._btn(sb, "Lưu File Đã Sắp Xếp…", self._save_result, TEAL)

        # ── View ──────────────────────────────────────────────────────────
        self._sec(sb, "🔍  Xem Nội Dung")
        self._btn(sb, "Xem File Nguồn",    lambda: self._view_file("source"), PEACH)
        self._btn(sb, "Xem File Kết Quả",  lambda: self._view_file("output"), PEACH)

    # ── Main panel ────────────────────────────────────────────────────────────
    def _build_main_panel(self, parent):
        panel = tk.Frame(parent, bg=BG)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # step title + description row
        info = tk.Frame(panel, bg=SURFACE0, pady=8)
        info.pack(fill=tk.X)

        self.lbl_title = tk.Label(info, text="─  Chờ sắp xếp  ─",
                                   font=("Segoe UI", 12, "bold"),
                                   bg=SURFACE0, fg=TEXT)
        self.lbl_title.pack(padx=16, anchor="w")

        self.lbl_desc = tk.Label(info, text="Chọn tập tin nguồn và nhấn 'Bắt Đầu Sắp Xếp'.",
                                  font=("Segoe UI", 9), bg=SURFACE0, fg=SUBTEXT,
                                  wraplength=900, justify="left")
        self.lbl_desc.pack(padx=16, pady=(3, 5), anchor="w")

        # canvas + scrollbars
        cf = tk.Frame(panel, bg=SURFACE0)
        cf.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.canvas = tk.Canvas(cf, bg="#fafbfc", highlightthickness=0)
        vsb = ttk.Scrollbar(cf, orient=tk.VERTICAL,   command=self.canvas.yview)
        hsb = ttk.Scrollbar(cf, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<MouseWheel>",
                          lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        self.vis = Visualiser(self.canvas)

        # legend
        leg = tk.Frame(panel, bg=SURFACE1)
        leg.pack(fill=tk.X)
        tk.Label(leg, text="  ■ Run bình thường (màu nhạt)",
                 font=("Segoe UI", 9), bg=SURFACE1, fg=SUBTEXT).pack(side=tk.LEFT, padx=8, pady=4)
        tk.Label(leg, text="  ■ Run đang được xử lý (màu đậm + viền đậm)",
                 font=("Segoe UI", 9), bg=SURFACE1, fg=TEXT).pack(side=tk.LEFT, pady=4)

        # status bar
        self.sv_status = tk.StringVar(value="Sẵn sàng.")
        tk.Label(panel, textvariable=self.sv_status,
                 font=("Segoe UI", 9), bg=SURFACE1,
                 fg=SUBTEXT, anchor="w", padx=10).pack(fill=tk.X, pady=(4, 0))

    # ══ UI HELPERS ════════════════════════════════════════════════════════════
    def _sec(self, parent, title: str):
        tk.Frame(parent, bg=SURFACE1, height=1).pack(fill=tk.X, pady=(8, 0))
        tk.Label(parent, text=title, font=("Segoe UI", 9, "bold"),
                 bg=SURFACE0, fg=BLUE).pack(padx=12, pady=(4, 3), anchor="w")

    def _btn(self, parent, text: str, cmd, color=BLUE):
        tk.Button(parent, text=text, command=cmd,
                  bg=color, fg="#ffffff", font=("Segoe UI", 9, "bold"),
                  relief="flat", cursor="hand2",
                  activebackground=TEXT, activeforeground="#ffffff",
                  padx=6, pady=5
                  ).pack(padx=12, pady=2, fill=tk.X)

    # ══ FILE OPERATIONS ═══════════════════════════════════════════════════════
    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Chọn tập tin nhị phân",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        if not path:
            return
        self.source_file = path
        size   = os.path.getsize(path)
        count  = size // FLOAT_SIZE
        fname  = Path(path).name
        self.lbl_file.config(
            text=f"📄 {fname}\n{size:,} bytes  ·  {count} số thực",
            fg=GREEN
        )
        self.sv_status.set(f"Đã chọn: {fname}  ({count} số thực)")
        self._reset_visualiser()

    def _generate_test_dlg(self):
        """Open a dialog to create a test binary file."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Tạo Tập Tin Thử Nghiệm")
        dlg.geometry("360x270")
        dlg.configure(bg=SURFACE0)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Tạo Tập Tin Thử Nghiệm",
                 font=("Segoe UI", 12, "bold"), bg=SURFACE0, fg=TEXT).pack(pady=16)

        fv = tk.Frame(dlg, bg=SURFACE0)
        fv.pack(padx=20, fill=tk.X)

        tk.Label(fv, text="Số phần tử:", bg=SURFACE0, fg=SUBTEXT,
                 font=("Segoe UI", 9), width=18, anchor="w").grid(row=0, column=0, pady=5)
        cnt_var = tk.IntVar(value=12)
        tk.Spinbox(fv, from_=4, to=200, textvariable=cnt_var,
                   bg=SURFACE1, fg=TEXT, font=("Segoe UI", 10),
                   buttonbackground=SURFACE1, insertbackground=TEXT,
                   width=8).grid(row=0, column=1, pady=5, sticky="w")

        tk.Label(fv, text="Giá trị min:", bg=SURFACE0, fg=SUBTEXT,
                 font=("Segoe UI", 9), width=18, anchor="w").grid(row=1, column=0, pady=5)
        min_var = tk.DoubleVar(value=-100.0)
        tk.Entry(fv, textvariable=min_var, bg=SURFACE1, fg=TEXT,
                 insertbackground=TEXT, font=("Segoe UI", 10),
                 width=10).grid(row=1, column=1, pady=5, sticky="w")

        tk.Label(fv, text="Giá trị max:", bg=SURFACE0, fg=SUBTEXT,
                 font=("Segoe UI", 9), width=18, anchor="w").grid(row=2, column=0, pady=5)
        max_var = tk.DoubleVar(value=100.0)
        tk.Entry(fv, textvariable=max_var, bg=SURFACE1, fg=TEXT,
                 insertbackground=TEXT, font=("Segoe UI", 10),
                 width=10).grid(row=2, column=1, pady=5, sticky="w")

        int_only = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="Chỉ số nguyên",
                       variable=int_only, bg=SURFACE0, fg=TEXT,
                       selectcolor=SURFACE1, activebackground=SURFACE0,
                       activeforeground=TEXT,
                       font=("Segoe UI", 9)).pack(pady=4)

        def _create():
            lo, hi = min_var.get(), max_var.get()
            if lo >= hi:
                messagebox.showerror("Lỗi", "Giá trị min phải nhỏ hơn max!", parent=dlg)
                return
            path = filedialog.asksaveasfilename(
                parent=dlg,
                title="Lưu tập tin thử nghiệm",
                defaultextension=".bin",
                filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
            )
            if not path:
                return
            n = cnt_var.get()
            if int_only.get():
                nums = [float(random.randint(int(math.ceil(lo)), int(math.floor(hi))))
                        for _ in range(n)]
            else:
                nums = [round(random.uniform(lo, hi), 2) for _ in range(n)]

            with open(path, "wb") as f:
                for v in nums:
                    f.write(struct.pack("d", v))

            self.source_file = path
            fname = Path(path).name
            self.lbl_file.config(
                text=f"📄 {fname}\n{n * FLOAT_SIZE:,} bytes  ·  {n} số thực",
                fg=GREEN
            )
            self.sv_status.set(f"Đã tạo: {fname}  ({n} số thực)")
            self._reset_visualiser()
            dlg.destroy()
            messagebox.showinfo("Thành Công",
                                f"Đã tạo tập tin với {n} số thực!\n\n{path}")

        tk.Button(dlg, text="  Tạo Tập Tin  ", command=_create,
                  bg=GREEN, fg=BG, font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2",
                  padx=16, pady=8).pack(pady=14)

    # ══ SORT ══════════════════════════════════════════════════════════════════
    def _start_sort(self):
        if not self.source_file:
            messagebox.showwarning("Chưa Chọn File",
                                   "Vui lòng chọn hoặc tạo tập tin nguồn trước!")
            return

        self.engine.chunk_size = self.chunk_size.get()
        self._reset_visualiser()
        p = Path(self.source_file)
        self.output_file = str(p.parent / (p.stem + "_sorted" + p.suffix))
        self.sv_status.set("Đang sắp xếp…")
        self.lbl_title.config(text="⏳  Đang sắp xếp…")

        def _run():
            try:
                steps = self.engine.sort(self.source_file, self.output_file)
                self.root.after(0, lambda: self._on_sort_done(steps))
            except Exception as exc:
                self.root.after(0, lambda: (
                    messagebox.showerror("Lỗi Sắp Xếp", str(exc)),
                    self.sv_status.set("Lỗi!")
                ))

        threading.Thread(target=_run, daemon=True).start()

    def _on_sort_done(self, steps: list[dict]):
        self.steps     = steps
        self.cur_step  = 0
        self.sv_status.set(f"Sắp xếp hoàn tất · {len(steps)} bước")
        self._show_step()

    # ══ STEP NAVIGATION ═══════════════════════════════════════════════════════
    def _show_step(self):
        if not self.steps:
            return
        s = self.steps[self.cur_step]
        total = len(self.steps)
        self.lbl_title.config(
            text=f"Bước {self.cur_step + 1} / {total}  –  {s['title']}")
        self.lbl_desc.config(text=s["description"])
        self.lbl_step.config(text=f"Bước:  {self.cur_step + 1} / {total}")
        self.vis.render(s)

    def _first_step(self):
        self.cur_step = 0
        self._show_step()

    def _last_step(self):
        if self.steps:
            self.cur_step = len(self.steps) - 1
            self._show_step()

    def _prev_step(self):
        if self.cur_step > 0:
            self.cur_step -= 1
            self._show_step()

    def _next_step(self):
        if self.steps and self.cur_step < len(self.steps) - 1:
            self.cur_step += 1
            self._show_step()

    def _toggle_play(self):
        if not self.steps:
            messagebox.showwarning("Chưa Sắp Xếp",
                                   "Hãy chạy sắp xếp trước khi phát!")
            return
        self.is_playing = not self.is_playing
        self.play_btn.config(text="⏸" if self.is_playing else "▶")
        if self.is_playing:
            self._autoplay_tick()

    def _autoplay_tick(self):
        if not self.is_playing:
            return
        if self.cur_step < len(self.steps) - 1:
            self.cur_step += 1
            self._show_step()
            self.root.after(self.speed_ms.get(), self._autoplay_tick)
        else:
            self.is_playing = False
            self.play_btn.config(text="▶")
            self.sv_status.set("Phát hoàn tất!")

    # ══ SAVE / VIEW ═══════════════════════════════════════════════════════════
    def _save_result(self):
        if not self.output_file or not os.path.exists(self.output_file):
            messagebox.showwarning("Chưa Có Kết Quả",
                                   "Hãy chạy sắp xếp trước để có file kết quả!")
            return
        dest = filedialog.asksaveasfilename(
            title="Lưu file đã sắp xếp",
            defaultextension=".bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        if dest:
            shutil.copy2(self.output_file, dest)
            messagebox.showinfo("Đã Lưu", f"File kết quả:\n{dest}")

    def _view_file(self, which: str):
        path = self.source_file if which == "source" else self.output_file
        if not path:
            messagebox.showwarning("Không Có File",
                                   "Chưa có file nguồn." if which == "source"
                                   else "Chưa có file kết quả. Hãy chạy sắp xếp!")
            return
        if not os.path.exists(path):
            messagebox.showerror("Lỗi", f"File không tồn tại:\n{path}")
            return

        numbers = SortEngine._read_floats(path)

        win = tk.Toplevel(self.root)
        win.title(f"Nội Dung: {Path(path).name}")
        win.geometry("540x500")
        win.configure(bg=SURFACE0)

        hdr_txt = "Nguồn (chưa sắp xếp)" if which == "source" else "Kết Quả (đã sắp xếp)"
        tk.Label(win, text=f"📊  {hdr_txt}  —  {Path(path).name}",
                 font=("Segoe UI", 12, "bold"), bg=SURFACE0, fg=TEXT).pack(pady=12)
        tk.Label(win, text=f"{len(numbers)} số thực  ·  {os.path.getsize(path):,} bytes",
                 font=("Segoe UI", 10), bg=SURFACE0, fg=SUBTEXT).pack()

        frm = tk.Frame(win, bg=SURFACE0)
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        txt = tk.Text(frm, bg=SURFACE1, fg=TEXT, font=("Consolas", 11),
                      relief="flat", insertbackground=TEXT, selectbackground=BLUE)
        sb  = ttk.Scrollbar(frm, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)

        # Column headers
        txt.insert(tk.END, f"{'Chỉ Số':>8}   {'Giá Trị':>16}\n")
        txt.insert(tk.END, "─" * 28 + "\n")
        for idx, v in enumerate(numbers):
            txt.insert(tk.END, f"{idx:>8}   {v:>16.6f}\n")
        txt.config(state="disabled")

    # ══ MISC ══════════════════════════════════════════════════════════════════
    def _reset_visualiser(self):
        self.steps    = []
        self.cur_step = 0
        self.is_playing = False
        if self.play_btn:
            self.play_btn.config(text="▶")
        self.lbl_title.config(text="─  Chờ sắp xếp  ─")
        self.lbl_desc.config(text="Nhấn 'Bắt Đầu Sắp Xếp' để bắt đầu.")
        self.lbl_step.config(text="Bước:  – / –")
        if self.canvas:
            self.canvas.delete("all")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    # App icon (simple coloured icon if no .ico file)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = App(root)
    root.mainloop()
