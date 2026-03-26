import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

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


def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


# =========================
# FETCH TITLE
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
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="YouTube"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "YouTube")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

    # Fresh thumbnail
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

    # Auto title fix
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

    # Load image
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumbnail")
    except:
        original = Image.new("RGB", (1280, 720), (30, 30, 30))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # BACKGROUND (FULL BIG)
    # =========================
    bg = original.copy().filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.30)
    bg = ImageEnhance.Color(bg).enhance(0.85)
    bg = bg.convert("RGBA")

    dark_overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 125))
    bg = Image.alpha_composite(bg, dark_overlay)

    # Warm glow
    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((250, 60, 1050, 660), fill=(255, 170, 80, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # MAIN BIG CARD
    # =========================
    card_x, card_y = 250, 55
    card_w, card_h = 780, 610

    # shadow
    shadow = Image.new("RGBA", (card_w + 80, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, card_w + 80, card_h + 80), 65, fill=(0, 0, 0, 190))
    shadow = shadow.filter(ImageFilter.GaussianBlur(35))
    bg.paste(shadow, (card_x - 40, card_y + 25), shadow)

    # card
    card = Image.new("RGBA", (card_w, card_h), (18, 18, 20, 242))
    card_mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, card_w, card_h), 55, fill=255)
    bg.paste(card, (card_x, card_y), card_mask)

    # =========================
    # TOP IMAGE (BIG & CLEAN)
    # =========================
    preview = ImageOps.fit(original.convert("RGBA"), (640, 250), method=Image.LANCZOS)
    preview_mask = Image.new("L", (640, 250), 0)
    ImageDraw.Draw(preview_mask).rounded_rectangle((0, 0, 640, 250), 38, fill=255)
    preview.putalpha(preview_mask)

    preview_x = 320
    preview_y = 95
    bg.paste(preview, (preview_x, preview_y), preview)

    # gold border
    border = Image.new("RGBA", (648, 258), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    bd.rounded_rectangle((0, 0, 648, 258), 40, outline=(226, 191, 123), width=4)
    bg.paste(border, (preview_x - 4, preview_y - 4), border)

    # 4k
    tag_font = load_font(28)
    draw.text((340, 318), "4k", fill="white", font=tag_font)

    # =========================
    # FONTS
    # =========================
    top_font = load_font(18)
    now_font = load_font(34)
    title_font = load_font(52)
    meta_font = load_font(22)
    time_font = load_font(24)
    btn_font = load_font(62)
    pause_font = load_font(72)

    # =========================
    # TEXTS
    # =========================
    draw.text((640, 82), "NOW PLAYING • PREMIUM PLAYER", fill=(175, 175, 175), font=top_font, anchor="mm")

    clean_title = trim(title.upper(), title_font, 620)

    draw.text((640, 395), "Now Playing", fill=(200, 200, 200), font=now_font, anchor="mm")
    draw.text((640, 470), clean_title, fill="white", font=title_font, anchor="mm")
    draw.text((640, 515), views, fill=(160, 160, 160), font=meta_font, anchor="mm")

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = 350
    bar_x2 = 930
    bar_y = 565

    draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 10), 10, fill=(105, 105, 105))

    progress = 0.40
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y, prog_x, bar_y + 10), 10, fill=(226, 191, 123))
    draw.ellipse((prog_x - 11, bar_y - 7, prog_x + 11, bar_y + 15), fill="white")

    draw.text((350, 603), "1:24", fill=(190, 190, 190), font=time_font)
    draw.text((880, 603), duration, fill=(190, 190, 190), font=time_font)

    # =========================
    # BUTTONS
    # =========================
    draw.text((500, 655), "<<", fill="white", font=btn_font, anchor="mm")

    pause_bg = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    pbd = ImageDraw.Draw(pause_bg)
    pbd.rounded_rectangle((0, 0, 120, 120), 36, fill=(55, 55, 60, 255))
    bg.paste(pause_bg, (580, 605), pause_bg)

    draw.text((640, 663), "II", fill="white", font=pause_font, anchor="mm")
    draw.text((780, 655), ">>", fill="white", font=btn_font, anchor="mm")

    # Save
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    # cleanup
    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
