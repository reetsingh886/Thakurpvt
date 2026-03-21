import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from youtubesearchpython import VideosSearch

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return url


def trim(text, max_len=35):
    return text if len(text) <= max_len else text[:max_len] + "..."


async def get_thumb(videoid: str, botname: str = "@YourBot"):
    videoid = extract_video_id(videoid)
    path = f"{CACHE_DIR}/{videoid}.png"

    if os.path.exists(path):
        return path

    # ===== FETCH DATA =====
    try:
        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = (await search.next())["result"][0]

        title = data.get("title", "Unknown Song")
        duration = data.get("duration", "3:00")
        views = data.get("viewCount", {}).get("short", "Unknown")

    except:
        title = "Unknown Song"
        duration = "3:00"
        views = "Unknown"

    title = re.sub(r"\W+", " ", title).title()
    title = trim(title, 30)

    # ===== THUMB =====
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return thumb_url
    except:
        return thumb_url

    try:
        base = Image.open(thumb_path).resize((1280, 720)).convert("RGB")
    except:
        return thumb_url

    # ===== BACKGROUND =====
    bg = base.filter(ImageFilter.GaussianBlur(25))
    overlay = Image.new("RGBA", (1280, 720), (20, 10, 0, 200))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(bg)

    # ===== LEFT IMAGE =====
    thumb = base.resize((500, 300))
    mask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 500, 300), 30, fill=255)

    x, y = 80, 200
    bg.paste(thumb, (x, y), mask)

    draw.rounded_rectangle((x-5, y-5, x+505, y+305), 30, outline="#ff7a1a", width=4)

    # ===== FONTS =====
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 48)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 26)
    except:
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # ===== TEXT =====
    tx = 650

    draw.rounded_rectangle((tx, 120, tx+260, 170), 25, fill="#ff7a1a")
    draw.text((tx+130, 145), "NOW PLAYING", fill="white", font=small_font, anchor="mm")

    draw.text((tx, 220), title, fill="white", font=title_font)
    draw.line((tx, 280, tx+500, 280), fill="#ff7a1a", width=3)

    draw.text((tx, 310), f"Duration: {duration}", fill="white", font=small_font)
    draw.text((tx, 350), f"Views: {views}", fill="#ff9a4d", font=small_font)
    draw.text((tx, 390), f"Player: {botname}", fill="#ff9a4d", font=small_font)

    # ===== PROGRESS =====
    bar_x, bar_y = tx, 470
    draw.line((bar_x, bar_y, bar_x+500, bar_y), fill="#555", width=6)
    draw.line((bar_x, bar_y, bar_x+200, bar_y), fill="#ff7a1a", width=6)
    draw.ellipse((bar_x+190, bar_y-8, bar_x+210, bar_y+8), fill="white")

    draw.text((bar_x, bar_y+15), "0:00", fill="white", font=small_font)
    draw.text((bar_x+430, bar_y+15), duration, fill="white", font=small_font)

    draw.text((900, 650), "Powered by You", fill="#ff7a1a", font=small_font)

    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
