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


# ✅ TEXT CLEANER (NO UNICODE ERROR)
def clean_text(text):
    return text.encode("ascii", "ignore").decode()


async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None

    # 🎧 FETCH DATA
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = clean_text(result.get("title", "Unknown"))
        duration = result.get("duration", "3:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = clean_text(result.get("viewCount", {}).get("short", "Unknown"))
        channel = clean_text(result.get("channel", {}).get("name", "Unknown"))

    except Exception as e:
        print(f"[YT ERROR] {e}")
        title = "Shashank Music"
        duration = "3:00"
        views = "0"
        channel = "Shashank"
        thumburl = None

    # 🌐 DOWNLOAD IMAGE
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

    # 🖼️ BACKGROUND
    if thumb_path and thumb_path.exists():
        bg = Image.open(thumb_path).resize((W, H)).convert("RGB")
    else:
        bg = Image.new("RGB", (W, H), (30, 20, 40))

    bg = bg.filter(ImageFilter.GaussianBlur(25))
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 🎵 ALBUM CIRCLE
    size = 300
    album = bg.crop((0, 0, size, size)).resize((size, size))

    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, size, size), fill=255)
    album.putalpha(mask)

    canvas.paste(album, (80, 200), album)

    # 🔤 SAFE FONT (NO ERROR)
    title_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

    # 🎶 TITLE
    draw.text((450, 200), title[:40], fill="white", font=title_font)

    # 📺 CHANNEL + VIEWS
    draw.text((450, 260), f"{channel}  |  {views}", fill="lightgray", font=small_font)

    # ⏱️ PROGRESS BAR
    bar_x1, bar_y = 450, 330
    bar_x2 = 1000

    draw.line((bar_x1, bar_y, bar_x2, bar_y), fill="gray", width=6)
    draw.line((bar_x1, bar_y, bar_x1 + 300, bar_y), fill="red", width=6)

    draw.ellipse((bar_x1 + 290, bar_y - 8, bar_x1 + 310, bar_y + 8), fill="red")

    # ⌛ TIME
    draw.text((450, 360), "0:00", fill="white", font=small_font)
    draw.text((950, 360), duration, fill="white", font=small_font)

    # 🎮 CONTROLS (NO EMOJI = NO ERROR)
    draw.text((450, 420), "<<   PLAY   >>", fill="white", font=title_font)

    # 💾 SAVE
    out = CACHE_DIR / f"{videoid}.png"
    canvas.save(out)

    if thumb_path and thumb_path.exists():
        os.remove(thumb_path)

    return str(out)
