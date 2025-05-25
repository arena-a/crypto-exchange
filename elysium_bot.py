import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, render_template
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ⚙️ Логируем как хакеры
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 🧠 Flask-приложение
app = Flask(__name__, static_folder='static', template_folder='templates')

# 🛡️ анти-спам
last_command_time = {}

@app.route('/')
def index():
    logger.info("Запрошен / - отдаём игру")
    try:
        return render_template('elysium_game.html')
    except Exception as e:
        logger.error(f"Ошибка загрузки шаблона: {e}")
        return "Ошибка загрузки игры", 500

@app.route('/telegram-webhook', methods=['POST'])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return '', 200

# 💬 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Добро пожаловать в Elysium! Используй /play чтобы начать игру!")

# 🎮 /play
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = datetime.now()

    if user_id in last_command_time and now - last_command_time[user_id] < timedelta(seconds=10):
        return

    last_command_time[user_id] = now

    web_app_url = os.getenv("WEB_APP_URL", "https://elysium-game.onrender.com")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🎮 Играть", web_app=WebAppInfo(url=web_app_url))]
    ])

    await update.message.reply_text(
        "🧿 Вход в подвал Elysium... Собери все 3 свитка!",
        reply_markup=keyboard
    )

# 📡 Инициализация бота
token = os.getenv("TELEGRAM_TOKEN", "")
if not token:
    raise ValueError("TELEGRAM_TOKEN не задан!")

application = Application.builder().token(token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("play", play))

async def initialize_app():
    await application.initialize()
    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        url_path="/telegram-webhook",
        webhook_url=os.getenv("WEBHOOK_URL", "https://elysium-game.onrender.com/telegram-webhook")
    )

# 🧨 Старт
if __name__ == "__main__":
    with app.app_context():
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(initialize_app())
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
