import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from py_yt import VideosSearch

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

async def get_thumb(videoid: str) -> str:
    path = f"{CACHE_DIR}/{videoid}_final.png"
    if os.path.exists(path):
        return path

    # FETCH DATA
    try:
        data = (await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next())["result"][0]
        title = re.sub(r"\W+", " ", data["title"]).strip().title()
        thumb_url = data["thumbnails"][0]["url"]
    except:
        title = "Unknown Song"
        thumb_url = "https://i.imgur.com/4L0rZ7P.jpg"

    # DOWNLOAD THUMB
    temp = f"{CACHE_DIR}/{videoid}.jpg"
    async with aiohttp.ClientSession() as session:
        async with session.get(thumb_url) as r:
            if r.status == 200:
                async with aiofiles.open(temp, "wb") as f:
                    await f.write(await r.read())

    # BASE BG
    base = Image.open(temp).resize((1280, 720)).convert("RGB")
    bg = base.filter(ImageFilter.GaussianBlur(20))
    bg = ImageEnhance.Brightness(bg).enhance(0.4)

    draw = ImageDraw.Draw(bg)

    # PANEL
    PANEL_W, PANEL_H = 820, 560
    PANEL_X = (1280 - PANEL_W)//2
    PANEL_Y = 80

    panel = Image.new("RGBA", (PANEL_W, PANEL_H), (25,25,25,240))
    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,PANEL_W,PANEL_H), 40, fill=255)
    bg.paste(panel, (PANEL_X, PANEL_Y), mask)

    # THUMB TOP
    TH_W, TH_H = 700, 320
    TH_X = PANEL_X + (PANEL_W - TH_W)//2
    TH_Y = PANEL_Y + 30

    thumb = base.resize((TH_W, TH_H))
    tmask = Image.new("L", (TH_W, TH_H), 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0,0,TH_W,TH_H), 30, fill=255)
    bg.paste(thumb, (TH_X, TH_Y), tmask)

    # GOLD BORDER
    draw.rounded_rectangle(
        (TH_X, TH_Y, TH_X+TH_W, TH_Y+TH_H),
        radius=30,
        outline="#d4af37",
        width=4
    )

    # FONTS
    try:
        font_big = ImageFont.truetype("ShashankMusic/assets/assets/font2.ttf", 60)
        font_small = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 28)
        font_time = ImageFont.truetype("ShashankMusic/assets/assets/font.ttf", 22)
    except:
        font_big = font_small = font_time = ImageFont.load_default()

    # NOW PLAYING
    draw.text(
        (PANEL_X + PANEL_W//2 - 90, TH_Y + TH_H + 20),
        "Now Playing",
        fill="#aaaaaa",
        font=font_small
    )

    # TITLE
    text = title.upper()
    if len(text) > 25:
        text = text[:25] + "..."

    tw = font_big.getlength(text)
    draw.text(
        (PANEL_X + (PANEL_W - tw)//2, TH_Y + TH_H + 70),
        text,
        fill="white",
        font=font_big
    )

    # PROGRESS BAR
    BAR_Y = TH_Y + TH_H + 150
    BAR_X = PANEL_X + 80
    BAR_W = PANEL_W - 160

    progress = BAR_W // 3

    draw.line((BAR_X, BAR_Y, BAR_X+BAR_W, BAR_Y), fill="#555", width=6)
    draw.line((BAR_X, BAR_Y, BAR_X+progress, BAR_Y), fill="#d4af37", width=6)

    draw.ellipse(
        (BAR_X+progress-8, BAR_Y-8, BAR_X+progress+8, BAR_Y+8),
        fill="white"
    )

    # TIME
    draw.text((BAR_X, BAR_Y+15), "1:24", fill="white", font=font_time)
    draw.text((BAR_X+BAR_W-60, BAR_Y+15), "3:45", fill="white", font=font_time)

    # CONTROLS (FIXED - NO UNICODE ERROR)
    controls = "<<   ||   >>"
    cw = font_big.getlength(controls)

    draw.text(
        (PANEL_X + (PANEL_W - cw)//2, BAR_Y + 60),
        controls,
        fill="white",
        font=font_big
    )

    # SAVE
    bg.save(path)

    try:
        os.remove(temp)
    except:
        pass

    return path
