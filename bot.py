# Ahar All-In-One Bot — fixed & stable
# Requirements (install these):
# pip install pyrogram tgcrypto yt-dlp requests pillow opencv-python libtorrent

import asyncio
import os
import time
import glob
import requests
import cv2
import yt_dlp
import shutil
import libtorrent as lt
from PIL import Image

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChatWriteForbidden

# --- BOT CONFIG ---
API_ID = 27409928
API_HASH = "5bb178e8905d57f05954c5d5ff263785"
BOT_TOKEN = "7073247917:AAGNOZDBzCMxjhaKukHlmCT90TGezix_jvE"  # REGENERATE this later!

# --- CHANNELS ---
# Bot must be an admin in these if they are channels/supergroups.
FORCE_SUB_CHANNEL = "@trrrytgch"
UPLOAD_CHANNEL = "@trrrytgch"

# --- PATHS ---
DOWNLOAD_DIRECTORY = "./downloads"
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)
COOKIES_FILE = "./cookies.txt"

# Initialize Pyrogram Client
app = Client(
    "Ahar_All_In_One_Bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# -------- Progress Helpers --------
def humanbytes(size):
    """Converts bytes to a human-readable format with /s."""
    if not size:
        return "0 B/s"
    power = 1024
    t_n = 0
    power_dict = {0: " ", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        t_n += 1
    return f"{size:.2f} {power_dict[t_n]}B/s"

def progress_bar(percentage):
    """Creates a text-based progress bar."""
    if percentage > 100: percentage = 100
    bar = '█' * int(percentage / 10)
    bar += '░' * (10 - len(bar))
    return f"|{bar}| {percentage:.1f}%"


# -------- 1) Force-subscription helper --------
async def check_membership(client: Client, message: Message) -> bool:
    try:
        await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=message.from_user.id)
        return True
    except UserNotParticipant:
        channel_link = f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}"
        join_button = InlineKeyboardMarkup([[InlineKeyboardButton("Join Our Channel", url=channel_link)]])
        await message.reply_text(
            f"To use me, you must first join our channel.\nPlease join **{FORCE_SUB_CHANNEL}** and then try again.",
            reply_markup=join_button,
            quote=True
        )
        return False
    except ChatAdminRequired:
        await message.reply_text(
            "I can't verify membership because I'm not an admin in the force-sub channel. "
            "Please make me an admin there or disable force-sub.",
            quote=True
        )
        return False
    except Exception as e:
        print(f"[check_membership] ERROR: {e}")
        await message.reply_text("An error occurred while checking your membership. Please try again.", quote=True)
        return False

# -------- 2) Upload video helper --------
async def upload_video(client: Client, message: Message, video_path: str, caption: str, thumb_path: str = None):
    status_message = await message.reply_text("Extracting video metadata...", quote=True)

    # --- Add user info ---
    user = message.from_user
    user_info = f"\n\n👤 Requested by: {user.first_name or 'Unknown'} (ID: `{user.id}`)"
    final_caption = caption + user_info

    duration, width, height = 0, 0, 0
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps and fps > 0 and frame_count and frame_count > 0:
                duration = int(frame_count / fps)
        cap.release()
    except Exception as e:
        print(f"[upload_video] Metadata extraction error: {e}")
        await status_message.edit_text("Warning: Could not extract video metadata.")

    last_update_time = 0
    
    async def progress(current, total):
        nonlocal last_update_time
        now = time.time()
        if now - last_update_time > 2:
            if total > 0:
                percentage = current * 100 / total
                bar = progress_bar(percentage)
                try:
                    await status_message.edit_text(f"**Uploading to Channel...**\n{bar}")
                except ChatWriteForbidden:
                    pass # Can't edit message in the other chat
                except Exception:
                    pass
                last_update_time = now

    try:
        await status_message.edit_text("Starting upload to channel…")
        await client.send_video(
            chat_id=UPLOAD_CHANNEL,
            video=video_path,
            caption=final_caption,
            duration=duration or None,
            width=width or None,
            height=height or None,
            thumb=thumb_path if (thumb_path and os.path.exists(thumb_path)) else None,
            supports_streaming=True,
            progress=progress
        )
        await status_message.edit_text("✅ **Upload complete!**\nFile sent to the channel. @trrrytgch")
    except Exception as e:
        print(f"[upload_video] Upload failed: {e}")
        await status_message.edit_text(f"❌ **Upload Failed!**\n\nError: `{e}`")
    finally:
        if thumb_path and os.path.exists(thumb_path):
            try: os.remove(thumb_path)
            except Exception: pass

# -------- 3) Commands --------
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if await check_membership(client, message):
        await message.reply_text(
            "**Welcome to Ahar All-In-One Bot!**\n\nUse /help to see all available commands.\n\n{Only can download files less than 2GB}",
            quote=True
        )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    if await check_membership(client, message):
        await message.reply_text(
            "**How to use me:**\n\n"
            "1. `/torrent <magnet link>` or reply to a `.torrent` file with `/torrent`.\n"
            "2. `/youtube <YouTube URL>`\n"
            "3. `/url <Direct Download URL>`\n"
            "4. `/ping` (check if I'm alive)\n\n"
            "**For YouTube:** To download private or member-only videos, place a `cookies.txt` file in my directory.",
            quote=True,
            disable_web_page_preview=True
        )

@app.on_message(filters.command("ping") & filters.private)
async def ping_command(_, message):
    await message.reply_text("🏓 Pong!", quote=True)

# ---- Torrent ----
@app.on_message(filters.command("torrent") & filters.private)
async def torrent_handler(client, message):
    if not await check_membership(client, message):
        return

    source = None
    link_type = None
    if message.reply_to_message and message.reply_to_message.document and \
       message.reply_to_message.document.file_name.lower().endswith(".torrent"):
        source = await message.reply_to_message.download(in_memory=False)
        link_type = "file"
    elif len(message.command) > 1:
        source = message.text.split(" ", 1)[1]
        if not source.startswith("magnet:"):
            await message.reply_text("Invalid magnet link.", quote=True)
            return
        link_type = "magnet link"
    else:
        await message.reply_text("Provide a magnet link or reply to a .torrent file.", quote=True)
        return

    status_message = await message.reply_text(f"Starting download from {link_type}…", quote=True)
    download_path = os.path.join(DOWNLOAD_DIRECTORY, f"torrent_{int(time.time())}")
    os.makedirs(download_path, exist_ok=True)

    ses = lt.session()
    ses.listen_on(6881, 6891)
    params = {'save_path': download_path}
    
    h = None
    if link_type == "file":
        info = lt.torrent_info(source)
        h = ses.add_torrent({'ti': info, 'save_path': download_path})
    else: # magnet
        h = lt.add_magnet_uri(ses, source, params)

    try:
        await status_message.edit_text("Downloading metadata from torrent...")
        while not h.has_metadata():
            await asyncio.sleep(1)
        
        await status_message.edit_text("Metadata found! Starting file download...")
        last_update_time = 0
        while not h.status().is_seeding:
            s = h.status()
            now = time.time()
            
            if now - last_update_time > 3: # Update every 3 seconds
                state_str = [
                    'queued', 'checking', 'downloading metadata', 'downloading',
                    'finished', 'seeding', 'allocating', 'checking fastresume'
                ]
                
                msg = f"**Downloading from Torrent...**\n\n" \
                      f"**Status:** `{state_str[s.state]}`\n" \
                      f"**Peers:** `{s.num_peers}`\n" \
                      f"**Speed:** `{humanbytes(s.download_rate)}` 🔽 | **Up:** `{humanbytes(s.upload_rate)}` 🔼\n" \
                      f"{progress_bar(s.progress * 100)}"
                try:
                    await status_message.edit_text(msg)
                    last_update_time = now
                except Exception:
                    pass
            await asyncio.sleep(1)

        await status_message.edit_text("Torrent download finished. Checking files...")
        
        files = glob.glob(os.path.join(download_path, "**", "*.*"), recursive=True)
        if not files:
            raise Exception("No files were downloaded from the torrent.")

        await status_message.edit_text(f"Found {len(files)} file(s) in torrent. Starting uploads...")
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            if file_name.endswith(('.!qB', '.parts')): continue # Skip temp files
            upload_caption = f"**Downloaded via Torrent:**\n`{file_name}`"
            await upload_video(client, message, file_path, caption=upload_caption)

        await status_message.edit_text("✅ **All torrent uploads complete!**")

    except Exception as e:
        print(f"[torrent_handler] ERROR: {e}")
        await status_message.edit_text(f"❌ **Torrent Download Failed!**\n\nError: `{e}`")
    finally:
        if 'ses' in locals():
            ses.pause()
            if h and h.is_valid():
                ses.remove_torrent(h)
        if os.path.exists(download_path):
            shutil.rmtree(download_path, ignore_errors=True)
        if link_type == "file" and source and os.path.exists(source):
            os.remove(source)

# ---- YouTube ----
# ---- YouTube ----
@app.on_message(filters.command("youtube") & filters.private)
async def youtube_handler(client, message):
    if not await check_membership(client, message):
        return
    if len(message.command) < 2:
        await message.reply_text("Please provide a YouTube URL.", quote=True)
        return

    url = message.text.split(" ", 1)[1].strip()
    status_message = await message.reply_text("Processing YouTube link…", quote=True)
    video_path = None
    thumb_path_to_clean = None
    final_thumb_path = None
    
    loop = asyncio.get_event_loop()
    last_update_time = 0

    def progress_hook(d):
        nonlocal last_update_time
        if d['status'] == 'downloading':
            now = time.time()
            if now - last_update_time > 3:
                percentage = d.get('fraction', 0) * 100
                speed = d.get('speed')
                
                # --- FIX: Handle cases where ETA is None ---
                eta_from_hook = d.get('eta')
                eta = int(eta_from_hook) if eta_from_hook is not None else 0
                # --- END FIX ---
                
                bar = progress_bar(percentage)
                speed_str = humanbytes(speed) if speed else "N/A"
                
                msg = f"**Downloading from YouTube...**\n" \
                      f"{bar}\n" \
                      f"**Speed:** `{speed_str}`\n" \
                      f"**ETA:** `{eta}s`"
                
                try:
                    # Schedule the async task on the running loop
                    asyncio.run_coroutine_threadsafe(status_message.edit_text(msg), loop)
                except Exception:
                    pass
                last_update_time = now

    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
            'writethumbnail': True,
            'noplaylist': True,
            'progress_hooks': [progress_hook],
        }
        
        if os.path.exists(COOKIES_FILE):
            ydl_opts['cookiefile'] = COOKIES_FILE

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_message.edit_text("Extracting video information…")
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            await loop.run_in_executor(None, lambda: ydl.download([url]))
            video_filename = ydl.prepare_filename(info)

        base, _ = os.path.splitext(video_filename)
        for ext in (".mp4", ".mkv", ".webm"):
            p = base + ext
            if os.path.exists(p):
                video_path = p
                break

        if not video_path:
            raise RuntimeError("Downloaded video file not found.")

        # Handle thumbnail
        for ext in ("webp", "jpg", "jpeg", "png"):
            p = f"{base}.{ext}"
            if os.path.exists(p):
                thumb_path_to_clean = p
                break
        
        if thumb_path_to_clean:
            final_thumb_path = base + "_thumb.jpg"
            Image.open(thumb_path_to_clean).convert("RGB").save(final_thumb_path, "jpeg")

        title = info.get('title', 'N/A')
        uploader = info.get('uploader', 'N/A')
        views = info.get('view_count', 0)
        caption = f"🎬 **{title}**\n👤 **Uploader:** {uploader}\n👀 **Views:** {views:,}"

        await status_message.edit_text("Download complete. Preparing to upload…")
        await upload_video(client, message, video_path, caption, final_thumb_path)
    except Exception as e:
        print(f"[youtube_handler] ERROR: {e}")
        await status_message.edit_text(f"❌ **YouTube Download Failed!**\n\nError: `{e}`")
    finally:
        if video_path and os.path.exists(video_path): os.remove(video_path)
        if thumb_path_to_clean and os.path.exists(thumb_path_to_clean): os.remove(thumb_path_to_clean)

# ---- Direct URL ----
@app.on_message(filters.command("url") & filters.private)
async def url_handler(client, message):
    if not await check_membership(client, message):
        return
    if len(message.command) < 2:
        await message.reply_text("Please provide a direct download URL.", quote=True)
        return

    url = message.text.split(" ", 1)[1].strip()
    status_message = await message.reply_text("Starting download from URL…", quote=True)
    output_path = None

    try:
        filename_guess = url.split('/')[-1].split('?')[0] or f"download_{int(time.time())}.mp4"
        output_path = os.path.join(DOWNLOAD_DIRECTORY, filename_guess)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            last_update_time = time.time()
            start_time = time.time()
            downloaded_bytes = 0

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        now = time.time()
                        
                        if now - last_update_time > 2:
                            if total_size > 0:
                                percentage = (downloaded_bytes / total_size) * 100
                                elapsed_time = now - start_time
                                speed = downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
                                
                                bar = progress_bar(percentage)
                                speed_str = humanbytes(speed)
                                
                                msg = f"**Downloading from URL...**\n" \
                                      f"{bar}\n" \
                                      f"**Speed:** `{speed_str}`"
                                try:
                                    await status_message.edit_text(msg)
                                except Exception:
                                    pass
                                last_update_time = now

        file_basename = os.path.basename(output_path)
        await status_message.edit_text(f"**Download complete:** `{file_basename}`\n\nNow preparing to upload…")
        await upload_video(client, message, output_path, caption=f"**Downloaded from URL:**\n`{file_basename}`")
    except Exception as e:
        print(f"[url_handler] ERROR: {e}")
        await status_message.edit_text(f"❌ **URL Download Failed!**\n\nError: `{e}`")
    finally:
        if output_path and os.path.exists(output_path):
            os.remove(output_path)

# -------- Main --------
if __name__ == "__main__":
    print("Bot is starting…")
    app.run()
