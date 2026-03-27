import os
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# Constants
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

WIDTH, HEIGHT = 1280, 720

# Thumbnail Box
THUMB_X = 105
THUMB_Y = 140
THUMB_W = 450
THUMB_H = 450
THUMB_RADIUS = 35
BORDER_WIDTH = 10

# Text Area
BADGE_X = 620
BADGE_Y = 135

TITLE_X = 620
TITLE_Y = 230

META_X = 620
META_Y = 380

BAR_X = 620
BAR_Y = 520
BAR_TOTAL = 500
BAR_RED = 250

FOOTER_X = 920
FOOTER_Y = 655

MAX_TITLE_WIDTH = 530

def trim_to_width(text: str, font, max_w: int) -> str:
    ellipsis = "..."
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis

def safe_text(text):
    return str(text).encode("ascii", "ignore").decode("ascii")

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_premium.png")
    if os.path.exists(cache_path):
        return cache_path

    # Fixed image source
    thumbnail = f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg"
    thumb_path = os.path.join(CACHE_DIR, f"{videoid}_thumb.jpg")

    # Download thumbnail
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    raise Exception("Thumbnail download failed")
    except Exception:
        return None

    # Open and blur background
    base = Image.open(thumb_path).convert("RGBA").resize((WIDTH, HEIGHT))
    bg = ImageEnhance.Brightness(base.filter(ImageFilter.GaussianBlur(18))).enhance(0.35)

    draw = ImageDraw.Draw(bg)

    # Fonts
    try:
        title_font = ImageFont.truetype("Shashank/assets/assets/font.ttf", 42)
        regular_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 26)
        small_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 22)
        badge_font = ImageFont.truetype("Shashank/assets/assets/font2.ttf", 24)
    except OSError:
        title_font = regular_font = small_font = badge_font = ImageFont.load_default()

    # Main thumb image
    thumb = Image.open(thumb_path).convert("RGBA").resize((THUMB_W, THUMB_H))

    # Rounded mask
    mask = Image.new("L", (THUMB_W, THUMB_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), THUMB_RADIUS, fill=255)

    # Red border
    border_img = Image.new("RGBA", (THUMB_W + BORDER_WIDTH*2, THUMB_H + BORDER_WIDTH*2), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_img)
    border_draw.rounded_rectangle(
        (0, 0, THUMB_W + BORDER_WIDTH*2 - 1, THUMB_H + BORDER_WIDTH*2 - 1),
        THUMB_RADIUS + 8,
        outline=(255, 59, 59, 255),
        width=BORDER_WIDTH
    )

    bg.paste(border_img, (THUMB_X - BORDER_WIDTH, THUMB_Y - BORDER_WIDTH), border_img)
    bg.paste(thumb, (THUMB_X, THUMB_Y), mask)

    # Badge: NOW PLAYING
    badge_w, badge_h = 220, 60
    badge = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge)
    badge_draw.rounded_rectangle((0, 0, badge_w, badge_h), 30, fill=(255, 59, 59, 255))
    bg.paste(badge, (BADGE_X, BADGE_Y), badge)

    draw.text((BADGE_X + 33, BADGE_Y + 14), "NOW PLAYING", fill="white", font=badge_font)

    # Fixed text (NO Unicode error)
    title = "Anuv Jain - HUSN (Official Video)"
    title = safe_text(trim_to_width(title, title_font, MAX_TITLE_WIDTH))

    draw.text((TITLE_X, TITLE_Y), title, fill="white", font=title_font)

    # Underline
    draw.line((TITLE_X, TITLE_Y + 70, TITLE_X + 420, TITLE_Y + 70), fill=(255, 59, 59), width=4)

    # Metadata
    draw.text((META_X, META_Y), "Duration: 4:00", fill="white", font=regular_font)
    draw.text((META_X, META_Y + 50), "Views: 261M views", fill=(255, 90, 90), font=regular_font)
    draw.text((META_X, META_Y + 100), "Player: @Rossymusicrobot", fill=(255, 90, 90), font=regular_font)

    # Progress bar
    draw.line((BAR_X, BAR_Y, BAR_X + BAR_TOTAL, BAR_Y), fill=(240, 240, 240), width=14)
    draw.line((BAR_X, BAR_Y, BAR_X + BAR_RED, BAR_Y), fill=(255, 59, 59), width=14)

    # Slider circle
    knob_x = BAR_X + BAR_RED
    draw.ellipse((knob_x - 14, BAR_Y - 14, knob_x + 14, BAR_Y + 14), fill="white")

    # Time text
    draw.text((BAR_X, BAR_Y + 30), "00:00", fill="white", font=small_font)
    draw.text((BAR_X + BAR_TOTAL - 65, BAR_Y + 30), "4:00", fill="white", font=small_font)

    # Footer
    draw.text((FOOTER_X, FOOTER_Y), "Powered by Mr Thakur", fill=(180, 180, 180), font=small_font)

    # Save
    bg.save(cache_path)

    try:
        os.remove(thumb_path)
    except:
        pass

    return cache_path
