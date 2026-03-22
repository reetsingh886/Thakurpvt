import os
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

W, H = 1280, 720


async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None

    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown")
        duration = result.get("duration", "3:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown")
        channel = result.get("channel", {}).get("name", "Unknown")

    except:
        title = "Shashank Music"
        duration = "3:00"
        views = "0"
        channel = "Shashank"
        thumburl = None

    # download thumbnail
    try:
        if thumburl:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        thumb_path = CACHE_DIR / f"{videoid}.jpg"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
    except:
        thumb_path = None

    if thumb_path and thumb_path.exists():
        bg = Image.open(thumb_path).resize((W, H)).convert("RGB")
    else:
        bg = Image.new("RGB", (W, H), (40, 20, 40))

    # blur background
    bg = bg.filter(ImageFilter.GaussianBlur(25))

    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # album circle
    size = 300
    album = bg.crop((0, 0, size, size)).resize((size, size))

    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, size, size), fill=255)
    album.putalpha(mask)

    canvas.paste(album, (80, 200), album)

    # fonts (no error fallback)
    try:
        title_font = ImageFont.truetype("arial.ttf", 50)
        small_font = ImageFont.truetype("arial.ttf", 30)
    except:
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # title
    draw.text((450, 200), title[:40], fill="white", font=title_font)

    # channel + views
    draw.text((450, 270), f"{channel}  |  {views}", fill="lightgray", font=small_font)

    # progress bar
    bar_x1, bar_y = 450, 350
    bar_x2 = 1000

    draw.line((bar_x1, bar_y, bar_x2, bar_y), fill="gray", width=6)
    draw.line((bar_x1, bar_y, bar_x1 + 300, bar_y), fill="red", width=6)

    # circle
    draw.ellipse((bar_x1 + 290, bar_y - 10, bar_x1 + 310, bar_y + 10), fill="red")

    # time
    draw.text((450, 380), "0:00", fill="white", font=small_font)
    draw.text((950, 380), duration, fill="white", font=small_font)

    # controls (simple icons)
    draw.text((450, 450), "⏮   ⏯   ⏭", fill="white", font=title_font)

    out = CACHE_DIR / f"{videoid}.png"
    canvas.save(out)

    return str(out)
