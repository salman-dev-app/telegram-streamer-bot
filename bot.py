import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import datetime
from base64 import urlsafe_b64encode
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
import os

# --- Configuration ---
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
WEB_SERVER_URL = os.getenv("WEB_SERVER_URL", "")

# --- Database ---
db_client = MongoClient(MONGO_URI)
db = db_client.get_database("LinkerBotDB")
users_collection = db.get_collection("users")
# ... (Database functions like add_user, etc.)

# --- Pyrogram and FastAPI Setup ---
# আমরা একটি "in_memory" সেশন ব্যবহার করব, যা Koyeb-এর জন্য ভালো
app = Client("LinkerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
web_app = FastAPI()

# --- Web Server Logic ---
async def stream_generator(message):
    async for chunk in app.stream_media(message, block=False):
        yield chunk

@web_app.get("/stream/{encoded_id}")
@web_app.get("/download/{encoded_id}")
async def handle_request(encoded_id: str, response: Response):
    try:
        # ... (Web server logic from the previous web_server.py)
        decoded_id_bytes = urlsafe_b64decode(encoded_id)
        decoded_id_str = decoded_id_bytes.decode('ascii')
        chat_id_str, message_id_str = decoded_id_str.split(':')
        message = await app.get_messages(chat=int(chat_id_str), message_ids=int(message_id_str))
        media = message.video or message.document or message.audio
        if not message or not media: raise HTTPException(status_code=404, detail="File not found.")
        file_size = media.file_size
        file_name = media.file_name or "file"
        response.headers["Content-Length"] = str(file_size)
        response.headers["Content-Disposition"] = f"attachment; filename=\"{file_name}\""
        return StreamingResponse(stream_generator(message), status_code=206, media_type=media.mime_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# --- Telegram Bot Logic ---
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    # ... (Start command logic)
    await message.reply_text("Welcome! Forward a file to get a streamable link.")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file(client: Client, message: Message):
    # ... (File handling logic from the previous bot.py)
    msg = await message.reply_text("Processing...")
    try:
        forwarded_message = await message.forward(LOG_CHANNEL_ID)
        id_str = f"{forwarded_message.chat.id}:{forwarded_message.id}"
        encoded_id = urlsafe_b64encode(id_str.encode('ascii')).decode('ascii')
        stream_link = f"{WEB_SERVER_URL}/stream/{encoded_id}"
        download_link = f"{WEB_SERVER_URL}/download/{encoded_id}"
        await msg.edit_text(f"✅ **Link Generated!**\n\n🎬 **Stream:** `{stream_link}`\n\n📥 **Download:** `{download_link}`", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error: `{e}`")

# --- Main execution logic ---
async def run_bot_and_server():
    # দুটিকে একসাথে অ্যাসিঙ্ক্রোনাসভাবে চালানো হচ্ছে
    await app.start()
    print("Pyrogram Client started.")
    
    config = uvicorn.Config(web_app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
    server = uvicorn.Server(config)
    print("Uvicorn server starting.")
    
    await server.serve()
    
    await app.stop()

if __name__ == "__main__":
    print("Starting bot and web server...")
    asyncio.run(run_bot_and_server())
