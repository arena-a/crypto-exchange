from flask import Flask, request, render_template
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import sqlite3
import uuid
from threading import Thread
import logging
import atexit

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
app = Flask(__name__)
TELEGRAM_TOKEN = "8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88"  # Замените на ваш токен
bot = Bot(token=TELEGRAM_TOKEN)

# Глобальная переменная для управления ботом
bot_loop = None
bot_app = None

# Инициализация базы данных SQLite
def init_db():
    try:
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscribers (chat_id INTEGER PRIMARY KEY)''')
        conn.commit()
        logger.info("База данных инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
    finally:
        conn.close()

init_db()

# Flask: Главная страница
@app.route('/')
def index():
    logger.info("Открыта главная страница.")
    return render_template('index.html')

# Flask: Обработка заявки
@app.route('/submit', methods=['POST'])
def submit():
    try:
        logger.info("Получен запрос на обработку заявки.")
        from_currency = request.form['from_currency']
        to_currency = request.form['to_currency']
        amount = request.form['amount']
        wallet = request.form['wallet']
        order_id = str(uuid.uuid4())[:8]

        # Формирование сообщения
        message = (
            f"Новая заявка #{order_id}\n"
            f"Отдаете: {amount} {from_currency}\n"
            f"Получаете: {to_currency}\n"
            f"Кошелек: {wallet}"
        )
        logger.info(f"Сформировано сообщение: {message}")

        # Синхронный вызов уведомлений
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notify_subscribers(message))
        loop.close()

        logger.info(f"Заявка #{order_id} обработана.")
        return f"Заявка #{order_id} принята! Уведомления отправлены."
    except Exception as e:
        logger.error(f"Ошибка обработки заявки: {e}")
        return "Произошла ошибка при обработке заявки.", 500

# Telegram: Отправка уведомлений всем подписчикам
async def notify_subscribers(message):
    try:
        logger.info("Начало отправки уведомлений подписчикам.")
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("SELECT chat_id FROM subscribers")
        subscribers = c.fetchall()
        conn.close()

        if not subscribers:
            logger.info("Нет подписчиков для отправки уведомлений.")
        else:
            for chat_id in subscribers:
                try:
                    await bot.send_message(chat_id=chat_id[0], text=message)
                    logger.info(f"Уведомление отправлено в чат {chat_id[0]}")
                except Exception as e:
                    logger.error(f"Ошибка отправки в чат {chat_id[0]}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при получении подписчиков: {e}")

# Telegram: Команда /start для подписки
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat_id
        conn = sqlite3.connect('subscribers.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text("Вы подписаны на уведомления о заявках!")
        logger.info(f"Новый подписчик: {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка подписки: {e}")

# Запуск Telegram-бота в отдельном потоке с явным циклом событий
def run_bot():
    global bot_loop, bot_app
    try:
        bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(bot_loop)
        bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        logger.info("Telegram-бот запущен.")
        bot_loop.run_until_complete(bot_app.run_polling())
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        if bot_loop:
            bot_loop.close()

# Функция для корректного завершения бота
def shutdown_bot():
    global bot_app, bot_loop
    try:
        if bot_app:
            logger.info("Завершение работы бота...")
            bot_loop.run_until_complete(bot_app.stop())
            bot_loop.run_until_complete(bot_app.updater.stop())
            bot_loop.run_until_complete(bot_app.bot.session.close())
            logger.info("Бот успешно завершен.")
    except Exception as e:
        logger.error(f"Ошибка при завершении бота: {e}")

# Регистрация функции завершения
atexit.register(shutdown_bot)

if __name__ == '__main__':
    # Запуск Telegram-бота в отдельном потоке
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    # Запуск Flask
    logger.info("Flask-сервер запущен.")
    app.run(debug=False)