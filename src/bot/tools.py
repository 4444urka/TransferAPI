from datetime import datetime

# def get_cached_trips(access_token):
#     """
#     Получает список поездок из кеша (Redis). Если кеш отсутствует или просрочен,
#     делает запрос к API, сериализует и сохраняет результат в кеше, а затем возвращает список поездок.
    
#     Args:
#         access_token (str): Access-токен для авторизации при запросе к API.
        
#     Returns:
#         list: Список поездок (ожидается, что каждая поездка представлена как словарь).
#     """
#     if not access_token:
#         return []
#     cache_key = "active_trips_list"
#     trips = cache.get(cache_key)
#     if trips is None:
#         trips = ApiClient.get_trips(access_token=access_token)['results']
#         if trips is None:
#             trips = []
#         cache.set(cache_key, trips, timeout=300)
#     return trips

# def get_trip_by_id(trip_id, access_token):
#     """
#     Извлекает поездку с указанным ID из кэшированного списка поездок.
    
#     Args:
#         trip_id (int): Идентификатор поездки.
#         access_token (str): Access-токен для получения данных (используется внутри get_cached_trips).
        
#     Returns:
#         dict: Найденная поездка или None, если поездка не найдена.
#     """
#     trips = get_cached_trips(access_token)
#     for trip in trips:
#         if isinstance(trip, dict) and trip.get('id') == trip_id:
#             return trip
#     return None

def format_booking(index, booking):

    try:
        departure_time = booking['trip']['departure_time']
        dt = datetime.fromisoformat(departure_time)
        booking_date = dt.strftime("%d.%m.%Y %H:%M")
    except:
        booking_date = "N/A"

    status = "✅ Активно" if booking['is_active'] else "❌ Отменено"
    price = float(booking['total_price'])
    price_str = f"{int(price)} руб." if price == int(price) else f"{price:.2f} руб."
    # seats_info = ", ".join([str(ts['seat']['seat_number']) for ts in booking['trip_seats'].all()])
    seats = booking.get('seat_numbers', [])
    if seats:
        # Преобразуем все элементы списка в строки
        seats_info = ", ".join(str(seat) for seat in seats)
    else:
        seats_info = "Не указаны"    
    text = (
        f"🚖 Бронирование #{index}!\n"
        f"📅 Дата: {booking_date}\n"
        f"📍 Откуда: г. {booking['trip']['origin']['name']}, {booking['pickup_location']}\n"
        f"🏁 Куда: г. {booking['trip']['destination']['name']}, {booking['dropoff_location']}\n"
        f"💵 Стоимость: {price_str}\n"
        f"💺 Места: {seats_info if seats_info else 'Не указаны'}\n"
        f"🔹 Статус: {status}"
    )
    return text

def show_bookings(response):
    """
    Форматирует ответ API бронирований для отправки в Telegram.
    Для каждого бронирования извлекается ID поездки, затем через кешированные данные
    определяется время отправления поездки.
    
    Args:
        response (dict): Ответ API бронирований, содержащий поле 'results' с данными бронирований.
        access_token (str): Access-токен для работы с API (используется для получения списка поездок).
        
    Returns:
        str: Отформатированное сообщение для Telegram.
    """
    try:
        bookings = response.get('results', [])
        if not bookings:
            return "🚖 У вас пока нет активных бронирований"
        formatted = []
        for idx, booking in enumerate(bookings, 1):
            # # trip = get_trip_by_id(trip_id, access_token=access_token)
            # try:
            #     departure_time = booking['trip']['departure_time']
            #     dt = datetime.fromisoformat(departure_time)
            #     booking_date = dt.strftime("%d.%m.%Y %H:%M")
            # except:
            #     booking_date = "N/A"
            
            # status = "✅ Активно" if booking.get('is_active') else "❌ Отменено"

            # total_price = booking.get('total_price', 0)
            # try:
            #     total_price_float = float(total_price)
            #     if total_price_float == int(total_price_float):
            #         price = f"{int(total_price_float)} руб."
            #     else:
            #         price = f"{total_price_float:.2f} руб."
            # except Exception:
            #     price = str(total_price)

            # text = (
            #     f"🚖 Бронирование #{idx}\n"
            #     f"📅 Дата: {booking_date}\n"
            #     f"📍 Откуда: {booking.get('pickup_location', 'N/A')}\n"
            #     f"🏁 Куда: {booking.get('dropoff_location', 'N/A')}\n"
            #     f"💵 Стоимость: {price}\n"
            #     f"🔹 Статус: {status}"
            # )
            text = format_booking(idx, booking)
            formatted.append(text)
        header = f"🚖 Найдено бронирований: {len(bookings)}\n\n"
        return header + "\n\n".join(formatted)
    except Exception as e:
        print(f"Ошибка форматирования: {str(e)}")
        return "⚠️ Не удалось получить информацию о бронированиях"
