from flask import Flask, request, render_template, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import requests
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
app = Flask(__name__)
TELEGRAM_TOKEN = "8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88"  # ← Ваш токен
ADMIN_CHAT_ID = "789334648"  # ← Ваш chat_id
bot = Bot(token=TELEGRAM_TOKEN)

# Хранение пользователей
AUTHORIZED_USERS = {}

# --- Команды бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    AUTHORIZED_USERS[user.id] = {"username": user.username}
    await update.message.reply_text("Привет! Заявка будет обработана.")
    logger.info(f"Пользователь {user} начал взаимодействие.")

async def get_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = requests.get('https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB ').json()
        rate = data.get('RUB', 'Ошибка')
        if rate != 'Ошибка':
            await update.message.reply_text(f"Курс USDT/RUB: {rate:.2f}")
        else:
            await update.message.reply_text("Не удалось получить курс.")
    except Exception as e:
        logger.error(f"Ошибка получения курса: {e}")
        await update.message.reply_text("Ошибка сети")

# --- Создание Telegram-приложения ---
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("get_rate", get_rate))

# --- Роуты сайта ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        amount = request.form.get('amount')
        wallet = request.form.get('wallet')
        user_chat_id = request.form.get('user_chat_id')

        message = f"🔔 Новая заявка\nСумма USDT: {amount}\nКошелек: {wallet}"
        asyncio.run(bot.send_message(chat_id=ADMIN_CHAT_ID, text=message))

        if user_chat_id and int(user_chat_id) in AUTHORIZED_USERS:
            asyncio.run(bot.send_message(
                chat_id=int(user_chat_id),
                text="✅ Ваша заявка принята!"
            ))

        return jsonify({
            'message': 'Заявка отправлена!',
            'error': False,
            'order_amount': amount,
            'order_wallet': wallet
        })

    return render_template('index.html')


# --- Webhook для Telegram ---
@app.route('/telegram-webhook', methods=['POST'])
async def telegram_webhook():
    update = Update.de_json(request.get_json(), bot)
    await telegram_app.process_update(update)
    return '', 200


# --- Точка входа ---
if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()

    async def set_and_run():
        await telegram_app.initialize()  # ✅ Обязательная инициализация

        WEBHOOK_URL = "https://crypto-exchange-10.onrender.com/telegram-webhook "
        await telegram_app.bot.set_webhook(url=WEBHOOK_URL)

        app.run(debug=False, host='0.0.0.0', port=5000)

    asyncio.run(set_and_run())
