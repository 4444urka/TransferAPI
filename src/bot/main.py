import os
import django
import logging
import time
from bot.setup import config
from telebot import TeleBot
from bot.handlers.auth_handlers import register_auth_handlers
from bot.handlers.booking_handlers import register_booking_handlers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

logger = logging.getLogger(__name__)

def setup_bot():
    # Инициализируем бот, но не запускаем его
    bot = TeleBot(config.BOT_TOKEN)
    register_auth_handlers(bot)
    register_booking_handlers(bot)
    return bot

def start_bot():
    bot = setup_bot()
    print("Telegram bot started...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_bot()