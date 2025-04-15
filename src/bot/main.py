import os
import sys
import django
import logging
import time
import logging.config
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from config.logging import LOGGING
from bot.setup import config
from telebot import TeleBot
from bot.handlers.auth_handlers import register_auth_handlers
from bot.handlers.booking_handlers import register_booking_handlers

# Применяем конфигурацию логирования из config/logging.py
logging.config.dictConfig(LOGGING)

# Получаем логгер для бота
logger = logging.getLogger('bot')

def setup_bot():
    logger.debug("Setting up Telegram bot...")
    bot = TeleBot(config.BOT_TOKEN)
    register_auth_handlers(bot)
    register_booking_handlers(bot)
    return bot

def start_bot():
    logger.debug("Starting Telegram bot...")
    bot = setup_bot()
    logger.info("Telegram bot started successfully!")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)
            time.sleep(5)

if __name__ == "__main__":
    logger.info("Bot script executed directly - starting bot...")
    start_bot()
else:
    logger.info("Bot module imported, not starting automatically")