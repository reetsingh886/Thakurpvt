import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch   # ✅ FIXED
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PANEL_W, PANEL_H = 763, 545
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 88
TRANSPARENCY = 170
INNER_OFFSET = 36

THUMB_W, THUMB_H = 542, 273
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET

TITLE_X = 377
META_X = 377
TITLE_Y = THUMB_Y + THUMB_H + 10
META_Y = TITLE_Y + 45

BAR_X, BAR_Y = 388, META_Y + 45
BAR_RED_LEN = 280
BAR_TOTAL_LEN = 480

ICONS_W, ICONS_H = 415, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 48

MAX_TITLE_WIDTH = 580


def clean(text):
    return re.sub(r"[^\x00-\x7F]+", "", text)


def trim_to_width(text, font, max_w):
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text), 0, -1):
        if font.getlength(text[:i] + "...") <= max_w:
            return text[:i] + "..."
    return text[:20]


async def get_thumb(videoid: str):

    cache_path = os.path.join(CACHE_DIR, f"{videoid}.png")
    if os.path.exists(cache_path):
        return cache_path

    # 🎯 FIXED YT DATA
    try:
        results = VideosSearch(videoid, limit=1)
        data = (await results.next())["result"][0]

        title = clean(data.get("title", "Unknown"))
        duration = data.get("duration", "3:00")
        views = data.get("viewCount", {}).get("short", "0")

    except:
        title = "Shashank Music"
        duration = "3:00"
        views = "0"

    # 🎯 FIXED THUMB (NO FAIL)
    thumbnail = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

    thumb_path = os.path.join(CACHE_DIR, f"{videoid}.jpg")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except:
        return YOUTUBE_IMG_URL

    # 🖼️ BACKGROUND
    base = Image.open(thumb_path).resize((1280, 720)).convert("RGBA")
    bg = base.filter(ImageFilter.GaussianBlur(20))
    bg = ImageEnhance.Brightness(bg).enhance(0.6)
    bg = ImageEnhance.Color(bg).enhance(1.3)

    # 🔥 PANEL
    panel = Image.new("RGBA", (PANEL_W, PANEL_H), (255, 255, 255, TRANSPARENCY))
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), 50, fill=255)
    bg.paste(panel, (PANEL_X, PANEL_Y), mask)

    # 🔥 GLOW BORDER
    glow = Image.new("RGBA", (PANEL_W+40, PANEL_H+40), (0,0,0,0))
    gdraw = ImageDraw.Draw(glow)
    for i in range(8):
        gdraw.rounded_rectangle(
            (i, i, PANEL_W+40-i, PANEL_H+40-i),
            radius=60,
            outline=(255,120,0,40-i*4)
        )
    bg.paste(glow, (PANEL_X-20, PANEL_Y-20), glow)

    draw = ImageDraw.Draw(bg)

    # 🖼️ THUMB SHADOW
    shadow = Image.new("RGBA", (THUMB_W+20, THUMB_H+20), (0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (0,0,THUMB_W+20,THUMB_H+20),
        25,
        fill=(0,0,0,120)
    )
    bg.paste(shadow, (THUMB_X-10, THUMB_Y-10), shadow)

    # 🖼️ THUMB
    thumb = base.resize((THUMB_W, THUMB_H))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0,0,THUMB_W,THUMB_H),20,fill=255)
    bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

    # 🔤 FONT SAFE
    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = small_font = ImageFont.load_default()

    # ✨ TITLE
    safe_title = trim_to_width(title, title_font, MAX_TITLE_WIDTH)
    draw.text((TITLE_X+1, TITLE_Y+1), safe_title, fill="white", font=title_font)
    draw.text((TITLE_X, TITLE_Y), safe_title, fill="black", font=title_font)

    # 📊 META
    draw.text((META_X, META_Y), f"YouTube | {views}", fill="black", font=small_font)

    # 🎚️ PROGRESS BAR
    draw.line([(BAR_X, BAR_Y), (BAR_X+BAR_TOTAL_LEN, BAR_Y)], fill=(180,180,180), width=6)
    draw.line([(BAR_X, BAR_Y), (BAR_X+BAR_RED_LEN, BAR_Y)], fill=(255,120,0), width=8)
    draw.ellipse(
        [(BAR_X+BAR_RED_LEN-8, BAR_Y-8),
         (BAR_X+BAR_RED_LEN+8, BAR_Y+8)],
        fill="white"
    )

    # ⏱️ TIME
    draw.text((BAR_X, BAR_Y+15), "00:00", fill="black", font=small_font)
    draw.text((BAR_X+BAR_TOTAL_LEN-60, BAR_Y+15), duration, fill="black", font=small_font)

    # 🧹 CLEANUP
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(cache_path)
    return cache_path
