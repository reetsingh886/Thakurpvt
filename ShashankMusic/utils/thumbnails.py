import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def changeImageSize(maxWidth, maxHeight, image):
    return image.resize((maxWidth, maxHeight))


def clean(text):
    return unidecode(str(text))


def trim(text, font, max_w):
    if font.getlength(text) <= max_w:
        return text
    while font.getlength(text + "...") > max_w:
        text = text[:-1]
    return text + "..."


async def get_thumb(videoid):

    final_path = f"{CACHE_DIR}/{videoid}_v4.png"
    if os.path.exists(final_path):
        return final_path

    # 🎯 FETCH DATA
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]

        title = clean(data.get("title", "Song"))
        title = re.sub(r"\W+", " ", title).title()

        duration = data.get("duration", "3:00")
        views = data.get("viewCount", {}).get("short", "0")
        channel = data.get("channel", {}).get("name", "Channel")

        thumbnail = data["thumbnails"][0]["url"].split("?")[0]

    except:
        title, duration, views, channel = "Shashank Music", "3:00", "0", "Channel"
        thumbnail = YOUTUBE_IMG_URL

    # 🎯 DOWNLOAD
    thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as r:
            if r.status == 200:
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await r.read())

    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")

    # 🔥 BACKGROUND
    bg = base.filter(ImageFilter.GaussianBlur(25))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)

    draw = ImageDraw.Draw(bg)

    # 🎯 LEFT IMAGE
    thumb = base.resize((480, 300))
    mask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 480, 300), 30, fill=255)
    bg.paste(thumb, (120, 200), mask)

    # 🔥 BIG FONTS
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font3.ttf", 70)
        meta_font = ImageFont.truetype("ShashankMusic/assets/font2.ttf", 36)
        small_font = ImageFont.truetype("ShashankMusic/assets/font2.ttf", 30)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    x = 650

    title = trim(title, title_font, 520)

    # 🔥 SHADOW TITLE (LOOK PREMIUM)
    draw.text((x+3, 223), title, fill="black", font=title_font)
    draw.text((x, 220), title, fill="white", font=title_font)

    # 🎯 META BIG
    draw.text((x, 320), f"Duration: {duration}", fill=(255,140,0), font=meta_font)
    draw.text((x, 370), f"Views: {views}", fill=(255,140,0), font=meta_font)
    draw.text((x, 420), f"Channel: {channel}", fill=(255,140,0), font=meta_font)

    # 🎯 NOW PLAYING
    draw.text((x, 170), "NOW PLAYING", fill=(255,140,0), font=small_font)

    # 🎯 PROGRESS BAR
    total = 460
    done = int(total * 0.5)
    bar_y = 520

    draw.line((x, bar_y, x + total, bar_y), fill=(120,120,120), width=6)
    draw.line((x, bar_y, x + done, bar_y), fill=(255,140,0), width=8)

    draw.ellipse((x + done - 9, bar_y - 9, x + done + 9, bar_y + 9), fill="white")

    draw.text((x, bar_y + 20), "0:00", fill="white", font=small_font)
    draw.text((x + total - 80, bar_y + 20), duration, fill="white", font=small_font)

    # 🎯 ICONS
    try:
        icons = Image.open("ShashankMusic/assets/play_icons.png").resize((420, 65))
        bg.paste(icons, (x, 570), icons)
    except:
        pass

    # CLEANUP
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(final_path)
    return final_path
