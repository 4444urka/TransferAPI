import re
import logging
from typing import Optional
from django.core.cache import cache

from .address_validator import validate_house_number, validate_building_number, validate_street_name, validate_house_number_realism
from .address_parser import extract_address_parts, extract_house_info, preprocess_street_name
from .street_api import StreetAPI

logger = logging.getLogger(__name__)

def find_street_by_name(address: str, city: str) -> Optional[str]:
    """
    Находит улицу по названию в указанном городе и возвращает адрес в стандартном формате.
    
    Args:
        address (str): Адрес для поиска
        city (str): Город для поиска
        
    Returns:
        Optional[str]: Адрес в стандартном формате или None, если улица не найден
    """
    if not address or not city:
        return None

    street_type, street_name, house_number = extract_address_parts(address)
    
    if not house_number:
        logger.warning(f"House number is required: {address}")
        return None

    if not validate_house_number(house_number):
        logger.warning(f"Invalid house number format: {house_number}")
        return None

    building_info = extract_house_info(address)
    building_number = None
    has_corpus = bool(re.search(r'к\.?\s*-?\d+|корпус\s*-?\d+', address))
    
    if building_info and 'к.' in building_info:
        building_number = building_info.split('к.')[1].strip()
        if not validate_building_number(building_number):
            logger.warning(f"Invalid building number format: {building_number}")
            return None

    if not validate_street_name(street_name):
        return None

    processed_street_name = preprocess_street_name(street_name)
    try:
        api = StreetAPI()
        
        street = api.search_street(processed_street_name, city, house_number)
        if not street:
            # Пробуем поискать без номера дома
            street = api.search_street(processed_street_name, city)
            if not street:
                return None

        # Проверяем реалистичность номера дома
        if not api.validate_house_number(int(house_number), street['street'], city):
            logger.warning(f"Unrealistic house number {house_number} for street {street['street']}")
            return None

        # Определяем тип улицы
        street_type = None
        if 'переулок' in street['street'].lower():
            street_type = 'пер.'
        elif 'проспект' in street['street'].lower():
            street_type = 'пр.'
        elif 'набережная' in street['street'].lower():
            street_type = 'наб.'
        elif 'проезд' in street['street'].lower():
            street_type = 'пр-д'
        elif 'шоссе' in street['street'].lower():
            street_type = 'ш.'
        elif 'бульвар' in street['street'].lower():
            street_type = 'б-р'
        else:
            street_type = 'ул.'

        # Убираем тип улицы из названия, если он есть
        street_name = street['street']
        for prefix in ['ул.', 'улица', 'пр.', 'проспект', 'пер.', 'переулок', 'наб.', 'набережная', 'пр-д', 'проезд', 'ш.', 'шоссе', 'б-р', 'бульвар']:
            if street_name.lower().startswith(prefix.lower()):
                street_name = street_name[len(prefix):].strip()
                break

        # Формируем результат с правильным типом улицы
        # result = f"{street_type} {street_name} {house_number}" # в это случае идёт запись "пер. Некрасовский переулок 5"
        result = f"{street_name} {house_number}" # а это типо фикс
        if building_number:
            result += f" к {building_number}"

        return result

    except Exception as e:
        logger.error(f"Error processing address {address}: {str(e)}")
        return None

def find_street_by_name_old(address: str, city: str) -> Optional[str]:
    """
    Находит улицу по названию в указанном городе
    """
    if not address or not city:
        return None

    cache_key = f"street_{city}_{address}"
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for address: {address}")
        return cached_result

    street_type, street_name, house_number = extract_address_parts(address)
    
    if house_number and not validate_house_number(house_number):
        logger.warning(f"Suspicious house number detected: {house_number}")
        return None
    
    building_info = extract_house_info(address)
    if building_info and 'к.' in building_info:
        building_number = building_info.split('к.')[1].strip()
        if not validate_building_number(building_number):
            logger.warning(f"Suspicious building number detected: {building_number}")
            return None

    if not validate_street_name(street_name):
        return None

    processed_street_name = preprocess_street_name(street_name)

    try:
        api = StreetAPI()
        
        result = api.search_street(processed_street_name, city, house_number)
        
        if not result:
            logger.warning(f"No street found for address: {address}")
            return None
            
        formatted_result = f"{street_type or 'ул.'} {result['street']}"
        if house_number:
            formatted_result += f" {house_number}"
            
        cache.set(cache_key, formatted_result, timeout=3600)  # кэш на 1 час
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error processing address {address}: {str(e)}")
        return None 