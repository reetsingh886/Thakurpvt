import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
# MAIN FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Always fresh render
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # Try best quality first
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
        original = Image.new("RGB", (1280, 720), (30, 30, 30))

    # =========================
    # BACKGROUND
    # =========================
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(24))
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 160))
    bg = Image.alpha_composite(bg, dark)

    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((150, 50, 1130, 710), fill=(255, 180, 90, 35))
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # MAIN CARD (BIG)
    # =========================
    card_x, card_y = 255, 40
    card_w, card_h = 770, 635

    # Shadow
    shadow = Image.new("RGBA", (card_w + 50, card_h + 50), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 50, card_h + 50), 65, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(35))
    bg.paste(shadow, (card_x - 25, card_y - 8), shadow)

    # Card
    card = Image.new("RGBA", (card_w, card_h), (22, 22, 24, 240))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 55, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP PREVIEW (BIG LIKE REFERENCE)
    # =========================
    preview = original.convert("RGBA").resize((650, 245))
    preview_mask = Image.new("L", (650, 245), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 650, 245), 30, fill=255)
    preview.putalpha(preview_mask)

    # Golden border
    border = Image.new("RGBA", (658, 253), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 658, 253), 33, outline=(220, 185, 120), width=4)

    preview_x = 315
    preview_y = 78
    bg.paste(border, (preview_x - 4, preview_y - 4), border)
    bg.paste(preview, (preview_x, preview_y), preview)

    # =========================
    # FONTS
    # =========================
    try:
        now_font = ImageFont.truetype(FONT, 34)
        title_font = ImageFont.truetype(FONT, 54)
        time_font = ImageFont.truetype(FONT, 26)
        btn_font = ImageFont.truetype(FONT, 54)
    except:
        now_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        btn_font = ImageFont.load_default()

    # =========================
    # TEXT
    # =========================
    title = trim(title, title_font, 590)

    # Now Playing
    draw.text((640, 370), "Now Playing", fill=(210, 210, 210), font=now_font, anchor="mm")

    # Title (bigger and lower like reference)
    draw.text((640, 445), title, fill="white", font=title_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 365
    bar_x2 = 915
    bar_y = 525

    # base
    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 9), 10, fill=(110, 110, 110))

    # progress fill
    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 9), 10, fill=(225, 185, 120))

    # knob
    draw.ellipse((prog_x - 11, bar_y - 8, prog_x + 11, bar_y + 14), fill="white")

    # Time
    draw.text((365, 565), "1:24", fill=(175, 175, 175), font=time_font)
    draw.text((875, 565), duration, fill=(175, 175, 175), font=time_font)

    # =========================
    # BUTTONS (REFERENCE SPACING)
    # =========================
    # Back
    draw.text((510, 625), "<<", fill="white", font=btn_font, anchor="mm")

    # Pause button bg
    draw.rounded_rectangle((585, 580, 695, 685), 28, fill=(58, 58, 64))
    draw.text((640, 632), "II", fill="white", font=btn_font, anchor="mm")

    # Next
    draw.text((770, 625), ">>", fill="white", font=btn_font, anchor="mm")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=96)

    # cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
