"""
════════════════════════════════════════════════════════
 RAJ VIDEO LAB v1.0  —  Batch Video Editor
 Created By Raj - Content World
════════════════════════════════════════════════════════
 Features:
  • Input/Output folder batch processing (same filenames)
  • Upscale: ORIGINAL | 1080p | 2K | 4K (Lanczos + sharpen)
  • Color Grading: ORIGINAL | 5 presets | Manual
  • Aspect Ratio: ORIGINAL | 9:16 | 16:9 | 1:1 | 4:5
  • Privacy: ORIGINAL | Blur (4 levels) | Pixelate (3 sizes)
             | 15 HD Stickers + Custom PNG
  • One video pe area set karo -> saari videos pe apply
  • Audio preserved, high-bitrate export (CRF 16)
════════════════════════════════════════════════════════
"""
import os, sys, math, queue, threading, subprocess, traceback
import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageTk

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".flv")

NEON = "#00e5ff"
NEON2 = "#ff2d78"
BG = "#0b0f14"
CARD = "#121820"

BLUR_LEVELS = {"Light": 21, "Medium": 41, "Strong": 71, "Extreme": 111}
PIXEL_LEVELS = {"Small": 0.10, "Medium": 0.05, "Large": 0.025}
RATIOS = {"9:16": 9/16, "16:9": 16/9, "1:1": 1.0, "4:5": 4/5}
UPSCALE_H = {"1080p": 1080, "2K": 1440, "4K": 2160}

# ─────────────────────────────────────────────
#  STICKER FACTORY  (vector-render, 512px HD)
# ─────────────────────────────────────────────
def _font(size, bold=True):
    for name in (("arialbd.ttf" if bold else "arial.ttf"),
                 "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _button(text, color, icon=None, tcolor="white"):
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([16, 156, 496, 356], radius=64, fill=color)
    f = _font(96)
    tw = d.textlength(text, font=f)
    ix = 0
    if icon:
        ix = 70
    d.text(((S - tw + ix) / 2, 208), text, font=f, fill=tcolor)
    if icon == "thumb":
        _thumb(d, 60, 200, 100, "white")
    elif icon == "arrow":
        d.polygon([(60, 256), (130, 200), (130, 232), (190, 232),
                   (190, 280), (130, 280), (130, 312)], fill="white")
    elif icon == "plus":
        d.rounded_rectangle([70, 244, 170, 268], radius=10, fill="white")
        d.rounded_rectangle([108, 206, 132, 306], radius=10, fill="white")
    return img

def _thumb(d, x, y, s, color):
    d.rounded_rectangle([x, y + s * 0.45, x + s * 0.28, y + s * 1.05], radius=10, fill=color)
    d.rounded_rectangle([x + s * 0.30, y + s * 0.40, x + s * 1.0, y + s * 1.05], radius=18, fill=color)
    d.rounded_rectangle([x + s * 0.38, y, x + s * 0.62, y + s * 0.55], radius=12, fill=color)

def _face(mouth):
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([56, 56, 456, 456], fill="#ffd93b", outline="#e0a800", width=8)
    if mouth == "laugh":
        d.arc([140, 130, 230, 220], 200, 340, fill="#7a4a00", width=16)
        d.arc([282, 130, 372, 220], 200, 340, fill="#7a4a00", width=16)
        d.pieslice([150, 230, 362, 400], 0, 180, fill="#7a2b06")
        d.pieslice([185, 300, 327, 400], 0, 180, fill="#ff8a80")
    else:  # wow
        d.ellipse([160, 150, 215, 225], fill="#5a3a00")
        d.ellipse([297, 150, 352, 225], fill="#5a3a00")
        d.ellipse([210, 260, 302, 380], fill="#7a2b06")
        d.arc([140, 100, 235, 150], 180, 360, fill="#7a4a00", width=12)
        d.arc([277, 100, 372, 150], 180, 360, fill="#7a4a00", width=12)
    return img

def _heart(color="#ff1744"):
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([76, 96, 266, 286], fill=color)
    d.ellipse([246, 96, 436, 286], fill=color)
    d.polygon([(90, 230), (422, 230), (256, 440)], fill=color)
    return img

def _star():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy, R, r = 256, 266, 210, 84
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    d.polygon(pts, fill="#ffcc00", outline="#e0a800")
    return img

def _fire():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(256, 30), (150, 200), (190, 210), (120, 360),
               (256, 470), (392, 360), (322, 210), (362, 200)], fill="#ff5722")
    d.polygon([(256, 150), (195, 280), (230, 285), (190, 380),
               (256, 445), (322, 380), (282, 285), (317, 280)], fill="#ffc107")
    d.polygon([(256, 260), (222, 340), (256, 420), (290, 340)], fill="#fff59d")
    return img

def _hundred():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = _font(190)
    d.text((70, 130), "100", font=f, fill="#e53935")
    d.rounded_rectangle([70, 340, 442, 372], radius=14, fill="#e53935")
    d.rounded_rectangle([70, 392, 442, 424], radius=14, fill="#e53935")
    return img

def _play():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([76, 136, 436, 376], radius=80, fill="#e53935")
    d.polygon([(216, 196), (216, 316), (326, 256)], fill="white")
    return img

def _warning():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(256, 46), (476, 436), (36, 436)], fill="#ffc107")
    d.polygon([(256, 96), (436, 412), (76, 412)], fill="#ffc107", outline="#5a4500")
    f = _font(220)
    d.text((216, 160), "!", font=f, fill="#1a1a1a")
    return img

def _bell():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.pieslice([116, 96, 396, 376], 180, 360, fill="#ffca28")
    d.rectangle([116, 236, 396, 356], fill="#ffca28")
    d.rounded_rectangle([86, 340, 426, 386], radius=20, fill="#ffb300")
    d.ellipse([226, 386, 286, 446], fill="#ffb300")
    d.rounded_rectangle([236, 66, 276, 110], radius=14, fill="#ffca28")
    return img

def _comment():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([56, 96, 456, 356], radius=70, fill="#2196f3")
    d.polygon([(150, 340), (150, 440), (250, 350)], fill="#2196f3")
    for i, x in enumerate((156, 236, 316)):
        d.ellipse([x, 196, x + 60, 256], fill="white")
    return img

def _tap():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([26, 176, 486, 336], radius=60, fill="#ffca28")
    f = _font(84)
    d.text((66, 216), "TAP HERE", font=f, fill="#1a1a1a")
    d.polygon([(256, 346), (216, 436), (296, 436)], fill="#ffca28")
    return img

def _clap():
    S = 512
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for ang in (-35, -10, 15):
        a = math.radians(ang)
        x1, y1 = 256 + 240 * math.cos(a - .09), 250 - 240 * math.sin(a - .09)
        x2, y2 = 256 + 240 * math.cos(a + .09), 250 - 240 * math.sin(a + .09)
        d.line([(256, 250), ((x1 + x2) / 2, (y1 + y2) / 2)], fill="#ffca28", width=18)
    d.ellipse([146, 230, 306, 430], fill="#ffb74d")
    d.ellipse([226, 210, 396, 420], fill="#ffca28", outline="#e09b00", width=6)
    for x in (250, 292, 334):
        d.rounded_rectangle([x, 160, x + 34, 260], radius=16, fill="#ffca28")
    return img

STICKERS = {
    "👍 LIKE":      lambda: _button("LIKE", "#1877f2", icon="thumb"),
    "❤ LOVE":       lambda: _heart(),
    "📤 SHARE":     lambda: _button("SHARE", "#00c853", icon="arrow"),
    "➕ FOLLOW":    lambda: _button("FOLLOW", "#1877f2", icon="plus"),
    "🔔 SUBSCRIBE": lambda: _bell(),
    "💬 COMMENT":   lambda: _comment(),
    "👆 TAP HERE":  lambda: _tap(),
    "😂 LAUGH":     lambda: _face("laugh"),
    "🔥 FIRE":      lambda: _fire(),
    "💯 100":       lambda: _hundred(),
    "😮 WOW":       lambda: _face("wow"),
    "⭐ STAR":      lambda: _star(),
    "👏 CLAP":      lambda: _clap(),
    "▶ PLAY":       lambda: _play(),
    "⚠ WARNING":    lambda: _warning(),
}

_sticker_cache = {}

def get_sticker(key, custom_path=None):
    """Returns HD RGBA PIL image with soft shadow for natural blend."""
    ck = custom_path or key
    if ck in _sticker_cache:
        return _sticker_cache[ck]
    if custom_path:
        base = Image.open(custom_path).convert("RGBA")
        m = max(base.size)
        canvas = Image.new("RGBA", (m, m), (0, 0, 0, 0))
        canvas.paste(base, ((m - base.width) // 2, (m - base.height) // 2), base)
        base = canvas.resize((512, 512), Image.LANCZOS)
    else:
        base = STICKERS[key]()
    # soft drop shadow -> video ke saath natural blend
    shadow = Image.new("RGBA", (560, 560), (0, 0, 0, 0))
    a = base.split()[3].point(lambda p: int(p * 0.45))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 255))
    sh.putalpha(a)
    shadow.paste(sh, (30, 34), sh)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    shadow.paste(base, (24, 24), base)
    _sticker_cache[ck] = shadow
    return shadow


# ─────────────────────────────────────────────
#  REGION / STICKER EDITOR WINDOW
# ─────────────────────────────────────────────
class RegionEditor(ctk.CTkToplevel):
    """Draw blur/pixelate rects + place/drag/resize stickers on first frame.
       Saved items are NORMALIZED (0-1) -> apply on ALL videos."""
    HANDLE = 14

    def __init__(self, master, frame_bgr, items):
        super().__init__(master)
        self.title("Privacy Editor — area set karo (saari videos pe apply hoga)")
        self.configure(fg_color=BG)
        self.grab_set()
        self.items = items          # shared list of dicts
        self.frame = frame_bgr
        H, W = frame_bgr.shape[:2]
        scr_w = self.winfo_screenwidth() - 160
        scr_h = self.winfo_screenheight() - 260
        self.scale = min(scr_w / W, scr_h / H, 1.0)
        self.dw, self.dh = int(W * self.scale), int(H * self.scale)
        self.ow, self.oh = W, H

        bar = ctk.CTkFrame(self, fg_color=CARD)
        bar.pack(fill="x", padx=8, pady=6)
        self.mode = ctk.StringVar(value="select")
        for txt, m in (("🖱 Select", "select"), ("◼ Add BLUR", "blur"), ("▦ Add PIXELATE", "pixel")):
            ctk.CTkRadioButton(bar, text=txt, variable=self.mode, value=m,
                               fg_color=NEON, text_color="white").pack(side="left", padx=8, pady=6)
        self.blur_lv = ctk.CTkOptionMenu(bar, values=list(BLUR_LEVELS), width=110,
                                         fg_color="#1e2a36", button_color=NEON, text_color="white")
        self.blur_lv.set("Medium"); self.blur_lv.pack(side="left", padx=4)
        self.pix_lv = ctk.CTkOptionMenu(bar, values=list(PIXEL_LEVELS), width=110,
                                        fg_color="#1e2a36", button_color=NEON, text_color="white")
        self.pix_lv.set("Medium"); self.pix_lv.pack(side="left", padx=4)

        bar2 = ctk.CTkFrame(self, fg_color=CARD)
        bar2.pack(fill="x", padx=8, pady=(0, 6))
        self.stk = ctk.CTkOptionMenu(bar2, values=list(STICKERS), width=170,
                                     fg_color="#1e2a36", button_color=NEON2, text_color="white")
        self.stk.set("👍 LIKE"); self.stk.pack(side="left", padx=8, pady=6)
        ctk.CTkButton(bar2, text="+ Add Sticker", fg_color=NEON2, text_color="white",
                      width=110, command=self.add_sticker).pack(side="left", padx=4)
        ctk.CTkButton(bar2, text="🖼 Custom PNG", fg_color="#333c48", text_color="white",
                      width=110, command=self.add_custom).pack(side="left", padx=4)
        ctk.CTkButton(bar2, text="🗑 Delete Selected", fg_color="#7a1f2b", text_color="white",
                      width=130, command=self.delete_sel).pack(side="left", padx=12)
        ctk.CTkButton(bar2, text="✅ SAVE & CLOSE", fg_color="#00c853", text_color="black",
                      width=140, command=self.destroy).pack(side="right", padx=8)

        self.canvas = tk.Canvas(self, width=self.dw, height=self.dh,
                                bg="black", highlightthickness=0, cursor="cross")
        self.canvas.pack(padx=8, pady=(0, 8))
        rgb = cv2.cvtColor(cv2.resize(frame_bgr, (self.dw, self.dh)), cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self._thumbs = {}
        self.sel = None
        self.drag = None
        self.canvas.bind("<ButtonPress-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.redraw()

    # ---- geometry helpers (display px <-> normalized) ----
    def to_disp(self, it):
        return (it["x"] * self.dw, it["y"] * self.dh, it["w"] * self.dw, it["h"] * self.dh)

    def redraw(self):
        self.canvas.delete("item")
        for i, it in enumerate(self.items):
            x, y, w, h = self.to_disp(it)
            sel = (i == self.sel)
            if it["type"] == "sticker":
                key = (it.get("custom") or it["key"], int(w), int(h))
                if key not in self._thumbs:
                    img = get_sticker(it["key"], it.get("custom")).resize(
                        (max(2, int(w)), max(2, int(h))), Image.LANCZOS)
                    self._thumbs[key] = ImageTk.PhotoImage(img)
                self.canvas.create_image(x, y, anchor="nw", image=self._thumbs[key], tags="item")
                if sel:
                    self.canvas.create_rectangle(x, y, x + w, y + h, outline=NEON2,
                                                 width=2, dash=(4, 3), tags="item")
            else:
                color = NEON if it["type"] == "blur" else "#ffca28"
                self.canvas.create_rectangle(x, y, x + w, y + h, outline=color,
                                             width=3 if sel else 2, tags="item")
                self.canvas.create_text(x + 6, y + 6, anchor="nw", tags="item",
                                        text=("BLUR " if it["type"] == "blur" else "PIXEL ") + it["param"],
                                        fill=color, font=("Arial", 11, "bold"))
            if sel:  # resize handle bottom-right
                hs = self.HANDLE
                self.canvas.create_rectangle(x + w - hs, y + h - hs, x + w, y + h,
                                             fill=NEON2, outline="white", tags="item")

    def hit(self, px, py):
        for i in range(len(self.items) - 1, -1, -1):
            x, y, w, h = self.to_disp(self.items[i])
            if x <= px <= x + w and y <= py <= y + h:
                corner = (px >= x + w - self.HANDLE and py >= y + h - self.HANDLE)
                return i, corner
        return None, False

    def on_down(self, e):
        m = self.mode.get()
        if m in ("blur", "pixel"):
            self.drag = ("new", e.x, e.y)
            self.items.append({"type": m, "x": e.x / self.dw, "y": e.y / self.dh,
                               "w": 0.001, "h": 0.001,
                               "param": self.blur_lv.get() if m == "blur" else self.pix_lv.get()})
            self.sel = len(self.items) - 1
        else:
            i, corner = self.hit(e.x, e.y)
            self.sel = i
            if i is not None:
                x, y, w, h = self.to_disp(self.items[i])
                self.drag = ("resize", e.x, e.y) if corner else ("move", e.x - x, e.y - y)
        self.redraw()

    def on_move(self, e):
        if self.drag is None or self.sel is None:
            return
        kind, a, b = self.drag
        it = self.items[self.sel]
        ex = min(max(e.x, 0), self.dw)
        ey = min(max(e.y, 0), self.dh)
        if kind == "new":
            it["x"], it["y"] = min(a, ex) / self.dw, min(b, ey) / self.dh
            it["w"], it["h"] = abs(ex - a) / self.dw, abs(ey - b) / self.dh
        elif kind == "move":
            it["x"] = min(max(ex - a, 0), self.dw - it["w"] * self.dw) / self.dw
            it["y"] = min(max(ey - b, 0), self.dh - it["h"] * self.dh) / self.dh
        elif kind == "resize":
            x, y, _, _ = self.to_disp(it)
            if it["type"] == "sticker":  # keep square
                s = max(24, max(ex - x, ey - y))
                it["w"], it["h"] = s / self.dw, s / self.dh
            else:
                it["w"] = max(10, ex - x) / self.dw
                it["h"] = max(10, ey - y) / self.dh
        self.redraw()

    def on_up(self, e):
        if self.drag and self.drag[0] == "new" and self.sel is not None:
            it = self.items[self.sel]
            if it["w"] * self.dw < 8 or it["h"] * self.dh < 8:
                self.items.pop(self.sel)
                self.sel = None
        self.drag = None
        self.mode.set("select")
        self.redraw()

    def add_sticker(self):
        self.items.append({"type": "sticker", "key": self.stk.get(), "custom": None,
                           "x": 0.36, "y": 0.36,
                           "w": 0.28 * min(self.dw, self.dh) / self.dw,
                           "h": 0.28 * min(self.dw, self.dh) / self.dh})
        self.sel = len(self.items) - 1
        self.mode.set("select")
        self.redraw()

    def add_custom(self):
        p = filedialog.askopenfilename(filetypes=[("PNG image", "*.png")])
        if not p:
            return
        self.items.append({"type": "sticker", "key": "custom", "custom": p,
                           "x": 0.36, "y": 0.36,
                           "w": 0.28 * min(self.dw, self.dh) / self.dw,
                           "h": 0.28 * min(self.dw, self.dh) / self.dh})
        self.sel = len(self.items) - 1
        self.mode.set("select")
        self.redraw()

    def delete_sel(self):
        if self.sel is not None:
            self.items.pop(self.sel)
            self.sel = None
            self.redraw()


# ─────────────────────────────────────────────
#  VIDEO PROCESSING ENGINE
# ─────────────────────────────────────────────
def apply_privacy(frame, items, cache):
    H, W = frame.shape[:2]
    for idx, it in enumerate(items):
        x, y = int(it["x"] * W), int(it["y"] * H)
        w, h = max(2, int(it["w"] * W)), max(2, int(it["h"] * H))
        x, y = max(0, min(x, W - 2)), max(0, min(y, H - 2))
        w, h = min(w, W - x), min(h, H - y)
        if it["type"] == "blur":
            k = BLUR_LEVELS[it["param"]]
            k = max(3, min(k, (min(w, h) // 2) * 2 + 1))
            if k % 2 == 0:
                k += 1
            frame[y:y+h, x:x+w] = cv2.GaussianBlur(frame[y:y+h, x:x+w], (k, k), 0)
        elif it["type"] == "pixel":
            f = PIXEL_LEVELS[it["param"]]
            sw, sh = max(1, int(w * f)), max(1, int(h * f))
            small = cv2.resize(frame[y:y+h, x:x+w], (sw, sh), interpolation=cv2.INTER_LINEAR)
            frame[y:y+h, x:x+w] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        else:  # sticker (pre-rendered per size in cache)
            ck = (idx, w, h)
            if ck not in cache:
                pil = get_sticker(it["key"], it.get("custom")).resize((w, h), Image.LANCZOS)
                arr = np.array(pil)
                cache[ck] = (cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2BGR),
                             (arr[:, :, 3:4].astype(np.float32)) / 255.0)
            rgb, alpha = cache[ck]
            roi = frame[y:y+h, x:x+w].astype(np.float32)
            frame[y:y+h, x:x+w] = (rgb * alpha + roi * (1 - alpha)).astype(np.uint8)
    return frame

def crop_ratio(frame, ratio):
    H, W = frame.shape[:2]
    cur = W / H
    if abs(cur - ratio) < 0.01:
        return frame
    if cur > ratio:  # too wide 
