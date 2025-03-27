import re
import logging

logger = logging.getLogger(__name__)

HOUSE_NUMBER_PATTERN = re.compile(r'^\d+$')
BUILDING_NUMBER_PATTERN = re.compile(r'к\s*\d+')
STREET_TYPE_PATTERN = re.compile(r'^(ул\.|улица|пр\.|проспект|пер\.|переулок|наб\.|набережная|пр-д|проезд|ш\.|шоссе|б-р|бульвар)')

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