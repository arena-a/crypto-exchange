from flask import Flask, request, render_template, jsonify
from telegram import Bot
import logging
import os
from threading import Thread
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
app = Flask(__name__)
TELEGRAM_TOKEN = "8098295902:AAE8YxldfN-stCXWoA5HW9UUoKunkw2cj88"  # Замените на env-переменную в продакшене!
ADMIN_CHAT_ID = "789334648"  # Ваш chat_id (админ)
bot = Bot(token=TELEGRAM_TOKEN)

# Хранение chat_id пользователей (временное, лучше использовать БД)
AUTHORIZED_USERS = {}

# Асинхронная отправка сообщений в Telegram
async def send_async_message(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

# Синхронная обёртка для Flask
def send_telegram_message(chat_id, text):
    asyncio.run(send_async_message(chat_id, text))

# Роуты Flask
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.form
            amount = data.get('amount')
            wallet = data.get('wallet')
            user_chat_id = data.get('user_chat_id')

            if not all([amount, wallet]):
                return jsonify({'error': True, 'message': 'Заполните все поля!'})

            # Сообщение для админа (вас)
            admin_message = (
                "🚀 Новая заявка!\n"
                f"• Сумма USDT: {amount}\n"
                f"• Кошелек RUB: {wallet}\n"
                f"• Chat ID: {user_chat_id or 'не указан'}"
            )
            send_telegram_message(ADMIN_CHAT_ID, admin_message)

            # Сообщение для пользователя (если chat_id есть)
            if user_chat_id:
                user_message = (
                    "✅ Ваша заявка принята!\n"
                    f"• Сумма: {amount} USDT\n"
                    f"• Кошелек: {wallet}\n\n"
                    "Скоро с вами свяжутся!"
                )
                send_telegram_message(user_chat_id, user_message)

            return jsonify({
                'error': False,
                'message': 'Заявка отправлена!',
                'data': {'amount': amount, 'wallet': wallet}
            })

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return jsonify({'error': True, 'message': str(e)})

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
