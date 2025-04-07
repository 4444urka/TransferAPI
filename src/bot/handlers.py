from telebot import types
from api import ApiClient 
from bot.setup import config
from datetime import datetime

def setup_handlers(bot):

    def auth_keyboard():
        """Reply-клавиатура для отправки контакта"""
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, 
            resize_keyboard=True
        )
        markup.add(types.KeyboardButton(
            "📱 Отправить номер", 
            request_contact=True
        ))
        return markup


    @bot.message_handler(commands=['start'])
    def handle_start(message):
        bot.send_message(message.chat.id, "Для входа отправьте номер телефона:", reply_markup=auth_keyboard())


    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        phone = message.contact.phone_number
        msg = bot.send_message(message.chat.id, "Введите пароль:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, lambda m: process_password(m, phone))


    def main_menu():
        """Inline-меню основное"""
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🚖 Мои бронирования", callback_data='bookings'),
            types.InlineKeyboardButton("🚪 Выйти", callback_data='logout')
        )
        return markup
    
    def process_password(message, phone):
        tokens = ApiClient.authenticate(phone, message.text)
        if tokens:
            config.store_user_data(message.chat.id, {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'phone': phone
            })
            user_id = ApiClient.get_user_info(tokens["access"])['id']
            ApiClient.update_chat_id(tokens['access'], user_id, message.chat.id)
            bot.send_message(message.chat.id, f"✅ Авторизация успешна!", reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "❌ Ошибка авторизации", reply_markup=auth_keyboard())


    @bot.message_handler(commands=['logout'])
    def handle_logout(message):
        chat_id = message.chat.id
        user_data = config.get_user_data(chat_id)
        
        try:
            # # Очищаем данные в Django
            if user_data and user_data.get('access'):
                user_id = ApiClient.get_user_info(user_data["access"])['id']
                ApiClient.update_chat_id(user_data['access'], user_id)
            
            # Удаляем данные из Redis
            config.delete_user_data(chat_id)
            
            bot.send_message(chat_id, "✅ Все ваши данные удалены!")
        except:
            bot.send_message(chat_id, "❌ Ошибка при выходе!")


    def format_bookings_response(response):
        try:
            bookings = response.get('results', [])
            if not bookings:
                return "🚖 У вас пока нет активных бронирований"

            formatted = []
            for idx, booking in enumerate(bookings, 1):
                # Парсинг даты и времени
                dt = datetime.fromisoformat(booking['booking_datetime'])
                booking_date = dt.strftime("%d.%m.%Y %H:%M")
                
                # Статус бронирования
                status = "✅ Активно" if booking['is_active'] else "❌ Отменено"
                
                # Форматирование цены
                price = f"{int(booking['total_price'])} руб." if booking['total_price'].is_integer() else f"{booking['total_price']:.2f} руб."

                # Сборка сообщения
                text = (
                    f"🚖 Бронирование #{idx}\n"
                    f"📅 Дата: {booking_date}\n"
                    f"📍  Откуда: {booking['pickup_location']}\n"
                    f"🏁 Куда: {booking['dropoff_location']}\n"
                    f"💵 Стоимость: {price}\n"
                    # f"💺 Места: {seats_info if seats_info else 'Не указаны'}\n"
                    f"🔹 Статус: {status}"
                )
                formatted.append(text)

            header = f"🚖 Найдено бронирований: {len(bookings)}\n\n"
            return header + "\n\n".join(formatted)

        except Exception as e:
            print(f"Ошибка форматирования: {str(e)}")
            return "⚠️ Не удалось получить информацию о бронированиях"

    @bot.callback_query_handler(func=lambda call: True)
    def handle_booking(call):
        chat_id = call.message.chat.id
        user_data = config.get_user_data(chat_id)
        if call.data == 'bookings':
            if not user_data:
                return bot.send_message(
                    chat_id, 
                    "❌ Требуется авторизация!",    
                    reply_markup=auth_keyboard()
                )
            
            response = ApiClient.get_bookings(user_data['access'])
            if not response:
                new_token = ApiClient.refresh_token(user_data['refresh'])
                if new_token:
                    config.store_user_data(chat_id, {'access': new_token['access']})
                    response = ApiClient.get_bookings(new_token['access'])
            
            if response:
                text = format_bookings_response(response)

                bot.send_message(chat_id, text, reply_markup=main_menu())
            else:
                bot.send_message(chat_id, "❌ Нет активных бронирований")
        elif call.data == 'logout':
            config.delete_user_data(chat_id)
            bot.answer_callback_query(call.id, "✅ Вы успешно вышли!")
            bot.send_message(
                chat_id, 
                "Для повторного входа авторизуйтесь:",
                reply_markup=auth_keyboard()
            )

            



