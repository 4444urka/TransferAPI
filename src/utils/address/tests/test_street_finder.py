from django.test import TestCase
import logging
from src.utils.address.find_address_by_name import find_address_by_name
from django.core.cache import cache

# Очистка кэша перед запуском тестов
cache.clear()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreetFinderTest(TestCase):
    """Тесты для функции поиска улицы с реальным API"""

    def setUp(self):
        """Настройка для тестов"""
        self.test_cases = [
            # Реальные адреса Владивостока
            ("Светланская 10", "Владивосток"),
            ("проспект 100-летия Владивостока 12", "Владивосток"),
            ("Океанский проспект 10", "Владивосток"),
            
            # Реальные адреса Уссурийска
            ("Ленина 10", "Уссурийск"),
            ("Краснознаменная 5", "Уссурийск"),
            
            # Реальные адреса Артема
            ("Кирова 15", "Артем"),
            ("Фрунзе 8", "Артем"),
        ]

    def test_valid_addresses(self):
        """Тест корректных адресов"""
        for address, city in self.test_cases:
            with self.subTest(address=address, city=city):
                try:
                    result = find_address_by_name(address, city)
                    self.assertIsNotNone(result, f"Не удалось найти адрес: {address}, {city}")
                    logger.info(f"Успешно обработан адрес: {address}, {city}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке адреса {address}, {city}: {str(e)}")
                    raise

    def test_invalid_addresses(self):
        """Тест некорректных адресов"""
        invalid_cases = [
            ("", "Владивосток"),  # Пустая улица
            ("Несуществующая", "Владивосток"),  # Без номера дома
            ("Ленина", "Владивосток"),  # Без номера дома
            ("10", "Владивосток"),  # Только номер
        ]

        for address, city in invalid_cases:
            with self.subTest(address=address, city=city):
                try:
                    result = find_address_by_name(address, city)
                    self.assertIsNone(result, f"Ожидался None для некорректного адреса: {address}, {city}")
                    logger.info(f"Успешно обработан некорректный адрес: {address}, {city}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке некорректного адреса {address}, {city}: {str(e)}")
                    raise

    def test_different_formats(self):
        """Тест разных форматов записи адресов"""
        formats = [
            ("Светланская 10", "Владивосток"),
            ("ул. Светланская 10", "Владивосток"),
            ("улица Светланская 10", "Владивосток"),
            ("Светланская, 10", "Владивосток"),
        ]

        for address, city in formats:
            with self.subTest(address=address, city=city):
                try:
                    result = find_address_by_name(address, city)
                    self.assertIsNotNone(result, f"Не удалось найти адрес: {address}, {city}")
                    logger.info(f"Успешно обработан адрес в формате: {address}, {city}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке формата адреса {address}, {city}: {str(e)}")
                    raise