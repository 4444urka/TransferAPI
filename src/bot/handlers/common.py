from telebot import types

def auth_keyboard():
    """
    Возвращает reply-клавиатуру для отправки номера
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить номер", request_contact=True))
    return markup

def main_menu():
    """
    Формирует основное inline-меню.
    """
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🚖 Мои бронирования", callback_data='bookings'),
        types.InlineKeyboardButton("🚪 Выйти", callback_data='logout')
    )
    markup.row(
        types.InlineKeyboardButton("💬 Оставить отзыв", callback_data='feedback'),
        types.InlineKeyboardButton("📅 О нас", callback_data='info')
    )
    return markup


def start_keyboard():
    """
    Возвращает клавиатуру для старта бота.
    """
    webapp = types.WebAppInfo(url="https://dfbe-51-15-184-156.ngrok-free.app/login/")  
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💬 Оставить отзыв"))
    markup.add(types.KeyboardButton("📱 Войти", web_app=webapp))
    return markup

