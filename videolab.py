"""
════════════════════════════════════════════════
 RAJ VIDEO LAB v1.0 — Batch Video Editor
 Created By Raj - Content World
════════════════════════════════════════════════
"""
import os, queue, threading, traceback
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from rajstickers import *
from rajeditor import RegionEditor, process_video

# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("⚡ RAJ VIDEO LAB v1.0 — Created By Raj Content World")
        self.geometry("760x760")
        self.configure(fg_color=BG)
        self.items = []          # privacy items (shared, normalized)
        self.q = queue.Queue()
        self.running = False

        ctk.CTkLabel(self, text="⚡ RAJ VIDEO LAB", font=("Arial Black", 30),
                     text_color=NEON).pack(pady=(16, 0))
        ctk.CTkLabel(self, text="Batch Video Editor  •  v1.0", font=("Arial", 13),
                     text_color="#7c8a99").pack()

        # folders
        card = self._card("📁  FOLDERS")
        self.in_var = tk.StringVar()
        self.out_var = tk.StringVar()
        self._folder_row(card, "Input Folder  ", self.in_var)
        self._folder_row(card, "Output Folder", self.out_var)

        # functions
        card = self._card("🎛  FUNCTIONS  (ORIGINAL = video ko touch nahi karega)")
        self.up_var = self._opt_row(card, "⬆ Upscale", ["ORIGINAL", "1080p", "2K", "4K"])
        self.col_var = self._opt_row(card, "🎨 Color Grading",
                                     ["ORIGINAL", "Cinematic", "Warm", "Cool", "Vintage", "Vibrant", "Manual"],
                                     cmd=self._toggle_manual)
        self.man_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.b_sl = self._slider(self.man_frame, "Brightness", -50, 50, 0)
        self.c_sl = self._slider(self.man_frame, "Contrast", 50, 150, 100)
        self.s_sl = self._slider(self.man_frame, "Saturation", 0, 200, 100)
        self.ratio_var = self._opt_row(card, "📐 Aspect Ratio", ["ORIGINAL", "9:16", "16:9", "1:1", "4:5"])

        # privacy
        card = self._card("🔒  PRIVACY  (Blur / Pixelate / Stickers)")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=6)
        self.priv_var = ctk.StringVar(value="ORIGINAL")
        ctk.CTkSegmentedButton(row, values=["ORIGINAL", "CUSTOM"], variable=self.priv_var,
                               selected_color=NEON2, text_color="white").pack(side="left")
        ctk.CTkButton(row, text="✏ Open Privacy Editor", fg_color=NEON2, text_color="white",
                      command=self.open_editor).pack(side="left", padx=12)
        self.priv_info = ctk.CTkLabel(row, text="0 items set", text_color="#7c8a99")
        self.priv_info.pack(side="left")

        # start + progress
        self.start_btn = ctk.CTkButton(self, text="🚀  START BATCH PROCESSING", height=52,
                                       font=("Arial Black", 17), fg_color=NEON,
                                       text_color="black", hover_color="#00b8cc",
                                       command=self.start)
        self.start_btn.pack(fill="x", padx=16, pady=(14, 6))
        self.pbar = ctk.CTkProgressBar(self, progress_color=NEON)
        self.pbar.set(0)
        self.pbar.pack(fill="x", padx=16, pady=4)
        self.status = ctk.CTkLabel(self, text="Ready.", text_color="#7c8a99")
        self.status.pack()
        self.logbox = ctk.CTkTextbox(self, height=150, fg_color="#0e141b",
                                     text_color="#9adfff", font=("Consolas", 12))
        self.logbox.pack(fill="both", expand=True, padx=16, pady=(4, 14))
        self.after(120, self._poll)

    # ---- UI builders ----
    def _card(self, title):
        f = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14)
        f.pack(fill="x", padx=16, pady=7)
        ctk.CTkLabel(f, text=title, font=("Arial", 14, "bold"),
                     text_color="white").pack(anchor="w", padx=12, pady=(10, 2))
        return f

    def _folder_row(self, parent, label, var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text=label, width=110, anchor="w",
                     text_color="#c9d6e2").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, fg_color="#0e141b",
                     text_color="white").pack(side="left", fill="x", expand=True, padx=6)
        ctk.CTkButton(row, text="Browse", width=80, fg_color="#333c48",
                      command=lambda: var.set(filedialog.askdirectory() or var.get())).pack(side="left")

    def _opt_row(self, parent, label, values, cmd=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=5)
        ctk.CTkLabel(row, text=label, width=150, anchor="w",
                     text_color="#c9d6e2").pack(side="left")
        var = ctk.StringVar(value="ORIGINAL")
        seg = ctk.CTkSegmentedButton(row, values=values, variable=var,
                                     selected_color=NEON, selected_hover_color="#00b8cc",
                                     text_color="white", command=cmd)
        seg.pack(side="left", fill="x", expand=True)
        return var

    def _slider(self, parent, label, lo, hi, default):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, width=100, anchor="w",
                     text_color="#8fa4b8").pack(side="left", padx=(24, 0))
        sl = ctk.CTkSlider(row, from_=lo, to=hi, progress_color=NEON)
        sl.set(default)
        sl.pack(side="left", fill="x", expand=True, padx=8)
        return sl

    def _toggle_manual(self, val):
        if val == "Manual":
            self.man_frame.pack(fill="x", padx=12, pady=2)
        else:
            self.man_frame.pack_forget()

    # ---- actions ----
    def first_frame(self):
        folder = self.in_var.get()
        vids = sorted([f for f in os.listdir(folder)
                       if f.lower().endswith(VIDEO_EXTS)]) if os.path.isdir(folder) else []
        if not vids:
            return None
        cap = cv2.VideoCapture(os.path.join(folder, vids[0]))
        ok, frame = cap.read()
        cap.release()
        return frame if ok else None

    def open_editor(self):
        frame = self.first_frame()
        if frame is None:
            messagebox.showwarning("Input Folder", "Pehle valid Input Folder select karo (jismein videos hain).")
            return
        ed = RegionEditor(self, frame, self.items)
        self.wait_window(ed)
        self.priv_info.configure(text=f"{len(self.items)} items set")
        if self.items:
            self.priv_var.set("CUSTOM")

    def log(self, msg):
        self.q.put(msg)

    def _poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg.startswith("PROGRESS "):
                    a, b = msg.split()[1].split("/")
                    self.pbar.set(min(1.0, int(a) / max(1, int(b))))
                elif msg.startswith("STATUS "):
                    self.status.configure(text=msg[7:])
                elif msg == "DONE":
                    self.running = False
                    self.start_btn.configure(state="normal", text="🚀  START BATCH PROCESSING")
                else:
                    self.logbox.insert("end", msg + "\n")
                    self.logbox.see("end")
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def start(self):
        if self.running:
            return
        inp, out = self.in_var.get(), self.out_var.get()
        if not os.path.isdir(inp) or not os.path.isdir(out):
            messagebox.showwarning("Folders", "Input aur Output dono valid folders select karo.")
            return
        if os.path.abspath(inp) == os.path.abspath(out):
            messagebox.showwarning("Folders", "Input aur Output folder alag hone chahiye.")
            return
        settings = {
            "upscale": self.up_var.get(),
            "color": self.col_var.get(),
            "manual": (self.b_sl.get(), self.c_sl.get() / 100.0, self.s_sl.get() / 100.0),
            "ratio": self.ratio_var.get(),
            "privacy": self.priv_var.get() == "CUSTOM",
            "items": list(self.items),
        }
        if settings["privacy"] and not settings["items"]:
            messagebox.showwarning("Privacy", "Privacy CUSTOM hai lekin koi area/sticker set nahi. Editor kholo ya ORIGINAL karo.")
            return
        if (settings["upscale"] == "ORIGINAL" and settings["color"] == "ORIGINAL"
                and settings["ratio"] == "ORIGINAL" and not settings["privacy"]):
            messagebox.showinfo("Kuch select karo", "Saare functions ORIGINAL pe hain — koi ek toh ON karo bhai 😄")
            return
        self.running = True
        self.start_btn.configure(state="disabled", text="⏳ PROCESSING...")
        threading.Thread(target=self._worker, args=(inp, out, settings), daemon=True).start()

    def _worker(self, inp, out, settings):
        try:
            vids = sorted([f for f in os.listdir(inp) if f.lower().endswith(VIDEO_EXTS)])
            self.log(f"══════ RAJ VIDEO LAB — {len(vids)} videos found ══════")
            done = 0
            for i, name in enumerate(vids, 1):
                self.log(f"STATUS Video {i}/{len(vids)}: {name}")
                self.log(f"▶ [{i}/{len(vids)}] {name}")
                base = os.path.splitext(name)[0]
                dst = os.path.join(out, base + ".mp4")   # same naam, .mp4 container
                ok = process_video(os.path.join(inp, name), dst, settings, self.log)
                if ok:
                    done += 1
                    self.log(f"✅ Done: {base}.mp4")
                self.q.put("PROGRESS 1/1")
            self.log(f"══════ COMPLETE: {done}/{len(vids)} videos ✅ ══════")
            self.q.put("STATUS All done! Output folder check karo.")
        except Exception:
            self.log("❌ ERROR:\n" + traceback.format_exc()[:600])
        finally:
            self.q.put("DONE")


if __name__ == "__main__":
    App().mainloop()
