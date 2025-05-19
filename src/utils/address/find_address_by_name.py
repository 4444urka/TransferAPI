import requests
import logging
from .cache_utils import cached_address_lookup

logger = logging.getLogger(__name__)

@cached_address_lookup(timeout=86400)  # 24 часа для кэширования
def find_address_by_name(address: str, city: str = None) -> str | None:
    """
    Ищет улицу по названию с использованием API геокодирования.
    
    Args:
        street: Название улицы
        city: Название города (опционально)
        
    Returns:
        Отформатированный адрес или None, если адрес не найден
    """
    
    if address is None or not address.strip() or address.isdigit():
        logger.error("Street name is empty or invalid")
        return None
    
    logger.debug(f"Trying to find address using API: '{address}' in '{city}'")
    
    headers = {
        'User-Agent': 'Armada (contact@example.com)'
    }

    params = {
        'format': 'json',
        'city': city,
        'street': address,
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
            logger.error(f"No results found for '{address}' in '{city}'")
            return None
        
        logger.debug(f"API response: {data}")
            
        # Получаем адрес из первого результата
        address = data[0].get('address')
        if not address:
            return None
            
        road = address.get('road')
        house_number = address.get('house_number')

        if road is None or house_number is None:
            return None
            
        result = f"{road}, д. {house_number}"
        
        logger.info(f"Address successfully found : {result}")
        return result

    except Exception as e:
        logger.error(f"Error in find_address_by_name: {e}")
        return None