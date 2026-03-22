
import os
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from ShashankMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def trim(text, font, max_w):
    try:
        while font.getbbox(text)[2] > max_w:
            text = text[:-1]
        return text + "..."
    except:
        return text


async def gen_thumb(videoid: str, title="Now Playing", duration="Live", views="Unknown", player_username=None):
    if player_username is None:
        player_username = getattr(app, "username", "MusicBot")

    path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(path):
        return path

    # ✅ DIRECT YT THUMB (NO LIBRARY)
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_path = f"{CACHE_DIR}/{videoid}.jpg"

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
    except:
        thumb_path = None

    # 🖤 CLEAN BG
    bg = Image.new("RGB", (1280, 720), (15, 10, 10))
    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB
    try:
        thumb = Image.open(thumb_path).resize((420, 420)).convert("RGBA")
    except:
        thumb = Image.new("RGBA", (420, 420), (40, 40, 40, 255))

    mask = Image.new("L", (420, 420), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 420, 420), 40, fill=255)
    thumb.putalpha(mask)

    # 🔴 BORDER
    border = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 460, 460), 50, outline=(255, 60, 60), width=8)

    bg.paste(border, (100, 130), border)
    bg.paste(thumb, (120, 150), thumb)

    # 🔤 FONT
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 44)
        meta_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 30)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 26)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    # 🔴 NOW PLAYING
    draw.rounded_rectangle((600, 140, 820, 190), 25, fill=(255, 60, 60))
    draw.text((630, 150), "NOW PLAYING", fill="white", font=small_font)

    # 🎵 TITLE
    title = trim(title, title_font, 550)
    draw.text((600, 230), title, fill="white", font=title_font)

    # underline
    draw.line((600, 290, 1000, 290), fill=(255, 60, 60), width=3)

    # 📊 META
    draw.text((600, 320), f"Duration: {duration}", fill="white", font=meta_font)
    draw.text((600, 360), f"Views: {views}", fill=(255, 80, 80), font=meta_font)
    draw.text((600, 400), f"Player: @{player_username}", fill=(255, 80, 80), font=meta_font)

    # 🎚 BAR
    bar_x, bar_y = 600, 470
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+12), 6, fill=(80,80,80))
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w//2, bar_y+12), 6, fill=(255,60,60))
    draw.ellipse((bar_x+bar_w//2-8, bar_y-4, bar_x+bar_w//2+8, bar_y+16), fill="white")

    draw.text((600, 510), "00:00", fill="white", font=small_font)
    draw.text((1080, 510), duration, fill="white", font=small_font)

    # ⚡ BRAND
    draw.text((900, 660), "Powered by Mr Thakur", fill=(180,180,180), font=small_font)

    try:
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path


# ✅ IMPORTANT FIX (GET_THUMB)
async def get_thumb(videoid, title="Now Playing", duration="Live", views="Unknown", player_username=None):
    return await gen_thumb(videoid, title, duration, views, player_username)
