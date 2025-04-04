import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import telebot
from bot.setup import config
from bot.handlers import setup_handlers 

bot = telebot.TeleBot(config.BOT_TOKEN)

def start():
    setup_handlers(bot)
    print("Telegram bot started...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    start()