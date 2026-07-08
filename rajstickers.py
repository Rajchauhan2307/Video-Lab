"""RAJ VIDEO LAB v1.0 — stickers + constants"""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
    else:
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
    shadow = Image.new("RGBA", (560, 560), (0, 0, 0, 0))
    a = base.split()[3].point(lambda p: int(p * 0.45))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 255))
    sh.putalpha(a)
    shadow.paste(sh, (30, 34), sh)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    shadow.paste(base, (24, 24), base)
    _sticker_cache[ck] = shadow
    return shadow
