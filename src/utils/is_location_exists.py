import requests
from django.core.cache import cache


def is_location_exists(street: str, city: str = None) -> bool:
    """
    Проверяет существование указанной локации с использованием кэширования.

    Args:
        street: Название улицы
        city: Название города (опционально)

    Returns:
        bool: True, если локация существует, False в противном случае
    """
    # Формируем уникальный ключ для кэша
    cache_key = f"location_check:{city}:{street}"

    # Пытаемся получить результат из кэша
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Если результата в кэше нет, выполняем запрос к API
    headers = {
        'User-Agent': 'Armada (contact@example.com)'  # Обязательно укажите свои данные
    }

    params = {
        'format': 'json',
        'city': city,
        'street': street,
        'addressdetails': 1,
        'countrycodes': 'ru',
        'limit': 5,
        'accept-language': 'ru'
    }

    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params=params,
            headers=headers,
            timeout=10
        )
        result = True if response.json() else False

        # Сохраняем результат в кэш на 24 часа (86400 секунд)
        cache.set(cache_key, result, 86400)

        return result
    except Exception as e:
        # В случае ошибки не кэшируем результат
        raise e
