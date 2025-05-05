# crypto-exchange
Crypto Exchange Prototype 
Криптообменник с Telegram-ботом
Простой прототип криптообменника с уведомлениями в Telegram для всех подписчиков.
Установка

Клонируйте репозиторий:
git clone <https://github.com/arena-a/crypto-exchange.git>
cd <crypto-exchange>


Установите зависимости:
pip install -r requirements.txt


Настройте Telegram-бота:

Получите токен бота у @BotFather.
Замените YOUR_TELEGRAM_BOT_TOKEN в crypto_exchange.py на ваш токен.


Запустите приложение:
python crypto_exchange.py


Откройте http://127.0.0.1:5000 в браузере.


Использование

Сайт: Форма для подачи заявки на обмен (валюта, сумма, кошелек).
Telegram-бот: Используйте команду /start для подписки на уведомления. Все подписчики получают уведомления о новых заявках.

Работа с репозиторием в VS Code

Инициализация репозитория (если еще не создан):
git init
git add .
git commit -m "Initial commit"
git remote add origin <https://github.com/arena-a/crypto-exchange.git>
git push -u origin main


Обновление репозитория:

Откройте VS Code.
Внесите изменения в код.
Используйте панель "Source Control" (Ctrl+Shift+G):
Нажмите "Stage Changes" (иконка "+") для добавления измененных файлов.
Введите сообщение коммита и нажмите "Commit" (иконка галочки).
Нажмите "Push" для отправки изменений в удаленный репозиторий (иконка "...", затем "Push").




Получение обновлений:

Используйте команду "Pull" в панели "Source Control" для синхронизации с удаленным репозиторием.



Структура проекта

crypto_exchange.py: Основной код (Flask + Telegram-бот).
templates/index.html: HTML-шаблон формы.
subscribers.db: SQLite база данных (создается автоматически).
.gitignore: Игнорируемые файлы.
requirements.txt: Зависимости проекта.

