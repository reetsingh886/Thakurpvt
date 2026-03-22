import os
import random
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from py_yt import VideosSearch
from ShashankMusic import app
import math

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760

FONT_REGULAR_PATH = "ShashankMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShashankMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShashankMusic/assets/ShashankBots.jpg"


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines[:2]


def random_gradient():
    colors = [
        [(15, 12, 41), (48, 43, 99), (36, 36, 62)],
        [(10, 10, 10), (35, 35, 40), (20, 20, 25)],
        [(26, 26, 46), (56, 56, 86), (40, 40, 60)],
        [(20, 25, 35), (45, 50, 70), (30, 35, 50)],
        [(12, 17, 30), (38, 43, 65), (25, 30, 45)],
    ]
    return random.choice(colors)


def apply_gradient(canvas, colors):
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(CANVAS_H):
        progress = y / CANVAS_H
        
        if progress < 0.4:
            t = progress / 0.4
            r = int(colors[0][0] * (1-t) + colors[1][0] * t)
            g = int(colors[0][1] * (1-t) + colors[1][1] * t)
            b = int(colors[0][2] * (1-t) + colors[1][2] * t)
        else:
            t = (progress - 0.4) / 0.6
            r = int(colors[1][0] * (1-t) + colors[2][0] * t)
            g = int(colors[1][1] * (1-t) + colors[2][1] * t)
            b = int(colors[1][2] * (1-t) + colors[2][2] * t)
        
        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, 255))
    
    return Image.alpha_composite(canvas, overlay)


def create_shape_mask(size):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)
    return mask


async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path if thumb_path else DEFAULT_THUMB).convert("RGBA")

    except:
        base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
        title = "ShashankMusic"
        duration = "Unknown"
        views = "Unknown Views"
        channel = "ShashankBots"

    try:
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
        canvas = apply_gradient(canvas, random_gradient())

        art_size = 450
        art_x = 80
        art_y = (CANVAS_H - art_size) // 2

        mask = create_shape_mask(art_size)
        art = base_img.resize((art_size, art_size))
        art.putalpha(mask)

        canvas.paste(art, (art_x, art_y), art)

        draw = ImageDraw.Draw(canvas)

        # BRAND NAME
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        draw.text((40, 30), app.username, fill="white", font=brand_font)

        # NOW PLAYING
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 60)
        draw.text((600, 150), "NOW PLAYING", fill=(120, 180, 255), font=np_font)

        # TITLE
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        draw.text((600, 260), title[:40], fill="white", font=title_font)

        # META
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        draw.text((600, 350), f"Views: {views}", fill="white", font=meta_font)
        draw.text((600, 400), f"Duration: {duration}", fill="white", font=meta_font)
        draw.text((600, 450), f"Channel: {channel}", fill="white", font=meta_font)

        out = CACHE_DIR / f"{videoid}_final.png"
        canvas.save(out)

        if thumb_path and thumb_path.exists():
            os.remove(thumb_path)

        return str(out)

    except Exception as e:
        print(e)
        traceback.print_exc()
        return None
