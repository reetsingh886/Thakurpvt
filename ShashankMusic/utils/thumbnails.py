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


def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


def trim_text(text, font, max_width):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_width and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


# =========================
# FORMATTERS
# =========================
def parse_duration_to_seconds(duration: str):
    try:
        parts = [int(x) for x in str(duration).split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except:
        pass
    return 240  # fallback 4 min


def format_time(seconds: int):
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


def format_views(views):
    try:
        v = str(views).replace(",", "").strip()
        if not v or v == "0":
            return "45M"
        n = int(v)
        if n >= 1_000_000_000:
            return f"{round(n/1_000_000_000, 1)}B".replace(".0", "")
        elif n >= 1_000_000:
            return f"{round(n/1_000_000, 1)}M".replace(".0", "")
        elif n >= 1_000:
            return f"{round(n/1_000, 1)}K".replace(".0", "")
        return str(n)
    except:
        return str(views) if views else "45M"


# =========================
# FETCH TITLE
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
# ICONS
# =========================
def draw_prev(draw, x, y, color="white"):
    draw.polygon([(x+28, y), (x, y+20), (x+28, y+40)], fill=color)
    draw.rectangle((x+33, y, x+40, y+40), fill=color)


def draw_play(draw, x, y, color=(25, 25, 25)):
    draw.polygon([(x, y), (x, y+40), (x+34, y+20)], fill=color)


def draw_next(draw, x, y, color="white"):
    draw.polygon([(x, y), (x+28, y+20), (x, y+40)], fill=color)
    draw.rectangle((x+33, y, x+40, y+40), fill=color)


def draw_shuffle(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+38, y+28), start=200, end=340, fill=color, width=width)
    draw.arc((x, y+18, x+38, y+46), start=20, end=160, fill=color, width=width)
    draw.polygon([(x+35, y+5), (x+48, y+7), (x+39, y+18)], fill=color)
    draw.polygon([(x+5, y+30), (x-7, y+40), (x+10, y+42)], fill=color)


def draw_repeat(draw, x, y, color="white", width=5):
    draw.arc((x, y, x+42, y+34), start=210, end=20, fill=color, width=width)
    draw.arc((x+5, y+10, x+47, y+44), start=30, end=200, fill=color, width=width)
    draw.polygon([(x+36, y+2), (x+52, y+4), (x+42, y+17)], fill=color)
    draw.polygon([(x+8, y+29), (x-4, y+40), (x+12, y+42)], fill=color)


# =========================
# MAIN
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "4:00")
    views = safe_text(views, "45M")

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

    # download thumbnail
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

    # load image
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1280, 720), (30, 30, 30))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # DYNAMIC TIME / VIEWS
    # =========================
    total_seconds = parse_duration_to_seconds(duration)
    progress = 0.58
    current_seconds = int(total_seconds * progress)

    current_time = format_time(current_seconds)
    total_time = format_time(total_seconds)
    pretty_views = format_views(views)

    # =========================
    # BACKGROUND = SAME THUMB BLUR
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(34))
    bg = ImageEnhance.Brightness(bg).enhance(0.28)
    bg = ImageEnhance.Color(bg).enhance(0.95)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 95))
    bg = Image.alpha_composite(bg, dark)

    # center soft glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((180, 100, 1100, 660), fill=(255, 255, 255, 16))
    glow = glow.filter(ImageFilter.GaussianBlur(110))
    bg = Image.alpha_composite(bg, glow)

    # =========================
    # GLASS CARD
    # =========================
    card_x, card_y = 80, 145
    card_w, card_h = 1120, 420

    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 80, card_h + 80), 42, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    bg.paste(shadow, (card_x - 40, card_y - 20), shadow)

    card_crop = bg.crop((card_x, card_y, card_x + card_w, card_y + card_h))
    card_crop = card_crop.filter(ImageFilter.GaussianBlur(8))

    glass = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 16))
    card_crop = Image.alpha_composite(card_crop.convert("RGBA"), glass)

    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 36, fill=255)
    bg.paste(card_crop, (card_x, card_y), mask)

    border = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, card_w - 1, card_h - 1), 36, outline=(255, 255, 255, 50), width=2)
    bg.paste(border, (card_x, card_y), border)

    draw = ImageDraw.Draw(bg)

    # =========================
    # ROUND ALBUM
    # =========================
    thumb_size = 270
    album = ImageOps.fit(original.convert("RGBA"), (thumb_size, thumb_size), method=Image.LANCZOS)

    circle_mask = Image.new("L", (thumb_size, thumb_size), 0)
    ImageDraw.Draw(circle_mask).ellipse((0, 0, thumb_size, thumb_size), fill=255)
    album.putalpha(circle_mask)

    ring = Image.new("RGBA", (thumb_size + 18, thumb_size + 18), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((0, 0, thumb_size + 17, thumb_size + 17), fill=(255, 255, 255, 255))

    album_glow = Image.new("RGBA", (thumb_size + 90, thumb_size + 90), (0, 0, 0, 0))
    ag = ImageDraw.Draw(album_glow)
    ag.ellipse((25, 25, thumb_size + 65, thumb_size + 65), fill=(255, 255, 255, 50))
    album_glow = album_glow.filter(ImageFilter.GaussianBlur(22))

    thumb_x = 140
    thumb_y = 220
    bg.paste(album_glow, (thumb_x - 35, thumb_y - 35), album_glow)
    bg.paste(ring, (thumb_x - 9, thumb_y - 9), ring)
    bg.paste(album, (thumb_x, thumb_y), album)

    # =========================
    # FONTS
    # =========================
    title_font = load_font(34)
    meta_font = load_font(22)
    time_font = load_font(18)

    # =========================
    # TEXT
    # =========================
    title = trim_text(title, title_font, 560)

    text_x = 575
    draw.text((text_x, 235), title, fill="white", font=title_font)
    draw.text((text_x, 315), f"YouTube | {pretty_views} views", fill=(220, 220, 220), font=meta_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = text_x
    bar_x2 = 1125
    bar_y = 390

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 8), 8, fill=(255, 255, 255))
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 8), 8, fill=(255, 0, 0))
    draw.ellipse((prog_x - 11, bar_y - 10, prog_x + 11, bar_y + 12), fill=(255, 0, 0))

    draw.text((bar_x1, 430), current_time, fill="white", font=time_font)
    draw.text((1060, 430), total_time, fill="white", font=time_font)

    # =========================
    # CONTROLS
    # =========================
    controls_y = 488

    draw_shuffle(draw, 585, controls_y, color="white")
    draw_prev(draw, 730, controls_y + 2, color="white")

    play_shadow = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    ps = ImageDraw.Draw(play_shadow)
    ps.ellipse((15, 15, 105, 105), fill=(255, 255, 255, 50))
    play_shadow = play_shadow.filter(ImageFilter.GaussianBlur(18))
    bg.paste(play_shadow, (810, 435), play_shadow)

    draw.ellipse((830, 455, 920, 545), fill=(255, 255, 255, 245))
    draw_play(draw, 865, 480, color=(25, 25, 25))

    draw_next(draw, 980, controls_y + 2, color="white")
    draw_repeat(draw, 1085, controls_y, color="white")

    # save
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
