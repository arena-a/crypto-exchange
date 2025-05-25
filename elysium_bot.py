import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ApplicationBuilder,
)

# рофл, пацан, логируем всё, чтобы не офанареть!
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# рофл, тут наш Flask, чтобы не рухнул к чертям
app = Flask(__name__, static_folder='static', template_folder='templates')

# храним время команд, чтобы спамеры не трынде́ли
last_command_time = {}

# рофл, корневой маршрут, чтобы игра грузилась
@app.route('/')
def index():
    logger.info("доступ к корневому маршруту /")
    try:
        return app.send_static_file('elysium_game.html')  # рофл, отдаём HTML с игрой!
    except Exception as e:
        logger.error(f"пиздец с файлом: {e}")
        return "файл не найден, братишка, чекни templates!", 404

# рофл, маршрут для вебхука, теперь синхронный, сука!
@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    logger.info("получен запрос на вебхук")
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)
    return '', 200

# рофл, команда /start, чтобы пацаны знали, что делать
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = datetime.now()
    if user_id in last_command_time and now - last_command_time[user_id] < timedelta(seconds=10):
        return  # спам-фильтр, а то пиздец!
    last_command_time[user_id] = now
    await update.message.reply_text("добро пожаловать в Elysium! /play — начни игру в мрачном подвале")
    # РОФЛ-КОММЕНТ: если бот молчит, пиздец, чекни токен и сеть!

# рофл, команда /play, чтобы братаны могли рвать подвал
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = datetime.now()
    if user_id in last_command_time and now - last_command_time[user_id] < timedelta(seconds=10):
        return  # спам-фильтр, а то пиздец!
    last_command_time[user_id] = now
    web_app_url = os.getenv("WEB_APP_URL", "https://elysium-game.onrender.com")
    await update.message.reply_text(
        "спустись в подвал Elysium! собери свитки NFT 👹",
        reply_markup={"inline_keyboard": [[{"text": "Играть", "web_app": {"url": web_app_url}}]]}
    )
    # РОФЛ-КОММЕНТ: если игра не грузит, пиздец, чекни WEB_APP_URL!

# рофл, инициализация бота, чтобы всё завелось
logger.info("инициализация бота Elysium")
token = os.getenv("TELEGRAM_TOKEN", "7756024049:AAFoN1mPyIO0BWWOnikB6nv4FL3vb-5F8wo")
if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
    logger.error("пиздец, токен не задан, братишка, возьми у BotFather!")
    raise ValueError("токен не задан, чекни переменные окружения!")
bot = ApplicationBuilder().token(token).build()
application = bot

# рофл, добавляем команды, чтобы пацаны не скучали
bot.add_handler(CommandHandler("start", start))
bot.add_handler(CommandHandler("play", play))

# рофл, запускаем всё, чтобы Render не трынде́л
if __name__ == "__main__":
    logger.info("устанавливаю вебхук: https://elysium-game.onrender.com/telegram-webhook")
    bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),  # порт от Render, сука!
        url_path="/telegram-webhook",
        webhook_url="https://elysium-game.onrender.com/telegram-webhook",
    )
    logger.info("вебхук успешно установлен")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
