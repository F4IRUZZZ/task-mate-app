import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date
import calendar as _cal

import database as db

# ── Tema dikontrol oleh _DARK (True=gelap, False=terang) ─────────────────────
_DARK = False   # default TERANG
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Palet warna [dark, light] ─────────────────────────────────────────────────
C = {
    "bg":        ["#1E2022", "#EEF0F5"],
    "frame":     ["#27292C", "#FFFFFF"],
    "input":     ["#32353A", "#F5F6FA"],
    "border":    ["#4A4F55", "#C8CDD6"],
    "text":      ["#DCE4EE", "#1A1A2E"],
    "subtext":   ["#8A9099", "#6B7280"],
    "ablue":     ["#1f538d", "#2563EB"],
    "ared":      ["#9c2b2b", "#DC2626"],
    "agreen":    ["#2b7a4e", "#16A34A"],
    "hblue":     ["#14375e", "#1D4ED8"],
    "hred":      ["#6e1e1e", "#B91C1C"],
    "hgreen":    ["#1a5233", "#15803D"],
    "rowhov":    ["#3A3D42", "#E2E8F0"],
    "sep":       ["#38393C", "#E2E8F0"],
    # Grid canvas
    "grid_line": ["#3A3D42", "#C0C8D4"],
    "grid_hdr":  ["#20222A", "#E8ECF2"],
    "grid_hfg":  ["#9CAAB8", "#4B5563"],
    "grid_base": ["#2A2D32", "#F7F8FC"],
    # Baris status
    "rp_bg":     ["#3A3E46", "#E2E8F0"],   # pending  → abu jelas
    "rp_fg":     ["#C0C6D0", "#475569"],
    "rd_bg":     ["#0F3D22", "#BBF7D0"],   # done     → hijau jelas
    "rd_fg":     ["#4ADE80", "#14532D"],
    "ro_bg":     ["#4A1515", "#FEE2E2"],   # overdue  → merah jelas
    "ro_fg":     ["#F87171", "#7F1D1D"],
    # Form fields
    "disinput":  ["#252729", "#E8E8E8"],
    "disborder": ["#404448", "#CCCCCC"],
    "distext":   ["#555A60", "#AAAAAA"],
}

def _c(key):
    return C[key][0] if _DARK else C[key][1]


# ═══════════════════════════════════════════════════════════════════════════════
#  GridCanvas  — tabel kustom dengan grid lines nyata
# ═══════════════════════════════════════════════════════════════════════════════
class GridCanvas(tk.Canvas):
    """
    Tabel berbasis Canvas: header + baris bercolour + grid lines horizontal
    dan vertikal yang sesungguhnya.  Tidak bergantung pada ttk.Treeview.
    """

    HEADER_H = 36
    ROW_H    = 40
    FONT     = ("Segoe UI", 11)
    HFONT    = ("Segoe UI", 11, "bold")
    PAD_X    = 10

    def __init__(self, parent, columns, **kw):
        """
        columns: [(col_id, header_text, width, anchor), ...]
        anchor: "center" | "w"
        """
        super().__init__(parent, highlightthickness=0, bd=0, **kw)
        self._cols   = list(columns)
        self._items  = []        # [{"iid": str, "values": tuple, "tag": str}]
        self._sel    = set()     # selected iids
        self._last_clicked = None  # iid terakhir diklik
        self._offset = 0         # scroll offset px
        self._yscb   = None      # yscrollcommand callback

        # colour defaults (updated via set_colors)
        self._bg     = "#2A2D32"; self._fg  = "#DCE4EE"
        self._hbg    = "#20222A"; self._hfg = "#9CAAB8"
        self._lc     = "#3A3D42"; self._selb = "#1f538d"
        self._tag_c  = {}  # tag -> (bg, fg)

        self.bind("<Configure>",  lambda e: self.after(5, self._render))
        self.bind("<Button-1>",   self._on_click)
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Button-4>",   lambda e: self._scroll(-3))
        self.bind("<Button-5>",   lambda e: self._scroll(3))

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_colors(self, bg, fg, hdr_bg, hdr_fg, line_color, sel_bg, tag_colors):
        self._bg   = bg;  self._fg  = fg
        self._hbg  = hdr_bg; self._hfg = hdr_fg
        self._lc   = line_color; self._selb = sel_bg
        self._tag_c = tag_colors
        self.configure(bg=bg)
        self._render()

    def delete_all(self):
        self._items.clear(); self._sel.clear(); self._offset = 0
        self._update_sb(); self._render()

    def insert(self, iid, values, tag=""):
        self._items.append({"iid": str(iid), "values": values, "tag": tag})

    def commit(self):
        """Call after bulk inserts to trigger one redraw."""
        self._offset = 0; self._update_sb(); self._render()

    def selection(self):
        return list(self._sel)

    def selection_remove(self, iids=None):
        if iids is None:
            self._sel.clear()
        else:
            for i in iids: self._sel.discard(str(i))
        self._render()

    def selection_set(self, iids):
        self._sel = {str(i) for i in iids}; self._render()

    def get_children(self):
        return [item["iid"] for item in self._items]

    def set_yscrollcommand(self, cmd):
        self._yscb = cmd

    def yview(self, *args):
        """Standard Tkinter scrollbar protocol."""
        if not args: return
        n = len(self._items)
        total_h = max(1, n * self.ROW_H)
        vis_h   = max(1, self.winfo_height() - self.HEADER_H)
        if args[0] == "moveto":
            frac = float(args[1])
            max_off = max(0, total_h - vis_h)
            self._offset = max(0, min(int(frac * total_h), max_off))
        elif args[0] == "scroll":
            amt  = int(args[1])
            unit = args[2]
            step = self.ROW_H if unit == "units" else vis_h
            self._offset += amt * step
            self._offset = max(0, min(self._offset, max(0, total_h - vis_h)))
        self._render(); self._update_sb()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _update_sb(self):
        if not self._yscb: return
        n = len(self._items)
        total_h = max(1, n * self.ROW_H)
        vis_h   = max(1, self.winfo_height() - self.HEADER_H)
        if total_h <= vis_h:
            self._yscb(0.0, 1.0)
        else:
            lo = self._offset / total_h
            hi = min(1.0, (self._offset + vis_h) / total_h)
            self._yscb(lo, hi)

    def _render(self):
        self.delete("all")
        cw = self.winfo_width(); ch = self.winfo_height()
        if cw < 4 or ch < 4: return

        HH = self.HEADER_H; RH = self.ROW_H

        # ── Baca warna LANGSUNG dari tema aktif setiap render ───────────────
        # (tidak bergantung pada stored self._bg agar selalu sinkron dengan tema)
        BG   = _c("grid_base")
        HBG  = _c("grid_hdr")
        HFG  = _c("grid_hfg")
        LC   = _c("grid_line")
        SELB = _c("ablue")
        FG   = _c("text")
        TAG  = {
            "pending": (_c("rp_bg"), _c("rp_fg")),
            "done":    (_c("rd_bg"), _c("rd_fg")),
            "overdue": (_c("ro_bg"), _c("ro_fg")),
        }

        # Paksa warna canvas widget agar area kosong juga ikut tema
        self.configure(bg=BG)
        self.create_rectangle(0, 0, cw, ch, fill=BG, outline="")

        # ── Hitung lebar kolom proporsional terhadap lebar canvas ──────────
        total_w = sum(w for _, _, w, _ in self._cols)
        scale   = cw / max(total_w, 1)
        col_widths = [int(w * scale) for _, _, w, _ in self._cols]
        col_widths[-1] = cw - sum(col_widths[:-1])

        # ── Header ─────────────────────────────────────────────────────────
        self.create_rectangle(0, 0, cw, HH, fill=HBG, outline="")
        x = 0
        for i, (col_id, col_text, _, col_anc) in enumerate(self._cols):
            tx = x + col_widths[i] // 2
            self.create_text(tx, HH // 2, text=col_text,
                             fill=HFG, font=self.HFONT, anchor="center")
            x += col_widths[i]

        self.create_line(0, HH, cw, HH, fill=LC, width=2)
        x = 0
        for col_w in col_widths[:-1]:
            x += col_w
            self.create_line(x, 0, x, HH, fill=LC, width=1)

        # ── Rows ───────────────────────────────────────────────────────────
        for i, item in enumerate(self._items):
            y0 = HH + i * RH - self._offset
            y1 = y0 + RH
            if y1 <= HH: continue
            if y0 >= ch: break

            iid = item["iid"]; tag = item["tag"]; vals = item["values"]
            checked = iid in self._sel
            if checked:
                bg, fg = SELB, "#FFFFFF"
            else:
                bg, fg = TAG.get(tag, (BG, FG))

            self.create_rectangle(0, max(y0, HH), cw, min(y1, ch),
                                   fill=bg, outline="")

            mid_y = (y0 + y1) // 2
            if mid_y < HH or mid_y > ch: continue

            x = 0
            vi = 0   # index ke vals, hanya naik untuk kolom non-cb
            for j, (col_id, _, _, col_anc) in enumerate(self._cols):
                cw_j = col_widths[j]
                # Kolom checkbox: tampilkan ☑/☐ tanpa ambil vals
                if col_id == "cb":
                    self.create_text(x + cw_j // 2, mid_y,
                                     text="☑" if checked else "☐",
                                     fill=fg, font=("Segoe UI", 13), anchor="center")
                else:
                    val = str(vals[vi]) if vi < len(vals) else ""
                    if col_anc == "center":
                        tx = x + cw_j // 2; ta = "center"
                    else:
                        tx = x + self.PAD_X; ta = "w"
                    self.create_text(tx, mid_y, text=val, fill=fg,
                                      font=self.FONT, anchor=ta,
                                      width=cw_j - self.PAD_X * 2)
                    vi += 1
                x += cw_j

        # ── Grid lines ─────────────────────────────────────────────────────
        for i in range(len(self._items) + 1):
            y = HH + i * RH - self._offset
            if HH <= y <= ch:
                self.create_line(0, y, cw, y, fill=LC, width=1)

        x = 0
        for col_w in col_widths[:-1]:
            x += col_w
            self.create_line(x, 0, x, ch, fill=LC, width=1)

        self.create_rectangle(0, 0, cw-1, ch-1, fill="", outline=LC, width=1)

    def _on_click(self, event):
        if event.y <= self.HEADER_H: return
        idx = (event.y - self.HEADER_H + self._offset) // self.ROW_H
        if 0 <= idx < len(self._items):
            iid = self._items[idx]["iid"]
            self._last_clicked = iid          # simpan yg baru diklik
            if iid in self._sel:
                self._sel.discard(iid)
            else:
                self._sel.add(iid)
        else:
            self._last_clicked = None
            self._sel.clear()
        self._render()
        self.event_generate("<<GridSelect>>")

    def _on_wheel(self, event):
        self._scroll(-3 if event.delta > 0 else 3)

    def _scroll(self, d):
        n = len(self._items)
        total_h = n * self.ROW_H
        vis_h   = max(1, self.winfo_height() - self.HEADER_H)
        max_off = max(0, total_h - vis_h)
        self._offset = max(0, min(self._offset + d * self.ROW_H, max_off))
        self._render(); self._update_sb()


# ═══════════════════════════════════════════════════════════════════════════════
#  CustomCalendar
# ═══════════════════════════════════════════════════════════════════════════════
class CustomCalendar(tk.Toplevel):
    CW = 46; CH = 42; PAD = 14; RADIUS = 18
    DAYS_SHORT = ["Mo","Tu","We","Th","Fr","Sa","Su"]
    MONTHS_ID  = ["Januari","Februari","Maret","April","Mei","Juni",
                  "Juli","Agustus","September","Oktober","November","Desember"]

    def __init__(self, parent, on_select, anchor_x, btn_top, btn_bottom,
                 initial_date=None, dark_mode=True):
        super().__init__(parent)
        self.on_select = on_select
        self._hover = None; self._day_cells = {}

        if dark_mode:
            self.CB="#1C1F21";self.CN="#17191B";self.CS="#2C2F32"
            self.CMF="#E8EDF2";self.CA="#5B8DD4";self.CAH="#FFFFFF"
            self.CHW="#4E7BC4";self.CHWK="#6499D9"
            self.CD="#CDD6E0";self.CWK="#7AABEE"
            self.CHV="#2A2E32";self.CSB="#1f538d";self.CSF="#FFFFFF"
            self.CTO="#2b9c54";self.CTF="#5FDD94"
            self.CFB="#252829";self.CFH="#333739"
            self.CFBT="#1A3E6A";self.CFBC="#3B1A1A"
        else:
            self.CB="#FFFFFF";self.CN="#F0F2F5";self.CS="#E0E4EA"
            self.CMF="#1A1A2E";self.CA="#2563EB";self.CAH="#1D4ED8"
            self.CHW="#2563EB";self.CHWK="#3B82F6"
            self.CD="#374151";self.CWK="#2563EB"
            self.CHV="#E5E7EB";self.CSB="#2563EB";self.CSF="#FFFFFF"
            self.CTO="#16A34A";self.CTF="#15803D"
            self.CFB="#F9FAFB";self.CFH="#E5E7EB"
            self.CFBT="#DBEAFE";self.CFBC="#FEE2E2"

        self.wm_overrideredirect(True)
        self.configure(bg=self.CB); self.resizable(False, False)
        today = datetime.today()
        self._today = (today.year, today.month, today.day)
        self._sel = None
        if initial_date:
            try:
                d = datetime.strptime(initial_date, "%Y-%m-%d")
                self._year, self._month = d.year, d.month
                self._sel = (d.year, d.month, d.day)
            except ValueError:
                self._year, self._month = today.year, today.month
        else:
            self._year, self._month = today.year, today.month

        self._build_ui()
        self.geometry("+9999+9999"); self.update_idletasks()
        W = self.winfo_reqwidth(); H = self.winfo_reqheight()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        x = max(min(anchor_x, sw-W-8), 8)
        TASKBAR=52; GAP=4
        y = btn_bottom+GAP if btn_bottom+H+GAP <= sh-TASKBAR else btn_top-H-GAP
        self.geometry(f"+{x}+{y}")
        self.config(highlightbackground="#3A3D40", highlightthickness=1)
        self.lift(); self.focus_force()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        nav = tk.Frame(self, bg=self.CN); nav.pack(fill="x", ipady=10)
        prev = tk.Label(nav, text="  ◀  ", bg=self.CN, fg=self.CA,
                        font=("Segoe UI",13), cursor="hand2")
        prev.pack(side="left", padx=(self.PAD-4, 0))
        prev.bind("<Button-1>", lambda e: self._change_month(-1))
        prev.bind("<Enter>", lambda e: prev.config(fg=self.CAH))
        prev.bind("<Leave>", lambda e: prev.config(fg=self.CA))
        self._lbl_month = tk.Label(nav, text="", bg=self.CN, fg=self.CMF,
                                    font=("Segoe UI",13,"bold"))
        self._lbl_month.pack(side="left", expand=True)
        nxt = tk.Label(nav, text="  ▶  ", bg=self.CN, fg=self.CA,
                       font=("Segoe UI",13), cursor="hand2")
        nxt.pack(side="right", padx=(0, self.PAD-4))
        nxt.bind("<Button-1>", lambda e: self._change_month(1))
        nxt.bind("<Enter>", lambda e: nxt.config(fg=self.CAH))
        nxt.bind("<Leave>", lambda e: nxt.config(fg=self.CA))
        tk.Frame(self, bg=self.CS, height=1).pack(fill="x")
        hdr = tk.Frame(self, bg=self.CB); hdr.pack(fill="x", padx=self.PAD, pady=(10,4))
        for i, d in enumerate(self.DAYS_SHORT):
            fg = self.CHWK if i >= 5 else self.CHW
            tk.Label(hdr, text=d, bg=self.CB, fg=fg,
                     font=("Segoe UI",9,"bold"), width=4, anchor="center").grid(row=0, column=i)
        self._cv = tk.Canvas(self, bg=self.CB, highlightthickness=0,
                              width=self.CW*7, height=self.CH*6+12)
        self._cv.pack(padx=self.PAD, pady=(2,8))
        self._cv.bind("<Motion>",   self._on_motion)
        self._cv.bind("<Leave>",    self._on_leave)
        self._cv.bind("<Button-1>", self._on_click)
        tk.Frame(self, bg=self.CS, height=1).pack(fill="x")
        foot = tk.Frame(self, bg=self.CB); foot.pack(fill="x", padx=self.PAD, pady=(8,10))
        bt = tk.Label(foot, text=" 📅 Hari Ini ", bg=self.CFBT,
                       fg="#7ADBFF" if self.CB=="#1C1F21" else "#1D4ED8",
                       font=("Segoe UI",10,"bold"), cursor="hand2", padx=6, pady=4)
        bt.pack(side="left")
        bt.bind("<Button-1>", self._go_today)
        bc = tk.Label(foot, text=" ✖ Hapus ", bg=self.CFBC,
                       fg="#FF7A7A" if self.CB=="#1C1F21" else "#DC2626",
                       font=("Segoe UI",10,"bold"), cursor="hand2", padx=6, pady=4)
        bc.pack(side="right")
        bc.bind("<Button-1>", self._clear_date)
        self._draw()

    def _draw(self):
        self._cv.delete("all"); self._day_cells.clear()
        self._lbl_month.config(text=f"{self.MONTHS_ID[self._month-1]}  {self._year}")
        first_wd = _cal.monthrange(self._year, self._month)[0]
        num_days = _cal.monthrange(self._year, self._month)[1]
        R = self.RADIUS; row, col = 0, first_wd
        for day in range(1, num_days+1):
            cx = col*self.CW+self.CW//2; cy = row*self.CH+self.CH//2+6
            is_sel = self._sel == (self._year, self._month, day)
            is_today = self._today == (self._year, self._month, day)
            is_weekend = col >= 5; is_hovered = self._hover == (row, col)
            if is_sel:
                self._cv.create_oval(cx-R,cy-R,cx+R,cy+R, fill=self.CSB, outline="#4A7BC4", width=1.5)
            elif is_today and is_hovered:
                self._cv.create_oval(cx-R,cy-R,cx+R,cy+R, fill=self.CHV, outline=self.CTO, width=2)
            elif is_today:
                self._cv.create_oval(cx-R,cy-R,cx+R,cy+R, fill="", outline=self.CTO, width=2)
            elif is_hovered:
                self._cv.create_oval(cx-R,cy-R,cx+R,cy+R, fill=self.CHV, outline="")
            fg = (self.CSF if is_sel else (self.CTF if is_today else (self.CWK if is_weekend else self.CD)))
            bold = is_sel or is_today
            self._cv.create_text(cx, cy, text=str(day), fill=fg,
                                  font=("Segoe UI", 11, "bold" if bold else "normal"))
            self._day_cells[(row, col)] = day
            col += 1
            if col == 7: col = 0; row += 1

    def _xy_to_cell(self, x, y):
        col = int(x // self.CW); row = int((y-6) // self.CH)
        return (row, col) if 0 <= col <= 6 and 0 <= row <= 5 else (None, None)

    def _on_motion(self, event):
        cell = self._xy_to_cell(event.x, event.y)
        if cell != self._hover:
            self._hover = cell if cell[0] is not None else None
            self._draw()

    def _on_leave(self, event):
        if self._hover is not None: self._hover = None; self._draw()

    def _on_click(self, event):
        row, col = self._xy_to_cell(event.x, event.y)
        if row is None: return
        day = self._day_cells.get((row, col))
        if day is None: return
        self._sel = (self._year, self._month, day); self._draw()
        self.on_select(f"{self._year:04d}-{self._month:02d}-{day:02d}")
        self.after(150, self.destroy)

    def _change_month(self, delta):
        m = self._month + delta; y = self._year
        if m > 12: m, y = 1, y+1
        if m < 1:  m, y = 12, y-1
        self._month, self._year = m, y; self._hover = None; self._draw()

    def _go_today(self, event=None):
        y, m, d = self._today
        self._year, self._month = y, m; self._sel = self._today; self._draw()
        self.on_select(f"{y:04d}-{m:02d}-{d:02d}"); self.after(150, self.destroy)

    def _clear_date(self, event=None):
        self._sel = None; self.on_select(""); self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
#  TaskmateApp
# ═══════════════════════════════════════════════════════════════════════════════
class TaskmateApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark" if _DARK else "light")
        super().__init__()
        self.title("Taskmate — Task Manager")
        self.geometry("1120x840"); self.minsize(860, 660)
        self.configure(fg_color=_c("bg"))
        self.after(0, lambda: self.state("zoomed"))

        sukses, pesan = db.test_koneksi()
        if not sukses:
            messagebox.showerror("Koneksi Gagal",
                f"Tidak dapat terhubung ke MySQL.\n\nError: {pesan}\n\n"
                "Pastikan MySQL sudah berjalan dan konfigurasi di database.py sudah benar.")
            self.destroy(); return

        self.tasks           = []
        self.selected_id     = None
        self.filter_mode     = tk.StringVar(value="All")
        self.all_task_names  = set(db.ambil_semua_nama_tugas())
        self._kat_list       = db.ambil_semua_kategori()
        self.autocomplete_win      = None
        self._autocomplete_listbox = None
        self._cal_popup      = None

        self._build_ui()
        self._refresh_table()

    # ── Bangun UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_form_frame()
        self._build_table_frame()

    # ── Frame Atas: Form ──────────────────────────────────────────────────────
    def _build_form_frame(self):
        self.form_frame = ctk.CTkFrame(self, fg_color=_c("frame"), corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=20, pady=(20,8), sticky="ew")
        self.form_frame.grid_columnconfigure((0,1), weight=1)

        # Header
        hdr = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(16,0))

        lhdr = ctk.CTkFrame(hdr, fg_color="transparent"); lhdr.pack(side="left")
        ctk.CTkLabel(lhdr, text="☑", font=("Segoe UI",26),
                     text_color=_c("ablue")).pack(side="left", padx=(0,8))
        ctk.CTkLabel(lhdr, text="Taskmate", font=("Segoe UI",22,"bold"),
                     text_color=_c("text")).pack(side="left")

        # Tombol toggle tema
        self.btn_theme = ctk.CTkButton(
            hdr, text="🌙 Gelap", width=120, height=32, corner_radius=16,
            fg_color=_c("input"), hover_color=_c("rowhov"),
            text_color=_c("text"), border_width=1, border_color=_c("border"),
            font=("Segoe UI",12), command=self._toggle_theme)
        self.btn_theme.pack(side="right")

        ctk.CTkFrame(self.form_frame, height=1, fg_color=_c("sep")).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(12,0))

        # ── Kolom Kiri ─────────────────────────────────────────────────────
        left = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        left.grid(row=2, column=0, sticky="nsew", padx=(20,10), pady=16)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Task Name", text_color=_c("subtext"),
                     font=("Segoe UI",12)).grid(row=0, column=0, sticky="w", pady=(0,4))

        self.entry_name_wrapper = ctk.CTkFrame(left, fg_color="transparent")
        self.entry_name_wrapper.grid(row=1, column=0, sticky="ew")
        self.entry_name_wrapper.grid_columnconfigure(0, weight=1)

        self.entry_name = ctk.CTkEntry(
            self.entry_name_wrapper, fg_color=_c("input"),
            border_color=_c("border"), text_color=_c("text"),
            height=36, corner_radius=6)
        self.entry_name.grid(row=0, column=0, sticky="ew")

        self.lbl_name_hint = ctk.CTkLabel(
            self.entry_name_wrapper,
            text="🔒 Hanya deadline yang dapat diubah saat memilih task",
            text_color="#F0A500", font=("Segoe UI",10), fg_color="transparent")

        self.entry_name.bind("<KeyRelease>", self._on_name_keyrelease)
        self.entry_name.bind("<FocusOut>",   self._schedule_ac_hide)
        self.entry_name.bind("<Escape>",     lambda e: self._hide_autocomplete())
        self.entry_name.bind("<Down>",       self._autocomplete_focus_list)

        ctk.CTkFrame(left, height=12, fg_color="transparent").grid(row=2, column=0)
        ctk.CTkLabel(left, text="Description", text_color=_c("subtext"),
                     font=("Segoe UI",12)).grid(row=3, column=0, sticky="w", pady=(0,4))
        self.entry_desc = ctk.CTkTextbox(
            left, fg_color=_c("input"), border_color=_c("border"),
            text_color=_c("text"), height=72, corner_radius=6, border_width=2)
        self.entry_desc.grid(row=4, column=0, sticky="ew")

        # ── Kolom Kanan ─────────────────────────────────────────────────────
        right = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        right.grid(row=2, column=1, sticky="nsew", padx=(10,20), pady=16)
        right.grid_columnconfigure(0, weight=1)

        # Kategori — editable + bisa tambah baru
        ctk.CTkLabel(right, text="Kategori", text_color=_c("subtext"),
                     font=("Segoe UI",12)).grid(row=0, column=0, sticky="w", pady=(0,4))

        self.combo_kategori = ctk.CTkComboBox(
            right, values=self._kat_list,
            fg_color=_c("input"), border_color=_c("border"),
            text_color=_c("text"), button_color=_c("border"),
            button_hover_color=_c("ablue"), height=36, corner_radius=6,
            state="normal",           # ← editable, user bisa ketik kategori baru
            command=self._on_kategori_changed)
        self.combo_kategori.set("Umum")
        self.combo_kategori.grid(row=1, column=0, sticky="ew", pady=(0,2))

        self.lbl_kat_hint = ctk.CTkLabel(
            right, text="💡 Ketik nama baru untuk buat kategori",
            text_color=_c("subtext"), font=("Segoe UI",10), fg_color="transparent")
        self.lbl_kat_hint.grid(row=2, column=0, sticky="w", pady=(0,10))

        ctk.CTkLabel(right, text="Deadline", text_color=_c("subtext"),
                     font=("Segoe UI",12)).grid(row=3, column=0, sticky="w", pady=(0,4))

        dl_row = ctk.CTkFrame(right, fg_color="transparent")
        dl_row.grid(row=4, column=0, sticky="ew")
        dl_row.grid_columnconfigure(0, weight=1)

        self.entry_deadline = ctk.CTkEntry(
            dl_row, fg_color=_c("input"), border_color=_c("border"),
            text_color=_c("text"), height=36, corner_radius=6,
            placeholder_text="YYYY-MM-DD  atau pilih  📅")
        self.entry_deadline.grid(row=0, column=0, sticky="ew", padx=(0,6))

        self.btn_calendar = ctk.CTkButton(
            dl_row, text="📅", width=38, height=36, corner_radius=6,
            fg_color=_c("ablue"), hover_color=_c("hblue"),
            text_color=_c("text"), font=("Segoe UI",15),
            command=self._open_calendar)
        self.btn_calendar.grid(row=0, column=1)

        # Tombol Aksi
        btn_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(4,20))
        cfg = {"width":145, "height":38, "corner_radius":6, "font":("Segoe UI",13,"bold")}

        ctk.CTkButton(btn_frame, text="➕ Add Task",
                      fg_color=_c("ablue"), hover_color=_c("hblue"),
                      text_color=_c("text"), command=self._add_task, **cfg).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Update Task",
                      fg_color=_c("ablue"), hover_color=_c("hblue"),
                      text_color=_c("text"), command=self._update_task, **cfg).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="✖ Clear Form",
                      fg_color=_c("input"), hover_color=_c("rowhov"),
                      text_color=_c("text"), border_width=1, border_color=_c("border"),
                      command=self._clear_form, **cfg).pack(side="left", padx=6)

    # ── Frame Bawah: Tabel ────────────────────────────────────────────────────
    def _build_table_frame(self):
        self.table_frame = ctk.CTkFrame(self, fg_color=_c("frame"), corner_radius=10)
        self.table_frame.grid(row=1, column=0, padx=20, pady=(0,20), sticky="nsew")
        self.table_frame.grid_rowconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # Controls
        ctrl = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        ctrl.grid(row=0, column=0, sticky="ew", padx=20, pady=(16,8))
        ctrl.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(ctrl, text="Filter:", text_color=_c("subtext"),
                     font=("Segoe UI",12)).grid(row=0, column=0, padx=(0,8))
        self.seg_filter = ctk.CTkSegmentedButton(
            ctrl, values=["All","Pending","Completed"],
            variable=self.filter_mode,
            fg_color=_c("input"), selected_color=_c("ablue"),
            selected_hover_color=_c("hblue"),
            unselected_color=_c("input"), unselected_hover_color=_c("rowhov"),
            text_color=_c("subtext"), font=("Segoe UI",12),
            command=lambda _: self._refresh_table())
        self.seg_filter.grid(row=0, column=1, sticky="w")

        btn_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_row.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(btn_row, text="✔ Mark Completed", width=155, height=34,
                      corner_radius=6, font=("Segoe UI",12,"bold"),
                      fg_color=_c("agreen"), hover_color=_c("hgreen"),
                      text_color="white", command=self._mark_completed).pack(side="left")

        # GridCanvas + Scrollbar
        gc_outer = ctk.CTkFrame(self.table_frame, fg_color=_c("grid_line"),
                                 corner_radius=8)
        gc_outer.grid(row=1, column=0, padx=20, sticky="nsew")
        gc_outer.grid_rowconfigure(0, weight=1)
        gc_outer.grid_columnconfigure(0, weight=1)

        cols = [
            ("cb",       "✓",          50,  "center"),
            ("name",     "Task Name",  220, "w"),
            ("desc",     "Deskripsi",  220, "w"),
            ("kategori", "Kategori",   110, "center"),
            ("status",   "Status",     100, "center"),
            ("deadline", "Deadline",   120, "center"),
        ]

        self.grid = GridCanvas(gc_outer, columns=cols,
                                bg=_c("grid_base"), cursor="arrow")
        self._apply_grid_colors()
        self.grid.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.grid.bind("<<GridSelect>>", self._on_grid_select)

        sb = tk.Scrollbar(gc_outer, orient="vertical",
                           command=self.grid.yview,
                           bg=_c("rowhov"), troughcolor=_c("grid_base"),
                           activebackground=_c("ablue"), width=12)
        sb.grid(row=0, column=1, sticky="ns", pady=1)
        self.grid.set_yscrollcommand(sb.set)

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.table_frame,
            text="Total Tasks: 0  |  Tidak ada task dipilih",
            text_color=_c("subtext"), font=("Segoe UI",11), anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=22, pady=(6,14))

    # ── Grid colours ──────────────────────────────────────────────────────────
    def _apply_grid_colors(self):
        self.grid.set_colors(
            bg        = _c("grid_base"),
            fg        = _c("text"),
            hdr_bg    = _c("grid_hdr"),
            hdr_fg    = _c("grid_hfg"),
            line_color= _c("grid_line"),
            sel_bg    = _c("ablue"),
            tag_colors= {
                "pending": (_c("rp_bg"), _c("rp_fg")),
                "done":    (_c("rd_bg"), _c("rd_fg")),
                "overdue": (_c("ro_bg"), _c("ro_fg")),
            }
        )

    # ── Toggle Tema ───────────────────────────────────────────────────────────
    def _toggle_theme(self):
        global _DARK
        _DARK = not _DARK
        ctk.set_appearance_mode("dark" if _DARK else "light")
        self.configure(fg_color=_c("bg"))
        # Rebuild kedua frame agar semua warna CTk ikut tema baru
        self.form_frame.destroy()
        self.table_frame.destroy()
        self._build_form_frame()
        self._build_table_frame()
        self.btn_theme.configure(text="☀️ Terang" if _DARK else "🌙 Gelap")
        self._refresh_table()

    # ── Kategori: handle input baru ───────────────────────────────────────────
    def _on_kategori_changed(self, value):
        """Dipanggil saat user pilih dari dropdown (bukan ketik manual)."""
        pass  # nilai sudah ter-set di combo

    def _resolve_kategori(self, nama):
        """
        Pastikan kategori ada di DB.
        Kalau belum ada, tanya user apakah mau buat baru.
        Return nama kategori (bersih) atau None jika batal.
        """
        nama = nama.strip()
        if not nama:
            messagebox.showwarning("Peringatan", "Nama kategori tidak boleh kosong.", parent=self)
            return None
        if nama in self._kat_list:
            return nama
        # Kategori belum ada → tanya user
        buat = messagebox.askyesno(
            "Kategori Baru",
            f'Kategori "{nama}" belum ada.\n\nBuat kategori baru ini?',
            parent=self)
        if not buat:
            return None
        try:
            db.tambah_kategori_baru(nama)
        except RuntimeError as e:
            messagebox.showerror("Error Database", str(e), parent=self); return None
        # Update daftar lokal & combo
        self._kat_list = db.ambil_semua_kategori()
        self.combo_kategori.configure(values=self._kat_list)
        return nama

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _get_form_values(self):
        name     = self.entry_name.get().strip()
        desc     = self.entry_desc.get("1.0","end-1c").strip()
        kategori = self.combo_kategori.get().strip()
        deadline = self.entry_deadline.get().strip()
        return name, desc, kategori, deadline

    def _validate_deadline(self, deadline):
        if not deadline: return True
        try: datetime.strptime(deadline, "%Y-%m-%d"); return True
        except ValueError: return False

    def _add_task(self):
        name, desc, kategori, deadline = self._get_form_values()
        if not name:
            messagebox.showwarning("Peringatan","Task Name tidak boleh kosong.", parent=self); return
        if not self._validate_deadline(deadline):
            messagebox.showwarning("Peringatan","Format Deadline harus YYYY-MM-DD.", parent=self); return
        kategori = self._resolve_kategori(kategori)
        if kategori is None: return
        try:
            db.tambah_tugas(name, desc, kategori, deadline)
        except RuntimeError as e:
            messagebox.showerror("Error Database", str(e), parent=self); return
        self.all_task_names.add(name)
        self._clear_form(); self._refresh_table()

    def _update_task(self):
        if self.selected_id is None:
            messagebox.showinfo("Info","Pilih task yang ingin diupdate deadlinenya.", parent=self); return
        deadline = self.entry_deadline.get().strip()
        if not self._validate_deadline(deadline):
            messagebox.showwarning("Peringatan","Format Deadline harus YYYY-MM-DD.", parent=self); return
        try:
            db.perbarui_deadline(self.selected_id, deadline)
        except RuntimeError as e:
            messagebox.showerror("Error Database", str(e), parent=self); return
        self._clear_form(); self._refresh_table()

    def _delete_task(self):
        sel_ids = [int(i) for i in self.grid.selection()]
        if not sel_ids:
            messagebox.showinfo("Info","Centang task yang ingin dihapus.", parent=self); return
        names = [t["name"] for t in self.tasks if t["id"] in sel_ids]
        label = f"{len(sel_ids)} task" if len(sel_ids) > 1 else f"\"{names[0]}\""
        if not messagebox.askyesno("Konfirmasi", f"Hapus {label}?", parent=self): return
        for tid in sel_ids:
            try:
                db.hapus_tugas(tid)
            except RuntimeError as e:
                messagebox.showerror("Error Database", str(e), parent=self); return
        self._clear_form(); self._refresh_table()

    def _mark_completed(self):
        sel_ids = [int(i) for i in self.grid.selection()]
        if not sel_ids:
            messagebox.showinfo("Info","Centang task yang ingin ditandai selesai.", parent=self); return
        for tid in sel_ids:
            try:
                db.tandai_selesai(tid)
            except RuntimeError as e:
                messagebox.showerror("Error Database", str(e), parent=self); return
        self.selected_id = None; self._refresh_table()

    def _clear_form(self):
        self.selected_id = None
        self._enable_name_desc()
        if self._cal_popup and self._cal_popup.winfo_exists():
            self._cal_popup.destroy(); self._cal_popup = None
        self.entry_name.delete(0,"end")
        self.entry_desc.delete("1.0","end")
        self.combo_kategori.set("Umum")
        self.entry_deadline.delete(0,"end")
        self.grid.selection_remove()
        self._update_status_bar()

    # ── Kunci / Buka Field ────────────────────────────────────────────────────
    def _disable_name_desc(self):
        self.entry_name.configure(state="disabled", fg_color=_c("disinput"),
                                   border_color=_c("disborder"), text_color=_c("distext"))
        self.entry_desc.configure(state="disabled", fg_color=_c("disinput"),
                                   border_color=_c("disborder"), text_color=_c("distext"))
        self.combo_kategori.configure(state="disabled")
        self.lbl_name_hint.grid(row=1, column=0, sticky="w", pady=(2,0))

    def _enable_name_desc(self):
        self.entry_name.configure(state="normal", fg_color=_c("input"),
                                   border_color=_c("border"), text_color=_c("text"))
        self.entry_desc.configure(state="normal", fg_color=_c("input"),
                                   border_color=_c("border"), text_color=_c("text"))
        self.combo_kategori.configure(state="normal")
        self.lbl_name_hint.grid_forget()

    # ── Pilih Semua ───────────────────────────────────────────────────────────
    def _select_all(self):
        self.grid.selection_set(self.grid.get_children())

    # ── Refresh Tabel ─────────────────────────────────────────────────────────
    def _refresh_table(self):
        self.grid.delete_all()
        try:
            self.tasks = db.ambil_semua_tugas(filter_status=self.filter_mode.get())
        except RuntimeError as e:
            messagebox.showerror("Error Database", str(e), parent=self); return

        today = date.today()
        for t in self.tasks:
            status   = t["status"]
            deadline = t["deadline"]
            if status == "Completed":
                tag = "done"
            elif deadline:
                try:
                    tag = "overdue" if datetime.strptime(deadline,"%Y-%m-%d").date() < today else "pending"
                except ValueError:
                    tag = "pending"
            else:
                tag = "pending"

            self.grid.insert(
                iid    = str(t["id"]),
                values = (t["name"], t["description"], t["kategori"], t["status"], t["deadline"]),
                tag    = tag)

        self.grid.commit()
        self._update_status_bar()

    def _update_status_bar(self):
        total   = len(self.tasks)
        checked = len(self.grid.selection()) if hasattr(self, "grid") else 0
        sel_text = f"{checked} task dicentang" if checked else "Tidak ada task dipilih"
        self.status_bar.configure(
            text=f"Total Tasks: {total}  |  {sel_text}  "
                 f"|  🟡 Pending  🟢 Selesai  🔴 Lewat Deadline")

    # ── Event: GridSelect ─────────────────────────────────────────────────────
    def _on_grid_select(self, event):
        sel = self.grid.selection()
        last = self.grid._last_clicked

        if not sel:
            self._clear_form(); return

        # Gunakan _last_clicked (baris yg baru diklik) bukan sel[0] yg urutannya acak
        task_id = int(last) if last else int(sel[0])
        task = next((t for t in self.tasks if t["id"] == task_id), None)

        # Jika task diklik ulang dan sudah tidak ada di seleksi → clear form
        if last and last not in self.grid._sel:
            self._clear_form(); return

        if not task:
            self._update_status_bar(); return

        self._hide_autocomplete()
        self.selected_id = task_id

        self._enable_name_desc()
        self.entry_name.delete(0,"end"); self.entry_name.insert(0, task["name"])
        self.entry_desc.delete("1.0","end"); self.entry_desc.insert("1.0", task["description"])
        self.combo_kategori.set(task["kategori"])
        self._disable_name_desc()

        self.entry_deadline.delete(0,"end"); self.entry_deadline.insert(0, task["deadline"])
        self._update_status_bar()

    # ── Autocomplete ──────────────────────────────────────────────────────────
    def _on_name_keyrelease(self, event):
        if event.keysym in ("Up","Down","Return","Escape","Tab",
                             "Shift_L","Shift_R","Control_L","Control_R"): return
        keyword = self.entry_name.get().strip()
        if len(keyword) < 1: self._hide_autocomplete(); return
        matches = sorted([n for n in self.all_task_names if keyword.lower() in n.lower()])
        if matches: self._show_autocomplete(matches)
        else: self._hide_autocomplete()

    def _schedule_ac_hide(self, event=None):
        """FocusOut handler: jadwalkan hide autocomplete, bisa dibatalkan saat klik listbox."""
        self._ac_hide_id = self.after(300, self._hide_autocomplete)

    def _cancel_ac_hide(self, event=None):
        """Batalkan pending hide jika ada, supaya klik listbox bisa diproses lebih dulu."""
        if getattr(self, "_ac_hide_id", None):
            self.after_cancel(self._ac_hide_id)
            self._ac_hide_id = None

    def _show_autocomplete(self, matches):
        self._hide_autocomplete()
        entry = self.entry_name
        x = entry.winfo_rootx(); y = entry.winfo_rooty() + entry.winfo_height() + 2
        width = entry.winfo_width()
        max_vis = 6; item_h = 28
        height = min(len(matches), max_vis) * item_h
        popup = tk.Toplevel(self); popup.wm_overrideredirect(True)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.configure(bg=_c("border")); popup.lift()
        frame = tk.Frame(popup, bg=_c("input"), bd=0)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        sb = tk.Scrollbar(frame, orient="vertical", bg=_c("rowhov"),
                           troughcolor=_c("input"), width=10)
        lb = tk.Listbox(frame, bg=_c("input"), fg=_c("text"),
                        selectbackground=_c("ablue"), selectforeground=_c("text"),
                        activestyle="none", font=("Segoe UI",11),
                        bd=0, highlightthickness=0, yscrollcommand=sb.set)
        sb.config(command=lb.yview)
        if len(matches) > max_vis: sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)
        for m in matches: lb.insert("end", m)

        def _sel(e=None):
            self._cancel_ac_hide()          # batalkan hide yang mungkin pending
            s = lb.curselection()
            if not s: s = (lb.nearest(e.y),) if e else ()
            if not s: return
            self.entry_name.delete(0,"end"); self.entry_name.insert(0, lb.get(s[0]))
            self._hide_autocomplete(); self.entry_name.focus()

        # <Button-1> batalkan hide SEBELUM FocusOut sempat destroy popup
        lb.bind("<Button-1>",        self._cancel_ac_hide)
        lb.bind("<ButtonRelease-1>", _sel)
        lb.bind("<Return>",          _sel)
        lb.bind("<Escape>",          lambda e: self._hide_autocomplete())
        self.autocomplete_win = popup; self._autocomplete_listbox = lb

    def _hide_autocomplete(self, event=None):
        if self.autocomplete_win:
            try: self.autocomplete_win.destroy()
            except Exception: pass
            self.autocomplete_win = None; self._autocomplete_listbox = None

    def _autocomplete_focus_list(self, event=None):
        if self.autocomplete_win and self._autocomplete_listbox:
            lb = self._autocomplete_listbox; lb.focus()
            lb.selection_clear(0,"end"); lb.selection_set(0); lb.activate(0)
        return "break"

    # ── Kalender Popup ────────────────────────────────────────────────────────
    def _open_calendar(self):
        if self._cal_popup and self._cal_popup.winfo_exists():
            self._cal_popup.destroy(); self._cal_popup = None; return
        btn = self.btn_calendar
        btn_top = btn.winfo_rooty(); btn_bottom = btn_top + btn.winfo_height()
        bx = btn.winfo_rootx(); initial = self.entry_deadline.get().strip()

        def on_date_selected(d):
            self.entry_deadline.delete(0,"end")
            if d: self.entry_deadline.insert(0, d)
            self._cal_popup = None

        self._cal_popup = CustomCalendar(
            self, on_date_selected, anchor_x=bx,
            btn_top=btn_top, btn_bottom=btn_bottom,
            initial_date=initial if initial else None,
            dark_mode=(ctk.get_appearance_mode() == "Dark"))

        def _on_root_click(event):
            if not self._cal_popup or not self._cal_popup.winfo_exists():
                self.unbind("<Button-1>"); return
            px=self._cal_popup.winfo_rootx(); py=self._cal_popup.winfo_rooty()
            pw=self._cal_popup.winfo_width(); ph=self._cal_popup.winfo_height()
            if not (px <= event.x_root <= px+pw and py <= event.y_root <= py+ph):
                self._cal_popup.destroy(); self._cal_popup = None
                self.unbind("<Button-1>")

        self.bind("<Button-1>", _on_root_click, add="+")


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = TaskmateApp()
    app.mainloop()