import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


# =========================
# TEXT TRIM
# =========================
def trim(text, font, max_w):
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
    path = f"{CACHE_DIR}/{videoid}.png"
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # -------------------------
    # Download thumbnail
    # -------------------------
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(thumb_url) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_file, "wb") as f:
                        await f.write(await r.read())
                else:
                    thumb_file = None
    except:
        thumb_file = None

    # -------------------------
    # Load thumb
    # -------------------------
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
    bg = original.resize((1280, 720)).filter(ImageFilter.GaussianBlur(22))
    dark = Image.new("RGBA", (1280, 720), (0, 0, 0, 110))
    bg = bg.convert("RGBA")
    bg.alpha_composite(dark)

    draw = ImageDraw.Draw(bg)

    # =========================
    # CENTER CARD
    # =========================
    card = Image.new("RGBA", (700, 560), (22, 22, 24, 235))
    card_mask = Image.new("L", (700, 560), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, 700, 560), 55, fill=255)
    bg.paste(card, (290, 80), card_mask)

    # Soft shadow
    shadow = Image.new("RGBA", (740, 600), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, 740, 600), 60, fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    bg.paste(shadow, (270, 65), shadow)

    # =========================
    # THUMB PREVIEW TOP
    # =========================
    preview = original.convert("RGBA").resize((610, 265))
    mask = Image.new("L", (610, 265), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 610, 265), 35, fill=255)
    preview.putalpha(mask)

    # golden border
    border = Image.new("RGBA", (618, 273), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 618, 273), 38, outline=(220, 180, 110), width=4)

    bg.paste(border, (331, 97), border)
    bg.paste(preview, (335, 101), preview)

    # =========================
    # FONTS
    # =========================
    try:
        small_font = ImageFont.truetype(FONT, 28)
        med_font = ImageFont.truetype(FONT, 34)
        title_font = ImageFont.truetype(FONT, 62)
        time_font = ImageFont.truetype(FONT, 26)
        icon_font = ImageFont.truetype(FONT, 80)
    except:
        small_font = ImageFont.load_default()
        med_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        time_font = ImageFont.load_default()
        icon_font = ImageFont.load_default()

    # =========================
    # TEXT
    # =========================
    title = trim(title, title_font, 540)

    draw.text((555, 395), "Now Playing", fill=(210, 210, 210), font=med_font, anchor="mm")
    draw.text((555, 455), title, fill="white", font=title_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 380
    bar_x2 = 910
    bar_y = 530

    # base line
    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 8), 10, fill=(110, 110, 110))

    # progress
    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)
    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 8), 10, fill=(220, 180, 110))

    # slider
    draw.ellipse((prog_x - 10, bar_y - 8, prog_x + 10, bar_y + 12), fill="white")

    # time text
    draw.text((380, 565), "1:24", fill=(170, 170, 170), font=time_font)
    draw.text((885, 565), duration, fill=(170, 170, 170), font=time_font)

    # =========================
    # PLAYER BUTTONS
    # =========================
    # Back
    draw.text((520, 625), "⏮", fill="white", font=icon_font, anchor="mm")

    # Pause background
    draw.rounded_rectangle((610, 575, 720, 675), 28, fill=(50, 50, 50))
    draw.text((665, 625), "⏸", fill="white", font=icon_font, anchor="mm")

    # Next
    draw.text((785, 625), "⏭", fill="white", font=icon_font, anchor="mm")

    # =========================
    # SAVE
    # =========================
    bg = bg.convert("RGB")
    bg.save(path, quality=95)

    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
