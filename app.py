import os
import logging
import asyncio
from flask import Flask, render_template, send_from_directory, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta

# отключаем debug-логи flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# настройки логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# переменные окружения (на Render задайте через Variables)
telegram_token = os.getenv("TELEGRAM_TOKEN", "7756024049:AAFoN1mPyIO0BWWOnikB6nv4FL3vb-5F8wo")  # токен бота
admin_chat_id = os.getenv("ADMIN_CHAT_ID", "789334648")  # ID админа
port = int(os.getenv("PORT", 5000))  # порт для Render

# инициализация
app = Flask(__name__, static_folder='static')
bot = Bot(token=telegram_token)
telegram_app = Application.builder().token(telegram_token).build()

# защита от спама команд
last_command_time = {}

# команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = datetime.now()
    if user_id in last_command_time and now - last_command_time[user_id] < timedelta(seconds=10):
        return
    last_command_time[user_id] = now
    await update.message.reply_text("добро пожаловать в Elysium! /play — начни игру в мрачном подвале")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = datetime.now()
    if user_id in last_command_time and now - last_command_time[user_id] < timedelta(seconds=10):
        return
    last_command_time[user_id] = now
    # на Render URL будет публичный, задайте его через переменные окружения или замените вручную
    web_app_url = os.getenv("WEB_APP_URL", "https://your-render-app.onrender.com")
    await update.message.reply_text(
        "спустись в подвал Elysium! собери свитки NFT 👹",
        reply_markup={"inline_keyboard": [[{"text": "Играть", "web_app": {"url": web_app_url}}]]}
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "вот что я умею:\n" \
              "/start — приветствие\n" \
              "/play — начать игру в Elysium\n" \
              "/help — список команд"
    await update.message.reply_text(message)

# регистрируем команды
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("play", play))
telegram_app.add_handler(CommandHandler("help", help))

# глобальный event loop
loop = asyncio.get_event_loop()

# инициализация бота
logger.info("инициализация бота Elysium")
loop.run_until_complete(bot.initialize())
loop.run_until_complete(telegram_app.initialize())

# настройка вебхука для Render
webhook_url = os.getenv("WEB_APP_URL", "https://your-render-app.onrender.com") + "/telegram-webhook"
logger.info(f"устанавливаю вебхук: {webhook_url}")
try:
    loop.run_until_complete(bot.set_webhook(webhook_url))
    logger.info("вебхук успешно установлен")
except Exception as e:
    logger.error(f"ошибка установки вебхука: {e}")

# flask роуты
@app.route("/")
def index():
    logger.info("доступ к корневому маршруту /")
    return render_template("elysium_game.html")

@app.route('/<path:path>')
def static_files(path):
    logger.info(f"доступ к статическому файлу: {path}")
    return send_from_directory('static', path)

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    logger.info("получен запрос на вебхук")
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        loop.run_until_complete(telegram_app.process_update(update))
        return "", 200
    except Exception as e:
        logger.error(f"ошибка в вебхуке Elysium: {e}")
        return "", 500

if __name__ == "__main__":
    # запускаем flask
    app.run(host="0.0.0.0", port=port)
