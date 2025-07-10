import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# Load environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_URL = os.getenv("APP_URL")

# Logging
logging.basicConfig(level=logging.INFO)

conversation_memory = {}
user_model_choice = {}

# --- Gemini Call ---
def call_gemini(nconversation, chatbot_prompt, solver, api_key):
    chat_parts = [{"text": chatbot_prompt}]
    for turn in nconversation:
        chat_parts.append({"text": turn["content"]})
    chat_parts.append({"text": solver})

    payload = {"contents": [{"parts": chat_parts}]}
    try:
        response = requests.post(
            url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
            json=payload,
        )
        data = response.json()
        if "candidates" not in data:
            return "❌ Gemini API fail", nconversation

        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        nconversation.append({"role": "user", "content": solver})
        nconversation.append({"role": "assistant", "content": reply})
        return reply, nconversation
    except Exception as e:
        return f"Gemini error: {e}", nconversation

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_model_choice[str(update.effective_chat.id)] = "gemini"
    await update.message.reply_text("👋 Lumos here! Use /model grok or /model gemini to switch engines!")

# --- Model Command ---
async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip().lower()

    if "grok" in text:
        user_model_choice[chat_id] = "grok"
        await update.message.reply_text("✅ Switched to GROK")
    elif "gemini" in text:
        user_model_choice[chat_id] = "gemini"
        await update.message.reply_text("✅ Switched to GEMINI")
    else:
        current = user_model_choice.get(chat_id, "gemini")
        await update.message.reply_text(f"🤖 Current model: {current}")

# --- Message Handler ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_msg = update.message.text

    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []
    if chat_id not in user_model_choice:
        user_model_choice[chat_id] = "gemini"

    chatbot_prompt = "You’re Lumosbot — a smart, savage AI with desi swag. Keep it witty, short, and cool. 😎"

    if user_model_choice[chat_id] == "grok":
        reply, updated_convo = "Grok API not implemented yet", conversation_memory[chat_id]
    else:
        reply, updated_convo = call_gemini(
            conversation_memory[chat_id], chatbot_prompt, user_msg, GEMINI_API_KEY
        )

    conversation_memory[chat_id] = updated_convo
    await update.message.reply_text(reply[:4096])

# --- MAIN ---
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", model))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    PORT = int(os.environ.get("PORT", 8443))
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{APP_URL}/{TELEGRAM_TOKEN}",
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
