import logging
from telebot import types
from bot.api import ApiClient
from bot.handlers.common import start_keyboard, main_menu
from bot.setup import config

logger = logging.getLogger(__name__)

def register_feedback_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "💬 Оставить отзыв")
    @bot.callback_query_handler(func=lambda call: call.data == 'feedback')
    def handle_feedback_request(event):
        if isinstance(event, types.Message):
            chat_id = event.chat.id
        elif isinstance(event, types.CallbackQuery):
            chat_id = event.message.chat.id
        else:
            logger.error("Unexpected event type")
            return

        logger.info(f"User {chat_id} wants to leave feedback.")
        user_data = config.get_user_data(chat_id)
        markup = main_menu() if user_data else start_keyboard()  
        msg = bot.send_message(chat_id, "Напишите отзыв о работе сервиса:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: handle_feedback_submission(m, markup))

    def handle_feedback_submission(message, markup):
        logger.info(f"Feedback received from user {message.chat.id}: {message.text}")
        try:
            ApiClient.send_feedback(message.chat.id, message.text)
            logger.info(f"Feedback successfully sent for user {message.chat.id}.")
        except Exception as e:
            logger.error(f"Error sending feedback for user {message.chat.id}: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при отправке отзыва. Попробуйте позже.")
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
            return
        bot.send_message(message.chat.id, "✅ Спасибо за оставленный отзыв!")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
