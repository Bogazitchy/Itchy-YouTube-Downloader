import customtkinter as ctk
import tkinter as tk
import threading, os, sys, time, json, urllib.request, io, ssl, http.cookiejar, subprocess, re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw
import yt_dlp

try:
    import pystray
    from pystray import MenuItem as TrayItem
    TRAY_OK = True
except ImportError:
    TRAY_OK = False

try:
    import winsound
    SOUND_OK = True
except ImportError:
    SOUND_OK = False

try:
    import pypresence
    DISCORD_OK = True
except ImportError:
    DISCORD_OK = False

try:
    from winotify import Notification, audio
    TOAST_OK = True
except ImportError:
    TOAST_OK = False

# ─── ffmpeg ───────────────────────────────────────────────────────────────────
def get_ffmpeg_dir():
    candidates = []
    if getattr(sys, "frozen", False):
        candidates += [Path(sys._MEIPASS), Path(sys.executable).parent,
                       Path(sys.executable).parent / "_internal"]
    else:
        candidates.append(Path(__file__).parent)
    for p in candidates:
        if (p / "ffmpeg.exe").exists(): return str(p)
    return None

FFMPEG_DIR   = get_ffmpeg_dir()
APP_DIR      = Path(sys.executable).parent if getattr(sys,"frozen",False) else Path(__file__).parent
HISTORY_FILE = APP_DIR / "history.json"
STATS_FILE   = APP_DIR / "stats.json"

# ─── Theme palettes ───────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

DARK = {
    "BG":      "#2A353A",
    "SURFACE": "#313F46",
    "SURF2":   "#3A4A52",
    "SURF3":   "#263035",
    "ACCENT":  "#FB923C",
    "ACCENT2": "#E67E22",
    "TEXT":    "#D1D9DD",
    "TEXT_DIM":"#5A7080",
    "TEXT_MID":"#8AA0AA",
    "BORDER":  "#3D5060",
    "BORDER2": "#304048",
    "RED":     "#EF4444",
    "YELLOW":  "#F59E0B",
    "GREEN":   "#FB923C",
    "ORANGE":  "#E67E22",
}
LIGHT = {
    "BG":      "#f0ebe0",
    "SURFACE": "#faf7f0",
    "SURF2":   "#f5f0e5",
    "SURF3":   "#ece6d8",
    "ACCENT":  "#111111",
    "ACCENT2": "#333333",
    "TEXT":    "#111111",
    "TEXT_DIM":"#999999",
    "TEXT_MID":"#555555",
    "BORDER":  "#c8b898",
    "BORDER2": "#d8c8a8",
    "RED":     "#aa2222",
    "YELLOW":  "#886600",
    "GREEN":   "#111111",
    "ORANGE":  "#885500",
}

_IS_DARK = True

def _ap(t):
    global BG,SURFACE,SURF2,SURF3,ACCENT,ACCENT2,TEXT,TEXT_DIM,TEXT_MID
    global BORDER,BORDER2,RED,YELLOW,GREEN,ORANGE,_IS_DARK
    BG=t["BG"];SURFACE=t["SURFACE"];SURF2=t["SURF2"];SURF3=t["SURF3"]
    ACCENT=t["ACCENT"];ACCENT2=t["ACCENT2"];TEXT=t["TEXT"]
    TEXT_DIM=t["TEXT_DIM"];TEXT_MID=t["TEXT_MID"]
    BORDER=t["BORDER"];BORDER2=t["BORDER2"]
    RED=t["RED"];YELLOW=t["YELLOW"];GREEN=t["GREEN"];ORANGE=t["ORANGE"]

_ap(DARK)

MONO_FONT   = "Courier New"
TITLE_FONT  = "Courier New"
FETCH_TIMEOUT = 20

# ─── Helpers ─────────────────────────────────────────────────────────────────
def clean_url(url):
    import urllib.parse as up
    url=url.strip(); parsed=up.urlparse(url)
    if "/shorts/" in parsed.path:
        vid=parsed.path.split("/shorts/")[-1].split("/")[0].split("?")[0]
        if vid: return f"https://www.youtube.com/watch?v={vid}"
    params=up.parse_qs(parsed.query)
    if "v" in params: return f"https://www.youtube.com/watch?v={params['v'][0]}"
    return url

def get_video_info(url, stop_event=None):
    result=[None]; error=[None]; done=threading.Event()
    def worker():
        try:
            opts={"quiet":True,"no_warnings":True,"skip_download":True,
                  "socket_timeout":10,"retries":1,"nocheckcertificate":True}
            with yt_dlp.YoutubeDL(opts) as ydl: result[0]=ydl.extract_info(url,download=False)
        except Exception as e: error[0]=e
        finally: done.set()
    threading.Thread(target=worker,daemon=True).start()
    deadline=time.time()+FETCH_TIMEOUT
    while not done.is_set():
        if stop_event and stop_event.is_set(): raise Exception("Iptal edildi.")
        if time.time()>deadline: raise Exception(f"Zaman asimi ({FETCH_TIMEOUT}s)")
        time.sleep(0.1)
    if error[0]: raise error[0]
    return result[0]

def build_format_list(info, mode):
    if mode=="mp3":
        return [("320k  EN YUKSEK","320"),("256k  YUKSEK","256"),
                ("192k  ORTA","192"),("128k  DUSUK","128")]
    if mode=="m4a":
        return [("256k  EN YUKSEK","256"),("192k  YUKSEK","192"),("128k  ORTA","128")]
    formats=info.get("formats",[])
    vfmts={}
    for f in formats:
        h=f.get("height"); fid=f.get("format_id",""); vc=f.get("vcodec") or "none"
        if not h or not fid or vc=="none": continue
        lbl=f"{h}p"
        if lbl not in vfmts or vc not in ("none","unknown_video"): vfmts[lbl]=fid
    if not vfmts:
        for f in formats:
            h=f.get("height"); fid=f.get("format_id","")
            if h and fid: vfmts.setdefault(f"{h}p",fid)
    tags={2160:"4K",1440:"2K",1080:"FHD",720:"HD",480:"SD",360:"LOW",240:"VLOW",144:"MIN"}
    results=[]
    for h in [2160,1440,1080,720,480,360,240,144]:
        lbl=f"{h}p"
        if lbl in vfmts: results.append((f"{lbl}  {tags.get(h,lbl)}",vfmts[lbl]))
    std={2160,1440,1080,720,480,360,240,144}
    for f in formats:
        h=f.get("height"); fid=f.get("format_id",""); vc=f.get("vcodec") or "none"
        if h and h not in std and fid and vc!="none":
            results.append((f"{h}p  OZEL",fid))
    return results

def load_history():
    try:
        if HISTORY_FILE.exists(): return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except: pass
    return []

def save_history(records):
    try: HISTORY_FILE.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
    except: pass

def load_stats_file():
    try:
        if STATS_FILE.exists(): return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except: pass
    return {"total_count":0,"total_bytes":0,"by_format":{"mp3":0,"mp4":0,"m4a":0}}

def save_stats_file(s):
    try: STATS_FILE.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding="utf-8")
    except: pass

class QueueItem:
    def __init__(self, url, title="", mode="mp4", quality_label="", fmt_id="", outdir=""):
        self.url=url; self.title=title or url[:50]; self.mode=mode
        self.quality_label=quality_label; self.fmt_id=fmt_id; self.outdir=outdir
        self.status="bekliyor"; self.progress=0.0; self.error=""
        self.row_frame=None; self.progress_bar=None; self.status_lbl=None; self.info=None

# ─── Retro card helper ────────────────────────────────────────────────────────
def rcard(parent, label="", **kw):
    """Retro terminal card with bracket decoration and optional label."""
    outer = ctk.CTkFrame(parent, fg_color=SURF2, corner_radius=6,
                         border_color=BORDER, border_width=1, **kw)
    if label:
        ctk.CTkLabel(outer, text=f"// {label}",
                     font=(MONO_FONT, 9), text_color=TEXT_DIM).pack(
            anchor="w", padx=12, pady=(8,2))
    return outer

def rbtn(parent, text, command=None, accent=False, danger=False, small=False, **kw):
    """Retro styled button."""
    h = 32 if small else 44
    fg = ACCENT if accent else (SURF3 if not danger else SURF2)
    tc = BG if accent else (RED if danger else TEXT_MID)
    bc = ACCENT if accent else (RED if danger else BORDER)
    return ctk.CTkButton(parent, text=text, command=command,
                         font=(MONO_FONT, 10 if small else 11, "bold"),
                         fg_color=fg, hover_color=ACCENT2 if accent else SURF2,
                         text_color=tc, border_color=bc, border_width=1,
                         height=h, corner_radius=6, **kw)

# ─── Pixel font canvas ───────────────────────────────────────────────────────
PIXEL_FONT = {
    'I': ["XXXXX","  X  ","  X  ","  X  ","  X  ","  X  ","XXXXX"],
    'T': ["XXXXX","  X  ","  X  ","  X  ","  X  ","  X  ","  X  "],
    'C': [" XXXX","X    ","X    ","X    ","X    ","X    "," XXXX"],
    'H': ["X   X","X   X","X   X","XXXXX","X   X","X   X","X   X"],
    'Y': ["X   X","X   X"," X X ","  X  ","  X  ","  X  ","  X  "],
}

def draw_pixel_text(canvas, text, x, y, pix, gap, color_top, color_bot):
    """Draw blocky pixel text on a tkinter Canvas."""
    cx = x
    rows = 7
    for ch in text.upper():
        if ch == ' ':
            cx += pix * 3 + gap
            continue
        pattern = PIXEL_FONT.get(ch)
        if not pattern:
            cx += pix * 5 + gap
            continue
        for row_i, row_str in enumerate(pattern):
            # Gradient: interpolate between top and bottom color
            t = row_i / (rows - 1)
            r = int(color_top[0] + (color_bot[0]-color_top[0])*t)
            g = int(color_top[1] + (color_bot[1]-color_top[1])*t)
            b = int(color_top[2] + (color_bot[2]-color_top[2])*t)
            fill = f"#{r:02x}{g:02x}{b:02x}"
            # Slightly darker shade for bottom edge (3D effect)
            dr = max(0, r-40); dg = max(0, g-40); db = max(0, b-40)
            dark = f"#{dr:02x}{dg:02x}{db:02x}"
            for col_i, pixel in enumerate(row_str):
                if pixel == 'X':
                    px = cx + col_i * pix
                    py = y + row_i * pix
                    # Main block
                    canvas.create_rectangle(px, py, px+pix-1, py+pix-1,
                        fill=fill, outline="")
                    # Bottom-right shadow for 3D depth
                    canvas.create_rectangle(px+1, py+pix-2, px+pix-1, py+pix-1,
                        fill=dark, outline="")
                    canvas.create_rectangle(px+pix-2, py+1, px+pix-1, py+pix-1,
                        fill=dark, outline="")
        cx += len(pattern[0]) * pix + gap

class PixelTitleCanvas(tk.Canvas):
    """Canvas that draws ITCHY in pixel/bitmap font style."""
    def __init__(self, parent, pix=10, **kw):
        super().__init__(parent, highlightthickness=0, bd=0, **kw)
        self._pix = pix
        self.bind("<Configure>", self._redraw)
        self._is_dark_mode = True

    def set_dark(self, dark):
        self._is_dark_mode = dark
        self._redraw()

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width() or 700
        h = self.winfo_height() or 80
        pix = self._pix
        gap = pix + 2
        # Total width for ITCHY: I=5,T=5,C=5,H=5,Y=5 cols each + gaps
        total_w = 5 * (5 * pix) + 4 * gap
        x = (w - total_w) // 2
        y = (h - 7 * pix) // 2
        if self._is_dark_mode:
            top = (240, 140, 20)   # bright orange-yellow
            bot = (180, 80, 10)    # darker burnt orange
        else:
            top = (0, 60, 200)     # bright blue
            bot = (0, 30, 140)     # dark blue
        draw_pixel_text(self, "ITCHY", x, y, pix, gap, top, bot)

# ════════════════════════════════════════════════════════════════════════════════
class ItchyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ITCHY YOUTUBE DOWNLOADER v1.0")
        self.geometry("1080x840")
        self.minsize(900, 720)
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self.after(10, lambda: self.state("zoomed"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._is_dark       = True
        self._info          = None
        self._formats       = []
        self._dl_path       = str(Path.home()/"Downloads")
        self._fetch_stop    = threading.Event()
        self._fetching      = False
        self._dl_cancelled  = False
        self._dl_paused     = False
        self._dl_pause_lock = threading.Event(); self._dl_pause_lock.set()
        self._downloading   = False
        self._ydl_instance  = None
        self._thumb_ref     = None
        self._logo_ref      = None
        self._pct_var       = ctk.StringVar(value="")
        self._quality_values= ["-- URL GIRIN --"]
        self._dropdown_open = False
        self._dropdown_win  = None
        self._speed_limit   = ctk.StringVar(value="0")
        self._queue         = []
        self._queue_running = False
        self._queue_stop    = False
        self._history       = load_history()
        self._tray_icon     = None
        self._notif_sound_var = ctk.BooleanVar(value=True)
        self._tray_var      = ctk.BooleanVar(value=False)
        self._active_tab    = "indir"
        self._clip_start    = ctk.StringVar(value="")
        self._clip_end      = ctk.StringVar(value="")
        self._clip_enabled  = ctk.BooleanVar(value=False)
        self._subtitle_var  = ctk.BooleanVar(value=False)
        self._sub_lang_var  = ctk.StringVar(value="tr")
        self._open_folder_var = ctk.BooleanVar(value=True)
        self._proxy_var     = ctk.StringVar(value="")
        self._cookie_file   = ctk.StringVar(value="")
        self._mini_mode     = False
        self._stats         = load_stats_file()
        self._last_dl_folder= ""
        self._batch_file    = ctk.StringVar(value="")
        self._anim_alpha    = 0.0
        self._anim_running  = False
        # New v1.0 features
        self._discord_rpc   = None
        self._discord_enabled = ctk.BooleanVar(value=False)
        self._discord_connected = False
        self._filesize_var  = ctk.StringVar(value="")
        self._hist_search_var = ctk.StringVar(value="")
        self._all_history   = []  # full history for search
        self._ytdlp_check_done = False

        self._build_ui()
        # Auto-check yt-dlp update on startup
        threading.Thread(target=self._auto_check_ytdlp, daemon=True).start()
        self._set_window_icon()
        self.bind("<Return>", lambda e: self._fetch_info())

    # ── Icon ──────────────────────────────────────────────────────────────────
    def _set_window_icon(self):
        cands=[]
        if getattr(sys,"frozen",False):
            cands+=[Path(sys._MEIPASS)/"logo.ico",
                    Path(sys.executable).parent/"logo.ico",
                    Path(sys.executable).parent/"_internal"/"logo.ico"]
        else: cands.append(Path(__file__).parent/"logo.ico")
        for p in cands:
            if p.exists():
                try: self.iconbitmap(str(p))
                except: pass
                break

    # ── Logo ──────────────────────────────────────────────────────────────────
    def _load_logo(self):
        cands=[]
        if getattr(sys,"frozen",False):
            for base in [Path(sys._MEIPASS),Path(sys.executable).parent,
                         Path(sys.executable).parent/"_internal"]:
                cands+=[base/"logo.png",base/"logo.ico"]
        else:
            base=Path(__file__).parent; cands+=[base/"logo.png",base/"logo.ico"]
        for p in cands:
            if not p.exists(): continue
            try:
                img=Image.open(str(p)).convert("RGBA")
                w,h=img.size; nh=80; nw=int(w*nh/h)
                img=img.resize((nw,nh),Image.LANCZOS)
                pixels=list(img.getdata())
                dd=[(r,g,b,0) if (r+g+b)/3<50 else (r,g,b,a) for r,g,b,a in pixels]
                img_d=Image.new("RGBA",img.size); img_d.putdata(dd)
                pixels2=list(img.getdata())
                dl=[(r,g,b,0) if (r+g+b)/3>200 else (r,g,b,a) for r,g,b,a in pixels2]
                img_l=Image.new("RGBA",img.size); img_l.putdata(dl)
                ci=ctk.CTkImage(light_image=img_l,dark_image=img_d,size=(nw,nh))
                self._logo_ref=ci; return ci
            except: continue
        return None

    # ── Halftone background ───────────────────────────────────────────────────
    def _draw_halftone_bg(self):
        try:
            self.update_idletasks()
            w = max(self.winfo_width(), 1200)
            h = max(self.winfo_height(), 900)
            dark = _IS_DARK
            if dark:
                bg_col = (42, 53, 58)   # #2A353A
                dot_col = (251, 146, 60) # #FB923C orange
                img = Image.new("RGB", (w, h), bg_col)
                draw = ImageDraw.Draw(img)
                spacing = 14
                for row in range(0, h + spacing, spacing):
                    for col in range(0, w + spacing, spacing):
                        dy = row / h
                        dx = abs(col / w - 0.5)
                        density = max(0, 1 - (dy * 0.7 + dx * 0.6) * 1.3)
                        if density < 0.06: continue
                        r = max(1, int(4 * density))
                        af = density * 0.25
                        dc = tuple(int(bg_col[i] + (dot_col[i]-bg_col[i]) * af) for i in range(3))
                        draw.ellipse([col-r, row-r, col+r, row+r], fill=dc)
            else:
                bg_col = (242, 236, 224)
                dot_col = (20, 20, 20)
                img = Image.new("RGB", (w, h), bg_col)
                draw = ImageDraw.Draw(img)
                spacing = 10
                for row in range(0, h + spacing, spacing):
                    for col in range(0, w + spacing, spacing):
                        nx = col / w; ny = row / h
                        density = max(0, (1 - nx * 0.6 - ny * 0.6) * 1.1 - 0.05)
                        if density < 0.06: continue
                        r = max(1, int(3 * density))
                        af = density * 0.4
                        dc = tuple(int(bg_col[i] + (dot_col[i]-bg_col[i]) * af) for i in range(3))
                        draw.ellipse([col-r, row-r, col+r, row+r], fill=dc)
            ci = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
            self._halftone_img = ci
            if hasattr(self, "_halftone_lbl"):
                self._halftone_lbl.configure(image=ci)
        except Exception:
            pass

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Guard: prevent any button command from triggering while building
        self._building = True

        # ── HALFTONE BACKGROUND ──
        self._halftone_lbl = ctk.CTkLabel(self, text="", fg_color=BG)
        self._halftone_lbl.place(x=0, y=0, relwidth=1, relheight=1)
        # Draw after window is shown
        self.after(200, self._draw_halftone_bg)

        # ── HEADER ──
        hdr=ctk.CTkFrame(self,fg_color=SURF3,corner_radius=0,height=120)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        # Left: created by
        lft=ctk.CTkFrame(hdr,fg_color="transparent"); lft.place(x=16,rely=0.5,anchor="w")
        ctk.CTkLabel(lft,text="created by:",font=(MONO_FONT,8),text_color=TEXT_DIM).pack(anchor="w")
        ctk.CTkLabel(lft,text="M.Mert",font=(MONO_FONT,9,"bold"),text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(lft,text="v1.0",font=(MONO_FONT,8),text_color=TEXT_DIM).pack(anchor="w")

        # Center: pixel canvas title
        self._pixel_canvas = PixelTitleCanvas(hdr, pix=9,
            bg=SURF3, width=520, height=80)  # halftone-aware
        self._pixel_canvas.set_dark(self._is_dark)
        self._pixel_canvas.place(relx=0.5, rely=0.46, anchor="center")


        # Right: theme toggle
        rgt=ctk.CTkFrame(hdr,fg_color="transparent")
        rgt.place(relx=0.985,rely=0.5,anchor="e")
        _icon = "[ DARK ]" if self._is_dark else "[ LIGHT]"
        self.theme_btn=ctk.CTkButton(rgt,text=_icon,
            font=(MONO_FONT,9,"bold"),width=72,height=26,corner_radius=4,
            fg_color=SURF2,hover_color=BORDER,text_color=ACCENT,
            border_color=BORDER,border_width=1,command=self._toggle_theme)
        self.theme_btn.pack()

        # Divider
        div_frame=ctk.CTkFrame(self,fg_color=SURF2,corner_radius=0,height=3)
        div_frame.pack(fill="x")
        ctk.CTkFrame(div_frame,fg_color=ACCENT,corner_radius=0,height=1).pack(fill="x",pady=(1,0))

        # ── TABS ──
        tab_bg=ctk.CTkFrame(self,fg_color=SURF3,corner_radius=0,height=36)
        tab_bg.pack(fill="x"); tab_bg.pack_propagate(False)
        self._tab_btns={}
        tabs=[("indir","[01] INDIR"),("queue","[02] KUYRUK"),("batch","[03] BATCH"),
              ("history","[04] GECMIS"),("stats","[05] ISTAT"),("settings","[06] AYARLAR")]
        for tid,tlbl in tabs:
            active=(tid=="indir")
            btn=ctk.CTkButton(tab_bg,text=tlbl,
                font=(MONO_FONT,9,"bold"),width=120,height=34,corner_radius=0,
                fg_color=SURF2 if active else SURF3,
                hover_color=SURF2,
                text_color=ACCENT if active else TEXT_DIM,
                border_color=BORDER if active else SURF3,
                border_width=1 if active else 0,
                command=lambda t=tid:self._switch_tab(t))
            btn.pack(side="left"); self._tab_btns[tid]=btn

        # ── PAGES ──
        self._pages={}
        container=ctk.CTkFrame(self,fg_color="transparent",corner_radius=0)
        container.pack(fill="both",expand=True)
        for tid in ["indir","queue","batch","history","stats","settings"]:
            pg=ctk.CTkScrollableFrame(container,fg_color="transparent",
                scrollbar_button_color=SURF2,scrollbar_button_hover_color=BORDER)
            pg.place(relx=0,rely=0,relwidth=1,relheight=1)
            self._pages[tid]=pg
        self._build_download_page(self._pages["indir"])
        self._build_queue_page(self._pages["queue"])
        self._build_batch_page(self._pages["batch"])
        self._build_history_page(self._pages["history"])
        self._build_stats_page(self._pages["stats"])
        self._build_settings_page(self._pages["settings"])
        self._building = False
        self._switch_tab("indir")

    # ── Tab switch with fade animation ────────────────────────────────────────
    def _switch_tab(self, tid):
        self._active_tab=tid
        for t,btn in self._tab_btns.items():
            active=(t==tid)
            btn.configure(
                fg_color=SURF2 if active else SURF3,
                text_color=ACCENT if active else TEXT_DIM,
                border_color=BORDER if active else SURF3,
                border_width=1 if active else 0)
        # Animate page in
        target=self._pages[tid]
        for t,pg in self._pages.items():
            if t!=tid: pg.lower()
        target.lift()
        self._fade_in(target)
        if tid=="history": self._refresh_history_page()
        if tid=="queue":   self._refresh_queue_ui()
        if tid=="stats":   self._refresh_stats_page()

    def _fade_in(self, widget):
        """Simple fade by briefly flashing the bg."""
        # Flash border accent on active page
        try: widget.configure(fg_color=SURF3)
        except: pass
        self.after(40, lambda: self._restore_page_bg(widget))

    def _restore_page_bg(self, widget):
        try: widget.configure(fg_color=BG)
        except: pass

    # ── Download Page ─────────────────────────────────────────────────────────
    def _build_download_page(self, body):
        PAD = dict(padx=28, pady=6)

        # URL card
        uc=rcard(body, "VIDEO LINKI"); uc.pack(fill="x",**PAD)
        ui=ctk.CTkFrame(uc,fg_color="transparent"); ui.pack(fill="x",padx=12,pady=(2,10))
        self.url_entry=ctk.CTkEntry(ui,
            placeholder_text="youtube.com/watch?v=... yapistir",
            font=(MONO_FONT,12),fg_color=SURF3,border_color=BORDER,border_width=1,
            text_color=TEXT,placeholder_text_color=TEXT_DIM,height=42,corner_radius=6)
        self.url_entry.pack(side="left",fill="x",expand=True,padx=(0,8))
        self.fetch_btn=rbtn(ui,text="[ ANALiZ ET ]",command=self._fetch_info,accent=True,width=140)
        self.fetch_btn.pack(side="left")
        # Drag & drop support
        self._setup_drag_drop(self.url_entry)
        # Add to queue shortcut
        ctk.CTkButton(uc,text="+ KUYRUGA EKLE",font=(MONO_FONT,9),
            fg_color="transparent",hover_color=SURF2,text_color=TEXT_DIM,
            height=20,corner_radius=4,border_width=0,
            command=self._add_to_queue_from_url).pack(anchor="e",padx=12,pady=(0,6))

        # Info card
        self.info_card=rcard(body,"VIDEO BiLGiSi"); self.info_card.pack(fill="x",**PAD)
        ir=ctk.CTkFrame(self.info_card,fg_color="transparent"); ir.pack(fill="x",padx=12,pady=10)
        self.thumb_lbl=ctk.CTkLabel(ir,text="",width=142,height=80); self.thumb_lbl.pack(side="left",padx=(0,12))
        self._draw_placeholder_thumb()
        it=ctk.CTkFrame(ir,fg_color="transparent"); it.pack(side="left",fill="both",expand=True)
        self.vid_title_lbl=ctk.CTkLabel(it,text="// SiSTEM HAZIR — URL GiRiN",
            font=(MONO_FONT,12,"bold"),text_color=TEXT_DIM,anchor="w",wraplength=520,justify="left")
        self.vid_title_lbl.pack(anchor="w")
        self.vid_meta_lbl=ctk.CTkLabel(it,text="",font=(MONO_FONT,9),text_color=TEXT_DIM,anchor="w")
        self.vid_meta_lbl.pack(anchor="w",pady=(6,0))

        # Format + Quality row
        fq=ctk.CTkFrame(body,fg_color="transparent"); fq.pack(fill="x",**PAD)

        # Format card
        fc=rcard(fq,"FORMAT"); fc.pack(side="left",padx=(0,8))
        seg=ctk.CTkFrame(fc,fg_color=SURF3,corner_radius=6,
                         border_color=BORDER2,border_width=1)
        seg.pack(padx=12,pady=(2,10))
        self.mode_var=ctk.StringVar(value="mp4")
        self.mp3_btn=ctk.CTkButton(seg,text="MP3",font=(MONO_FONT,10,"bold"),
            width=72,height=34,corner_radius=4,fg_color=SURF3,hover_color=SURF2,
            text_color=TEXT_DIM,border_width=0,command=lambda:self._set_mode("mp3"))
        self.mp3_btn.pack(side="left",padx=(4,2),pady=4)
        self.mp4_btn=ctk.CTkButton(seg,text="MP4",font=(MONO_FONT,10,"bold"),
            width=72,height=34,corner_radius=4,fg_color=ACCENT,hover_color=ACCENT2,
            text_color=BG,border_width=0,command=lambda:self._set_mode("mp4"))
        self.mp4_btn.pack(side="left",padx=(2,2),pady=4)
        self.m4a_btn=ctk.CTkButton(seg,text="M4A",font=(MONO_FONT,10,"bold"),
            width=72,height=34,corner_radius=4,fg_color=SURF3,hover_color=SURF2,
            text_color=TEXT_DIM,border_width=0,command=lambda:self._set_mode("m4a"))
        self.m4a_btn.pack(side="left",padx=(2,4),pady=4)

        # Quality card — pill buttons
        qc=rcard(fq,"KALITE"); qc.pack(side="left",fill="both",expand=True)
        self._qual_pill_host=ctk.CTkFrame(qc,fg_color="transparent")
        self._qual_pill_host.pack(fill="x",padx=12,pady=(2,6))
        self.quality_var=ctk.StringVar(value="-- URL GIRIN --")
        self._build_quality_pills()
        self.filesize_lbl=ctk.CTkLabel(qc,textvariable=self._filesize_var,
            font=(MONO_FONT,9),text_color=ACCENT,anchor="w")
        self.filesize_lbl.pack(anchor="w",padx=12,pady=(0,8))

        # Clip card
        clip_card=rcard(body,"KLiP KESME"); clip_card.pack(fill="x",**PAD)
        cr=ctk.CTkFrame(clip_card,fg_color="transparent"); cr.pack(fill="x",padx=12,pady=(2,10))
        self._clip_chk=ctk.CTkCheckBox(cr,text="AKTiF",
            variable=self._clip_enabled,font=(MONO_FONT,10,"bold"),
            text_color=TEXT_MID,fg_color=ACCENT,hover_color=ACCENT2,checkmark_color=BG,
            command=self._toggle_clip_ui); self._clip_chk.pack(side="left",padx=(0,16))
        ctk.CTkLabel(cr,text="START:",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left")
        ctk.CTkEntry(cr,textvariable=self._clip_start,placeholder_text="00:00:00",
            font=(MONO_FONT,11),fg_color=SURF3,border_color=BORDER,text_color=TEXT,
            height=34,corner_radius=6,width=100).pack(side="left",padx=(4,16))
        ctk.CTkLabel(cr,text="END:",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left")
        ctk.CTkEntry(cr,textvariable=self._clip_end,placeholder_text="00:00:00",
            font=(MONO_FONT,11),fg_color=SURF3,border_color=BORDER,text_color=TEXT,
            height=34,corner_radius=6,width=100).pack(side="left",padx=(4,0))
        ctk.CTkLabel(cr,text="  [HH:MM:SS]",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left")

        # Sub + options row
        so=ctk.CTkFrame(body,fg_color="transparent"); so.pack(fill="x",**PAD)
        sub_card=rcard(so,"ALTYAZI"); sub_card.pack(side="left",padx=(0,8))
        si=ctk.CTkFrame(sub_card,fg_color="transparent"); si.pack(padx=12,pady=(2,10))
        ctk.CTkCheckBox(si,text="iNDiR",variable=self._subtitle_var,
            font=(MONO_FONT,10),text_color=TEXT_MID,fg_color=ACCENT,hover_color=ACCENT2,
            checkmark_color=BG).pack(anchor="w")
        lr=ctk.CTkFrame(si,fg_color="transparent"); lr.pack(fill="x",pady=(4,0))
        ctk.CTkLabel(lr,text="DiL:",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left")
        ctk.CTkOptionMenu(lr,variable=self._sub_lang_var,
            values=["tr","en","de","fr","es","ja","ko","ar"],
            font=(MONO_FONT,10),fg_color=SURF3,button_color=ACCENT,button_hover_color=ACCENT2,
            text_color=TEXT,dropdown_fg_color=SURF2,dropdown_text_color=TEXT,
            width=70,height=28,corner_radius=4).pack(side="left",padx=(4,0))

        opts_card=rcard(so,"SECENEKLER"); opts_card.pack(side="left",fill="both",expand=True)
        oi=ctk.CTkFrame(opts_card,fg_color="transparent"); oi.pack(padx=12,pady=(2,10),anchor="w")
        ctk.CTkCheckBox(oi,text="iNDiRME SONRASI KLASORU AC",
            variable=self._open_folder_var,font=(MONO_FONT,10),text_color=TEXT_MID,
            fg_color=ACCENT,hover_color=ACCENT2,checkmark_color=BG).pack(anchor="w")
        rbtn(oi,text="[M] MiNi MOD",command=self._toggle_mini_mode,small=True).pack(anchor="w",pady=(8,0))

        # Save path
        path_card=rcard(body,"KAYIT KLASORU"); path_card.pack(fill="x",**PAD)
        pi=ctk.CTkFrame(path_card,fg_color="transparent"); pi.pack(fill="x",padx=12,pady=(2,10))
        self.path_entry=ctk.CTkEntry(pi,font=(MONO_FONT,11),fg_color=SURF3,border_color=BORDER,
            border_width=1,text_color=TEXT_MID,height=38,corner_radius=6)
        self.path_entry.insert(0,self._dl_path)
        self.path_entry.pack(side="left",fill="x",expand=True,padx=(0,8))
        rbtn(pi,text="[D] SEC",command=self._browse_path,small=True,width=90).pack(side="left")

        # Download buttons
        dl_row=ctk.CTkFrame(body,fg_color="transparent"); dl_row.pack(fill="x",**PAD)
        self.dl_btn=ctk.CTkButton(dl_row,text="▼  [ iNDiR ]  ▼",
            font=(TITLE_FONT,18,"bold"),
            fg_color=SURF3,hover_color=SURF2,text_color=ACCENT,
            border_color=ACCENT,border_width=1,
            height=52,corner_radius=6,
            command=self._start_download,state="disabled")
        self.dl_btn.pack(side="left",fill="x",expand=True,padx=(0,8))
        self.pause_btn=rbtn(dl_row,text="[P] DURDUR",command=self._toggle_pause,
            small=False,width=120,state="disabled")
        self.pause_btn.pack(side="left",padx=(0,8))
        self.cancel_dl_btn=rbtn(dl_row,text="[X] iPTAL",command=self._cancel_download,
            danger=True,width=110,state="disabled")
        self.cancel_dl_btn.pack(side="left")

        # Progress card
        prog=rcard(body,"PROGRESS"); prog.pack(fill="x",**PAD)
        pi2=ctk.CTkFrame(prog,fg_color="transparent"); pi2.pack(fill="x",padx=12,pady=(2,10))
        sr=ctk.CTkFrame(pi2,fg_color="transparent"); sr.pack(fill="x",pady=(0,6))
        self.status_lbl=ctk.CTkLabel(sr,text="// SiSTEM HAZIR",
            font=(MONO_FONT,10),text_color=TEXT_DIM,anchor="w")
        self.status_lbl.pack(side="left",fill="x",expand=True)
        self.pct_lbl=ctk.CTkLabel(sr,textvariable=self._pct_var,
            font=(MONO_FONT,11,"bold"),text_color=ACCENT,anchor="e",width=55)
        self.pct_lbl.pack(side="right")
        self.progress_bar=ctk.CTkProgressBar(pi2,fg_color=SURF3,progress_color=ACCENT,
            height=12,corner_radius=4,border_color=BORDER,border_width=1)
        self.progress_bar.set(0); self.progress_bar.pack(fill="x")

        # Log
        self.log_box=ctk.CTkTextbox(body,font=(MONO_FONT,10),fg_color=SURF3,
            text_color=TEXT_DIM,border_color=BORDER2,border_width=1,corner_radius=6,
            height=90,wrap="word",state="disabled")
        self.log_box.pack(fill="x",padx=28,pady=(0,4))
        ctk.CTkLabel(body,text="// created by M.Mert",
            font=(MONO_FONT,9),text_color=TEXT_DIM,anchor="e").pack(fill="x",padx=28,pady=(0,14))

    # ── Quality pills ─────────────────────────────────────────────────────────
    def _build_quality_pills(self):
        for w in self._qual_pill_host.winfo_children(): w.destroy()
        vals = self._quality_values
        pairs = vals if (vals and isinstance(vals[0], tuple)) else [(v,v) for v in vals]
        for lbl,fid in pairs:
            is_sel=(lbl==self.quality_var.get())
            pill=ctk.CTkButton(self._qual_pill_host,text=lbl,
                font=(MONO_FONT,9,"bold" if is_sel else "normal"),
                height=28,corner_radius=14,
                fg_color=SURF3 if not is_sel else ACCENT,
                hover_color=SURF2 if not is_sel else ACCENT2,
                text_color=ACCENT if not is_sel else BG,
                border_color=ACCENT if not is_sel else ACCENT,
                border_width=1,
                command=lambda l=lbl:self._select_quality(l))
            pill.pack(side="left",padx=(0,5),pady=2)

    def _select_quality(self,label):
        self.quality_var.set(label); self._build_quality_pills()
        if self._formats:
            self.dl_btn.configure(state="normal")
            self._estimate_filesize(label)

    def _estimate_filesize(self,label):
        """Estimate file size based on quality label and duration."""
        if not self._info: return
        duration=self._info.get("duration",0) or 0
        if not duration: self._filesize_var.set(""); return
        mode=self.mode_var.get()
        # Rough bitrate estimates
        bitrate_map={
            "320k":320,"256k":256,"192k":192,"128k":128,
            "4K":25000,"2K":12000,"1080p":4000,"720p":2000,
            "480p":1000,"360p":600,"240p":350,"144p":150,
        }
        bps=None
        for key,bps_val in bitrate_map.items():
            if key in label:
                bps=bps_val; break
        if bps is None:
            self._filesize_var.set(""); return
        # bytes = (bitrate_kbps * 1000 / 8) * duration_seconds
        size_bytes=int((bps*1000/8)*duration)
        self._filesize_var.set(f"~~ TAHMINI BOYUT: {self._fmt_bytes(size_bytes)}")

    def _populate_quality(self,info):
        self._formats=build_format_list(info,self.mode_var.get())
        if self._formats:
            self._quality_values=self._formats
            self.quality_var.set(self._formats[0][0])
            self.dl_btn.configure(state="normal")
            self._estimate_filesize(self._formats[0][0])
        else:
            self._quality_values=[("-- FORMAT YOK --","")]
            self.quality_var.set("-- FORMAT YOK --")
            self.dl_btn.configure(state="disabled")
            self._filesize_var.set("")
        self._build_quality_pills()

    # ── Queue Page ────────────────────────────────────────────────────────────
    def _build_queue_page(self, body):
        ctrl=rcard(body,"KUYRUK KONTROL"); ctrl.pack(fill="x",padx=28,pady=(16,6))
        ci=ctk.CTkFrame(ctrl,fg_color="transparent"); ci.pack(fill="x",padx=12,pady=(2,8))
        self.q_url_entry=ctk.CTkEntry(ci,placeholder_text="Link ekle...",
            font=(MONO_FONT,11),fg_color=SURF3,border_color=BORDER,border_width=1,
            text_color=TEXT,placeholder_text_color=TEXT_DIM,height=38,corner_radius=6)
        self.q_url_entry.pack(side="left",fill="x",expand=True,padx=(0,8))
        rbtn(ci,text="[+] EKLE",command=self._queue_add_url,accent=True,small=True,width=90).pack(side="left",padx=(0,6))
        rbtn(ci,text="CLR",command=self._queue_clear,small=True,width=60).pack(side="left")

        mq=ctk.CTkFrame(ctrl,fg_color="transparent"); mq.pack(fill="x",padx=12,pady=(0,10))
        ctk.CTkLabel(mq,text="FMT:",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left")
        self.q_mode_var=ctk.StringVar(value="mp4")
        for val,lbl in [("mp3","MP3"),("mp4","MP4"),("m4a","M4A")]:
            ctk.CTkRadioButton(mq,text=lbl,variable=self.q_mode_var,value=val,
                font=(MONO_FONT,10),text_color=TEXT_MID,fg_color=ACCENT,hover_color=ACCENT2
                ).pack(side="left",padx=(10,0))
        ctk.CTkLabel(mq,text="  QLT:",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left",padx=(12,0))
        self.q_quality_var=ctk.StringVar(value="720p  HD")
        ctk.CTkOptionMenu(mq,variable=self.q_quality_var,
            values=["1080p  FHD","720p  HD","480p  SD","360p  LOW",
                    "320k  EN YUKSEK","192k  ORTA","128k  DUSUK"],
            font=(MONO_FONT,10),fg_color=SURF3,button_color=ACCENT,button_hover_color=ACCENT2,
            text_color=TEXT,dropdown_fg_color=SURF2,dropdown_text_color=TEXT,
            width=160,height=30,corner_radius=4).pack(side="left",padx=(6,0))

        qbr=ctk.CTkFrame(body,fg_color="transparent"); qbr.pack(fill="x",padx=28,pady=(0,6))
        self.q_start_btn=ctk.CTkButton(qbr,text="▶  [ BASLAT ]",
            font=(MONO_FONT,13,"bold"),fg_color=SURF3,hover_color=SURF2,
            text_color=ACCENT,border_color=ACCENT,border_width=1,
            height=44,corner_radius=6,command=self._queue_start)
        self.q_start_btn.pack(side="left",fill="x",expand=True,padx=(0,8))
        rbtn(qbr,text="[S] DUR",command=self._queue_stop_all,danger=True,width=100).pack(side="left")

        self.q_list_frame=ctk.CTkFrame(body,fg_color="transparent")
        self.q_list_frame.pack(fill="x",padx=28,pady=(0,20))

    def _build_queue_row(self,parent,item):
        row=ctk.CTkFrame(parent,fg_color=SURF2,corner_radius=6,
            border_color=BORDER,border_width=1); row.pack(fill="x",pady=(0,4))
        item.row_frame=row
        top=ctk.CTkFrame(row,fg_color="transparent"); top.pack(fill="x",padx=10,pady=(8,4))
        colors={"bekliyor":TEXT_DIM,"analiz":YELLOW,"indiriliyor":ACCENT,
                "tamamlandi":GREEN,"hata":RED,"iptal":ORANGE}
        c=colors.get(item.status,TEXT_DIM)
        item.status_lbl=ctk.CTkLabel(top,
            text=f"[{item.status.upper()[:3]}] {item.title[:52]}",
            font=(MONO_FONT,10),text_color=c,anchor="w")
        item.status_lbl.pack(side="left",fill="x",expand=True)
        ctk.CTkButton(top,text="[X]",font=(MONO_FONT,9),width=32,height=22,
            fg_color="transparent",hover_color=SURF3,text_color=TEXT_DIM,
            command=lambda i=item:self._queue_remove(i)).pack(side="right")
        item.progress_bar=ctk.CTkProgressBar(row,fg_color=SURF3,progress_color=ACCENT,
            height=4,corner_radius=2)
        item.progress_bar.set(item.progress); item.progress_bar.pack(fill="x",padx=10,pady=(0,8))

    def _refresh_queue_ui(self):
        for w in self.q_list_frame.winfo_children(): w.destroy()
        if not self._queue:
            ctk.CTkLabel(self.q_list_frame,text="// KUYRUK BOS. URL EKLEYiN.",
                font=(MONO_FONT,11),text_color=TEXT_DIM).pack(pady=30); return
        for item in self._queue: self._build_queue_row(self.q_list_frame,item)

    # ── Batch Page ────────────────────────────────────────────────────────────
    def _build_batch_page(self,body):
        ctk.CTkLabel(body,text="// BATCH iNDiRME",font=(MONO_FONT,13,"bold"),
            text_color=ACCENT).pack(anchor="w",padx=28,pady=(16,6))

        fp=rcard(body,"DOSYA YUKLE"); fp.pack(fill="x",padx=28,pady=(0,6))
        fi=ctk.CTkFrame(fp,fg_color="transparent"); fi.pack(fill="x",padx=12,pady=(2,10))
        self.batch_file_entry=ctk.CTkEntry(fi,textvariable=self._batch_file,
            placeholder_text=".txt dosyasi sec...",font=(MONO_FONT,10),
            fg_color=SURF3,border_color=BORDER,text_color=TEXT_MID,height=34,corner_radius=6)
        self.batch_file_entry.pack(side="left",fill="x",expand=True,padx=(0,8))
        rbtn(fi,text="[F] SEC",command=self._batch_pick_file,small=True,width=80).pack(side="left",padx=(0,6))
        rbtn(fi,text="YUKLE",command=self._batch_load_file,accent=True,small=True,width=70).pack(side="left")

        tc=rcard(body,"LiNKLER (her satira bir link)"); tc.pack(fill="x",padx=28,pady=(0,6))
        self.batch_text=ctk.CTkTextbox(tc,font=(MONO_FONT,10),fg_color=SURF3,
            text_color=TEXT,border_color=BORDER2,border_width=1,corner_radius=6,height=150)
        self.batch_text.pack(fill="x",padx=12,pady=(2,10))

        br=ctk.CTkFrame(body,fg_color="transparent"); br.pack(fill="x",padx=28,pady=(0,6))
        bfc=rcard(br,"FORMAT"); bfc.pack(side="left",padx=(0,8))
        self.batch_mode_var=ctk.StringVar(value="mp4")
        bfi=ctk.CTkFrame(bfc,fg_color="transparent"); bfi.pack(padx=12,pady=(2,10))
        for val,lbl in [("mp3","MP3"),("mp4","MP4"),("m4a","M4A")]:
            ctk.CTkRadioButton(bfi,text=lbl,variable=self.batch_mode_var,value=val,
                font=(MONO_FONT,10),text_color=TEXT_MID,fg_color=ACCENT,hover_color=ACCENT2
                ).pack(anchor="w",pady=2)

        bqc=rcard(br,"KALITE"); bqc.pack(side="left",padx=(0,8))
        self.batch_qual_var=ctk.StringVar(value="720p  HD")
        bqi=ctk.CTkFrame(bqc,fg_color="transparent"); bqi.pack(padx=12,pady=(2,10))
        ctk.CTkOptionMenu(bqi,variable=self.batch_qual_var,
            values=["1080p  FHD","720p  HD","480p  SD","360p  LOW",
                    "320k  EN YUKSEK","192k  ORTA","128k  DUSUK"],
            font=(MONO_FONT,10),fg_color=SURF3,button_color=ACCENT,button_hover_color=ACCENT2,
            text_color=TEXT,dropdown_fg_color=SURF2,dropdown_text_color=TEXT,
            width=160,height=30,corner_radius=4).pack()

        ctk.CTkButton(br,text="▶  [ BATCH BASLAT ]",
            font=(MONO_FONT,13,"bold"),fg_color=SURF3,hover_color=SURF2,
            text_color=ACCENT,border_color=ACCENT,border_width=1,
            height=44,corner_radius=6,command=self._batch_start).pack(
            side="left",fill="both",expand=True)

        self.batch_log=ctk.CTkTextbox(body,font=(MONO_FONT,10),fg_color=SURF3,
            text_color=TEXT_DIM,border_color=BORDER2,border_width=1,corner_radius=6,
            height=110,wrap="word",state="disabled")
        self.batch_log.pack(fill="x",padx=28,pady=(0,20))

    # ── History Page ──────────────────────────────────────────────────────────
    def _build_history_page(self,body):
        top=ctk.CTkFrame(body,fg_color="transparent"); top.pack(fill="x",padx=28,pady=(16,8))
        ctk.CTkLabel(top,text="// iNDiRME GECMiSi",font=(MONO_FONT,13,"bold"),text_color=ACCENT).pack(side="left")
        rbtn(top,text="[C] TEMiZLE",command=self._clear_history,small=True,width=110).pack(side="right")
        # Search bar
        search_row=ctk.CTkFrame(body,fg_color=SURF2,corner_radius=6,border_color=BORDER,border_width=1)
        search_row.pack(fill="x",padx=28,pady=(0,8))
        sr=ctk.CTkFrame(search_row,fg_color="transparent"); sr.pack(fill="x",padx=12,pady=8)
        ctk.CTkLabel(sr,text="[?] ARA:",font=(MONO_FONT,9),text_color=TEXT_DIM).pack(side="left",padx=(0,8))
        self._hist_search_var=ctk.StringVar(value="")
        self._hist_search_var.trace_add("write",lambda *a:self._refresh_history_page())
        ctk.CTkEntry(sr,textvariable=self._hist_search_var,
            placeholder_text="Baslik, format veya tarih ara...",
            font=(MONO_FONT,10),fg_color=SURF3,border_color=BORDER,text_color=TEXT,
            placeholder_text_color=TEXT_DIM,height=32,corner_radius=4).pack(side="left",fill="x",expand=True)
        # Filter buttons
        self._hist_filter=ctk.StringVar(value="ALL")
        for val in ["ALL","MP3","MP4","M4A"]:
            ctk.CTkButton(sr,text=val,font=(MONO_FONT,9,"bold"),width=44,height=28,
                corner_radius=4,fg_color=SURF3,hover_color=BORDER,
                text_color=ACCENT,border_color=BORDER,border_width=1,
                command=lambda v=val:self._set_hist_filter(v)).pack(side="left",padx=(6,0))
        self.hist_frame=ctk.CTkFrame(body,fg_color="transparent"); self.hist_frame.pack(fill="x",padx=28)

    def _set_hist_filter(self,val):
        self._hist_filter.set(val); self._refresh_history_page()

    def _refresh_history_page(self):
        for w in self.hist_frame.winfo_children(): w.destroy()
        if not self._history:
            ctk.CTkLabel(self.hist_frame,text="// HENUZ iNDiRME YAPILMADI.",
                font=(MONO_FONT,11),text_color=TEXT_DIM).pack(pady=30); return
        query=getattr(self,"_hist_search_var",ctk.StringVar()).get().lower().strip()
        filt=getattr(self,"_hist_filter",ctk.StringVar(value="ALL")).get()
        filtered=[r for r in self._history if
            (not query or query in r.get("title","").lower() or
             query in r.get("date","").lower() or query in r.get("mode","").lower()) and
            (filt=="ALL" or r.get("mode","").upper()==filt)]
        if not filtered:
            ctk.CTkLabel(self.hist_frame,text="// SONUC BULUNAMADI.",
                font=(MONO_FONT,11),text_color=TEXT_DIM).pack(pady=20); return
        for rec in reversed(filtered[-50:]):
            row=ctk.CTkFrame(self.hist_frame,fg_color=SURF2,corner_radius=6,
                border_color=BORDER,border_width=1); row.pack(fill="x",pady=(0,4))
            ri=ctk.CTkFrame(row,fg_color="transparent"); ri.pack(fill="x",padx=12,pady=8)
            icon={"mp3":"[MP3]","m4a":"[M4A]","mp4":"[MP4]"}.get(rec.get("mode","mp4"),"[DL]")
            ctk.CTkLabel(ri,text=f"{icon} {rec.get('title','?')[:58]}",
                font=(MONO_FONT,11,"bold"),text_color=TEXT,anchor="w").pack(anchor="w")
            ctk.CTkLabel(ri,
                text=f"FMT:{rec.get('mode','').upper()} | QLT:{rec.get('quality','')} | {rec.get('date','')}",
                font=(MONO_FONT,9),text_color=TEXT_DIM,anchor="w").pack(anchor="w",pady=(2,0))
            btn_row=ctk.CTkFrame(ri,fg_color="transparent"); btn_row.pack(anchor="e",pady=(4,0))
            rbtn(btn_row,text="[▶] OYNATiCIDA AC",command=lambda r=rec:self._play_in_media(r),
                small=True,width=160).pack(side="left",padx=(0,6))
            rbtn(btn_row,text="[R] TEKRAR iNDiR",command=lambda r=rec:self._redownload(r),
                small=True,width=150).pack(side="left")

    # ── Stats Page ─────────────────────────────────────────────────────────────
    def _build_stats_page(self,body):
        ctk.CTkLabel(body,text="// iSTATiSTiKLER",font=(MONO_FONT,13,"bold"),
            text_color=ACCENT).pack(anchor="w",padx=28,pady=(16,8))
        self.stats_frame=ctk.CTkFrame(body,fg_color="transparent"); self.stats_frame.pack(fill="x",padx=28)

    def _refresh_stats_page(self):
        for w in self.stats_frame.winfo_children(): w.destroy()
        s=self._stats; total=s.get("total_count",0); tb=s.get("total_bytes",0); bf=s.get("by_format",{})
        cards=[("TOPLAM iNDiRME",str(total),"ADET"),("TOPLAM BOYUT",self._fmt_bytes(tb),""),
               ("MP3",str(bf.get("mp3",0)),"ADET"),("MP4",str(bf.get("mp4",0)),"ADET"),
               ("M4A",str(bf.get("m4a",0)),"ADET")]
        grid=ctk.CTkFrame(self.stats_frame,fg_color="transparent"); grid.pack(fill="x")
        for i,(lbl,val,unit) in enumerate(cards):
            card=ctk.CTkFrame(grid,fg_color=SURF2,corner_radius=6,border_color=BORDER,border_width=1)
            card.grid(row=i//3,column=i%3,padx=5,pady=5,sticky="ew"); grid.columnconfigure(i%3,weight=1)
            ctk.CTkLabel(card,text=f"// {lbl}",font=(MONO_FONT,8),text_color=TEXT_DIM).pack(pady=(10,2))
            ctk.CTkLabel(card,text=val,font=(TITLE_FONT,24,"bold"),text_color=ACCENT).pack()
            ctk.CTkLabel(card,text=unit,font=(MONO_FONT,8),text_color=TEXT_DIM).pack(pady=(0,10))
        rbtn(self.stats_frame,text="[R] SIFIRLA",command=self._reset_stats,
            danger=True,small=True,width=120).pack(pady=(12,0))

    def _reset_stats(self):
        self._stats={"total_count":0,"total_bytes":0,"by_format":{"mp3":0,"mp4":0,"m4a":0}}
        save_stats_file(self._stats); self._refresh_stats_page()

    # ── Settings Page ─────────────────────────────────────────────────────────
    def _build_settings_page(self,body):
        def sec(title):
            f=ctk.CTkFrame(body,fg_color=SURF2,corner_radius=6,border_color=BORDER,border_width=1)
            f.pack(fill="x",padx=28,pady=(8,0))
            ctk.CTkLabel(f,text=f"// {title}",font=(MONO_FONT,9,"bold"),text_color=ACCENT
                ).pack(anchor="w",padx=12,pady=(10,4)); return f

        ctk.CTkLabel(body,text="// AYARLAR",font=(MONO_FONT,13,"bold"),
            text_color=ACCENT).pack(anchor="w",padx=28,pady=(16,4))

        spd=sec("iNDiRME HIZ LiMiTi")
        sr=ctk.CTkFrame(spd,fg_color="transparent"); sr.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkLabel(sr,text="MAKS HIZ (MB/s) — 0=LiMiTSiZ:",font=(MONO_FONT,10),
            text_color=TEXT_MID).pack(side="left")
        ctk.CTkEntry(sr,textvariable=self._speed_limit,width=70,font=(MONO_FONT,11),
            fg_color=SURF3,border_color=BORDER,text_color=TEXT,
            height=30,corner_radius=4).pack(side="left",padx=(10,0))

        upd=sec("YT-DLP GUNCELLEME")
        ur=ctk.CTkFrame(upd,fg_color="transparent"); ur.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkLabel(ur,text="YouTube degisikliklerine karsi guncel tutun.",
            font=(MONO_FONT,10),text_color=TEXT_MID).pack(side="left")
        rbtn(ur,text="[ GUNCELLE ]",command=self._update_ytdlp,accent=True,small=True,width=120).pack(side="right")

        notif=sec("BiLDiRiMLER")
        nr=ctk.CTkFrame(notif,fg_color="transparent"); nr.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkCheckBox(nr,text="iNDiRME TAMAMLANINCA SES",
            variable=self._notif_sound_var,font=(MONO_FONT,10),text_color=TEXT_MID,
            fg_color=ACCENT,hover_color=ACCENT2,checkmark_color=BG).pack(side="left")

        tray=sec("SiSTEM TEPSiSi")
        tr=ctk.CTkFrame(tray,fg_color="transparent"); tr.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkCheckBox(tr,text="KUCULTUNCE TEPSiYE GiZLE",
            variable=self._tray_var,font=(MONO_FONT,10),text_color=TEXT_MID,
            fg_color=ACCENT,hover_color=ACCENT2,checkmark_color=BG,
            command=self._toggle_tray).pack(side="left")

        prx=sec("PROXY")
        pr=ctk.CTkFrame(prx,fg_color="transparent"); pr.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkLabel(pr,text="URL:",font=(MONO_FONT,10),text_color=TEXT_DIM,width=36).pack(side="left")
        ctk.CTkEntry(pr,textvariable=self._proxy_var,placeholder_text="http://proxy:port veya socks5://...",
            font=(MONO_FONT,10),fg_color=SURF3,border_color=BORDER,text_color=TEXT,
            height=30,corner_radius=4).pack(side="left",fill="x",expand=True,padx=(6,0))

        ck=sec("COOKiE")
        cr=ctk.CTkFrame(ck,fg_color="transparent"); cr.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkEntry(cr,textvariable=self._cookie_file,placeholder_text="cookies.txt yolu...",
            font=(MONO_FONT,10),fg_color=SURF3,border_color=BORDER,text_color=TEXT,
            height=30,corner_radius=4).pack(side="left",fill="x",expand=True,padx=(0,8))
        rbtn(cr,text="[F] SEC",command=self._pick_cookie_file,small=True,width=80).pack(side="left")

        disc=sec("DISCORD RPC")
        dr=ctk.CTkFrame(disc,fg_color="transparent"); dr.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkCheckBox(dr,text="DISCORD STATUS GOSTER (indirirken)",
            variable=self._discord_enabled,font=(MONO_FONT,10),text_color=TEXT_MID,
            fg_color=ACCENT,hover_color=ACCENT2,checkmark_color=BG,
            command=self._toggle_discord).pack(side="left")
        self._discord_status_lbl=ctk.CTkLabel(dr,text="",font=(MONO_FONT,9),text_color=TEXT_DIM)
        self._discord_status_lbl.pack(side="left",padx=(12,0))

        ytupd=sec("OTOMATIK YT-DLP KONTROLU")
        yu=ctk.CTkFrame(ytupd,fg_color="transparent"); yu.pack(fill="x",padx=12,pady=(0,12))
        ctk.CTkLabel(yu,text="Program acilisinda otomatik guncelleme kontrolu yapar.",
            font=(MONO_FONT,10),text_color=TEXT_MID).pack(side="left")
        self._ytdlp_update_lbl=ctk.CTkLabel(yu,text="",font=(MONO_FONT,9),text_color=ACCENT)
        self._ytdlp_update_lbl.pack(side="left",padx=(10,0))

        ctk.CTkLabel(body,text="",height=20).pack()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _gcard(self, parent, **kw):
        return ctk.CTkFrame(parent,fg_color=SURF2,corner_radius=6,
                             border_color=BORDER,border_width=1,**kw)

    def _draw_placeholder_thumb(self):
        bg=(6,21,20) if _IS_DARK else (224,232,255)
        fg=(0,80,60) if _IS_DARK else (0,83,200)
        img=Image.new("RGB",(142,80),color=bg); draw=ImageDraw.Draw(img)
        cx,cy=71,40; draw.polygon([(cx-12,cy-14),(cx-12,cy+14),(cx+16,cy)],fill=fg)
        ci=ctk.CTkImage(light_image=img,dark_image=img,size=(142,80))
        self.thumb_lbl.configure(image=ci,text=""); self._thumb_ref=ci

    def _set_mode(self,mode):
        self.mode_var.set(mode)
        for m,btn in {"mp3":self.mp3_btn,"mp4":self.mp4_btn,"m4a":self.m4a_btn}.items():
            if m==mode: btn.configure(fg_color=ACCENT,text_color=BG,hover_color=ACCENT2)
            else: btn.configure(fg_color=SURF3,text_color=TEXT_DIM,hover_color=SURF2)
        if self._info: self._populate_quality(self._info)

    def _log(self,msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end",f">> {msg}\n")
        self.log_box.see("end"); self.log_box.configure(state="disabled")

    def _status(self,msg,color=None):
        self.status_lbl.configure(text=f"// {msg}",text_color=color or TEXT_DIM)

    def _set_progress(self,val,pct_str=""):
        self.progress_bar.set(val); self._pct_var.set(pct_str)

    def _browse_path(self):
        from tkinter import filedialog
        folder=filedialog.askdirectory(initialdir=self._dl_path)
        if folder:
            self._dl_path=folder
            self.path_entry.delete(0,"end"); self.path_entry.insert(0,folder)

    def _toggle_clip_ui(self): pass

    def _seconds_to_hms(self,secs):
        if not secs: return "?"
        h,r=divmod(int(secs),3600); m,s=divmod(r,60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def _validate_time(self,s):
        s=s.strip()
        if not s: return None
        parts=s.split(":")
        try:
            if len(parts)==3: return int(parts[0])*3600+int(parts[1])*60+int(parts[2])
            if len(parts)==2: return int(parts[0])*60+int(parts[1])
            return int(parts[0])
        except: return None

    def _load_stats(self): return load_stats_file()

    def _update_stats(self,mode,filesize=0):
        self._stats["total_count"]=self._stats.get("total_count",0)+1
        self._stats["total_bytes"]=self._stats.get("total_bytes",0)+filesize
        bf=self._stats.setdefault("by_format",{"mp3":0,"mp4":0,"m4a":0})
        bf[mode]=bf.get(mode,0)+1; save_stats_file(self._stats)

    def _fmt_bytes(self,b):
        if b<1024: return f"{b}B"
        if b<1024**2: return f"{b/1024:.1f}KB"
        if b<1024**3: return f"{b/1024**2:.1f}MB"
        return f"{b/1024**3:.2f}GB"

    # ── Fetch ─────────────────────────────────────────────────────────────────
    def _fetch_info(self):
        if self._fetching: self._fetch_stop.set(); return
        url=clean_url(self.url_entry.get())
        if not url: self._log("URL BOS OLAMAZ."); return
        self.url_entry.delete(0,"end"); self.url_entry.insert(0,url)
        self._fetching=True; self._fetch_stop.clear()
        self.fetch_btn.configure(text="[X] iPTAL",fg_color=SURF3,
            hover_color=SURF2,text_color=RED,border_color=RED,border_width=1)
        self.dl_btn.configure(state="disabled")
        self._draw_placeholder_thumb()
        self.vid_title_lbl.configure(text="// ANALiZ EDiLiYOR...",text_color=TEXT_DIM)
        self.vid_meta_lbl.configure(text="")
        self._log(f"ANALIZ: {url[:65]}...")
        self._status(f"ANALiZ EDiLiYOR... (max {FETCH_TIMEOUT}s)",YELLOW)
        threading.Thread(target=self._fetch_thread,args=(url,),daemon=True).start()

    def _fetch_thread(self,url):
        try:
            info=get_video_info(url,self._fetch_stop)
            if self._fetch_stop.is_set(): self.after(0,self._on_fetch_cancelled)
            else:
                self._info=info; self.after(0,self._on_fetch_done,info)
        except Exception as e: self.after(0,self._on_fetch_error,str(e))

    def _reset_fetch_btn(self):
        self._fetching=False
        self.fetch_btn.configure(text="[ ANALiZ ET ]",fg_color=ACCENT,
            hover_color=ACCENT2,border_width=0,text_color=BG)

    def _on_fetch_done(self,info):
        self._reset_fetch_btn()
        title=info.get("title","BILINMIYOR")
        duration=self._seconds_to_hms(info.get("duration"))
        channel=info.get("uploader","?")
        views=f"{info.get('view_count',0):,}".replace(",",".")
        self.vid_title_lbl.configure(text=title,text_color=TEXT)
        self.vid_meta_lbl.configure(
            text=f"[CH] {channel}   [DU] {duration}   [VW] {views}",
            text_color=TEXT_MID)
        self._populate_quality(info)
        self._log(f"OK '{title[:55]}' HAZIR.")
        self._status("VIDEO BULUNDU — KALiTE SECIN VE iNDiRiN.",GREEN)
        vid_id=info.get("id") or ""; thumb_url=info.get("thumbnail") or ""
        threading.Thread(target=self._load_thumbnail,args=(thumb_url,vid_id),daemon=True).start()

    def _load_thumbnail(self,url,vid_id=""):
        candidates=[]
        if url: candidates.append(url)
        if vid_id:
            candidates+=[f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
                          f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                          f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"]
        headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0",
                 "Accept":"image/avif,image/webp,image/*,*/*;q=0.8",
                 "Referer":"https://www.youtube.com/"}
        ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
        opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        for thu in candidates:
            try:
                resp=opener.open(urllib.request.Request(thu,headers=headers),timeout=12)
                data=resp.read()
                if len(data)<800: continue
                img=Image.open(io.BytesIO(data)).convert("RGB")
                w,h=img.size; th=int(w*9/16)
                if th<h: img=img.crop((0,(h-th)//2,w,(h-th)//2+th))
                img=img.resize((142,80),Image.LANCZOS)
                ci=ctk.CTkImage(light_image=img,dark_image=img,size=(142,80))
                self.after(0,self.thumb_lbl.configure,{"image":ci,"text":""})
                self._thumb_ref=ci; return
            except: continue

    def _on_fetch_cancelled(self):
        self._reset_fetch_btn()
        self.vid_title_lbl.configure(text="// ANALiZ iPTAL EDiLDi.",text_color=TEXT_DIM)
        self._log("ANALIZ IPTAL."); self._status("ANALiZ iPTAL EDiLDi.",ORANGE)

    def _on_fetch_error(self,err):
        self._reset_fetch_btn()
        self.vid_title_lbl.configure(text="// VIDEO ALINAMADI.",text_color=RED)
        self._log(f"HATA: {err[:120]}"); self._status("VIDEO ALINAMADI.",RED)

    # ── Download ──────────────────────────────────────────────────────────────
    def _start_download(self):
        if not self._info or not self._formats: return
        sel_label=self.quality_var.get()
        sel_fmt=next((f[1] for f in self._formats if f[0]==sel_label),None)
        if not sel_fmt: return
        url=self.url_entry.get().strip(); mode=self.mode_var.get()
        outdir=self.path_entry.get().strip() or self._dl_path
        cs=None; ce=None
        if self._clip_enabled.get():
            cs=self._validate_time(self._clip_start.get())
            ce=self._validate_time(self._clip_end.get())
        sub=self._subtitle_var.get(); sub_lang=self._sub_lang_var.get()
        self._dl_cancelled=False; self._dl_paused=False
        self._dl_pause_lock.set(); self._downloading=True
        self.dl_btn.configure(state="disabled",text="iNDiRiLiYOR...")
        self.fetch_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal",text="[P] DURDUR")
        self.cancel_dl_btn.configure(state="normal")
        self._set_progress(0,"")
        self._log(f"iNDiRME >> {mode.upper()} / {sel_label}")
        self._discord_set_downloading(self._info.get("title","") if self._info else "")
        threading.Thread(target=self._download_thread,
            args=(url,mode,sel_fmt,outdir,self._info.get("title",""),sel_label,cs,ce,sub,sub_lang),
            daemon=True).start()

    def _toggle_pause(self):
        if not self._downloading: return
        if self._dl_paused:
            self._dl_paused=False; self._dl_pause_lock.set()
            self.pause_btn.configure(text="[P] DURDUR",fg_color=SURF3,text_color=TEXT_MID,
                border_color=BORDER)
            self._status("DEVAM EDiYOR...",YELLOW); self._log("DEVAM ETTiRiLDi.")
        else:
            self._dl_paused=True; self._dl_pause_lock.clear()
            self.pause_btn.configure(text="[R] DEVAM",fg_color=SURF2,text_color=GREEN,
                border_color=GREEN)
            self._status("DURAKLATILDI.",ORANGE); self._log("DURAKLATILDI.")

    def _cancel_download(self):
        if not self._downloading: return
        self._dl_cancelled=True; self._dl_pause_lock.set()
        if self._ydl_instance:
            try: self._ydl_instance.params['abort']=True
            except: pass
        self._log("iPTAL EDiLiYOR..."); self._status("iPTAL EDiLiYOR...",RED)
        self.after(3000,self._force_cancel_check)

    def _force_cancel_check(self):
        if self._dl_cancelled and self._downloading:
            self.after(0,self._on_download_cancelled)

    def _build_ydl_opts(self,mode,fmt_id,outdir,clip_start=None,clip_end=None,subtitle=False,sub_lang="tr"):
        outtmpl=os.path.join(outdir,"%(title)s.%(ext)s")
        base={"quiet":True,"no_warnings":True,"outtmpl":outtmpl,
              "progress_hooks":[self._progress_hook],"socket_timeout":15,
              "retries":3,"nocheckcertificate":True}
        try:
            spd=float(self._speed_limit.get())
            if spd>0: base["ratelimit"]=int(spd*1024*1024)
        except: pass
        if FFMPEG_DIR: base["ffmpeg_location"]=FFMPEG_DIR
        proxy=self._proxy_var.get().strip()
        if proxy: base["proxy"]=proxy
        ck=self._cookie_file.get().strip()
        if ck and Path(ck).exists(): base["cookiefile"]=ck
        pp_args={}
        if clip_start is not None or clip_end is not None:
            ss=["-ss",str(clip_start)] if clip_start is not None else []
            to=["-to",str(clip_end)] if clip_end is not None else []
            pp_args={"default":ss+to}
        if subtitle:
            base["writesubtitles"]=True; base["writeautomaticsub"]=True
            base["subtitleslangs"]=[sub_lang,"en"]; base["subtitlesformat"]="srt"
        if mode=="mp3":
            opts={**base,"format":"bestaudio/best",
                    "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":fmt_id}]}
            if pp_args: opts["postprocessor_args"]=pp_args
            return opts
        if mode=="m4a":
            opts={**base,"format":"bestaudio[ext=m4a]/bestaudio/best",
                    "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"m4a","preferredquality":fmt_id}]}
            if pp_args: opts["postprocessor_args"]=pp_args
            return opts
        fmt_str=(f"{fmt_id}+bestaudio[ext=m4a]/{fmt_id}+bestaudio/"
                 f"bestvideo[height<={fmt_id}]+bestaudio/best")
        merger=["-c:v","copy","-c:a","aac","-b:a","192k"]
        opts_pp={"merger":merger,**pp_args} if pp_args else {"merger":merger}
        return {**base,"format":fmt_str,"merge_output_format":"mp4",
                "postprocessors":[{"key":"FFmpegVideoConvertor","preferedformat":"mp4"},
                                   {"key":"FFmpegMetadata"}],
                "postprocessor_args":opts_pp}

    def _download_thread(self,url,mode,fmt_id,outdir,title="",quality_label="",
                          clip_start=None,clip_end=None,subtitle=False,sub_lang="tr"):
        try:
            opts=self._build_ydl_opts(mode,fmt_id,outdir,clip_start,clip_end,subtitle,sub_lang)
            self._ydl_instance=yt_dlp.YoutubeDL(opts)
            with self._ydl_instance as ydl: ydl.download([url])
            if not self._dl_cancelled:
                self._add_history(title,mode,quality_label,url)
                self._update_stats(mode)
                self.after(0,self._on_download_done)
            else: self.after(0,self._on_download_cancelled)
        except Exception as e:
            if self._dl_cancelled: self.after(0,self._on_download_cancelled)
            else: self.after(0,self._on_download_error,str(e))
        finally: self._ydl_instance=None

    def _progress_hook(self,d):
        self._dl_pause_lock.wait()
        if self._dl_cancelled: raise Exception("iPTAL.")
        s=d.get("status")
        if s=="downloading":
            total=d.get("total_bytes") or d.get("total_bytes_estimate",0)
            dl=d.get("downloaded_bytes",0); spd=d.get("speed",0) or 0; eta=d.get("eta",0) or 0
            pct=(dl/total) if total else 0
            self.after(0,self._set_progress,pct,f"{pct*100:.0f}%")
            self.after(0,self._status,
                f"iNDiRiLiYOR... {spd/1024/1024:.1f}MB/s {'ETA:'+str(eta)+'s' if eta else ''}",YELLOW)
        elif s=="finished":
            self.after(0,self._set_progress,0.99,"99%")
            self.after(0,self._status,"iSLENiYOR (ffmpeg)...",YELLOW)

    def _reset_dl_ui(self):
        self._downloading=False
        self.dl_btn.configure(state="normal",text="▼  [ iNDiR ]  ▼")
        self.fetch_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled",text="[P] DURDUR",
            fg_color=SURF3,text_color=TEXT_MID,border_color=BORDER)
        self.cancel_dl_btn.configure(state="disabled")

    def _on_download_done(self):
        self._set_progress(1.0,"100%"); self._status("OK — iNDiRME TAMAMLANDI!",GREEN)
        folder=self.path_entry.get(); self._last_dl_folder=folder
        self._log(f"OK >> {folder}")
        self._reset_dl_ui(); self._play_done_sound()
        self._tray_notify("ITCHY","Indirme tamamlandi!")
        self._send_toast("ITCHY","Indirme tamamlandi!","Dosya klasore kaydedildi.")
        self._discord_set_idle()
        if self._open_folder_var.get(): self._open_folder(folder)

    def _on_download_cancelled(self):
        self._set_progress(0,""); self._status("iPTAL EDiLDi.",ORANGE)
        self._log("iPTAL."); self._reset_dl_ui()

    def _on_download_error(self,err):
        self._set_progress(0,""); self._status("iNDiRME BASARISIZ.",RED)
        self._log(f"HATA: {err[:120]}"); self._reset_dl_ui()

    def _open_folder(self,path):
        try:
            import subprocess
            if sys.platform=="win32": subprocess.Popen(f'explorer "{path}"')
            elif sys.platform=="darwin": subprocess.Popen(["open",path])
            else: subprocess.Popen(["xdg-open",path])
        except: pass

    # ── History ───────────────────────────────────────────────────────────────
    def _add_history(self,title,mode,quality,url):
        rec={"title":title,"mode":mode,"quality":quality,"url":url,
             "date":datetime.now().strftime("%d.%m.%Y %H:%M")}
        self._history.append(rec); save_history(self._history)

    def _clear_history(self):
        self._history=[]; save_history(self._history); self._refresh_history_page()

    def _redownload(self,rec):
        self._switch_tab("indir")
        self.url_entry.delete(0,"end"); self.url_entry.insert(0,rec.get("url",""))
        self._fetch_info()

    # ── Queue ─────────────────────────────────────────────────────────────────
    def _add_to_queue_from_url(self):
        url=clean_url(self.url_entry.get())
        if not url or not self._info: self._log("ONCE ANALiZ ET'E BASIN."); return
        sel=self.quality_var.get()
        fmt=next((f[1] for f in self._formats if f[0]==sel),None)
        if not fmt: return
        item=QueueItem(url=url,title=self._info.get("title",""),mode=self.mode_var.get(),
            quality_label=sel,fmt_id=fmt,outdir=self.path_entry.get() or self._dl_path)
        item.info=self._info; self._queue.append(item)
        self._log(f"KUYRUGA EKLENDi: {item.title[:40]}")
        self._switch_tab("queue"); self._refresh_queue_ui()

    def _queue_add_url(self):
        url=clean_url(self.q_url_entry.get())
        if not url: return
        self.q_url_entry.delete(0,"end")
        item=QueueItem(url=url,title=url[:55],mode=self.q_mode_var.get(),
            quality_label=self.q_quality_var.get(),fmt_id="",outdir=self._dl_path)
        self._queue.append(item); self._refresh_queue_ui()

    def _queue_remove(self,item):
        if item in self._queue: self._queue.remove(item)
        self._refresh_queue_ui()

    def _queue_clear(self):
        self._queue=[]; self._refresh_queue_ui()

    def _queue_start(self):
        if self._queue_running: return
        self._queue_running=True; self._queue_stop=False
        self.q_start_btn.configure(state="disabled")
        threading.Thread(target=self._queue_worker,daemon=True).start()

    def _queue_stop_all(self):
        self._queue_stop=True; self._queue_running=False
        self.q_start_btn.configure(state="normal")
        if self._ydl_instance:
            try: self._ydl_instance.params['abort']=True
            except: pass

    def _queue_worker(self):
        for item in self._queue:
            if self._queue_stop: break
            if item.status=="tamamlandi": continue
            item.status="analiz"; self.after(0,self._q_update_row,item)
            try:
                if not item.info: item.info=get_video_info(item.url)
                item.title=item.info.get("title",item.url[:50])
                if not item.fmt_id:
                    fmts=build_format_list(item.info,item.mode)
                    prefix=item.quality_label.split("  ")[0]
                    matched=next((f[1] for f in fmts if f[0].startswith(prefix)),
                                  fmts[0][1] if fmts else "best")
                    item.fmt_id=matched
            except Exception as e:
                item.status="hata"; item.error=str(e)
                self.after(0,self._q_update_row,item); continue
            item.status="indiriliyor"; self.after(0,self._q_update_row,item)
            try:
                def make_hook(it):
                    def hook(d):
                        if self._queue_stop: raise Exception("Durduruldu")
                        if d.get("status")=="downloading":
                            total=d.get("total_bytes") or d.get("total_bytes_estimate",0)
                            dl=d.get("downloaded_bytes",0)
                            it.progress=(dl/total) if total else 0
                            self.after(0,self._q_update_row,it)
                    return hook
                opts=self._build_ydl_opts(item.mode,item.fmt_id,item.outdir)
                opts["progress_hooks"]=[make_hook(item)]
                self._ydl_instance=yt_dlp.YoutubeDL(opts)
                with self._ydl_instance as ydl: ydl.download([item.url])
                item.status="tamamlandi"; item.progress=1.0
                self._add_history(item.title,item.mode,item.quality_label,item.url)
                self._update_stats(item.mode)
            except Exception as e:
                item.status="iptal" if self._queue_stop else "hata"; item.error=str(e)
            finally: self._ydl_instance=None
            self.after(0,self._q_update_row,item)
        self._queue_running=False
        self.after(0,self.q_start_btn.configure,{"state":"normal"})
        if not self._queue_stop:
            self._play_done_sound()
            self._tray_notify("ITCHY","Kuyruk tamamlandi!")

    def _q_update_row(self,item):
        if not item.row_frame: return
        colors={"bekliyor":TEXT_DIM,"analiz":YELLOW,"indiriliyor":ACCENT,
                "tamamlandi":GREEN,"hata":RED,"iptal":ORANGE}
        c=colors.get(item.status,TEXT_DIM)
        if item.status_lbl:
            item.status_lbl.configure(
                text=f"[{item.status.upper()[:3]}] {item.title[:52]}",text_color=c)
        if item.progress_bar:
            item.progress_bar.configure(progress_color=c); item.progress_bar.set(item.progress)

    # ── Batch ─────────────────────────────────────────────────────────────────
    def _batch_pick_file(self):
        from tkinter import filedialog
        f=filedialog.askopenfilename(filetypes=[("Text","*.txt"),("All","*.*")])
        if f: self._batch_file.set(f)

    def _batch_load_file(self):
        p=self._batch_file.get().strip()
        if not p or not Path(p).exists(): return
        try:
            lines=Path(p).read_text(encoding="utf-8").splitlines()
            self.batch_text.delete("1.0","end")
            self.batch_text.insert("end","\n".join(l.strip() for l in lines if l.strip()))
        except Exception as e: self._batch_log_append(f"HATA: {e}")

    def _batch_log_append(self,msg):
        self.batch_log.configure(state="normal")
        self.batch_log.insert("end",f">> {msg}\n")
        self.batch_log.see("end"); self.batch_log.configure(state="disabled")

    def _batch_start(self):
        raw=self.batch_text.get("1.0","end").strip()
        if not raw: return
        urls=[clean_url(l.strip()) for l in raw.splitlines() if l.strip()]
        if not urls: return
        mode=self.batch_mode_var.get(); qlabel=self.batch_qual_var.get()
        self._batch_log_append(f"{len(urls)} LiNK BULUNDU. BASLIYOR...")
        threading.Thread(target=self._batch_worker,args=(urls,mode,qlabel,self._dl_path),daemon=True).start()

    def _batch_worker(self,urls,mode,quality_label,outdir):
        for i,url in enumerate(urls,1):
            self.after(0,self._batch_log_append,f"[{i}/{len(urls)}] {url[:55]}")
            try:
                info=get_video_info(url)
                title=info.get("title","video")
                fmts=build_format_list(info,mode)
                prefix=quality_label.split("  ")[0]
                fmt=next((f[1] for f in fmts if f[0].startswith(prefix)),
                          fmts[0][1] if fmts else "best")
                opts={"quiet":True,"no_warnings":True,
                      "outtmpl":os.path.join(outdir,"%(title)s.%(ext)s"),
                      "socket_timeout":15,"retries":3,"nocheckcertificate":True}
                if FFMPEG_DIR: opts["ffmpeg_location"]=FFMPEG_DIR
                proxy=self._proxy_var.get().strip()
                if proxy: opts["proxy"]=proxy
                if mode=="mp3":
                    opts["format"]="bestaudio/best"
                    opts["postprocessors"]=[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
                elif mode=="m4a":
                    opts["format"]="bestaudio[ext=m4a]/bestaudio/best"
                    opts["postprocessors"]=[{"key":"FFmpegExtractAudio","preferredcodec":"m4a","preferredquality":"192"}]
                else:
                    opts["format"]=f"{fmt}+bestaudio[ext=m4a]/{fmt}+bestaudio/best"
                    opts["merge_output_format"]="mp4"
                    opts["postprocessors"]=[{"key":"FFmpegVideoConvertor","preferedformat":"mp4"}]
                    opts["postprocessor_args"]={"merger":["-c:v","copy","-c:a","aac","-b:a","192k"]}
                with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
                self._add_history(title,mode,quality_label,url)
                self._update_stats(mode)
                self.after(0,self._batch_log_append,f"OK: {title[:48]}")
            except Exception as e:
                self.after(0,self._batch_log_append,f"HATA [{url[:35]}]: {str(e)[:50]}")
        self.after(0,self._batch_log_append,"BATCH TAMAMLANDI!")
        self._play_done_sound()

    # ── Mini mode ─────────────────────────────────────────────────────────────
    def _toggle_mini_mode(self):
        if not self._mini_mode:
            # Enter mini mode
            self._mini_mode = True
            self._full_geo = self.geometry()
            # Hide all widgets
            for w in self.winfo_children():
                try: w.pack_forget()
                except: pass
            self.geometry("500x80")
            self.resizable(False, False)
            self.configure(fg_color=SURF3)
            # Mini bar
            mf = ctk.CTkFrame(self, fg_color=SURF2, corner_radius=0,
                               border_color=ACCENT, border_width=1)
            mf.pack(fill="x", padx=4, pady=4)
            # Restore button (prominent)
            ctk.CTkButton(mf, text="[↑]", font=(MONO_FONT,11,"bold"),
                width=40, height=38, corner_radius=4,
                fg_color=SURF3, hover_color=BORDER, text_color=ACCENT,
                border_color=ACCENT, border_width=1,
                command=self._exit_mini_mode).pack(side="left", padx=(4,6), pady=4)
            # URL entry
            self._mini_url_entry = ctk.CTkEntry(mf,
                placeholder_text="URL yapistir...",
                font=(MONO_FONT,11), fg_color=SURF3, border_color=BORDER,
                text_color=TEXT, height=38, corner_radius=6)
            self._mini_url_entry.pack(side="left", fill="x", expand=True, padx=(0,6))
            self._mini_url_entry.bind("<Return>", lambda e: self._mini_download())
            # Download button
            ctk.CTkButton(mf, text="[▼] iNDiR", font=(MONO_FONT,10,"bold"),
                width=90, height=38, corner_radius=4,
                fg_color=ACCENT, hover_color=ACCENT2, text_color=BG,
                command=self._mini_download).pack(side="left", padx=(0,4), pady=4)
            self._mini_frame = mf
        else:
            self._exit_mini_mode()

    def _exit_mini_mode(self):
        """Restore full window from mini mode."""
        self._mini_mode = False
        # Destroy all current widgets
        for w in self.winfo_children():
            try: w.destroy()
            except: pass
        # Restore geometry
        self.geometry(getattr(self, "_full_geo", "1080x840"))
        self.resizable(True, True)
        self.configure(fg_color=BG)
        # Rebuild
        self._pct_var = ctk.StringVar(value="")
        try: self.unbind("<Return>")
        except: pass
        self._build_ui()
        self._set_window_icon()
        self.bind("<Return>", lambda e: self._fetch_info())
        self.after(10, lambda: self.state("zoomed"))

    def _mini_download(self):
        url=clean_url(self._mini_url_entry.get() if hasattr(self,"_mini_url_entry") else "")
        if not url: return
        self._toggle_mini_mode()
        self.url_entry.delete(0,"end"); self.url_entry.insert(0,url)
        self._fetch_info()

    # ── Cookie file ───────────────────────────────────────────────────────────
    def _pick_cookie_file(self):
        from tkinter import filedialog
        f=filedialog.askopenfilename(filetypes=[("Text","*.txt"),("All","*.*")])
        if f: self._cookie_file.set(f)

    # ── Settings actions ──────────────────────────────────────────────────────
    def _update_ytdlp(self):
        self._log("YT-DLP GUNCELLENIYOR...")
        def worker():
            try:
                import subprocess
                r=subprocess.run([sys.executable,"-m","pip","install","-U","yt-dlp",
                                   "--break-system-packages","--quiet"],
                    capture_output=True,text=True,timeout=60)
                msg="YT-DLP GUNCELLENDi!" if r.returncode==0 else f"HATA: {r.stderr[:60]}"
            except Exception as e: msg=f"HATA: {e}"
            self.after(0,self._log,msg)
        threading.Thread(target=worker,daemon=True).start()

    def _play_done_sound(self):
        if SOUND_OK and self._notif_sound_var.get():
            try: winsound.MessageBeep(winsound.MB_ICONINFORMATION)
            except: pass

    def _toggle_tray(self):
        if self._tray_var.get(): self._start_tray()
        else: self._stop_tray()

    def _start_tray(self):
        if not TRAY_OK or self._tray_icon: return
        img=Image.new("RGB",(64,64),color=(0,229,176))
        draw=ImageDraw.Draw(img); draw.polygon([(20,16),(20,48),(50,32)],fill=(4,13,12))
        menu=(TrayItem("Goster",self._tray_show),TrayItem("Cikis",self._tray_quit))
        self._tray_icon=pystray.Icon("itchy",img,"ITCHY Downloader",menu)
        threading.Thread(target=self._tray_icon.run,daemon=True).start()

    def _stop_tray(self):
        if self._tray_icon:
            try: self._tray_icon.stop()
            except: pass
            self._tray_icon=None

    def _tray_show(self): self.after(0,self.deiconify); self.after(0,self.lift)
    def _tray_quit(self): self._stop_tray(); self.after(0,self.destroy)

    def _tray_notify(self,title,msg):
        if self._tray_icon:
            try: self._tray_icon.notify(msg,title)
            except: pass

    # ── Drag & drop ───────────────────────────────────────────────────────────
    def _setup_drag_drop(self, widget):
        """Enable drag & drop URL into entry widget."""
        try:
            import tkinterdnd2 as dnd
            widget.drop_target_register(dnd.DND_TEXT, dnd.DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)
        except ImportError:
            # Fallback: bind paste event
            widget.bind("<Button-3>", self._show_paste_menu)

    def _on_drop(self, event):
        data = event.data.strip().strip("{}")
        url = clean_url(data)
        if url:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            self._fetch_info()

    def _show_paste_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Yapistir", command=self._paste_url)
        try: menu.tk_popup(event.x_root, event.y_root)
        finally: menu.grab_release()

    def _paste_url(self):
        try:
            txt = self.clipboard_get().strip()
            if txt:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, txt)
        except: pass

    # ── Windows Toast notification ─────────────────────────────────────────────
    def _send_toast(self, title, heading, body=""):
        if not TOAST_OK: return
        try:
            toast = Notification(
                app_id="ITCHY Downloader",
                title=heading,
                msg=body,
                duration="short"
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except: pass

    # ── Discord RPC ───────────────────────────────────────────────────────────
    def _toggle_discord(self):
        if self._discord_enabled.get():
            self._discord_connect()
        else:
            self._discord_disconnect()

    def _discord_connect(self):
        if not DISCORD_OK:
            self._discord_status_lbl.configure(text="[pypresence yuklu degil]",text_color=RED)
            return
        try:
            self._discord_rpc = pypresence.Presence("1234567890")  # placeholder app id
            self._discord_rpc.connect()
            self._discord_connected = True
            self._discord_status_lbl.configure(text="[BAGLANDI]",text_color=GREEN)
            self._discord_set_idle()
        except Exception as e:
            self._discord_status_lbl.configure(
                text=f"[BAGLANAMADI — Discord acik mi?]",text_color=RED)
            self._discord_connected = False

    def _discord_disconnect(self):
        if self._discord_rpc:
            try: self._discord_rpc.close()
            except: pass
        self._discord_connected = False
        self._discord_rpc = None
        if hasattr(self,"_discord_status_lbl"):
            self._discord_status_lbl.configure(text="",text_color=TEXT_DIM)

    def _discord_set_downloading(self, title=""):
        if not self._discord_connected or not self._discord_rpc: return
        try:
            self._discord_rpc.update(
                state="Indiriliyor...",
                details=title[:80] if title else "Video indiriliyor",
                large_image="itchy_logo",
                large_text="ITCHY YouTube Downloader v1.0",
                start=int(time.time())
            )
        except: pass

    def _discord_set_idle(self):
        if not self._discord_connected or not self._discord_rpc: return
        try:
            self._discord_rpc.update(
                state="Bekliyor...",
                details="ITCHY YouTube Downloader",
                large_image="itchy_logo",
                large_text="ITCHY v1.0"
            )
        except: pass

    # ── Media player ──────────────────────────────────────────────────────────
    def _play_in_media(self, rec):
        """Open downloaded file in system default media player."""
        title = rec.get("title","")
        outdir = self._dl_path
        # Try to find the file
        if not title: return
        # Search for file matching title
        found = None
        for ext in ["mp4","mp3","m4a","webm","mkv"]:
            # Clean filename (yt-dlp sanitizes special chars)
            for f in Path(outdir).glob(f"*.{ext}"):
                if title[:20].lower() in f.stem.lower():
                    found = str(f); break
            if found: break
        if found:
            try:
                if sys.platform == "win32":
                    os.startfile(found)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", found])
                else:
                    subprocess.Popen(["xdg-open", found])
                self._log(f"OYNATICI: {Path(found).name}")
            except Exception as e:
                self._log(f"OYNATICI HATASI: {e}")
        else:
            # Open folder if file not found
            self._open_folder(outdir)
            self._log("DOSYA BULUNAMADI — KLASOR ACILDI.")

    # ── Auto yt-dlp update check ───────────────────────────────────────────────
    def _auto_check_ytdlp(self):
        """Silently check if yt-dlp has an update available on startup."""
        try:
            time.sleep(3)  # wait for app to fully load
            result = subprocess.run(
                [sys.executable, "-m", "pip", "index", "versions", "yt-dlp"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                # Parse latest version
                out = result.stdout
                import re
                match = re.search(r"Available versions: ([^ ,]+)", out)
                if match:
                    latest = match.group(1).strip()
                    # Get installed version
                    ver_result = subprocess.run(
                        [sys.executable, "-m", "pip", "show", "yt-dlp"],
                        capture_output=True, text=True, timeout=10
                    )
                    inst_match = re.search(r"Version: ([^ ]+)", ver_result.stdout)
                    if inst_match:
                        installed = inst_match.group(1).strip()
                        if installed != latest:
                            self.after(0, self._notify_ytdlp_update, installed, latest)
        except: pass

    def _notify_ytdlp_update(self, installed, latest):
        try:
            if hasattr(self, "_ytdlp_update_lbl"):
                self._ytdlp_update_lbl.configure(
                    text=f"[GUNCELLEME VAR: {installed} -> {latest}]",
                    text_color=YELLOW)
            self._log(f"YT-DLP GUNCELLEME: {installed} -> {latest} (Ayarlar > Guncelle)")
        except: pass

    # ── Theme toggle ──────────────────────────────────────────────────────────
    def _toggle_theme(self):
        if getattr(self, "_theme_switching", False): return
        self._theme_switching = True

        global _IS_DARK
        self._is_dark = not self._is_dark
        _IS_DARK = self._is_dark
        _ap(DARK if self._is_dark else LIGHT)

        self.withdraw()

        # Unbind ALL events first to prevent callback accumulation
        try: self.unbind("<Return>")
        except: pass
        try: self.unbind_all("<Return>")
        except: pass

        # Destroy children
        for w in list(self.winfo_children()):
            try: w.destroy()
            except: pass

        # Reset state
        self._info=None; self._formats=[]; self._fetching=False
        self._fetch_stop=threading.Event()
        self._dl_cancelled=False; self._dl_paused=False
        self._dl_pause_lock=threading.Event(); self._dl_pause_lock.set()
        self._downloading=False; self._ydl_instance=None
        self._thumb_ref=None; self._logo_ref=None
        self._pct_var=ctk.StringVar(value="")
        self._quality_values=["-- URL GIRIN --"]
        self._dropdown_open=False; self._dropdown_win=None
        self._active_tab="indir"
        self._clip_start=ctk.StringVar(value="")
        self._clip_end=ctk.StringVar(value="")
        self._clip_enabled=ctk.BooleanVar(value=False)
        self._subtitle_var=ctk.BooleanVar(value=False)
        self._sub_lang_var=ctk.StringVar(value="tr")
        self._open_folder_var=ctk.BooleanVar(value=True)
        self._batch_file=ctk.StringVar(value="")
        self._filesize_var=ctk.StringVar(value="")
        self._hist_search_var=ctk.StringVar(value="")

        self.configure(fg_color=BG)
        self._build_ui()
        self._set_window_icon()
        # Bind ONCE
        self.bind("<Return>", lambda e: self._fetch_info())

        self.deiconify()
        self.state("zoomed")
        self._theme_switching = False

    def _on_close(self):
        if self._tray_var.get() and TRAY_OK: self.withdraw()
        else: self._stop_tray(); self.destroy()

# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ItchyApp()
    app.mainloop()