import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")  # if applicable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Store conversations + model choice
conversation_memory = {}
user_model_choice = {}

# Safe reply
def safe_send_message(update, text):
    max_length = 4096
    if len(text) <= max_length:
        update.message.reply_text(text)
    else:
        for i in range(0, len(text), max_length):
            update.message.reply_text(text[i:i + max_length])

# === Gemini API ===
def call_gemini(nconversation, chatbot_prompt, solver, api_key):
    chat_parts = [{"text": chatbot_prompt}]
    for turn in nconversation:
        chat_parts.append({"text": turn["content"]})
    chat_parts.append({"text": solver})

    payload = {"contents": [{"parts": chat_parts}]}

    try:
        response = requests.post(
            url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": api_key
            },
            json=payload
        )

        data = response.json()

        if "candidates" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown error from Gemini.")
            print(f"Gemini API Error: {error_msg}")
            return f"❌ Gemini API fail: {error_msg}", nconversation

        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        nconversation.append({"role": "user", "content": solver})
        nconversation.append({"role": "assistant", "content": reply})
        return reply, nconversation

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "❌ Gemini is down bad rn 😵. Try again later.", nconversation

# === Grok API (dummy placeholder) ===
def call_grok(nconversation, chatbot_prompt, solver, api_key):
    # If you have a real Grok API, update the URL and headers
    prompt_text = chatbot_prompt + "\n" + "\n".join(
        f"{turn['role']}: {turn['content']}" for turn in nconversation
    ) + f"\nuser: {solver}"

    try:
        response = requests.post(
            url="https://api.grok.x.com/v1/chat",  # Replace with real Grok endpoint
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "grok-1",  # Change this if needed
                "prompt": prompt_text,
                "max_tokens": 512,
                "temperature": 0.7
            }
        )

        data = response.json()
        reply = data.get("reply", "Grok didn't say anything 🤐")

        nconversation.append({"role": "user", "content": solver})
        nconversation.append({"role": "assistant", "content": reply})
        return reply, nconversation

    except Exception as e:
        print(f"Grok API Error: {e}")
        return "❌ Grok is acting sus rn 😐", nconversation

# /start
def start(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    user_model_choice[chat_id] = "gemini"  # default
    update.message.reply_text("👋 Yo! I’m Lumos, your savage AI with desi swag. Use /model to switch AI engines 🔄")

# /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Send messages to chat. Use /model gemini or /model grok to switch AI brains 🧠")

# /model command
def model_command(update: Update, context: CallbackContext, force_model=None):
    chat_id = str(update.message.chat_id)

    if force_model:
        chosen_model = force_model
    else:
        text = update.message.text.strip().lower()
        if "grok" in text:
            chosen_model = "grok"
        elif "gemini" in text:
            chosen_model = "gemini"
        else:
            current_model = user_model_choice.get(chat_id, "gemini")
            update.message.reply_text(f"🤖 You're currently using: {current_model}")
            return

    user_model_choice[chat_id] = chosen_model
    update.message.reply_text(f"✅ Switched to {chosen_model.upper()}")



# Message handler
def handle_message(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    user_msg = update.message.text

    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []
    if chat_id not in user_model_choice:
        user_model_choice[chat_id] = "gemini"  # default model

    selected_model = user_model_choice[chat_id]

    chatbot_prompt = "You’re Lumosbot — a smart, savage AI with desi swag. Keep it very very short, witty, and straight to the point. Drop facts, crack jokes, no bhashan. Act cool, reply cooler. 😎"

    if selected_model == "grok":
        response, updated_convo = call_grok(
            conversation_memory[chat_id], chatbot_prompt, user_msg, GROK_API_KEY
        )
    else:
        response, updated_convo = call_gemini(
            conversation_memory[chat_id], chatbot_prompt, user_msg, GEMINI_API_KEY
        )

    conversation_memory[chat_id] = updated_convo
    safe_send_message(update, response)

# Error handling
def error_handler(update: object, context: CallbackContext):
    logging.error(msg="Unhandled exception:", exc_info=context.error)

# Main
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("model", model_command))
    dp.add_handler(CommandHandler("model_grok", lambda update, context: model_command(update, context, force_model="grok")))
    dp.add_handler(CommandHandler("model_gemini", lambda update, context: model_command(update, context, force_model="gemini")))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    print("🤖 Lumos is live with Gemini + Grok toggle power!")
    updater.idle()

if __name__ == "__main__":
    main()