# Gemini Telegram Bot

A Telegram bot powered by Google's Gemini API, built with `python-telegram-bot` and deployed using webhooks. Ask it anything!

## Features

* Uses Gemini 2.0 Flash model via Google Generative Language API
* Sends long replies in Telegram-safe chunks
* Webhook-ready for deployment on platforms like Render or Heroku
* Structured using `python-telegram-bot v20.x`
* Secure API key management via `.env`

---

## 🚀 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/RoysonDsz/TelegramBot.git
cd gemini-telegram-bot
```

### 2. Create a `.env` file

Create a `.env` file in the root directory with the following variables:

```
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_API_KEY=your_telegram_bot_token_here
PORT=8443
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the bot (for deployment)

```bash
python script.py
```
