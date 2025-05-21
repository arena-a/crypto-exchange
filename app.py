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
TELEGRAM_TOKEN = "8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88"  # ← Замените на ваш токен
ADMIN_CHAT_ID = "789334648"  # ← Ваш chat_id для уведомлений
bot = Bot(token=TELEGRAM_TOKEN)

# Хранение пользователей
AUTHORIZED_USERS = {}  # Здесь будут храниться chat_id тех, кто написал /start

# --- Обработчики команд бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    AUTHORIZED_USERS[user.id] = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    logger.info(f"Пользователь {user} начал взаимодействие.")
    await update.message.reply_text("Добро пожаловать! Вы будете получать уведомления о заявках.")

async def get_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB ')
        data = response.json()
        rate = data.get('RUB', 'Ошибка')
        if rate != 'Ошибка':
            await update.message.reply_text(f"Курс USDT/RUB: {rate:.2f}")
        else:
            await update.message.reply_text("Не удалось получить курс. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка получения курса: {e}")
        await update.message.reply_text("Ошибка сети")

# --- Создание и запуск Telegram-бота ---
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

        if not all([amount, wallet]):
            return jsonify({'message': 'Заполните все поля!', 'error': True})

        message = (
            f"🔔 Новая заявка\n"
            f"Сумма USDT: {amount}\n"
            f"Кошелек RUB: {wallet}"
        )

        # Отправляем админу
        asyncio.run(bot.send_message(chat_id=ADMIN_CHAT_ID, text=message))

        # Отправляем клиенту, если он есть в списке
        if user_chat_id and int(user_chat_id) in AUTHORIZED_USERS:
            asyncio.run(bot.send_message(
                chat_id=int(user_chat_id),
                text="✅ Ваша заявка успешно отправлена!"
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

    # Установка webhook
    WEBHOOK_URL = "https://crypto-exchange-9.onrender.com/telegram-webhook "
    async def set_and_run():
        await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
        await telegram_app.start()
        await telegram_app.updater.stop()  # Важно для Render
        await app.run_task(host='0.0.0.0', port=5000)

    asyncio.run(set_and_run())
