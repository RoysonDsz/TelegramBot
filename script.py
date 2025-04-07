import os
import requests
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")

# Corrected API URL for generateContent
MODEL_NAME = "models/gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

# Function to call Gemini API
def gemini_response(user_input):
    payload = {
        "contents": [{
            "parts": [{"text": user_input}]
        }]
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        try:
            # Extracting the first response
            full_reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response received.")

            # Splitting long responses
            MAX_MESSAGE_LENGTH = 4000
            messages = [full_reply[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(full_reply), MAX_MESSAGE_LENGTH)]
            return messages

        except IndexError:
            return ["No valid response received from Server."]
    else:
        return [f"API Error: {response.status_code} - {response.text}"]

# Telegram Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your AI bot , engineered by Royson Dsz. Ask me anything!")

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    bot_replies = gemini_response(user_message)  # Call Gemini API

    # Sending messages in chunks
    for reply in bot_replies:
        await update.message.reply_text(reply)

# Main function to run the bot
def main():
    app = Application.builder().token(TELEGRAM_API_KEY).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")

    # Corrected webhook configuration
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        url_path=TELEGRAM_API_KEY,
        webhook_url=f"https://telegrambot-aig0.onrender.com/{TELEGRAM_API_KEY}"
    )

if __name__ == "__main__":
    main()
