import requests
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache

logger = logging.getLogger(__name__)

class StreetAPI:
    """
    Класс для работы с API геокодинга
    """
    def __init__(self, base_url: str = 'https://nominatim.openstreetmap.org/search'):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Armada (contact@example.com)'
        }
        
        # Словарь альтернативных названий городов Приморского края
        self.city_aliases = {
            'Артем': ['Артём', 'Артемовский', 'Артёмовский', 'Артёмовский городской округ'],
            'Уссурийск': ['Уссурийский', 'Уссурийский городской округ'],
            'Владивосток': ['Владивостокский', 'Владивостокский городской округ'],
            'Арсеньев': ['Арсеньевский', 'Арсеньевский городской округ'],
            'Дальнегорск': ['Дальнегорский', 'Дальнегорский городской округ'],
            'Дальнереченск': ['Дальнереченский', 'Дальнереченский городской округ'],
            'Лесозаводск': ['Лесозаводский', 'Лесозаводский городской округ'],
            'Находка': ['Находкинский', 'Находкинский городской округ'],
            'Партизанск': ['Партизанский', 'Партизанский городской округ'],
            'Спасск-Дальний': ['Спасск-Дальний городской округ', 'Спасский', 'Спасск'],
            'Фокино': ['Фокинский', 'Фокинский городской округ'],
            'Большой Камень': ['Большекаменский', 'Большекаменский городской округ'],
            'Партизанский': ['Партизанский район'],
            'Лазовский': ['Лазовский район'],
            'Ольгинский': ['Ольгинский район'],
            'Тернейский': ['Тернейский район'],
            'Красноармейский': ['Красноармейский район'],
            'Пожарский': ['Пожарский район'],
            'Хасанский': ['Хасанский район'],
            'Ханкайский': ['Ханкайский район'],
            'Черниговский': ['Черниговский район'],
            'Чугуевский': ['Чугуевский район'],
            'Шкотовский': ['Шкотовский район'],
            'Яковлевский': ['Яковлевский район']
        }

    def _get_city_variants(self, city: str) -> list:
        """
        Возвращает варианты названия города
        """
        variants = [city]
        if city in self.city_aliases:
            variants.extend(self.city_aliases[city])
        return variants

    def search_street(self, street_name: str, city: str, house_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Поиск улицы через API
        """
        cache_key = f"street_api:{city}:{street_name}:{house_number}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for street: {street_name} in city: {city}")
            return cached_result

        try:
            city_variants = self._get_city_variants(city)
            
            for city_variant in city_variants:
                # Сначала пробуем точный поиск
                params = {
                    'format': 'json',
                    'q': f"{street_name} {city_variant}",
                    'addressdetails': 1,
                    'countrycodes': 'ru',
                    'limit': 10,
                    'accept-language': 'ru'
                }
                
                if house_number:
                    params['q'] += f" {house_number}"
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    # Если точный поиск не дал результатов, пробуем нечеткий поиск
                    params['q'] = f"{street_name} {city_variant}"
                    response = requests.get(
                        self.base_url,
                        params=params,
                        headers=self.headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                if not data:
                    continue
                    
                for item in data:
                    address = item.get('address')
                    if not address:
                        continue
                        
                    road = address.get('road')
                    if not road:
                        continue
                        
                    # Проверяем, что улица находится в нужном городе
                    city_found = False
                    for city_field in ['city', 'town', 'suburb', 'state_district', 'state', 'county']:
                        field_value = address.get(city_field, '').lower()
                        if any(variant.lower() in field_value for variant in city_variants):
                            city_found = True
                            break
                    
                    if not city_found:
                        continue
                        
                    result = {
                        'street': road,
                        'house_number': address.get('house_number'),
                        'full_address': item.get('display_name')
                    }

                    cache.set(cache_key, result, timeout=3600)  # кэшируем на 1 час
                    return result
            
            logger.warning(f"No results found for street: {street_name} in city: {city}")
            return None
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during API request: {str(e)}")
            return None 