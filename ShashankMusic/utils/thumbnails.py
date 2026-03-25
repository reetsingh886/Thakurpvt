import os
import random

import aiofiles
import aiohttp

from PIL import Image, ImageEnhance, ImageOps

from config import YOUTUBE_IMG_URL


# ✅ Resize function safe
def changeImageSize(maxWidth, maxHeight, image):
    if image.size[0] == 0 or image.size[1] == 0:
        return image

    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]

    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])

    return image.resize((newWidth, newHeight))


# ✅ Main thumbnail function
async def get_thumb(videoid):
    os.makedirs("cache", exist_ok=True)

    final_path = f"cache/{videoid}.png"
    temp_path = f"cache/thumb_{videoid}.jpg"

    # ✅ Agar pehle se bana hua hai to wahi use karo
    if os.path.isfile(final_path):
        return final_path

    try:
        print(f"[THUMB] Generating thumbnail for videoid: {videoid}")

        # ✅ Direct YouTube thumbnail URL
        thumbnail = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"

        # ✅ Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status != 200:
                    print(f"[THUMB ERROR] Thumbnail fetch failed: {resp.status}")
                    return YOUTUBE_IMG_URL

                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(await resp.read())

        # ✅ Open image
        youtube = Image.open(temp_path).convert("RGB")
        image1 = changeImageSize(1280, 720, youtube)

        # ✅ Light enhancement
        bg = ImageEnhance.Brightness(image1).enhance(1.1)
        bg = ImageEnhance.Contrast(bg).enhance(1.1)

        # ✅ Random border color
        colors = [
            "white", "red", "orange", "yellow",
            "green", "cyan", "blue", "violet", "pink"
        ]
        border = random.choice(colors)

        final = ImageOps.expand(bg, border=7, fill=border)
        final = changeImageSize(1280, 720, final)

        # ✅ Save final image
        final.save(final_path)

        # ✅ Cleanup temp
        try:
            os.remove(temp_path)
        except:
            pass

        print(f"[THUMB] Saved thumbnail: {final_path}")
        return final_path

    except Exception as e:
        print(f"[THUMB ERROR] {e}")
        return YOUTUBE_IMG_URL
