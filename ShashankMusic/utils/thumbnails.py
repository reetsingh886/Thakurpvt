import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from ShashankMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return url


def trim(text, font, max_w):
    try:
        while font.getbbox(text)[2] > max_w:
            text = text[:-1]
        return text + "..."
    except:
        return text


async def get_thumb(videoid: str, title: str, player_username=None):
    videoid = extract_video_id(videoid)

    if player_username is None:
        player_username = getattr(app, "username", "MusicBot")

    path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(path):
        return path

    # 🎵 CLEAN TITLE (NO ERROR)
    title = re.sub(r"\W+", " ", title).title()
    duration = "3:00"

    # 🖼 THUMB (ALWAYS WORK)
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

    # 🖤 BLACK BG
    bg = Image.new("RGB", (1280, 720), (0, 0, 0))
    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB
    try:
        thumb = Image.open(thumb_path).resize((420, 420)).convert("RGBA")
        thumb = ImageEnhance.Contrast(thumb).enhance(1.15)
        thumb = ImageEnhance.Brightness(thumb).enhance(1.05)
    except:
        thumb = Image.new("RGBA", (420, 420), (40, 40, 40, 255))

    mask = Image.new("L", (420, 420), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 420, 420), 40, fill=255)
    thumb.putalpha(mask)

    # 🔥 SHADOW
    shadow = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, 460, 460), 50, fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(60))
    bg.paste(shadow, (100, 130), shadow)

    # 🔥 BORDER
    border = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 460, 460), 50, outline=(255, 120, 40), width=4)

    bg.paste(border, (100, 130), border)
    bg.paste(thumb, (120, 150), thumb)

    # 🅵🅾🅽🆃
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 44)
        meta_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 30)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 26)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    # 🔴 BADGE
    draw.rounded_rectangle((600, 140, 830, 195), 25, fill=(255, 120, 40))
    draw.text((635, 152), "NOW PLAYING", fill="white", font=small_font)

    # 🎵 TITLE
    title = trim(title, title_font, 550)
    draw.text((600, 240), title, fill="white", font=title_font)

    draw.line((600, 300, 1000, 300), fill=(255, 120, 40), width=3)

    # 📊 META
    draw.text((600, 330), f"Duration: {duration}", fill="white", font=meta_font)
    draw.text((600, 370), f"Player: @{player_username}", fill=(255, 140, 90), font=meta_font)

    # 🎚 PROGRESS BAR
    bar_x, bar_y = 600, 480
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+10), 6, fill=(70,70,70))
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w//2, bar_y+10), 6, fill=(255,120,40))
    draw.ellipse((bar_x+bar_w//2-8, bar_y-5, bar_x+bar_w//2+8, bar_y+15), fill="white")

    draw.text((600, 510), "00:00", fill="white", font=small_font)
    draw.text((1080, 510), duration, fill="white", font=small_font)

    # 🔥 FOOTER
    draw.text((820, 660), "Powered by Mr Thakur", fill=(255, 120, 40), font=small_font)

    # CLEANUP
    try:
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
