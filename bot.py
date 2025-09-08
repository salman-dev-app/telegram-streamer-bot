from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, WEB_SERVER_URL, LOG_CHANNEL_ID, ADMIN_ID
from database import add_user, get_all_users, get_total_users
from base64 import urlsafe_b64encode

app = Client("LinkerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text("Welcome! Forward any file to me and I will generate a streamable and a direct download link for you.")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_command(client: Client, message: Message):
    if message.reply_to_message:
        broadcast_msg = message.reply_to_message
        total_users = get_total_users()
        await message.reply_text(f"Broadcasting started to {total_users} users...")
        
        success_count = 0
        for user in get_all_users():
            try:
                await broadcast_msg.copy(user["user_id"])
                success_count += 1
            except Exception:
                pass
        
        await message.reply_text(f"Broadcast complete. Sent to {success_count} / {total_users} users.")
    else:
        await message.reply_text("Please reply to a message to broadcast it.")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file(client: Client, message: Message):
    msg = await message.reply_text("⏳ Processing your file, please wait...")
    try:
        forwarded_message = await message.forward(LOG_CHANNEL_ID)
        
        # We will use the message ID from the log channel for permanent access
        id_str = f"{forwarded_message.chat.id}:{forwarded_message.id}"
        id_bytes = id_str.encode('ascii')
        encoded_id = urlsafe_b64encode(id_bytes).decode('ascii')
        
        stream_link = f"{WEB_SERVER_URL}/stream/{encoded_id}"
        download_link = f"{WEB_SERVER_URL}/download/{encoded_id}"
        
        media = message.video or message.document or message.audio
        file_name = media.file_name
        
        reply_text = (
            f"✅ **Link Generated Successfully!**\n\n"
            f"**File Name:** `{file_name}`\n\n"
            f"🎬 **Stream Link:** `{stream_link}`\n\n"
            f"📥 **Download Link:** `{download_link}`"
        )
        
        await msg.edit_text(reply_text, disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ An error occurred: `{e}`")

print("Bot is running...")
app.run()
