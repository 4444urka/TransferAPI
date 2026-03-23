import re
import logging

logger = logging.getLogger(__name__)

def simplify_address(address: str) -> str:
    """
    Упрощает адрес, удаляя префиксы типа "ул.", "д." и т.д.
    Преобразует адрес в формат "Название улицы Номер дома"
    
    Примеры:
    - "ул. Шилкинская д. 21" -> "Шилкинская 21"
    - "Улица Ленина, дом 10" -> "Ленина 10"
    - "проспект Красного Знамени, д. 45" -> "Красного Знамени 45"
    
    Args:
        address: Исходный адрес
        
    Returns:
        Упрощенный адрес в формате "Название улицы Номер дома"
    """
    if not address or not isinstance(address, str):
        logger.warning(f"Invalid address provided: {address}")
        return ""
    
    # Сохраняем исходный адрес для логирования
    original_address = address
    
    # Удаляем префиксы типа "ул.", "улица", "д.", "дом" и т.д.
    prefixes = [
        r'(?:ул\.?|улица)\s+',
        r'(?:пр\.?|пр-т|проспект)\s+',
        r'(?:пер\.?|переулок)\s+',
        r'(?:б-р|бульвар)\s+',
        r'(?:пл\.?|площадь)\s+',
        r'(?:ш\.?|шоссе)\s+',
        r'(?:наб\.?|набережная)\s+',
        r'(?:д\.?|дом)\s+'
    ]
    
    for prefix in prefixes:
        address = re.sub(prefix, '', address, flags=re.IGNORECASE)
    
    # Удаляем запятые и лишние пробелы
    address = re.sub(r',', '', address)
    address = re.sub(r'\s+', ' ', address).strip()
    
    # Делаем первую букву заглавной
    if address:
        address = address[0].upper() + address[1:]
    
    logger.info(f"Simplified address: '{original_address}' -> '{address}'")
    return address

def preprocess_address(address: str) -> str:
    """
    Предобрабатывает адрес, оставляя только название улицы и номер дома.
    
    Функция удаляет:
    - названия городов, районов, регионов
    - почтовые индексы
    - номера квартир и офисов
    - дополнительные уточнения в скобках
    - лишние пробелы и знаки пунктуации
    
    Args:
        address: Исходный адрес
        
    Returns:
        Обработанный адрес, содержащий только название улицы и номер дома
    """
    if not address or not isinstance(address, str):
        logger.warning(f"Invalid address provided: {address}")
        return ""
    
    # Сохраняем исходный адрес для логирования
    original_address = address
    
    # Приводим к нижнему регистру для удобства обработки
    address = address.lower()
    
    # Удаляем почтовые индексы (6 цифр)
    address = re.sub(r'\b\d{6}\b', '', address)
    
    # Удаляем указания на город, район, область и т.д.
    city_patterns = [
        r'г\.?\s*[а-яё\-]+',  # г. Владивосток
        r'город\s+[а-яё\-]+',  # город Владивосток
        r'[а-яё\-]+\s+обл\.?',  # Приморский обл.
        r'[а-яё\-]+\s+область',  # Приморский область
        r'[а-яё\-]+\s+район',  # Первомайский район
        r'р-н\s+[а-яё\-]+',  # р-н Первомайский
    ]
    
    for pattern in city_patterns:
        address = re.sub(pattern, '', address)
    
    # Удаляем указания на квартиру, офис и т.д.
    flat_patterns = [
        r'кв\.?\s*\d+',  # кв. 123
        r'квартира\s+\d+',  # квартира 123
        r'оф\.?\s*\d+',  # оф. 123
        r'офис\s+\d+',  # офис 123
        r'помещение\s+\d+',  # помещение 123
    ]
    
    for pattern in flat_patterns:
        address = re.sub(pattern, '', address)
    
    # Удаляем содержимое в скобках (часто дополнительные уточнения)
    address = re.sub(r'\([^)]*\)', '', address)
    
    # Находим улицу и дом с помощью регулярных выражений
    # Ищем паттерны типа "ул. Ленина, д. 10" или "Ленина 10"
    street_house_patterns = [
        # Улица + дом с указанием типа
        r'((?:ул|улица|пр|проспект|пер|переулок|б-р|бульвар|пл|площадь|ш|шоссе|наб|набережная)\.?\s+[а-яё\-]+)(?:[,\s]+(?:д|дом)\.?\s*(\d+[\w\/\-]*))?\b',
        
        # Дом + улица с указанием типа
        r'(?:д|дом)\.?\s*(\d+[\w\/\-]*)(?:[,\s]+(?:по|на)?\s+(?:ул|улица|пр|проспект|пер|переулок|б-р|бульвар|пл|площадь|ш|шоссе|наб|набережная)\.?\s+([а-яё\-]+))\b',
        
        # Просто название улицы и номер дома без указания типа
        r'([а-яё\-]+)(?:[,\s]+(?:д|дом)\.?\s*(\d+[\w\/\-]*))\b',
        
        # Название улицы и номер дома без разделителей
        r'([а-яё\-]+)\s+(\d+[\w\/\-]*)\b',
    ]
    
    street = None
    house_number = None
    
    for pattern in street_house_patterns:
        match = re.search(pattern, address)
        if match:
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:
                street = groups[0]
                house_number = groups[1]
            elif len(groups) >= 1:
                street = groups[0]
                # Ищем номер дома отдельно
                house_match = re.search(r'\b(?:д|дом)\.?\s*(\d+[\w\/\-]*)\b', address)
                if house_match:
                    house_number = house_match.group(1)
                else:
                    # Пытаемся найти просто число, которое может быть номером дома
                    house_match = re.search(r'\b(\d+[\w\/\-]*)\b', address)
                    if house_match:
                        house_number = house_match.group(1)
            break
    
    # Если не удалось найти улицу и дом по паттернам, возвращаем исходную строку
    if not street:
        logger.warning(f"Could not extract street and house number from: {original_address}")
        return original_address.strip()
    
    # Формируем результат
    if house_number:
        result = f"{street}, д. {house_number}"
    else:
        result = street
    
    logger.info(f"Preprocessed address: '{original_address}' -> '{result}'")
    return result.strip()

def preprocess_and_find_address(address: str, city: str = None, find_address_func=None):
    """
    Предобрабатывает адрес и передает его в функцию поиска адреса.
    
    Args:
        address: Исходный адрес
        city: Название города (опционально)
        find_address_func: Функция для поиска адреса (find_address_by_name)
        
    Returns:
        Результат работы функции поиска адреса или None
    """
    if not find_address_func:
        logger.error("find_address_func is not provided")
        return None
        
    if not address:
        logger.warning("Empty address provided")
        return None
    
    # Предобрабатываем адрес
    preprocessed_address = preprocess_address(address)
    
    # Если после предобработки адрес пустой, возвращаем None
    if not preprocessed_address:
        logger.warning(f"Preprocessing resulted in empty address: {address}")
        return None
    
    # Вызываем функцию поиска адреса с предобработанным адресом
    logger.info(f"Calling find_address_func with preprocessed address: '{preprocessed_address}'")
    return find_address_func(preprocessed_address, city) 