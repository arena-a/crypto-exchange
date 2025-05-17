from flask import Flask, request, render_template, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
from threading import Thread
import asyncio
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
app = Flask(__name__)
TELEGRAM_TOKEN = "8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88"  # Убедитесь, что токен верный
ADMIN_CHAT_ID = "789334648"  # Убедитесь, что ID верный
bot = Bot(token=TELEGRAM_TOKEN)

# Создаём цикл событий для асинхронных вызовов
loop = asyncio.new_event_loop()
Thread(target=loop.run_forever, daemon=True).start()

# Функции для обработки команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /start от {update.message.chat_id}")
    await context.bot.send_message(chat_id=update.message.chat_id, text="Добро пожаловать! Используйте /get_rate для курса или /check_orders для проверки заявок.")

async def get_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /get_rate от {update.message.chat_id}")
    try:
        response = requests.get('https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB')
        data = response.json()
        if data.get('RUB'):
            rate = data['RUB']
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"Текущий курс USDT/RUB: {rate:.2f}")
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text="Ошибка получения курса.")
    except Exception as e:
        logger.error(f"Ошибка API: {str(e)}")
        await context.bot.send_message(chat_id=update.message.chat_id, text="Ошибка сети.")

async def check_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получена команда /check_orders от {update.message.chat_id}")
    await context.bot.send_message(chat_id=update.message.chat_id, text="Функция проверки заявок пока не реализована. Скоро будет доступна!")

# Настройка приложения Telegram
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("get_rate", get_rate))
application.add_handler(CommandHandler("check_orders", check_orders))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            logger.info("Получен POST-запрос на обработку заявки.")
            amount = request.form.get('amount')
            wallet = request.form.get('wallet')

            if not all([amount, wallet]):
                return jsonify({'message': 'Заполните все поля!', 'error': True})

            # Формирование сообщения
            message = (
                f"Новая заявка\n"
                f"Сумма USDT: {amount}\n"
                f"Кошелек для RUB: {wallet}"
            )
            logger.info(f"Сформировано сообщение для Telegram: {message}")

            # Отправка в Telegram
            future = asyncio.run_coroutine_threadsafe(
                bot.send_message(chat_id=ADMIN_CHAT_ID, text=message), loop
            )
            response = future.result(timeout=10)
            logger.info(f"Telegram-ответ: {response}")

            return jsonify({'message': 'Заявка отправлена в Telegram!', 'error': False, 'show_order': True, 'order_amount': amount, 'order_wallet': wallet})
        except Exception as e:
            logger.error(f"Ошибка обработки заявки: {str(e)}")
            return jsonify({'message': f'Ошибка: {str(e)}', 'error': True})

    return render_template('index.html')

# Обработка обновлений Telegram
@app.route('/telegram-webhook', methods=['POST'])
async def telegram_webhook():
    update = Update.de_json(request.get_json(), bot)
    await application.process_update(update)
    return '', 200

if __name__ == '__main__':
    logger.info("Flask-сервер запущен.")
    app.run(debug=False, host='0.0.0.0', port=5000)