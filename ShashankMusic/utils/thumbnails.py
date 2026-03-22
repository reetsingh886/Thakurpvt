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

async def get_thumb(videoid: str):

    cache_path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(cache_path):
        return cache_path

    # 🎯 FETCH DATA
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]
        title = re.sub(r"\W+", " ", data.get("title", "Song")).title()
        views = data.get("viewCount", {}).get("short", "0")
        duration = data.get("duration", "3:00")
    except:
        title, views, duration = "Shashank Music", "0", "3:00"

    duration_text = duration

    # 🎯 THUMB
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

    async with aiohttp.ClientSession() as session:
        async with session.get(thumb_url) as r:
            if r.status == 200:
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await r.read())

    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")

    # 🔥 BACKGROUND BLUR
    bg = base.filter(ImageFilter.GaussianBlur(25))
    bg = ImageEnhance.Brightness(bg).enhance(0.5)

    draw = ImageDraw.Draw(bg)

    # 🎯 CARD
    card = Image.new("RGBA", (900, 500), (20, 20, 25, 200))
    mask = Image.new("L", (900, 500), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 900, 500), 40, fill=255)
    bg.paste(card, (190, 110), mask)

    # 🎯 INNER IMAGE
    inner = base.resize((760, 300))
    imask = Image.new("L", inner.size, 0)
    ImageDraw.Draw(imask).rounded_rectangle((0, 0, 760, 300), 25, fill=255)
    bg.paste(inner, (260, 140), imask)

    # 🎯 FONTS
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/assets/font2.ttf", 52)
        meta_font = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 28)
        time_font = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 24)
    except:
        title_font = meta_font = time_font = ImageFont.load_default()

    # 🎯 TITLE CENTER
    text = title[:40]
    w = draw.textlength(text, font=title_font)
    draw.text(((CANVAS_W - w)//2, 460), text, fill="white", font=title_font)

    # 🎯 META
    meta = f"YouTube • {views}"
    w2 = draw.textlength(meta, font=meta_font)
    draw.text(((CANVAS_W - w2)//2, 520), meta, fill=(255,140,0), font=meta_font)

    # 🎯 BAR
    BAR_TOTAL = 500
    BAR_DONE = 250

    bar_x = (CANVAS_W - BAR_TOTAL)//2
    bar_y = 580

    draw.line([(bar_x, bar_y), (bar_x+BAR_TOTAL, bar_y)], fill=(100,100,100), width=6)
    draw.line([(bar_x, bar_y), (bar_x+BAR_DONE, bar_y)], fill=(255,140,0), width=8)

    draw.ellipse([
        (bar_x+BAR_DONE-10, bar_y-10),
        (bar_x+BAR_DONE+10, bar_y+10)
    ], fill="white")

    # 🎯 TIME
    draw.text((bar_x, bar_y+20), "0:00", fill="white", font=time_font)
    draw.text((bar_x+BAR_TOTAL-70, bar_y+20), duration_text, fill="white", font=time_font)

    # 🎯 CONTROLS
    icons_path = "ShashankMusic/assets/assets/play_icons.png"
    if os.path.exists(icons_path):
        ic = Image.open(icons_path).resize((300, 70)).convert("RGBA")
        bg.paste(ic, ((CANVAS_W-300)//2, 630), ic)

    # 🎯 NOW PLAYING
    draw.text((220, 120), "NOW PLAYING", fill=(255,140,0), font=meta_font)

    os.remove(thumb_path)
    bg.save(cache_path)

    return cache_path
