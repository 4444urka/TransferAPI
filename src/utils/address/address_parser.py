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
        
        # Удаляем дублирование типа улицы в начале названия
        address = re.sub(r'^(улица|ул\.)\s+(улица|ул\.)\s+', '', address)
        address = re.sub(r'^(проспект|пр\.)\s+(проспект|пр\.)\s+', '', address)
        address = re.sub(r'^(переулок|пер\.)\s+(переулок|пер\.)\s+', '', address)
        address = re.sub(r'^(набережная|наб\.)\s+(набережная|наб\.)\s+', '', address)
        address = re.sub(r'^(шоссе|ш\.)\s+(шоссе|ш\.)\s+', '', address)
        address = re.sub(r'^(бульвар|б-р)\s+(бульвар|б-р)\s+', '', address)
        address = re.sub(r'^(проезд|пр-д)\s+(проезд|пр-д)\s+', '', address)
        
        # Удаляем дублирование типа улицы в середине названия
        address = re.sub(r'\bулица\s+улица\b|\bулица\s+ул\.\b|\bул\.\s+улица\b', '', address)
        address = re.sub(r'\bпроспект\s+проспект\b|\bпроспект\s+пр\.\b|\bпр\.\s+проспект\b', '', address)
        address = re.sub(r'\bпереулок\s+переулок\b|\bпереулок\s+пер\.\b|\bпер\.\s+переулок\b', '', address)
        address = re.sub(r'\bнабережная\s+набережная\b|\bнабережная\s+наб\.\b|\bнаб\.\s+набережная\b', '', address)
        address = re.sub(r'\bшоссе\s+шоссе\b|\bшоссе\s+ш\.\b|\bш\.\s+шоссе\b', '', address)
        address = re.sub(r'\bбульвар\s+бульвар\b|\bбульвар\s+б-р\b|\bб-р\s+бульвар\b', '', address)
        address = re.sub(r'\bпроезд\s+проезд\b|\bпроезд\s+пр-д\b|\bпр-д\s+проезд\b', '', address)
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
    
    # Удаляем лишние пробелы
    address = re.sub(r'\s+', ' ', address).strip()
    return street_type, address, house_number

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
    
    street_types = [
        (r'\bулица\s+улица\b|\bулица\s+ул\.\b|\bул\.\s+улица\b', 'улица'),
        (r'\bпроспект\s+проспект\b|\bпроспект\s+пр\.\b|\bпр\.\s+проспект\b', 'проспект'),
        (r'\bпереулок\s+переулок\b|\bпереулок\s+пер\.\b|\bпер\.\s+переулок\b', 'переулок'),
        (r'\bнабережная\s+набережная\b|\bнабережная\s+наб\.\b|\bнаб\.\s+набережная\b', 'набережная'),
        (r'\bшоссе\s+шоссе\b|\bшоссе\s+ш\.\b|\bш\.\s+шоссе\b', 'шоссе'),
        (r'\bбульвар\s+бульвар\b|\bбульвар\s+б-р\b|\bб-р\s+бульвар\b', 'бульвар'),
        (r'\bпроезд\s+проезд\b|\bпроезд\s+пр-д\b|\bпр-д\s+проезд\b', 'проезд')
    ]
    
    for pattern, replacement in street_types:
        street_name = re.sub(pattern, replacement, street_name)
    
    street_name = re.sub(r'^(улица|ул\.)\s+(улица|ул\.)\s+', 'улица ', street_name)
    street_name = re.sub(r'^(проспект|пр\.)\s+(проспект|пр\.)\s+', 'проспект ', street_name)
    street_name = re.sub(r'^(переулок|пер\.)\s+(переулок|пер\.)\s+', 'переулок ', street_name)
    street_name = re.sub(r'^(набережная|наб\.)\s+(набережная|наб\.)\s+', 'набережная ', street_name)
    street_name = re.sub(r'^(шоссе|ш\.)\s+(шоссе|ш\.)\s+', 'шоссе ', street_name)
    street_name = re.sub(r'^(бульвар|б-р)\s+(бульвар|б-р)\s+', 'бульвар ', street_name)
    street_name = re.sub(r'^(проезд|пр-д)\s+(проезд|пр-д)\s+', 'проезд ', street_name)
    
    street_name = re.sub(r'\s+', ' ', street_name).strip()
    return street_name 