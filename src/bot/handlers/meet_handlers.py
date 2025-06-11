from telebot import types
import logging
from bot.handlers.common import start_keyboard

logger = logging.getLogger(__name__)


def register_meet_handlers(bot):
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        logger.info(f"User {message.chat.id} started the bot.")
        bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=start_keyboard())
    