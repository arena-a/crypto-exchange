import os
import logging
import asyncio
import requests
from flask import Flask, request, render_template, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask_cors import CORS

# отключаем debug-логи flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# настройки логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# переменные окружения
telegram_token = os.environ.get("TELEGRAM_TOKEN")
admin_chat_id = os.environ.get("ADMIN_CHAT_ID")
port = int(os.environ.get("PORT", 10000))  # 10000 для render

if not telegram_token or not admin_chat_id:
    logger.error(f"TELEGRAM_TOKEN={telegram_token}, ADMIN_CHAT_ID={admin_chat_id}")
    raise ValueError("TELEGRAM_TOKEN или ADMIN_CHAT_ID не заданы")

# инициализация
app = Flask(__name__)
CORS(app)
bot = Bot(token=telegram_token)
telegram_app = Application.builder().token(telegram_token).connection_pool_size(20).build()

# команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("добро пожаловать в cryptodropbot!")

async def get_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get("https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB")
        rate = res.json().get("RUB", "неизвестно")
        await update.message.reply_text(f"курс USDT/RUB: {rate}")
    except Exception as e:
        await update.message.reply_text("ошибка при получении курса")

# регистрируем команды
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("get_rate", get_rate))

# глобальный event loop
loop = asyncio.get_event_loop()

# инициализация приложения и установка вебхука
logger.info("инициализация приложения")
loop.run_until_complete(telegram_app.initialize())
render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "https://crypto-exchange-12.onrender.com")
webhook_url = f"{render_url}/telegram-webhook"
logger.info(f"устанавливаю вебхук: {webhook_url}")
try:
    loop.run_until_complete(bot.set_webhook(webhook_url))
    logger.info("вебхук успешно установлен")
except Exception as e:
    logger.error(f"ошибка установки вебхука: {e}")

# функция для отправки сообщений (асинхронная)
async def send_message_async(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"ошибка отправки сообщения: {e}")

# flask роуты
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        amount = request.form.get("amount")
        wallet = request.form.get("wallet")
        user_chat_id = request.form.get("user_chat_id")

        if not amount or not wallet:
            return jsonify({"message": "все поля обязательны", "error": True})

        message = f"🔔 новая заявка\nсумма USDT: {amount}\nкошелек RUB: {wallet}"
        try:
            # запускаем асинхронные задачи без ожидания
            loop.create_task(send_message_async(admin_chat_id, message))
            if user_chat_id:
                loop.create_task(send_message_async(user_chat_id, "✅ ваша заявка отправлена!"))
            return jsonify({"message": "OK", "error": False})
        except Exception as e:
            logger.error(f"ошибка в обработке формы: {e}")
            return jsonify({"message": "ошибка сервера", "error": True})

    return render_template("index.html")

# вебхук для telegram (синхронный)
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        loop.run_until_complete(telegram_app.process_update(update))
        return "", 200
    except Exception as e:
        logger.error(f"ошибка в вебхуке: {e}")
        return "", 500

# запуск приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
