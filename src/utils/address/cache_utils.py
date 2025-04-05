import hashlib
import functools
import logging
import threading
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Используем threading.local() для хранения временных результатов 
# в рамках текущего потока, чтобы избежать повторных вызовов
_local_cache = threading.local()

def cached_address_lookup(timeout=86400):
    """
    Декоратор для кэширования результатов поиска адреса.
    Предотвращает повторные вызовы функции с одними и теми же параметрами
    в рамках выполнения одного запроса.
    
    Args:
        timeout: Время жизни кэша в секундах (по умолчанию 24 часа)
    
    Returns:
        Декорированная функция с кэшированием
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(street, city=None, *args, **kwargs):
            # Инициализируем локальный кэш для текущего потока, если его нет
            if not hasattr(_local_cache, 'results'):
                _local_cache.results = {}
                
            # Формируем ключ для кэша на основе параметров запроса
            request_key = f"street:{city}:{street}".lower()
            
            # Сначала проверяем локальный кэш текущего потока (запроса)
            if request_key in _local_cache.results:
                logger.debug(f"Using request-local result for: '{street}' in '{city}'")
                return _local_cache.results[request_key]
                
            # Затем проверяем глобальный кэш
            cache_key = f"street_lookup:{hashlib.md5(request_key.encode()).hexdigest()}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                # Сохраняем результат в локальный кэш текущего потока
                _local_cache.results[request_key] = cached_result
                logger.info(f"Found address in cache: '{street}' in '{city}'")
                return cached_result
            
            # Вызываем оригинальную функцию
            result = func(street, city, *args, **kwargs)
            
            # Сохраняем результат в локальный кэш текущего потока
            _local_cache.results[request_key] = result
            
            # Кэшируем результат
            if result is not None:
                # Положительный результат кэшируем на полное время
                cache.set(cache_key, result, timeout=timeout)
                logger.info(f"Address successfully cached: {result}")
            else:
                # Отрицательный результат кэшируем на меньшее время
                negative_cache_timeout = timeout // 4  # например, 6 часов вместо 24
                cache.set(cache_key, result, timeout=negative_cache_timeout)
                logger.info(f"Non existable address successfully cached: '{street}' in '{city}'")
                
            return result
        return wrapper
    return decorator
