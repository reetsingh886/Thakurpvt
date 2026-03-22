import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720


# ✅ SAFE TEXT (NO UNICODE ERROR)
def safe_text(text):
    try:
        return text.encode("ascii", "ignore").decode()
    except:
        return "Unknown"


def trim_to_width(text, font, max_w):
    ellipsis = "..."
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text), 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return text[:20]


async def get_thumb(videoid: str):

    cache_path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.exists(cache_path):
        return cache_path

    # 🎯 FETCH DATA
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]

        raw_title = data.get("title", "Song")
        title = safe_text(raw_title)

        views = safe_text(data.get("viewCount", {}).get("short", "0"))
        duration = safe_text(data.get("duration", "3:00"))

    except:
        title, views, duration = "Shashank Music", "0", "3:00"

    # 🎯 THUMB
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
    except:
        return YOUTUBE_IMG_URL

    base = Image.open(thumb_path).resize((CANVAS_W, CANVAS_H)).convert("RGBA")

    # 🔥 BACKGROUND
    bg = base.filter(ImageFilter.GaussianBlur(25))
    bg = ImageEnhance.Brightness(bg).enhance(0.5)

    draw = ImageDraw.Draw(bg)

    # 🎯 CARD
    card_w, card_h = 900, 520
    card_x = (CANVAS_W - card_w)//2
    card_y = 100

    card = Image.new("RGBA", (card_w, card_h), (25, 25, 30, 210))
    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 40, fill=255)
    bg.paste(card, (card_x, card_y), mask)

    # 🎯 IMAGE
    inner = base.resize((760, 300))
    imask = Image.new("L", inner.size, 0)
    ImageDraw.Draw(imask).rounded_rectangle((0, 0, 760, 300), 25, fill=255)
    bg.paste(inner, (card_x + 70, card_y + 40), imask)

    # 🔥 FONTS (SAFE)
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/assets/font2.ttf", 52)
        meta_font = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 28)
        time_font = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 24)
    except:
        title_font = meta_font = time_font = ImageFont.load_default()

    # 🎯 TITLE CENTER
    text = trim_to_width(title, title_font, 900)
    w = draw.textlength(text, font=title_font)
    draw.text(((CANVAS_W - w)//2, card_y + 360), text, fill="white", font=title_font)

    # 🎯 META
    meta = f"YouTube • {views}"
    w2 = draw.textlength(meta, font=meta_font)
    draw.text(((CANVAS_W - w2)//2, card_y + 420), meta, fill=(255,140,0), font=meta_font)

    # 🎯 BAR
    BAR_TOTAL = 500
    BAR_DONE = 250

    bar_x = (CANVAS_W - BAR_TOTAL)//2
    bar_y = card_y + 470

    draw.line([(bar_x, bar_y), (bar_x + BAR_TOTAL, bar_y)], fill=(120,120,120), width=6)
    draw.line([(bar_x, bar_y), (bar_x + BAR_DONE, bar_y)], fill=(255,140,0), width=8)

    draw.ellipse([
        (bar_x + BAR_DONE - 10, bar_y - 10),
        (bar_x + BAR_DONE + 10, bar_y + 10)
    ], fill="white")

    # 🎯 TIME
    draw.text((bar_x, bar_y + 20), "0:00", fill="white", font=time_font)
    draw.text((bar_x + BAR_TOTAL - 70, bar_y + 20), duration, fill="white", font=time_font)

    # 🎯 CONTROLS
    icons_path = "ShashankMusic/assets/assets/play_icons.png"
    if os.path.isfile(icons_path):
        ic = Image.open(icons_path).resize((300, 70)).convert("RGBA")
        bg.paste(ic, ((CANVAS_W - 300)//2, card_y + 510), ic)

    # 🎯 NOW PLAYING
    draw.text((card_x + 40, card_y - 30), "NOW PLAYING", fill=(255,140,0), font=meta_font)

    # CLEANUP
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(cache_path)
    return cache_path
