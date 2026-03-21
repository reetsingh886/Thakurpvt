import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from youtubesearchpython import VideosSearch

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def clean_title(title):
    title = re.sub(r"\W+", " ", str(title)).strip()
    return title.title()


def trim(text, font, max_w):
    try:
        while font.getlength(text) > max_w:
            text = text[:-1]
        return text
    except:
        return text


async def get_thumb(videoid: str):

    videoid = videoid.split("v=")[-1].strip()
    path = f"{CACHE_DIR}/{videoid}_final.png"

    if os.path.exists(path):
        return path

    # 🔒 SAFE FETCH
    try:
        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        res = await search.next()

        if not res or "result" not in res or not res["result"]:
            raise Exception("No result")

        data = res["result"][0]

        title = clean_title(data.get("title") or "Unknown Song")
        thumb_url = (data.get("thumbnails") or [{}])[0].get("url")
        duration = data.get("duration") or "3:00"
        views = (data.get("viewCount") or {}).get("short") or "Unknown"

        if not thumb_url:
            raise Exception("No thumbnail")

    except:
        return None  # ❗ important (no crash)

    # ⬇️ DOWNLOAD
    thumb_path = f"{CACHE_DIR}/{videoid}_raw.png"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
                else:
                    return None
    except:
        return None

    # 🎨 BG
    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    bg = base.filter(ImageFilter.GaussianBlur(25))
    bg = ImageEnhance.Brightness(bg).enhance(0.6)

    draw = ImageDraw.Draw(bg)

    # 🧊 PANEL
    panel = Image.new("RGBA", (760, 460), (255, 255, 255, 150))
    mask = Image.new("L", (760, 460), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 760, 460), 40, fill=255)
    bg.paste(panel, (260, 120), mask)

    # 🖼 THUMB
    thumb = base.resize((500, 240))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 500, 240), 25, fill=255)
    bg.paste(thumb, (390, 140), tmask)

    # 🔤 FONT
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 36)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 22)
    except:
        title_font = small_font = ImageFont.load_default()

    # 🎵 TITLE
    title = trim(title, title_font, 500)
    draw.text((400, 400), title, fill="black", font=title_font)

    # 📊 META
    draw.text((400, 440), f"YouTube | {views}", fill="black", font=small_font)

    # 🎚 BAR
    bar_x, bar_y = 400, 480
    draw.line((bar_x, bar_y, bar_x+260, bar_y), fill="red", width=6)
    draw.line((bar_x+260, bar_y, bar_x+420, bar_y), fill="gray", width=5)
    draw.ellipse((bar_x+250, bar_y-8, bar_x+270, bar_y+8), fill="red")

    draw.text((400, 500), "00:00", fill="black", font=small_font)
    draw.text((800, 500), duration, fill="black", font=small_font)

    # 🧹 CLEAN
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
