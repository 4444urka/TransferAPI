import requests
import hashlib
import re
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def find_street_by_name(street: str, city: str = None) -> str | None:
    """
    Ищет улицу по названию с использованием кэширования и предварительной обработки адреса.
    
    Args:
        street: Название улицы
        city: Название города (опционально)
        
    Returns:
        Отформатированный адрес или None, если адрес не найден
    """
    street = street.strip()
    house_info = extract_house_info(street)
    
    street_name = re.sub(r'\s*д\.\s*\d+(\s*к\.?\s*\d+)?$', '', street)
    street_name = re.sub(r'\s*\d+(\s*к\.?\s*\d+)?$', '', street_name)
    street_name = street_name.rstrip(',.')
    
    # Предварительная обработка названия улицы для улучшения поиска
    street_name_processed = preprocess_street_name(street_name)
    
    # Формируем ключ для кэша на основе параметров запроса
    cache_key = f"street:{city}:{street}".lower()
    cache_key = f"street_lookup:{hashlib.md5(cache_key.encode()).hexdigest()}"
    
    # Проверяем, есть ли результат в кэше
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Получен адрес из кэша: '{street}' в '{city}'")
        return cached_result
    
    logger.info(f"Поиск адреса через API: '{street_name_processed}' в '{city}' (исходный запрос: '{street_name}')")
    
    headers = {
        'User-Agent': 'Armada (contact@example.com)'
    }

    params = {
        'format': 'json',
        'city': city,
        'street': street_name_processed,
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
            logger.debug(f"Address not found trying fallback search: {street_name}")
            return fallback_search(street_name, city, cache_key, house_info)
        
        logger.debug(f"Found data: {data}")
            
        # Получаем адрес из первого результата
        address = data[0].get('address')
        if not address:
            logger.debug(f"Address is empty trying fallback search: {street_name}")
            return fallback_search(street_name, city, cache_key, house_info)
            
        road = address.get('road')
        
        # Если номер дома предоставлен пользователем, используем его
        if house_info:
            house_number = house_info
        else:
            logger.debug("There is no house info trying to get it from the response")
            # Иначе пытаемся получить номер дома из результата
            house_number = address.get('house_number')
            
            # Если номер дома не найден, то щщем в исходном запросе
            if house_number is None:
                logger.debug("House number not found trying to get it from the original request")
                house_match = re.search(r'(\d+)(\s*к\.?\s*\d+)?$', street)
                if house_match:
                    house_number = house_match.group(0).strip()

        if road is None:
            logger.debug(f"Road is empty trying fallback search: {street_name}")
            return fallback_search(street_name, city, cache_key, house_info)
            
        if house_number is None:
            logger.debug(f"House number is empty trying to return only street: {road}")
            # возвращаем только улицу, если номер дома не получили
            result = f"{road}"
            cache.set(cache_key, result, timeout=86400)
            logger.info(f"Улица найдена без номера дома: {result}")
            return result
            
        result = f"{road}, д. {house_number}"
        
        # Кэшируем положительный результат на 24 часа
        cache.set(cache_key, result, timeout=86400)
        logger.info(f"Адрес успешно найден и кэширован: {result}")
        return result

    except Exception as e:
        logger.error(f"Ошибка в find_street_by_name: {e}")
        # Не кэшируем ошибки, чтобы повторить запрос при следующем вызове
        return None


def extract_house_info(street_text):
    """
    Извлекает информацию о номере дома и корпусе из адресной строки.
    """
    # паттерны типа "д. 10", "дом 10", "10 к. 2", "10к2", "10 корпус 2"
    house_corpus_patterns = [
        r'д\.\s*(\d+)(?:\s*к\.?\s*(\d+))?',
        r'дом\s*(\d+)(?:\s*к\.?\s*(\d+))?',
        r'(\d+)(?:\s*к\.?\s*(\d+))',
        r'(\d+)к(\d+)',
        r'(\d+)\s*корпус\s*(\d+)'
    ]
    
    for pattern in house_corpus_patterns:
        match = re.search(pattern, street_text)
        if match:
            house = match.group(1)
            corpus = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
            
            if corpus:
                return f"{house} к. {corpus}"
            return house
            
    # если не нашли паттерны с корпусом, поищем просто номер дома
    simple_house_match = re.search(r'(\d+)\s*$', street_text)
    if simple_house_match:
        return simple_house_match.group(1)
        
    return None


def fallback_search(street_name, city, cache_key, house_info=None):
    """
    Резервный поиск с менее строгими параметрами.
    
    Args:
        street_name: Название улицы
        city: Название города
        cache_key: Ключ кэша для сохранения результата
        house_info: Информация о номере дома, если есть
    """
    try:
        simplified_street = re.sub(r'^(ул\.|улица|пр\.|проспект|бульвар|б-р|переулок|пер\.|проезд|набережная|наб\.)\s+', '', street_name, flags=re.IGNORECASE)
        
        headers = {
            'User-Agent': 'Armada (contact@example.com)'
        }

        params = {
            'format': 'json',
            'q': f"{simplified_street} {city if city else ''}",
            'addressdetails': 1,
            'countrycodes': 'ru',
            'limit': 5,
            'accept-language': 'ru'
        }
        
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params=params,
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            # Кэшируем отрицательный результат на 6 часов
            cache.set(cache_key, None, timeout=21600)
            return None
            
        # Перебираем результаты и ищем первый с подходящей улицей
        for item in data:
            address = item.get('address')
            if not address:
                continue
                
            road = address.get('road')
            if not road:
                continue
                
            if house_info:
                result = f"{road}, д. {house_info}"
            else:
                house_number = address.get('house_number')
                if house_number:
                    result = f"{road}, д. {house_number}"
                else:
                    result = f"{road}"
                    
            cache.set(cache_key, result, timeout=86400)
            logger.info(f"Адрес найден в резервном поиске: {result}")
            return result
            
        # Если не нашли подходящий результат
        cache.set(cache_key, None, timeout=21600)
        return None
        
    except Exception as e:
        logger.error(f"Ошибка в fallback_search: {e}")
        return None


def preprocess_street_name(street_name):
    """
    Предварительно обрабатывает название улицы, заменяя сокращения и приводя к стандартному виду.
    """
    street_name = street_name.lower()
    street_name = re.sub(r'\bпр-т\b', 'проспект', street_name)
    street_name = re.sub(r'\bул\.\b', 'улица', street_name)
    street_name = re.sub(r'\bд\.\b', 'дом', street_name)
    street_name = re.sub(r'\bпр\b', 'проспект', street_name)
    street_name = re.sub(r'\bнаб\.\b', 'набережная', street_name)
    street_name = re.sub(r'\bпер\.\b', 'переулок', street_name)
    street_name = re.sub(r'\bшос\.\b', 'шоссе', street_name)
    street_name = re.sub(r'\bбул\.\b', 'бульвар', street_name)
    street_name = re.sub(r'\s+', ' ', street_name).strip()
    return street_name