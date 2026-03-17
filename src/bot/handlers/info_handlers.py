from bot.handlers.common import main_menu
from telebot import types

def register_info_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'info')
    def handle_info_callback(call):
        """Handler to process callback_data='info' and display information about the service."""
        about_message = (
            "Добро пожаловать в наш сервис!\n\n"
            "Мы предоставляем удобные и надежные решения для бронирования поездок, оплаты и управления транспортом.\n"
            "Если у вас есть вопросы, свяжитесь с нашей службой поддержки."
        )
        bot.send_message(call.message.chat.id, about_message, reply_markup=main_menu())


