import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


# =========================
# SAFE TEXT
# =========================
def safe_text(text, default="Unknown Song"):
    if text is None:
        return default
    text = str(text).strip()
    return text if text else default


def trim(text, font, max_w):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


# =========================
# FETCH YT TITLE
# =========================
async def fetch_youtube_title(videoid: str):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={videoid}&format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title")
                    if title:
                        return title.strip()
    except:
        pass
    return None


# =========================
# DRAW ICONS
# =========================
def draw_shuffle(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+42, y+28), start=200, end=340, fill=color, width=width)
    draw.arc((x, y+20, x+42, y+48), start=20, end=160, fill=color, width=width)
    draw.polygon([(x+38, y+6), (x+54, y+8), (x+44, y+20)], fill=color)
    draw.polygon([(x+4, y+30), (x-8, y+42), (x+10, y+44)], fill=color)


def draw_prev(draw, x, y, size=40, color="white"):
    draw.polygon([(x + size*0.55, y), (x, y + size/2), (x + size*0.55, y + size)], fill=color)
    draw.rectangle((x + size*0.62, y, x + size*0.72, y + size), fill=color)
    draw.polygon([(x + size*1.1, y), (x + size*0.55, y + size/2), (x + size*1.1, y + size)], fill=color)


def draw_play(draw, x, y, size=40, color="white"):
    draw.polygon([(x, y), (x, y+size), (x+size, y+size/2)], fill=color)


def draw_next(draw, x, y, size=40, color="white"):
    draw.polygon([(x, y), (x + size*0.55, y + size/2), (x, y + size)], fill=color)
    draw.rectangle((x + size*0.62, y, x + size*0.72, y + size), fill=color)
    draw.polygon([(x + size*0.72, y), (x + size*1.27, y + size/2), (x + size*0.72, y + size)], fill=color)


def draw_repeat(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+48, y+38), start=210, end=20, fill=color, width=width)
    draw.arc((x+6, y+10, x+54, y+48), start=30, end=200, fill=color, width=width)
    draw.polygon([(x+40, y+2), (x+58, y+4), (x+48, y+18)], fill=color)
    draw.polygon([(x+10, y+32), (x-4, y+44), (x+14, y+46)], fill=color)


# =========================
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    if title.lower() in ["unknown song", "unknown", "none", ""]:
        yt_title = await fetch_youtube_title(videoid)
        if yt_title:
            title = yt_title

    # -------------------------
    # Download best thumbnail
    # -------------------------
    thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
                else:
                    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
                    async with s.get(thumb_url) as r2:
                        if r2.status == 200:
                            async with aiofiles.open(thumb_file, "wb") as f:
                                await f.write(await r2.read())
                        else:
                            thumb_file = None
    except:
        thumb_file = None

    # -------------------------
    # Load original image
    # -------------------------
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumbnail")
    except:
        original = Image.new("RGB", (1280, 720), (30, 30, 30))

    # Fit full image nicely
    fitted = ImageOps.contain(original, (1280, 720), method=Image.LANCZOS)
    canvas = Image.new("RGB", (1280, 720), (15, 15, 15))
    canvas.paste(fitted, ((1280 - fitted.width) // 2, (720 - fitted.height) // 2))
    original = canvas

    # =========================
    # BACKGROUND = SAME SONG THUMB BLUR
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(34))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)
    bg = ImageEnhance.Color(bg).enhance(0.95)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 120))
    bg = Image.alpha_composite(bg, dark)

    # =========================
    # GLASS CARD
    # =========================
    card_x, card_y = 70, 170
    card_w, card_h = 1140, 380

    glass = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 18))
    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 36, fill=255)

    shadow = Image.new("RGBA", (card_w+80, card_h+80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w+80, card_h+80), 40, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(35))
    bg.paste(shadow, (card_x-40, card_y-20), shadow)

    bg.paste(glass, (card_x, card_y), mask)

    outline = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(outline)
    od.rounded_rectangle((0, 0, card_w-1, card_h-1), 36, outline=(255, 255, 255, 55), width=2)
    bg.paste(outline, (card_x, card_y), outline)

    draw = ImageDraw.Draw(bg)

    # =========================
    # LEFT BIG ROUND THUMB
    # =========================
    circle_size = 300
    thumb_img = ImageOps.fit(original.convert("RGBA"), (circle_size, circle_size), method=Image.LANCZOS)

    mask = Image.new("L", (circle_size, circle_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, circle_size, circle_size), fill=255)
    thumb_img.putalpha(mask)

    border_size = circle_size + 18
    border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.ellipse((0, 0, border_size-1, border_size-1), fill=(255, 255, 255, 255))

    thumb_x = 130
    thumb_y = 210
    bg.paste(border, (thumb_x-9, thumb_y-9), border)
    bg.paste(thumb_img, (thumb_x, thumb_y), thumb_img)

    # =========================
    # FONTS
    # =========================
    title_font = load_font(36)
    meta_font = load_font(20)
    time_font = load_font(18)

    # =========================
    # TEXT
    # =========================
    clean_title = trim(title, title_font, 610)
    draw.text((560, 250), clean_title, fill="white", font=title_font)
    draw.text((560, 320), f"YouTube  |  {views} views", fill=(235, 235, 235), font=meta_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 560
    bar_x2 = 1120
    bar_y = 370

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), 8, fill=(255, 255, 255))
    progress = 0.58
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 10), 8, fill=(255, 0, 0))
    draw.ellipse((prog_x - 10, bar_y - 8, prog_x + 10, bar_y + 12), fill=(255, 0, 0))

    draw.text((560, 410), "00:00", fill="white", font=time_font)
    draw.text((1065, 410), duration, fill="white", font=time_font)

    # =========================
    # BUTTONS (PERFECT ALIGNMENT)
    # =========================
    icon_y = 465
    draw_shuffle(draw, 560, icon_y, color="white")
    draw_prev(draw, 700, icon_y+2, size=34, color="white")
    draw_play(draw, 840, icon_y+2, size=34, color="white")
    draw_next(draw, 955, icon_y+2, size=34, color="white")
    draw_repeat(draw, 1080, icon_y, color="white")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
