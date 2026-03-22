import os
import aiohttp
import aiofiles
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

W, H = 1280, 720


def clean(text):
    return text.encode("ascii", "ignore").decode()


async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None

    try:
        results = VideosSearch(url, limit=1)
        data = (await results.next())["result"][0]

        title = clean(data.get("title", "Unknown"))
        duration = data.get("duration", "3:00")
        views = clean(data.get("viewCount", {}).get("short", "0"))
        channel = clean(data.get("channel", {}).get("name", "Unknown"))
        thumburl = data["thumbnails"][0]["url"].split("?")[0]

    except:
        title = "Shashank Music"
        duration = "3:00"
        views = "0"
        channel = "Shashank"
        thumburl = None

    # download image
    try:
        if thumburl:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as r:
                    if r.status == 200:
                        thumb_path = CACHE_DIR / f"{videoid}.jpg"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await r.read())
    except:
        thumb_path = None

    # background
    if thumb_path and thumb_path.exists():
        bg = Image.open(thumb_path).resize((W, H)).convert("RGB")
    else:
        bg = Image.new("RGB", (W, H), (20, 10, 5))

    bg = bg.filter(ImageFilter.GaussianBlur(30))

    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 🎨 ORANGE GRADIENT OVERLAY
    overlay = Image.new("RGBA", (W, H), (255, 120, 0, 80))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(canvas)

    # 📦 CARD (left side)
    card = Image.new("RGBA", (420, 420), (0, 0, 0, 180))
    card = card.filter(ImageFilter.GaussianBlur(2))
    canvas.paste(card, (80, 150), card)

    # 🖼️ album image
    if thumb_path and thumb_path.exists():
        album = Image.open(thumb_path).resize((400, 400))
    else:
        album = Image.new("RGB", (400, 400), (50, 50, 50))

    canvas.paste(album, (90, 160))

    # 🔤 font safe
    title_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

    # 🟠 NOW PLAYING TAG
    draw.rounded_rectangle((550, 120, 800, 170), radius=20, fill=(255, 120, 0))
    draw.text((580, 130), "NOW PLAYING", fill="white", font=small_font)

    # 🎶 TITLE
    draw.text((550, 200), title[:35], fill="white", font=title_font)

    # 📊 INFO
    draw.text((550, 260), f"Duration: {duration}", fill="white", font=small_font)
    draw.text((550, 300), f"Views: {views}", fill="orange", font=small_font)
    draw.text((550, 340), f"Player: @{channel}", fill="orange", font=small_font)

    # 🎚️ PROGRESS BAR
    bar_x1, bar_y = 550, 420
    bar_x2 = 1100

    draw.line((bar_x1, bar_y, bar_x2, bar_y), fill="gray", width=8)
    draw.line((bar_x1, bar_y, bar_x1 + 300, bar_y), fill="orange", width=8)

    draw.ellipse((bar_x1 + 290, bar_y - 10, bar_x1 + 310, bar_y + 10), fill="white")

    # ⏱️ TIME
    draw.text((550, 450), "00:00", fill="white", font=small_font)
    draw.text((1050, 450), duration, fill="white", font=small_font)

    # 👑 CREDIT
    draw.text((850, 650), "Powered by Shashank", fill="orange", font=small_font)

    # save
    out = CACHE_DIR / f"{videoid}.png"
    canvas.convert("RGB").save(out)

    if thumb_path and thumb_path.exists():
        os.remove(thumb_path)

    return str(out)
