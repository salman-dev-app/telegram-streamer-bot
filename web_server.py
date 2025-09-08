from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from base64 import urlsafe_b64decode

app_for_files = Client("FileDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
web_app = FastAPI()

async def stream_generator(message):
    async for chunk in app_for_files.stream_media(message, block=False):
        yield chunk

@web_app.get("/stream/{encoded_id}")
@web_app.get("/download/{encoded_id}")
async def handle_request(encoded_id: str, response: Response):
    try:
        decoded_id_bytes = urlsafe_b64decode(encoded_id)
        decoded_id_str = decoded_id_bytes.decode('ascii')
        chat_id_str, message_id_str = decoded_id_str.split(':')
        
        message = await app_for_files.get_messages(chat=int(chat_id_str), message_ids=int(message_id_str))
        
        media = message.video or message.document or message.audio
        if not message or not media:
            raise HTTPException(status_code=404, detail="File not found.")

        file_size = media.file_size
        file_name = media.file_name or "file"
        
        response.headers["Content-Length"] = str(file_size)
        response.headers["Content-Disposition"] = f"attachment; filename=\"{file_name}\""
        
        return StreamingResponse(stream_generator(message), status_code=206, media_type=media.mime_type)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@web_app.on_event("startup")
async def startup_event():
    await app_for_files.start()

@web_app.on_event("shutdown")
async def shutdown_event():
    await app_for_files.stop()
