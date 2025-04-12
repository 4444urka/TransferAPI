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
        try:
            chat_id = call.message.chat.id
            user_data = config.get_user_data(chat_id)
            
            if call.data == 'bookings':
                # Первичная проверка авторизации
                if not user_data or not user_data.get('refresh'):
                    logger.warning(f"Unauthorized access attempt: {chat_id}")
                    bot.send_message(chat_id, "❌ Требуется авторизация!", reply_markup=auth_keyboard())
                    return

                # Попытка получить бронирования с текущим токеном
                access_token = user_data.get('access', '')
                response = ApiClient.get_bookings(access_token)
                
                # Если токен устарел, пробуем обновить
                if not response:
                    logger.info(f"Token refresh initiated for: {chat_id}")
                    try:
                        new_tokens = ApiClient.refresh_tokens(user_data['refresh'])
                    except KeyError:
                        logger.error("Refresh token missing in user_data")
                        bot.send_message(chat_id, "❌ Сессия устарела, войдите снова", reply_markup=auth_keyboard())
                        return
                    except Exception as e:
                        logger.error(f"Refresh failed: {str(e)}")
                        bot.send_message(chat_id, "🔒 Ошибка авторизации, войдите снова", reply_markup=auth_keyboard())
                        return

                    if new_tokens and 'access' in new_tokens and 'refresh' in new_tokens:
                        # Обновляем данные и повторяем запрос
                        config.store_user_data(chat_id, {
                            'access': new_tokens['access'],
                            'refresh': new_tokens['refresh']
                        })
                        response = ApiClient.get_bookings(new_tokens['access'])

                # Обработка финального результата
                if response:
                    text = show_bookings(response)
                    bot.send_message(chat_id, text, reply_markup=main_menu())
                else:
                    bot.send_message(chat_id, "❌ Нет активных бронирований или ошибка доступа")

            elif call.data == 'logout':
                config.delete_user_data(chat_id)
                bot.answer_callback_query(call.id, "✅ Вы успешно вышли!")
                bot.send_message(chat_id, "Для повторного входа авторизуйтесь:", reply_markup=auth_keyboard())

        except Exception as e:
            logger.critical(f"Critical error in booking handler: {str(e)}", exc_info=True)
            bot.send_message(chat_id, "⚠️ Произошла внутренняя ошибка, попробуйте позже")