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
TELEGRAM_TOKEN = "8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88"
ADMIN_CHAT_ID = "789334648"
bot = Bot(token=TELEGRAM_TOKEN)

# Хранение chat_id пользователей
AUTHORIZED_USERS = {}

# Функции для обработки команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = user.id
    AUTHORIZED_USERS[chat_id] = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    logger.info(f"Пользователь {user} начал взаимодействие.")
    await update.message.reply_text("Добро пожаловать! Вы будете получать уведомления о ваших заявках.")

async def get_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB ')
        data = response.json()
        rate = data.get('RUB', 'Ошибка')
        await update.message.reply_text(f"Текущий курс USDT/RUB: {rate:.2f}")
    except Exception as e:
        await update.message.reply_text("Ошибка получения курса.")

async def check_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функция проверки заявок пока не реализована.")

# Настройка приложения Telegram
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("get_rate", get_rate))
telegram_app.add_handler(CommandHandler("check_orders", check_orders))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            logger.info("Получен POST-запрос на обработку заявки.")
            amount = request.form.get('amount')
            wallet = request.form.get('wallet')
            user_chat_id = request.form.get('user_chat_id')

            if not all([amount, wallet]):
                return jsonify({'message': 'Заполните все поля!', 'error': True})

            # Формирование сообщения админу
            message = (
                f"🔔 Новая заявка\n"
                f"Сумма USDT: {amount}\n"
                f"Кошелек для RUB: {wallet}"
            )
            logger.info(f"Сформировано сообщение для Telegram: {message}")

            # Отправляем вам (админу)
            asyncio.run(bot.send_message(chat_id=ADMIN_CHAT_ID, text=message))

            # Отправляем пользователю, если он есть в списке
            if user_chat_id and int(user_chat_id) in AUTHORIZED_USERS:
                asyncio.run(bot.send_message(
                    chat_id=int(user_chat_id),
                    text="✅ Ваша заявка успешно отправлена!"
                ))

            return jsonify({
                'message': 'Заявка отправлена в Telegram!',
                'error': False,
                'show_order': True,
                'order_amount': amount,
                'order_wallet': wallet
            })

        except Exception as e:
            logger.error(f"Ошибка обработки заявки: {str(e)}")
            return jsonify({'message': f'Ошибка: {str(e)}', 'error': True})

    return render_template('index.html')


# Обработка обновлений Telegram
@app.route('/telegram-webhook', methods=['POST'])
async def telegram_webhook():
    update = Update.de_json(request.get_json(), bot)
    await telegram_app.process_update(update)
    return '', 200


if __name__ == '__main__':
    WEBHOOK_URL = "https://crypto-exchange-5.onrender.com/telegram-webhook "
    asyncio.run(telegram_app.bot.set_webhook(url=WEBHOOK_URL))
    app.run(debug=False, host='0.0.0.0', port=5000)
