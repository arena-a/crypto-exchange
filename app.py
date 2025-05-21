import os
import logging
import asyncio
import nest_asyncio
import requests

from flask import Flask, request, render_template, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройки
TELEGRAM_TOKEN = os.environ.get("8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88")
ADMIN_CHAT_ID = os.environ.get("789334648")  # пример: "789334648"
bot = Bot(token=TELEGRAM_TOKEN)

# Flask-приложение
app = Flask(__name__)

# Telegram bot app
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в CryptoDropBot!")

# Команда /get_rate
async def get_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get('https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB')
        rate = res.json().get('RUB', 'Неизвестно')
        await update.message.reply_text(f"Курс USDT/RUB: {rate}")
    except Exception as e:
        await update.message.reply_text("Ошибка при получении курса.")

# Регистрируем команды
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("get_rate", get_rate))

# HTML форма
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        amount = request.form.get('amount')
        wallet = request.form.get('wallet')
        user_chat_id = request.form.get('user_chat_id')

        if not amount or not wallet:
            return jsonify({'message': 'Все поля обязательны', 'error': True})

        message = f"🔔 Новая заявка\nСумма USDT: {amount}\nКошелек RUB: {wallet}"
        asyncio.create_task(bot.send_message(chat_id=ADMIN_CHAT_ID, text=message))

        if user_chat_id:
            asyncio.create_task(bot.send_message(chat_id=int(user_chat_id), text="✅ Ваша заявка отправлена!"))

        return jsonify({'message': 'OK', 'error': False})

    return render_template("index.html")

# Обработка Telegram Webhook
@app.route('/telegram-webhook', methods=['POST'])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await telegram_app.process_update(update)
    return '', 200

# Запуск приложения
if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(telegram_app.initialize())
    asyncio.run(bot.set_webhook("https://crypto-exchange-12.onrender.com/telegram-webhook"))
    telegram_app.run_task()
    app.run(host="0.0.0.0", port=5000)
