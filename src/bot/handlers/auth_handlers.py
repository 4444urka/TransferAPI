import logging
from telebot import types
from bot.api import ApiClient
from bot.setup import config
from bot.handlers.common import auth_keyboard, main_menu

logger = logging.getLogger(__name__)

def register_auth_handlers(bot):
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        logger.info(f"User {message.chat.id} started the bot.")
        bot.send_message(message.chat.id, "Для входа отправьте номер телефона:", reply_markup=auth_keyboard())

    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        logger.debug(f"Received contact from: {message.chat.id}")
        phone = f"+{message.contact.phone_number}"
        msg = bot.send_message(message.chat.id, "Введите пароль:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: process_password(m, phone))

    def process_password(message, phone):
        tokens = ApiClient.authenticate(phone, message.text)
        logger.debug(f"Trying to authenticate user: {message.chat.id}")
        if tokens:
            config.store_user_data(message.chat.id, {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'phone': phone
            })
            user_info = ApiClient.get_user_info(tokens["access"])
            user_id = user_info['id'] if user_info else None
            ApiClient.update_chat_id(tokens['access'], user_id, message.chat.id)
            logger.info(f"User {message.chat.id} authenticated successfully.")
            bot.send_message(message.chat.id, "✅ Авторизация успешна!", reply_markup=main_menu())
        else:
            logger.error(f"Authentication failed for user: {message.chat.id}")
            bot.send_message(message.chat.id, "❌ Ошибка авторизации", reply_markup=auth_keyboard())

    @bot.message_handler(commands=['logout'])
    def handle_logout(message):
        chat_id = message.chat.id
        user_data = config.get_user_data(chat_id)
        try:
            logger.debug(f"User {chat_id} logging out.")
            if user_data and user_data.get('access'):
                user_info = ApiClient.get_user_info(user_data["access"])
                user_id = user_info['id'] if user_info else None
                ApiClient.update_chat_id(user_data['access'], user_id)
            config.delete_user_data(chat_id)
            logger.info(f"User {chat_id} logged out successfully.")
            bot.send_message(chat_id, "✅ Все ваши данные удалены!")
        except Exception as e:
            logger.error(f"Error logging out user {chat_id}: {e}")
            bot.send_message(chat_id, "❌ Ошибка при выходе!")
