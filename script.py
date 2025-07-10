import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_URL = os.getenv("APP_URL")  # e.g., https://lumos-bot.onrender.com
PORT = int(os.environ.get("PORT", 8443))

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Memory
conversation_memory = {}
user_model_choice = {}

# === Safe Reply ===
async def safe_send_message(update: Update, text: str):
    max_length = 4096
    for i in range(0, len(text), max_length):
        await update.message.reply_text(text[i:i + max_length])

# === Gemini API ===
def call_gemini(nconversation, chatbot_prompt, solver, api_key):
    chat_parts = [{"text": chatbot_prompt}]
    for turn in nconversation:
        chat_parts.append({"text": turn["content"]})
    chat_parts.append({"text": solver})

    payload = {"contents": [{"parts": chat_parts}]}
    try:
        res = requests.post(
            url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
            json=payload
        )
        data = res.json()
        if "candidates" not in data:
            err = data.get("error", {}).get("message", "Unknown error.")
            return f"❌ Gemini fail: {err}", nconversation
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        nconversation.append({"role": "user", "content": solver})
        nconversation.append({"role": "assistant", "content": reply})
        return reply, nconversation
    except Exception as e:
        return f"❌ Gemini error: {str(e)}", nconversation

# === Grok API ===
def call_grok(nconversation, chatbot_prompt, solver, api_key):
    prompt = chatbot_prompt + "\n" + "\n".join(f"{t['role']}: {t['content']}" for t in nconversation) + f"\nuser: {solver}"
    try:
        res = requests.post(
            url="https://api.grok.x.com/v1/chat",  # Replace with actual Grok endpoint
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "grok-1", "prompt": prompt, "max_tokens": 512, "temperature": 0.7}
        )
        data = res.json()
        reply = data.get("reply", "🤐 Grok didn't say anything.")
        nconversation.append({"role": "user", "content": solver})
        nconversation.append({"role": "assistant", "content": reply})
        return reply, nconversation
    except Exception as e:
        return f"❌ Grok error: {str(e)}", nconversation

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    user_model_choice[chat_id] = "gemini"
    await update.message.reply_text("👋 Yo! I’m Lumos, your savage AI with desi swag. Use /model to switch AI engines 🔄")

# === /help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Send me a message. Use /model gemini or /model grok to switch AI brains 🧠")

# === /model ===
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    args = context.args
    if not args:
        current = user_model_choice.get(chat_id, "gemini")
        await update.message.reply_text(f"🤖 You're currently using: {current}")
        return
    chosen = args[0].lower()
    if chosen in ["gemini", "grok"]:
        user_model_choice[chat_id] = chosen
        await update.message.reply_text(f"✅ Switched to {chosen.upper()}")
    else:
        await update.message.reply_text("❌ Unknown model. Use /model gemini or /model grok")

# === Text Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    user_msg = update.message.text
    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []
    if chat_id not in user_model_choice:
        user_model_choice[chat_id] = "gemini"

    selected_model = user_model_choice[chat_id]
    chatbot_prompt = (
        "You’re Lumosbot — a smart, savage AI with desi swag. Keep it very short, witty, and straight to the point. "
        "Drop facts, crack jokes, no bhashan. Act cool, reply cooler. 😎"
    )

    if selected_model == "grok":
        response, convo = call_grok(conversation_memory[chat_id], chatbot_prompt, user_msg, GROK_API_KEY)
    else:
        response, convo = call_gemini(conversation_memory[chat_id], chatbot_prompt, user_msg, GEMINI_API_KEY)

    conversation_memory[chat_id] = convo
    await safe_send_message(update, response)

# === Error Handler ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

# === Main ===
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Webhook setup for Render
    webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=webhook_url
    )

# === Run App ===
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
