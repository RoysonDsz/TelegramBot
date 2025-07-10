import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters # Updated import

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

# Safe reply - Make this async
async def safe_send_message(update: Update, text: str):
    max_length = 4096
    if len(text) <= max_length:
        await update.message.reply_text(text) # Await added
    else:
        for i in range(0, len(text), max_length):
            await update.message.reply_text(text[i:i + max_length]) # Await added

# === Gemini API === (No change needed here as requests is synchronous)
def call_gemini(nconversation, chatbot_prompt, solver, api_key):
    # ... (your existing call_gemini function remains the same, as requests is synchronous)
    # If you later switch to an async HTTP client like httpx, you'd make this async.
    pass # Placeholder for brevity

# === Grok API (dummy placeholder) === (No change needed here for requests)
def call_grok(nconversation, chatbot_prompt, solver, api_key):
    # ... (your existing call_grok function remains the same, as requests is synchronous)
    pass # Placeholder for brevity

# /start - Make this async
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # Updated ContextTypes
    chat_id = str(update.message.chat_id)
    user_model_choice[chat_id] = "gemini"  # default
    await update.message.reply_text("👋 Yo! I’m Lumos, your savage AI with desi swag. Use /model to switch AI engines 🔄") # Await added

# /help - Make this async
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # Updated ContextTypes
    await update.message.reply_text("🤖 Send messages to chat. Use /model gemini or /model grok to switch AI brains 🧠") # Await added

# /model command - Make this async
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE, force_model=None): # Updated ContextTypes
    chat_id = str(update.message.chat_id)

    if force_model:
        chosen_model = force_model
    else:
        # Check context.args for /model arguments
        if context.args:
            arg = context.args[0].lower()
            if arg == "grok":
                chosen_model = "grok"
            elif arg == "gemini":
                chosen_model = "gemini"
            else:
                current_model = user_model_choice.get(chat_id, "gemini")
                await update.message.reply_text(f"🤖 You're currently using: {current_model}. Use /model gemini or /model grok.")
                return
        else:
            current_model = user_model_choice.get(chat_id, "gemini")
            await update.message.reply_text(f"🤖 You're currently using: {current_model}. Use /model gemini or /model grok to switch.")
            return


    user_model_choice[chat_id] = chosen_model
    await update.message.reply_text(f"✅ Switched to {chosen_model.upper()}") # Await added

# Message handler - Make this async
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): # Updated ContextTypes
    chat_id = str(update.message.chat_id)
    user_msg = update.message.text

    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []
    if chat_id not in user_model_choice:
        user_model_choice[chat_id] = "gemini"  # default model

    selected_model = user_model_choice[chat_id]

    chatbot_prompt = "You’re Lumosbot — a smart, savage AI with desi swag. Keep it very very short, witty, and straight to the point. Drop facts, crack jokes, no bhashan. Act cool, reply cooler. 😎"

    # You might want to add a "bot is typing..." indicator here
    # await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    if selected_model == "grok":
        response, updated_convo = call_grok(
            conversation_memory[chat_id], chatbot_prompt, user_msg, GROK_API_KEY
        )
    else:
        response, updated_convo = call_gemini(
            conversation_memory[chat_id], chatbot_prompt, user_msg, GEMINI_API_KEY
        )

    conversation_memory[chat_id] = updated_convo
    await safe_send_message(update, response) # Await added

# Error handling - Make this async
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE): # Updated ContextTypes
    logging.error(msg="Unhandled exception:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("Whoops! Something went wrong on my end. The dev has been notified.")

# Main function needs to be async and run using asyncio
async def main():
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("model", model_command))
    # For these lambda handlers, they also need to be async or call an async function
    application.add_handler(CommandHandler("model_grok", lambda update, context: model_command(update, context, force_model="grok")))
    application.add_handler(CommandHandler("model_gemini", lambda update, context: model_command(update, context, force_model="gemini")))


    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) # Using filters.TEXT
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    print("🤖 Lumos is live with Gemini + Grok toggle power!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES) # Start polling
    # For a persistent deployment like Render, you might just need run_polling()
    # and let the process manager handle restarts if it crashes.
    # If you need to keep it running indefinitely without explicit idle, run_until_disconnected() might be used in more complex scenarios.


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) # This runs the async main function
