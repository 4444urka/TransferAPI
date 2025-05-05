from telebot import types
from datetime import datetime
from bot.api import ApiClient
from bot.setup import config
from bot.handlers.common import main_menu, auth_keyboard
from bot.tools import show_bookings
import logging

logger = logging.getLogger('bot.booking_handlers')  # More specific logger name



def register_booking_handlers(bot):
    logger.info("Registering booking handlers")
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_booking(call):
        try:
            chat_id = call.message.chat.id
            logger.debug(f"Received callback query: {call.data} from user {chat_id}")
            user_data = config.get_user_data(chat_id)
            
            if call.data == 'bookings':
                # Initial authorization check
                logger.info(f'Checking user authorization for chat_id: {chat_id}')
                if not user_data or not user_data.get('refresh'):
                    logger.warning(f"Unauthorized access attempt: {chat_id}")
                    bot.send_message(chat_id, "❌ Требуется авторизация!", reply_markup=auth_keyboard())
                    return

                # Attempting to get bookings with current token
                logger.debug(f"Fetching bookings for user: {chat_id}")
                access_token = user_data.get('access', '')
                response = ApiClient.get_bookings(access_token)
                
                # If token is expired, try to refresh
                if not response:
                    logger.info(f"Token refresh initiated for: {chat_id}")
                    try:
                        new_tokens = ApiClient.refresh_tokens(user_data['refresh'])
                    except KeyError:
                        logger.error("Refresh token missing in user_data")
                        bot.send_message(chat_id, "❌ Сессия устарела, войдите снова", reply_markup=auth_keyboard())
                        return
                    except Exception as e:
                        logger.error(f"Refresh failed: {str(e)}", exc_info=True)
                        bot.send_message(chat_id, "🔒 Ошибка авторизации, войдите снова", reply_markup=auth_keyboard())
                        return

                    if new_tokens and 'access' in new_tokens and 'refresh' in new_tokens:
                        # Update tokens and retry request
                        logger.info(f"Tokens successfully refreshed for user {chat_id}")
                        config.store_user_data(chat_id, {
                            'access': new_tokens['access'],
                            'refresh': new_tokens['refresh']
                        })
                        logger.debug(f"Retrying booking fetch with new token: {chat_id}")
                        response = ApiClient.get_bookings(new_tokens['access'])
                    else:
                        logger.warning(f"Received invalid tokens during refresh: {new_tokens}")

                # Process final result
                if response:
                    logger.info(f"Successfully retrieved bookings for user {chat_id}")
                    logger.debug(f"Booking data: {response}")
                    text = show_bookings(response)
                    bot.send_message(chat_id, text, reply_markup=main_menu())
                else:
                    logger.warning(f"Failed to retrieve bookings for user {chat_id}")
                    bot.send_message(chat_id, "❌ Нет активных бронирований или ошибка доступа")

            elif call.data == 'logout':
                logger.info(f"User {chat_id} is logging out")
                config.delete_user_data(chat_id)
                bot.answer_callback_query(call.id, "✅ Вы успешно вышли!")
                bot.send_message(chat_id, "Для повторного входа авторизуйтесь:", reply_markup=auth_keyboard())
                logger.debug(f"User {chat_id} successfully logged out")
            else:
                logger.warning(f"Unknown callback query: {call.data} from user {chat_id}")

        except Exception as e:
            logger.critical(f"Critical error in booking handler: {str(e)}", exc_info=True)
            try:
                bot.send_message(chat_id, "⚠️ Произошла внутренняя ошибка, попробуйте позже")
                logger.debug("Error message sent to user")
            except Exception as send_error:
                logger.error(f"Failed to send error message: {str(send_error)}")