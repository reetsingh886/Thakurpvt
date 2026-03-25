from pyrogram import Client, filters
from pyrogram.types import Message
from youtubesearchpython import VideosSearch

# =========================================================
# AUTOPLAY STORAGE (temporary in-memory)
# =========================================================
AUTO_PLAY_CHATS = set()
LAST_PLAYED = {}

def is_autoplay_enabled(chat_id: int) -> bool:
    return chat_id in AUTO_PLAY_CHATS

def enable_autoplay(chat_id: int):
    AUTO_PLAY_CHATS.add(chat_id)

def disable_autoplay(chat_id: int):
    AUTO_PLAY_CHATS.discard(chat_id)

def save_last_played(chat_id: int, title: str):
    if title:
        LAST_PLAYED[chat_id] = title

def get_last_played(chat_id: int):
    return LAST_PLAYED.get(chat_id)

# =========================================================
# COMMANDS
# /autoplay
# /autoplay on
# /autoplay off
# /autoplayon
# /autoplayoff
# =========================================================
@Client.on_message(filters.command(["autoplay", "autoplayon", "autoplayoff"]) & filters.group)
async def autoplay_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    cmd = message.command[0].lower()

    if cmd == "autoplayon":
        enable_autoplay(chat_id)
        return await message.reply_text("✅ **AutoPlay Enabled**")

    if cmd == "autoplayoff":
        disable_autoplay(chat_id)
        return await message.reply_text("❌ **AutoPlay Disabled**")

    # /autoplay
    if len(message.command) == 1:
        status = "ON" if is_autoplay_enabled(chat_id) else "OFF"
        return await message.reply_text(
            f"🎵 **AutoPlay Status:** `{status}`\n\n"
            f"**Use:**\n"
            f"`/autoplay on`\n"
            f"`/autoplay off`"
        )

    # /autoplay on/off
    mode = message.command[1].lower()

    if mode == "on":
        enable_autoplay(chat_id)
        return await message.reply_text("✅ **AutoPlay Enabled**")

    if mode == "off":
        disable_autoplay(chat_id)
        return await message.reply_text("❌ **AutoPlay Disabled**")

    return await message.reply_text(
        "❌ **Usage:**\n\n"
        "`/autoplay on`\n"
        "`/autoplay off`"
    )

# =========================================================
# YOUTUBE RELATED SEARCH
# =========================================================
async def get_related_song(query: str):
    try:
        search = VideosSearch(query, limit=5)
        results = search.result().get("result", [])

        if not results:
            return None

        for video in results:
            title = video.get("title")
            url = video.get("link")
            duration = video.get("duration", "Unknown")

            if title and url:
                return {
                    "title": title,
                    "url": url,
                    "duration": duration
                }

        return None
    except Exception as e:
        print(f"[AUTOPLAY SEARCH ERROR] {e}")
        return None

# =========================================================
# MAIN AUTOPLAY HANDLER
# NOTE:
# play_func must accept: (chat_id, url, title)
# Example:
# async def play_func(chat_id, url, title):
#     await stream_song(chat_id, url, title)
# =========================================================
async def run_autoplay(client, chat_id: int, play_func):
    try:
        if not is_autoplay_enabled(chat_id):
            return False

        last_song = get_last_played(chat_id)
        if not last_song:
            print(f"[AUTOPLAY] No last song found for {chat_id}")
            return False

        recommended = await get_related_song(last_song + " official audio")
        if not recommended:
            print(f"[AUTOPLAY] No recommendation found for {last_song}")
            return False

        title = recommended["title"]
        url = recommended["url"]

        save_last_played(chat_id, title)

        await play_func(chat_id, url, title)

        try:
            await client.send_message(
                chat_id,
                f"🎵 **AutoPlay Started**\n\n"
                f"▶️ **Now Playing:** **{title}**"
            )
        except Exception as e:
            print(f"[AUTOPLAY MESSAGE ERROR] {e}")

        return True

    except Exception as e:
        print(f"[AUTOPLAY RUN ERROR] {e}")
        return False
