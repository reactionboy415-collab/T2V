import os
import json
import time
import random
import string
import threading
import httpx
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- [ SETTINGS ] ---
TOKEN = "8277221126:AAEjU6HiL4VoMqBRknMUEOg-6fKsuG-0gRs"
MODEL_NAME = "Wan 2.2 (Lightning)"
HOST_URL = "https://zerogpu-aoti-wan2-2-fp8da-aoti.hf.space"

# --- [ FLASK SERVER FOR RENDER UPTIME ] ---
app = Flask('')
@app.route('/')
def home(): 
    return f"⚡ {MODEL_NAME} Bot is Running!"

def run_flask():
    # Render automatically provides a PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- [ WAN 2.2 BYPASS ENGINE ] ---
class WanBypass:
    def __init__(self):
        self.host = HOST_URL

    def get_headers(self):
        # Generates a fake identity for every single request
        fake_ip = ".".join(map(str, (random.randint(1, 254) for _ in range(4))))
        return {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 125)}.0.0.0 Safari/537.36",
            "X-Forwarded-For": fake_ip,
            "Origin": "https://huggingface.co",
            "Referer": "https://huggingface.co/spaces/zerogpu-aoti/wan2-2-fp8da-aoti",
            "Accept": "text/event-stream",
        }

    async def generate_video(self, prompt):
        sess = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        headers = self.get_headers()
        
        # Exact payload for Wan 2.2 Text-to-Video
        payload = {
            "data": [prompt, "ugly, blurry, low quality, distorted", 5.0, 1, 3, 4, random.randint(1, 10**8), True],
            "fn_index": 0,
            "session_hash": sess
        }

        async with httpx.AsyncClient(timeout=None, headers=headers) as client:
            try:
                # 1. Join the ZeroGPU Queue
                join_res = await client.post(f"{self.host}/gradio_api/queue/join?session_hash={sess}", json=payload)
                if join_res.status_code != 200: return None
                
                # 2. Listen to the SSE stream until completion
                async with client.stream("GET", f"{self.host}/gradio_api/queue/data?session_hash={sess}") as response:
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "): continue
                        
                        try:
                            data = json.loads(line[6:])
                            msg = data.get("msg")
                            
                            if msg == "process_completed":
                                output = data.get("output", {}).get("data", [])
                                if output and isinstance(output[0], dict):
                                    path = output[0].get("video", {}).get("path")
                                    if path:
                                        return f"{self.host}/gradio_api/file={path}"
                        except:
                            continue
                return None
            except Exception as e:
                print(f"Error: {e}")
                return None

# --- [ TELEGRAM BOT HANDLERS ] ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"💀 **CR T2V** 💀\n\n"
        f"🚀 **Model:** {MODEL_NAME}\n"
        f"💎 **Status:** Working\n\n"
        f"😎 **Developer:** @cbxdq\n\n"
        f"Just send me a prompt to generate a video!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    
    # Initial Response
    status_msg = await update.message.reply_text(
        f"⚡ **Assembin...**\n🎬 **Prompt:** `{user_prompt}`",
        parse_mode='Markdown'
    )
    
    engine = WanBypass()
    video_url = await engine.generate_video(user_prompt)
    
    if video_url:
        caption = (
            f"✅ **Generation Complete!**\n\n"
            f"🤖 **Model:** {MODEL_NAME}\n"
            f"📝 **Prompt:** `{user_prompt}`\n\n"
            f"💀 * Powered By Chirag 😎*"
        )
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_url,
                caption=caption,
                parse_mode='Markdown'
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ **Error sending video:** {e}")
    else:
        await status_msg.edit_text("❌ **Bypass Failed.** Try a different prompt or wait a moment.")

# --- [ MAIN RUNNER ] ---
if __name__ == '__main__':
    # Start the Flask web server in the background for Render's health check
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Initialize the Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print(f"🚀 {MODEL_NAME} Bot is live and bypassing...")
    application.run_polling()
