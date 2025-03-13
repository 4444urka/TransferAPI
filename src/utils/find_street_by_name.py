import requests
import hashlib
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def find_street_by_name(street: str, city: str = None) -> str | None:
    """
    Ищет улицу по названию с использованием кэширования.
    
    Args:
        street: Название улицы
        city: Название города (опционально)
        
    Returns:
        Отформатированный адрес или None, если адрес не найден
    """
    # Формируем ключ для кэша на основе параметров запроса
    cache_key = f"street:{city}:{street}".lower()
    cache_key = f"street_lookup:{hashlib.md5(cache_key.encode()).hexdigest()}"
    
    # Проверяем, есть ли результат в кэше
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Получен адрес из кэша: '{street}' в '{city}'")
        return cached_result
    
    logger.info(f"Поиск адреса через API: '{street}' в '{city}'")
    
    headers = {
        'User-Agent': 'Armada (contact@example.com)'
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
        
        # Проверяем успешность запроса
        response.raise_for_status()
        
        # Получаем данные из ответа
        data = response.json()
        
        # Проверяем, что в ответе есть данные
        if not data:
            # Кэшируем отрицательный результат на 6 часов
            cache.set(cache_key, None, timeout=21600)
            return None
            
        # Получаем адрес из первого результата
        address = data[0].get('address')
        if not address:
            cache.set(cache_key, None, timeout=21600)
            return None
            
        road = address.get('road')
        house_number = address.get('house_number')

        if road is None or house_number is None:
            cache.set(cache_key, None, timeout=21600)
            return None
            
        result = f"{road}, д. {house_number}"
        
        # Кэшируем положительный результат на 24 часа
        cache.set(cache_key, result, timeout=86400)
        logger.info(f"Адрес успешно найден и кэширован: {result}")
        return result

    except Exception as e:
        logger.error(f"Ошибка в find_street_by_name: {e}")
        # Не кэшируем ошибки, чтобы повторить запрос при следующем вызове
        return None