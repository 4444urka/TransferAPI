import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def extract_address_parts(address: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Разбирает адрес на компоненты: тип улицы, название улицы, номер дома
    """
    address = ' '.join(address.split())
    
    # Сначала ищем тип улицы
    street_type_match = re.match(r'^(ул\.|улица|пр\.|проспект|пер\.|переулок|наб\.|набережная|пр-д|проезд|ш\.|шоссе|б-р|бульвар)', address)
    if street_type_match:
        street_type = street_type_match.group(1)
        address = address[len(street_type):].strip()
    else:
        street_type = None
    
    # Ищем номер дома и корпус
    house_patterns = [
        r'д\.\s*(\d+)',  # д. 10
        r'дом\s*(\d+)',  # дом 10
        r'(\d+)\s*$',    # просто число в конце
        r'(\d+)\s*к\.',  # число перед корпусом
    ]
    
    house_number = None
    for pattern in house_patterns:
        match = re.search(pattern, address)
        if match:
            house_number = match.group(1)
            # Удаляем номер дома и все после него из названия улицы
            address = address[:match.start()].strip()
            break
    
    return street_type, address.strip(), house_number

def extract_house_info(street_text: str) -> Optional[str]:
    """
    Извлекает информацию о номере дома и корпусе из адресной строки.
    """
    # паттерны типа "д. 10", "дом 10", "10 к. 2", "10к2", "10 корпус 2"
    house_corpus_patterns = [
        r'д\.\s*(\d+)(?:\s*к\.?\s*(-?\d+(?:\.\d+)?))?',
        r'дом\s*(\d+)(?:\s*к\.?\s*(-?\d+(?:\.\d+)?))?',
        r'(\d+)(?:\s*к\.?\s*(-?\d+(?:\.\d+)?))',
        r'(\d+)к(-?\d+(?:\.\d+)?)',
        r'(\d+)\s*корпус\s*(-?\d+(?:\.\d+)?)'
    ]
    
    for pattern in house_corpus_patterns:
        match = re.search(pattern, street_text)
        if match:
            house = match.group(1)
            corpus = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
            
            if corpus:
                if str(corpus).startswith('-'):
                    logger.warning(f"Negative building number detected: {corpus}")
                    return None
                if '.' in str(corpus):
                    logger.warning(f"Decimal building number detected: {corpus}")
                    return None
                return f"{house} к. {corpus}"
            return house
            
    # если не нашли паттерны с корпусом, поищем просто номер дома
    simple_house_match = re.search(r'(\d+)\s*$', street_text)
    if simple_house_match:
        return simple_house_match.group(1)
        
    return None

def preprocess_street_name(street_name: str) -> str:
    """
    Предварительно обрабатывает название улицы, заменяя сокращения и приводя к стандартному виду.
    """
    street_name = street_name.lower()
    street_name = re.sub(r'\bдом\b|\bд\.\b', '', street_name)
    street_name = re.sub(r'\bпр-т\b', 'проспект', street_name)
    street_name = re.sub(r'\bул\.\b', 'улица', street_name)
    street_name = re.sub(r'\bпр\b', 'проспект', street_name)
    street_name = re.sub(r'\bнаб\.\b', 'набережная', street_name)
    street_name = re.sub(r'\bпер\.\b', 'переулок', street_name)
    street_name = re.sub(r'\bшос\.\b', 'шоссе', street_name)
    street_name = re.sub(r'\bбул\.\b', 'бульвар', street_name)
    street_name = re.sub(r'\s+', ' ', street_name).strip()
    return street_name 