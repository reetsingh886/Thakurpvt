import os
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return url


async def get_thumb(videoid: str) -> str:
    videoid = extract_video_id(videoid)
    path = f"{CACHE_DIR}/{videoid}.png"

    # ✅ Cache check
    if os.path.exists(path):
        return path

    # ✅ Always working thumbnail
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    thumb_path = f"{CACHE_DIR}/{videoid}_raw.jpg"

    # Download thumbnail safely
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return thumb_url
    except Exception:
        return thumb_url

    try:
        base = Image.open(thumb_path).resize((1280, 720)).convert("RGB")
    except Exception:
        return thumb_url

    # ===== BACKGROUND =====
    bg = base.filter(ImageFilter.GaussianBlur(30))

    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 180))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(bg)

    # ===== CARD =====
    card_w, card_h = 820, 520
    card_x = (1280 - card_w) // 2
    card_y = (720 - card_h) // 2

    card = Image.new("RGBA", (card_w, card_h), (25, 25, 25, 255))
    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w, card_h), 40, fill=255)

    bg.paste(card, (card_x, card_y), mask)

    # ===== THUMB =====
    thumb = base.resize((720, 300))

    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, 720, 300), 30, fill=255)

    bg.paste(thumb, (card_x + 50, card_y + 40), tmask)

    # ===== FONTS =====
    try:
        title_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 42)
        small_font = ImageFont.truetype("ShashankMusic/assets/font.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # ===== TEXT =====
    draw.text((card_x + card_w // 2, card_y + 360),
              "Now Playing",
              fill="white",
              font=small_font,
              anchor="mm")

    # Song name (videoid fallback)
    song = f"{videoid[:15]}..."
    draw.text((card_x + card_w // 2, card_y + 410),
              song,
              fill="white",
              font=title_font,
              anchor="mm")

    # ===== PROGRESS BAR =====
    bar_x = card_x + 110
    bar_y = card_y + 470

    draw.line((bar_x, bar_y, bar_x + 600, bar_y), fill="gray", width=6)
    draw.line((bar_x, bar_y, bar_x + 260, bar_y), fill="gold", width=6)

    draw.ellipse((bar_x + 250, bar_y - 8, bar_x + 270, bar_y + 8), fill="white")

    draw.text((bar_x, bar_y + 15), "0:00", fill="white", font=small_font)
    draw.text((bar_x + 550, bar_y + 15), "3:00", fill="white", font=small_font)

    # ===== CLEANUP =====
    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(path)
    return path
