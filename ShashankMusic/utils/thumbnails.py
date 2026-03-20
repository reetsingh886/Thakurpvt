import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL
from ShashankMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def trim_to_width(text, font, max_w):
    try:
        while font.getlength(text) > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..."
    except:
        return text


async def get_thumb(videoid: str, player_username: str = None):
    if player_username is None:
        player_username = getattr(app, "username", "MusicBot")

    final_path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(final_path):
        return final_path

    # 🔍 FETCH DATA
    try:
        results = VideosSearch(videoid, limit=1)
        res = await results.next()
        data = res["result"][0]

        title = re.sub(r"\W+", " ", data.get("title", "Unknown")).title()
        thumb_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration", "Live")
        views = data.get("viewCount", {}).get("short", "0")

    except:
        title, thumb_url, duration, views = "Unknown", YOUTUBE_IMG_URL, "Live", "0"

    thumb_path = f"{CACHE_DIR}/{videoid}.png"

    # ⬇ DOWNLOAD
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
                else:
                    thumb_path = None
    except:
        thumb_path = None

    # 🎨 BACKGROUND (SHRUTI STYLE GLOW)
    base = Image.new("RGB", (1280, 720), (10, 10, 10))

    glow = Image.new("RGB", (1280, 720), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((200, 0, 1100, 720), fill=(255, 60, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(200))

    bg = Image.blend(base, glow, 0.45).convert("RGBA")

    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB
    try:
        thumb = Image.open(thumb_path).resize((520, 520)).convert("RGBA")
    except:
        thumb = Image.new("RGBA", (520, 520), (40, 40, 40, 255))

    # 🔷 HEXAGON MASK
    hex_points = [
        (260, 0), (520, 130), (520, 390),
        (260, 520), (0, 390), (0, 130)
    ]

    mask = Image.new("L", (520, 520), 0)
    ImageDraw.Draw(mask).polygon(hex_points, fill=255)

    hex_thumb = Image.new("RGBA", (520, 520))
    hex_thumb.paste(thumb, (0, 0), mask)

    # 🔥 SHADOW
    shadow = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.polygon([(x+40, y+40) for x, y in hex_points], fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    bg.paste(shadow, (60, 60), shadow)

    # 🔥 BORDER + GLOW
    border = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    border_hex = [(x+40, y+40) for x, y in hex_points]

    bd.polygon(border_hex, outline=(255, 40, 150), width=14)

    bg.paste(border.filter(ImageFilter.GaussianBlur(40)), (60, 60))
    bg.paste(border.filter(ImageFilter.GaussianBlur(20)), (60, 60))
    bg.paste(border, (60, 60))

    bg.paste(hex_thumb, (100, 100), hex_thumb)

    # 🅵🅾🅽🆃
    try:
        font_path = "ShashankMusic/assets/font.ttf"
        title_font = ImageFont.truetype(font_path, 44)
        meta_font = ImageFont.truetype(font_path, 28)
        small_font = ImageFont.truetype(font_path, 24)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    # 🔴 NOW PLAYING TAG
    draw.rounded_rectangle((700, 120, 950, 170), 20, fill=(255, 40, 150))
    draw.text((730, 130), "NOW PLAYING", fill="white", font=small_font)

    # 🎵 TITLE (GLOW TEXT)
    title = trim_to_width(title, title_font, 480)
    draw.text((703, 203), title, fill=(255, 40, 150), font=title_font)
    draw.text((700, 200), title, fill="white", font=title_font)

    # LINE
    draw.line((700, 260, 1100, 260), fill=(255, 40, 150), width=3)

    # 📊 META
    draw.text((700, 290), f"Duration: {duration}", fill="white", font=meta_font)
    draw.text((700, 330), f"Views: {views}", fill=(255, 120, 180), font=meta_font)
    draw.text((700, 370), f"Player: @{player_username}", fill=(255, 120, 180), font=meta_font)

    # 🎚 BAR
    bar_x, bar_y = 700, 450
    bar_w = 420

    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+12), 8, fill=(70,70,70))
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w//2, bar_y+12), 8, fill=(255,40,150))
    draw.ellipse((bar_x+bar_w//2-8, bar_y-4, bar_x+bar_w//2+8, bar_y+16), fill="white")

    # 🏷 BRAND
    draw.text((900, 670), "Powered by Mr Thakur", fill=(255, 40, 150), font=small_font)

    # 🧹 CLEAN
    try:
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
    except:
        pass

    bg.save(final_path)
    return final_path
