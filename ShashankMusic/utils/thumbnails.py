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


def clean_title(text):
    text = str(text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\[.*?\]|\(.*?\)", "", text)
    text = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s\-]", "", text)
    return text.strip().title()


def trim(text, font, max_w):
    try:
        while font.getbbox(text)[2] > max_w:
            text = text[:-1]
        return text + "..."
    except:
        return text


async def get_thumb(videoid: str, title=None, player_username=None):
    videoid = extract_video_id(videoid)

    if player_username is None:
        player_username = getattr(app, "username", "MusicBot")

    # 🔥 SUPER FIX TITLE (NO FAIL)
    if not title or len(str(title)) < 3:
        title = "Music Playing"

    title = clean_title(title)

    if len(title) < 3:
        title = "Unknown Track"

    if len(title) > 40:
        title = title[:40] + "..."

    path = f"{CACHE_DIR}/{videoid}_silver.png"
    if os.path.exists(path):
        return path

    # 🖼 THUMB
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

    # 🪙 SILVER BG
    bg = Image.new("RGB", (1280, 720), (40, 40, 40))
    draw = ImageDraw.Draw(bg)

    for i in range(720):
        shade = int(40 + (i / 720) * 90)
        draw.line((0, i, 1280, i), fill=(shade, shade, shade))

    # glow
    glow = Image.new("RGB", (1280, 720), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((200, 0, 1100, 720), fill=(220, 220, 220))
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    bg = Image.blend(bg, glow, 0.25)

    draw = ImageDraw.Draw(bg)

    # 🖼 THUMB
    try:
        thumb = Image.open(thumb_path).resize((420, 420)).convert("RGBA")
        thumb = ImageEnhance.Contrast(thumb).enhance(1.2)
    except:
        thumb = Image.new("RGBA", (420, 420), (60, 60, 60, 255))

    mask = Image.new("L", (420, 420), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 420, 420), 40, fill=255)
    thumb.putalpha(mask)

    # shadow
    shadow = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, 460, 460), 50, fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(70))
    bg.paste(shadow, (100, 130), shadow)

    # border
    border = Image.new("RGBA", (460, 460), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 460, 460), 50, outline=(230, 230, 230), width=4)

    bg.paste(border, (100, 130), border)
    bg.paste(thumb, (120, 150), thumb)

    # fonts
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 44)
        meta_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 30)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 26)
    except:
        title_font = meta_font = small_font = ImageFont.load_default()

    # badge
    draw.rounded_rectangle((600, 140, 830, 195), 25, fill=(200, 200, 200))
    draw.text((635, 152), "NOW PLAYING", fill="black", font=small_font)

    # title
    title = trim(title, title_font, 550)
    draw.text((600, 240), title, fill="white", font=title_font)

    draw.line((600, 300, 1000, 300), fill=(220, 220, 220), width=3)

    # meta
    draw.text((600, 330), "Duration: 3:00", fill="white", font=meta_font)
    draw.text((600, 370), f"Player: @{player_username}", fill=(220, 220, 220), font=meta_font)

    # progress
    bar_x, bar_y = 600, 480
    bar_w = 500

    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+10), 6, fill=(90,90,90))
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w//2, bar_y+10), 6, fill=(220,220,220))
    draw.ellipse((bar_x+bar_w//2-8, bar_y-5, bar_x+bar_w//2+8, bar_y+15), fill="white")

    draw.text((600, 510), "00:00", fill="white", font=small_font)
    draw.text((1080, 510), "3:00", fill="white", font=small_font)

    # footer
    draw.text((820, 660), "Powered by Mr Thakur", fill=(220, 220, 220), font=small_font)

    try:
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
