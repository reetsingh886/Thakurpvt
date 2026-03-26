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


# =========================
# FETCH TITLE FROM YOUTUBE
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
# FETCH VIEWS FROM YOUTUBE
# =========================
async def fetch_youtube_views(videoid: str):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={videoid}&format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return "YouTube"
    except:
        pass
    return "YouTube"


# =========================
# LOAD FONTS SAFELY
# =========================
def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


# =========================
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="YouTube"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "YouTube")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Fresh generate every time
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # Auto title fetch if missing
    if title.lower() in ["unknown song", "unknown", "none", ""]:
        yt_title = await fetch_youtube_title(videoid)
        if yt_title:
            title = yt_title

    if views.lower() in ["0", "none", "", "unknown"]:
        views = await fetch_youtube_views(videoid)

    # Download best thumbnail
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

    # Load original image
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumbnail")
    except:
        original = Image.new("RGB", (1600, 900), (25, 25, 25))

    original = ImageOps.fit(original, (1600, 900), method=Image.LANCZOS)

    # =========================
    # BACKGROUND
    # =========================
    bg = original.copy().filter(ImageFilter.GaussianBlur(30))
    bg = ImageEnhance.Brightness(bg).enhance(0.33)
    bg = ImageEnhance.Color(bg).enhance(0.85)
    bg = bg.convert("RGBA")

    overlay = Image.new("RGBA", (1600, 900), (10, 10, 10, 110))
    bg = Image.alpha_composite(bg, overlay)

    draw = ImageDraw.Draw(bg)

    # =========================
    # MAIN CARD
    # =========================
    card_x, card_y = 355, 70
    card_w, card_h = 890, 760

    # shadow
    shadow = Image.new("RGBA", (card_w + 100, card_h + 100), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 100, card_h + 100), 72, fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(45))
    bg.paste(shadow, (card_x - 50, card_y + 20), shadow)

    # card
    card = Image.new("RGBA", (card_w, card_h), (20, 20, 22, 240))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 65, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP IMAGE
    # =========================
    preview = ImageOps.fit(original.convert("RGBA"), (700, 300), method=Image.LANCZOS)
    preview_mask = Image.new("L", (700, 300), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 700, 300), 42, fill=255)
    preview.putalpha(preview_mask)

    preview_x = 450
    preview_y = 115
    bg.paste(preview, (preview_x, preview_y), preview)

    # golden border
    border = Image.new("RGBA", (708, 308), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 708, 308), 44, outline=(220, 185, 120), width=4)
    bg.paste(border, (preview_x - 4, preview_y - 4), border)

    # subtle top text
    small_top_font = load_font(20)
    draw.text((800, 100), "NOW PLAYING • PREMIUM PLAYER", fill=(170, 170, 170), font=small_top_font, anchor="mm")

    # 4k text
    tag_font = load_font(42)
    draw.text((470, 375), "4k", fill="white", font=tag_font)

    # =========================
    # FONTS
    # =========================
    now_font = load_font(44)
    title_font = load_font(68)
    time_font = load_font(30)
    btn_font = load_font(74)
    pause_font = load_font(86)

    # =========================
    # TEXT
    # =========================
    clean_title = trim(title.upper(), title_font, 680)

    draw.text((800, 465), "Now Playing", fill=(195, 195, 195), font=now_font, anchor="mm")
    draw.text((800, 555), clean_title, fill="white", font=title_font, anchor="mm")

    meta_font = load_font(24)
    draw.text((800, 605), f"{views}", fill=(160, 160, 160), font=meta_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 475
    bar_x2 = 1125
    bar_y = 655

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), 10, fill=(95, 95, 95))

    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 10), 10, fill=(220, 185, 120))
    draw.ellipse((prog_x - 12, bar_y - 8, prog_x + 12, bar_y + 16), fill="white")

    draw.text((475, 700), "1:24", fill=(185, 185, 185), font=time_font)
    draw.text((1060, 700), duration, fill=(185, 185, 185), font=time_font)

    # =========================
    # BUTTONS
    # =========================
    # Prev / Next icons safe
    draw.text((620, 770), "<<", fill="white", font=btn_font, anchor="mm")

    # Pause button bg
    pause_bg = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    pbd = ImageDraw.Draw(pause_bg)
    pbd.rounded_rectangle((0, 0, 150, 150), 45, fill=(55, 55, 60, 255))
    bg.paste(pause_bg, (725, 695), pause_bg)

    draw.text((800, 770), "II", fill="white", font=pause_font, anchor="mm")
    draw.text((980, 770), ">>", fill="white", font=btn_font, anchor="mm")

    # Save
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    # cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
