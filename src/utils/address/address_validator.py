import re
import logging
from typing import Optional, Tuple
from .street_api import StreetAPI
from django.core.cache import cache

logger = logging.getLogger(__name__)

HOUSE_NUMBER_PATTERN = re.compile(r'^\d+$')
BUILDING_NUMBER_PATTERN = re.compile(r'к\s*\d+')
STREET_TYPE_PATTERN = re.compile(r'^(ул\.|улица|пр\.|проспект|пер\.|переулок|наб\.|набережная|пр-д|проезд|ш\.|шоссе|б-р|бульвар)')

def extract_house_number_range(address: str) -> Optional[Tuple[int, int]]:
    """
    Извлекает диапазон номеров домов из адреса.
    
    Args:
        address (str): Адрес в формате "ул. Название, 1-10" или "ул. Название, 1"
        
    Returns:
        Optional[Tuple[int, int]]: Кортеж (минимальный номер, максимальный номер) или None
    """
    # Ищем диапазон номеров
    range_match = re.search(r'(\d+)\s*-\s*(\d+)', address)
    if range_match:
        try:
            min_num = int(range_match.group(1))
            max_num = int(range_match.group(2))
            return min_num, max_num
        except ValueError:
            return None
    
    # Ищем одиночный номер
    single_match = re.search(r'(\d+)\s*$', address)
    if single_match:
        try:
            num = int(single_match.group(1))
            return num, num
        except ValueError:
            return None
    
    return None

def validate_house_number(house_number: str) -> bool:
    """
    Проверяет корректность формата номера дома.
    
    Args:
        house_number (str): Номер дома для проверки
        
    Returns:
        bool: True если формат корректный, False если нет
    """
    if not house_number:
        return False

    try:
        number = int(house_number)
        if number <= 0:
            logger.warning(f"Invalid house number: {house_number}")
            return False
        return True
    except ValueError:
        logger.warning(f"Invalid house number format: {house_number}")
        return False

def validate_building_number(building_number: str) -> bool:
    """
    Проверяет корректность формата номера корпуса.
    
    Args:
        building_number (str): Номер корпуса для проверки
        
    Returns:
        bool: True если формат корректный, False если нет
    """
    if not building_number:
        return False

    try:
        number = int(building_number)
        if number <= 0:
            logger.warning(f"Invalid building number: {building_number}")
            return False
        return True
    except ValueError:
        logger.warning(f"Invalid building number format: {building_number}")
        return False

def validate_street_name(street_name: str) -> bool:
    """
    Проверяет корректность формата названия улицы.
    
    Args:
        street_name (str): Название улицы для проверки
        
    Returns:
        bool: True если формат корректный, False если нет
    """
    if not street_name:
        logger.warning("Invalid street name: empty string")
        return False

    if len(street_name) > 100:  
        logger.warning(f"Street name too long: {street_name}")
        return False

    if not re.match(r'^[а-яА-ЯёЁa-zA-Z0-9\s\-,\.]+$', street_name):
        logger.warning(f"Street name contains invalid characters: {street_name}")
        return False

    return True

def validate_house_number_realism(house_number: int, street_name: str, city: str) -> bool:
    """
    Проверяет реалистичность номера дома на улице.
    
    Args:
        house_number (int): Номер дома для проверки
        street_name (str): Название улицы
        city (str): Город
        
    Returns:
        bool: True если номер реалистичный, False если нет
    """
    try:
        cache_key = f"house_ranges_{city}_{street_name}"
        cached_ranges = cache.get(cache_key)
        
        if cached_ranges:
            for min_num, max_num in cached_ranges:
                if min_num <= house_number <= max_num:
                    return True
            return False
            
        api = StreetAPI()
        
        street_info = api.search_street(street_name, city)
        if not street_info:
            logger.warning(f"Street not found: {street_name}, {city}")
            return False
            
        house_ranges = api.get_house_ranges(street_name, city)
        if not house_ranges:
            logger.warning(f"No house ranges found for street: {street_name}, {city}")
            return False
            
        cache.set(cache_key, house_ranges, timeout=86400)
            
        for min_num, max_num in house_ranges:
            if min_num <= house_number <= max_num:
                return True
                
        max_house_number = max(max_num for _, max_num in house_ranges)
        if house_number > max_house_number * 1.5:  # Допускаем отклонение на 50%
            logger.warning(f"House number {house_number} is too large for street {street_name}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating house number realism: {str(e)}")
        return False 