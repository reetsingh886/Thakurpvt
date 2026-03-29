import os
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from youtubesearchpython import VideosSearch

# ---------------- FONT LOAD ---------------- #
def load_font(size):
    font_paths = [
        "ShashankMusic/assets/font.ttf",
        "assets/font.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


# ---------------- TEXT SHORT ---------------- #
def truncate(text, length):
    return text[:length] + "..." if len(text) > length else text


# ---------------- DOWNLOAD IMAGE ---------------- #
async def download_image(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download image: {url}")
            with open(path, "wb") as f:
                f.write(await resp.read())


# ---------------- GENERATE THUMB ---------------- #
async def gen_thumb(thumbnail, title, userid, duration, views, channel):
    os.makedirs("cache", exist_ok=True)

    bg_path = f"cache/bg_{userid}.png"
    final_path = f"cache/thumb_{userid}.png"

    # Download thumbnail
    await download_image(thumbnail, bg_path)

    # Open original image
    main = Image.open(bg_path).convert("RGB")

    # Create blurred background
    bg = main.resize((1280, 720)).filter(ImageFilter.GaussianBlur(12))
    bg = bg.convert("RGBA")

    # Dark overlay
    dark = Image.new("RGBA", bg.size, (0, 0, 0, 90))
    bg = Image.alpha_composite(bg, dark)

    # Resize center image
    center = main.resize((820, 460)).convert("RGBA")

    # Rounded mask
    mask = Image.new("L", center.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, center.size[0], center.size[1]), radius=35, fill=255)
    center.putalpha(mask)

    # Paste center image
    x = (1280 - 820) // 2
    y = 80
    bg.paste(center, (x, y), center)

    draw = ImageDraw.Draw(bg)

    # Neon pink border
    for i in range(8):
        draw.rounded_rectangle(
            (x - i, y - i, x + 820 + i, y + 460 + i),
            radius=35,
            outline=(255, 20, 147, 180),
            width=2
        )

    # Fonts
    title_font = load_font(52)
    info_font = load_font(36)
    small_font = load_font(28)

    # Short text
    title = truncate(title, 45)
    channel = truncate(channel, 30)

    # Bottom Title
    draw.text((80, 585), title, font=title_font, fill="white", stroke_width=2, stroke_fill="black")

    # Pink info line
    info_text = f"YouTube : {views} | Time : {duration} | Player : @{channel}"
    draw.text((140, 655), info_text, font=info_font, fill=(255, 20, 147), stroke_width=1, stroke_fill="black")

    # Watermark corners
    draw.text((30, 675), "THAKUR", font=small_font, fill="white")
    draw.text((1110, 20), "VAISHU", font=small_font, fill="yellow")

    bg = bg.convert("RGB")
    bg.save(final_path, quality=95)

    return final_path


# ---------------- MAIN FUNCTION ---------------- #
async def get_thumb(videoid, user_id, user_name):
    results = VideosSearch(videoid, limit=1).result()

    if not results.get("result"):
        raise Exception("No YouTube results found")

    data = results["result"][0]

    title = data.get("title", "Unknown Title")
    duration = data.get("duration", "Unknown")
    views = data.get("viewCount", {}).get("short", "Unknown Views")
    channel = user_name

    thumbnails = data.get("thumbnails", [])
    if not thumbnails:
        raise Exception("Thumbnail not found")

    thumbnail = thumbnails[0]["url"]

    return await gen_thumb(thumbnail, title, user_id, duration, views, channel)
