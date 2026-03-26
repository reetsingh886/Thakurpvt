import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


def trim(text, font, max_w):
    try:
        while font.getbbox(text)[2] > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Download YouTube thumbnail
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
    except:
        thumb_file = None

    # Background
    bg = Image.new("RGB", (1280, 720), (18, 10, 8))

    glow = Image.new("RGB", (1280, 720), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((180, 40, 1100, 700), fill=(255, 90, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    bg = Image.blend(bg, glow, 0.45)

    draw = ImageDraw.Draw(bg)

    # Left Thumbnail (same reference style)
    try:
        thumb = Image.open(thumb_file).convert("RGBA")
        thumb = thumb.resize((430, 430))
    except:
        thumb = Image.new("RGBA", (430, 430), (35, 35, 35, 255))

    mask = Image.new("L", (430, 430), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 430, 430), 55, fill=255)
    thumb.putalpha(mask)

    # Shadow
    shadow = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, 460, 460), 60, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    bg.paste(shadow, (85, 135), shadow)

    # Border glow
    border = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 450, 450), 60, outline=(255, 90, 70), width=7)

    glow_border = border.filter(ImageFilter.GaussianBlur(18))
    bg.paste(glow_border, (95, 145), glow_border)
    bg.paste(border, (95, 145), border)
    bg.paste(thumb, (105, 155), thumb)

    # Fonts
    try:
        badge_font = ImageFont.truetype(FONT, 30)
        title_font = ImageFont.truetype(FONT, 56)
        meta_font = ImageFont.truetype(FONT, 42)
        small_font = ImageFont.truetype(FONT, 32)
    except:
        badge_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # NOW PLAYING badge
    draw.rounded_rectangle((610, 150, 930, 220), 35, fill=(255, 90, 70))
    draw.text((685, 168), "NOW PLAYING", fill="black", font=badge_font)

    # Title
    title = trim(title, title_font, 540)
    draw.text((610, 260), title, fill="white", font=title_font)

    # Underline
    draw.line((610, 345, 1120, 345), fill=(255, 90, 70), width=5)

    # Meta section
    draw.text((610, 395), "Duration:", fill="white", font=meta_font)
    draw.text((855, 395), duration, fill=(255, 110, 90), font=meta_font)

    draw.text((610, 480), "Views:", fill="white", font=meta_font)
    draw.text((780, 480), views, fill=(255, 110, 90), font=meta_font)

    # Progress bar
    bar_x = 610
    bar_y = 575
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + 12), 8, fill=(190, 190, 190))
    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w // 2, bar_y + 12), 8, fill=(255, 90, 70))
    draw.ellipse((bar_x + bar_w // 2 - 12, bar_y - 8, bar_x + bar_w // 2 + 12, bar_y + 16), fill="white")

    draw.text((610, 605), "00:00", fill="white", font=small_font)
    draw.text((1045, 605), duration, fill="white", font=small_font)

    bg.save(path)
    return path
