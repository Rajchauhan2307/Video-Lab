"""RAJ VIDEO LAB v1.0 — editor + processing engine"""
import os, subprocess
import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
from rajstickers import *

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
            if it["type"] == "sticker":  # keep sticker's real shape
                ar = it.get("ar", 1.0)
                s = max(30, ex - x)
                it["w"], it["h"] = s / self.dw, (s * ar) / self.dh
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
        img = get_sticker(self.stk.get())
        ar = img.height / img.width
        w_px = 0.42 * min(self.dw, self.dh)
        self.items.append({"type": "sticker", "key": self.stk.get(), "custom": None,
                           "ar": ar, "x": 0.36, "y": 0.36,
                           "w": w_px / self.dw,
                           "h": (w_px * ar) / self.dh})
        self.sel = len(self.items) - 1
        self.mode.set("select")
        self.redraw()

    def add_custom(self):
        p = filedialog.askopenfilename(filetypes=[("PNG image", "*.png")])
        if not p:
            return
        img = get_sticker("custom", p)
        ar = img.height / img.width
        w_px = 0.42 * min(self.dw, self.dh)
        self.items.append({"type": "sticker", "key": "custom", "custom": p,
                           "ar": ar, "x": 0.36, "y": 0.36,
                           "w": w_px / self.dw,
                           "h": (w_px * ar) / self.dh})
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
    if cur > ratio:  # too wide -> crop sides
        nw = int(H * ratio)
        x = (W - nw) // 2
        return frame[:, x:x+nw]
    nh = int(W / ratio)
    y = (H - nh) // 2
    return frame[y:y+nh, :]

def color_grade(frame, mode, manual):
    f = frame.astype(np.float32)
    if mode == "Manual":
        b, c, s = manual
        f = (f - 127.5) * c + 127.5 + b
        f = np.clip(f, 0, 255)
        hsv = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * s, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    presets = {  # (temp shift, contrast, saturation, fade)
        "Cinematic": (10, 1.14, 1.10, 0),
        "Warm":      (16, 1.04, 1.08, 0),
        "Cool":      (-16, 1.06, 1.02, 0),
        "Vintage":   (12, 0.94, 0.78, 14),
        "Vibrant":   (4, 1.12, 1.35, 0),
    }
    t, c, s, fade = presets[mode]
    f[:, :, 2] = np.clip(f[:, :, 2] + t, 0, 255)      # R
    f[:, :, 0] = np.clip(f[:, :, 0] - t * 0.7, 0, 255)  # B
    f = np.clip((f - 127.5) * c + 127.5 + fade, 0, 255)
    hsv = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * s, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def upscale(frame, target_h):
    H, W = frame.shape[:2]
    if H >= target_h:
        return frame
    scale = target_h / H
    out = cv2.resize(frame, (int(W * scale), target_h), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(out, (0, 0), 1.1)
    return cv2.addWeighted(out, 1.4, blur, -0.4, 0)  # unsharp = detail boost

def even(v):
    return v if v % 2 == 0 else v - 1

def process_video(src, dst, settings, log):
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        log(f"❌ Open failed: {os.path.basename(src)}")
        return False
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    ok, first = cap.read()
    if not ok:
        cap.release()
        log(f"❌ Read failed: {os.path.basename(src)}")
        return False
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # figure output dims from first frame through pipeline
    test = first.copy()
    if settings["ratio"] != "ORIGINAL":
        test = crop_ratio(test, RATIOS[settings["ratio"]])
    if settings["upscale"] != "ORIGINAL":
        test = upscale(test, UPSCALE_H[settings["upscale"]])
    oh, ow = even(test.shape[0]), even(test.shape[1])

    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}",
           "-r", f"{fps:.4f}", "-i", "-",
           "-i", src,
           "-map", "0:v:0", "-map", "1:a:0?",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", dst]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
    scache = {}
    n = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if settings["privacy"] and settings["items"]:
                frame = apply_privacy(frame, settings["items"], scache)
            if settings["ratio"] != "ORIGINAL":
                frame = crop_ratio(frame, RATIOS[settings["ratio"]])
            if settings["color"] != "ORIGINAL":
                frame = color_grade(frame, settings["color"], settings["manual"])
            if settings["upscale"] != "ORIGINAL":
                frame = upscale(frame, UPSCALE_H[settings["upscale"]])
            if frame.shape[0] != oh or frame.shape[1] != ow:
                frame = cv2.resize(frame, (ow, oh))
            proc.stdin.write(frame.tobytes())
            n += 1
            if n % 30 == 0:
                log(f"PROGRESS {n}/{total}")
    finally:
        cap.release()
        try:
            proc.stdin.close()
        except Exception:
            pass
        err = proc.stderr.read().decode(errors="ignore")
        proc.wait()
    if proc.returncode != 0:
        log(f"❌ FFmpeg error: {err[:300]}")
        return False
    return True
