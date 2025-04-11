from telebot import types
from datetime import datetime
from bot.api import ApiClient
from bot.setup import config
from bot.handlers.common import main_menu, auth_keyboard
from bot.tools import show_bookings
import logging

logger = logging.getLogger(__name__)



def register_booking_handlers(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_booking(call):
        chat_id = call.message.chat.id
        user_data = config.get_user_data(chat_id)
        if call.data == 'bookings':
            if not user_data:
                logger.warning(f"User {chat_id} is not authorized")
                return bot.send_message(chat_id, "❌ Требуется авторизация!", reply_markup=auth_keyboard())
            response = ApiClient.get_bookings(user_data['access'])
            if not response:
                logger.info(f"Access token expired for user {chat_id}, refreshing...")
                new_token = ApiClient.refresh_tokens(user_data['refresh'])
                if new_token:
                    logger.info(f"Tokens refreshed for user {chat_id}")
                    config.store_user_data(chat_id, {'refresh': new_token['refresh'], 'access': new_token['access']})
                    response = ApiClient.get_bookings(new_token['access'])
            if response:
                text = show_bookings(response)
                bot.send_message(chat_id, text, reply_markup=main_menu())
            else:
                bot.send_message(chat_id, "❌ Нет активных бронирований")
        elif call.data == 'logout':
            config.delete_user_data(chat_id)
            bot.answer_callback_query(call.id, "✅ Вы успешно вышли!")
            bot.send_message(chat_id, "Для повторного входа авторизуйтесь:", reply_markup=auth_keyboard())
