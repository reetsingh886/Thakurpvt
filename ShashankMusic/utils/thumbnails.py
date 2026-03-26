import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "font.ttf"))


# =========================
# HELPERS
# =========================
def safe_text(text, default="Unknown Song"):
    if text is None:
        return default
    text = str(text).strip()
    return text if text else default


def load_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()


def trim_text(text, font, max_width):
    text = safe_text(text)
    try:
        while len(text) > 3 and font.getlength(text) > max_width:
            text = text[:-1]
        return text + "..." if len(text) > 3 else text
    except:
        return text


def safe_round(draw, box, radius, fill=None, outline=None, width=1):
    try:
        x1, y1, x2, y2 = box
        if x2 <= x1 or y2 <= y1:
            return
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    except:
        try:
            draw.rectangle(box, fill=fill, outline=outline, width=width)
        except:
            pass


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
# MAIN THUMB FUNCTION
# =========================
async def get_thumb(videoid: str, title="Unknown Song", duration="0:00", views="0"):
    title = safe_text(title, "Unknown Song")
    duration = safe_text(duration, "0:00")
    views = safe_text(views, "0")

    path = f"{CACHE_DIR}/{videoid}.png"
    thumb_file = f"{CACHE_DIR}/{videoid}.jpg"

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

    # Load image safely
    try:
        if thumb_file and os.path.exists(thumb_file):
            original = Image.open(thumb_file).convert("RGB")
        else:
            raise Exception("No thumb")
    except:
        original = Image.new("RGB", (1280, 720), (20, 12, 8))

    original = ImageOps.fit(original, (1280, 720), method=Image.LANCZOS)

    # =========================
    # BACKGROUND
    # =========================
    bg = original.copy().filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.26)
    bg = ImageEnhance.Color(bg).enhance(0.95)
    bg = bg.convert("RGBA")

    dark = Image.new("RGBA", (1280, 720), (18, 8, 5, 120))
    bg = Image.alpha_composite(bg, dark)

    glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((180, 80, 1110, 670), fill=(255, 100, 80, 22))
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)

    # =========================
    # LEFT COVER BOX
    # =========================
    cover_x, cover_y = 90, 125
    cover_outer = 430
    cover_inner = 350

    safe_round(
        draw,
        (cover_x, cover_y, cover_x + cover_outer, cover_y + cover_outer),
        radius=45,
        outline=(255, 95, 95),
        width=8,
        fill=(10, 10, 10, 145)
    )

    album_x = cover_x + 40
    album_y = cover_y + 40

    try:
        album = ImageOps.fit(original.copy(), (cover_inner, cover_inner), method=Image.LANCZOS)
        album = album.convert("RGBA")

        cover_mask = Image.new("L", (cover_inner, cover_inner), 0)
        ImageDraw.Draw(cover_mask).rounded_rectangle((0, 0, cover_inner, cover_inner), 10, fill=255)

        bg.paste(album, (album_x, album_y), cover_mask)
    except:
        pass

    # =========================
    # FONTS
    # =========================
    now_font = load_font(28)
    title_font = load_font(44)
    info_font = load_font(28)
    time_font = load_font(20)

    # =========================
    # RIGHT TEXT AREA
    # =========================
    text_x = 610

    # Now Playing pill
    pill_x, pill_y = text_x, 145
    pill_w, pill_h = 250, 65
    safe_round(
        draw,
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=32,
        fill=(255, 95, 95)
    )
    draw.text((pill_x + 34, pill_y + 14), "NOW PLAYING", fill="black", font=now_font)

    # Title
    title = trim_text(title, title_font, 530)
    draw.text((text_x, 245), title, fill="white", font=title_font)

    # underline
    draw.line((text_x, 330, 1200, 330), fill=(255, 95, 95), width=5)

    # Duration & Views
    draw.text((text_x, 385), "Duration:", fill=(220, 220, 220), font=info_font)
    draw.text((800, 385), duration, fill=(255, 95, 95), font=info_font)

    draw.text((text_x, 475), "Views:", fill=(220, 220, 220), font=info_font)
    draw.text((800, 475), f"{views} views", fill=(255, 95, 95), font=info_font)

    # =========================
    # PROGRESS BAR
    # =========================
    bar_x1 = text_x
    bar_x2 = 1210
    bar_y = 585

    progress = 0.45
    prog_x = int(bar_x1 + (bar_x2 - bar_x1) * progress)

    try:
        safe_round(draw, (bar_x1, bar_y, bar_x2, bar_y + 8), radius=8, fill=(240, 240, 240))
        safe_round(draw, (bar_x1, bar_y, prog_x, bar_y + 8), radius=8, fill=(255, 95, 95))
    except:
        draw.line((bar_x1, bar_y, bar_x2, bar_y), fill="white", width=6)
        draw.line((bar_x1, bar_y, prog_x, bar_y), fill=(255, 95, 95), width=6)

    draw.ellipse((prog_x - 12, bar_y - 11, prog_x + 12, bar_y + 13), fill="white")

    draw.text((bar_x1, 615), "00:00", fill=(235, 235, 235), font=time_font)
    draw.text((1135, 615), duration, fill=(235, 235, 235), font=time_font)

    # Save
    bg = bg.convert("RGB")
    bg.save(path, quality=98)

    try:
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
    except:
        pass

    return path
