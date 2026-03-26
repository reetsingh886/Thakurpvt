import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


# =========================
# SAFE TEXT
# =========================
def safe_text(text, default="Unknown Song"):
    if text is None:
        return default
    text = str(text).strip()
    return text if text else default


def trim(text, font, max_w):
    text = safe_text(text)
    try:
        while font.getbbox(text)[2] > max_w and len(text) > 3:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


# =========================
# FETCH TITLE FROM YOUTUBE
# =========================
async def fetch_youtube_title(videoid: str):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={videoid}&format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title")
                    if title:
                        return title.strip()
    except:
        pass
    return None


# =========================
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="45 views"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "45 views")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Fresh generate
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # Auto fix title
    if title.lower() in ["unknown song", "unknown", "none", ""]:
        yt_title = await fetch_youtube_title(videoid)
        if yt_title:
            title = yt_title

    # Download thumbnail
    thumb_url = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
                else:
                    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
                    async with s.get(thumb_url) as r2:
                        if r2.status == 200:
                            async with aiofiles.open(thumb_file, "wb") as f:
                                await f.write(await r2.read())
                        else:
                            thumb_file = None
    except:
        thumb_file = None

    # Load original
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1600, 900), (80, 60, 90))

    original = original.resize((1600, 900))

    # =========================
    # BACKGROUND
    # =========================
    bg = original.copy().filter(ImageFilter.GaussianBlur(22))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    bg = bg.convert("RGBA")

    # Purple warm overlay
    overlay = Image.new("RGBA", (1600, 900), (120, 70, 130, 70))
    bg = Image.alpha_composite(bg, overlay)

    draw = ImageDraw.Draw(bg)

    # =========================
    # GLASS CARD
    # =========================
    card_x, card_y = 320, 140
    card_w, card_h = 960, 620

    # shadow
    shadow = Image.new("RGBA", (card_w + 60, card_h + 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 60, card_h + 60), 55, fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    bg.paste(shadow, (card_x - 30, card_y + 20), shadow)

    # glass card
    glass = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 185))
    glass_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(glass_mask).rounded_rectangle((0, 0, card_w, card_h), 45, fill=255)
    bg.paste(glass, (card_x, card_y), glass_mask)

    # =========================
    # TOP IMAGE
    # =========================
    preview = original.convert("RGBA").resize((640, 280))
    preview_mask = Image.new("L", (640, 280), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 640, 280), 28, fill=255)
    preview.putalpha(preview_mask)

    preview_x = 480
    preview_y = 180
    bg.paste(preview, (preview_x, preview_y), preview)

    # =========================
    # FONTS
    # =========================
    try:
        title_big = ImageFont.truetype(FONT, 74)
        song_font = ImageFont.truetype(FONT, 46)
        small_font = ImageFont.truetype(FONT, 26)
        time_font = ImageFont.truetype(FONT, 24)
        icon_font = ImageFont.truetype(FONT, 54)
    except:
        title_big = ImageFont.load_default()
        song_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        icon_font = ImageFont.load_default()

    # =========================
    # TEXT ON IMAGE
    # =========================
    image_draw = ImageDraw.Draw(preview)
    big_title = trim(title.upper(), title_big, 520)

    image_draw.text((320, 95), big_title, fill="black", font=title_big, anchor="mm")
    image_draw.text((320, 165), "ANUV JAIN", fill="black", font=song_font, anchor="mm")
    bg.paste(preview, (preview_x, preview_y), preview)

    # =========================
    # SONG INFO
    # =========================
    title = trim(title, song_font, 560)
    draw.text((500, 490), title, fill=(20, 20, 20), font=song_font)

    draw.text((500, 545), f"YouTube | {views}", fill=(35, 35, 35), font=small_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 500
    bar_x2 = 1080
    bar_y = 605

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 8), 8, fill=(120, 120, 120))
    progress = 0.58
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 8), 8, fill=(230, 0, 0))
    draw.ellipse((prog_x - 9, bar_y - 7, prog_x + 9, bar_y + 11), fill=(230, 0, 0))

    draw.text((500, 635), "00:00", fill="black", font=time_font)
    draw.text((1035, 635), duration, fill="black", font=time_font)

    # =========================
    # CONTROLS
    # =========================
    draw.text((585, 700), "⌁", fill="black", font=icon_font, anchor="mm")
    draw.text((680, 700), "⏮", fill="black", font=icon_font, anchor="mm")
    draw.text((800, 700), "⏯", fill="black", font=icon_font, anchor="mm")
    draw.text((920, 700), "⏭", fill="black", font=icon_font, anchor="mm")
    draw.text((1030, 700), "▢", fill="black", font=icon_font, anchor="mm")

    # Save
    bg = bg.convert("RGB")
    bg.save(path, quality=96)

    # Cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
