import os
import django
import logging
from django.test import TestCase
import re

# Настраиваем Django (если еще не настроено в settings)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils.find_street_by_name import find_street_by_name
from utils.street_validate_regex import street_validate_regex


class StreetFinderTest(TestCase):

    def test_find_street(self):
        test_cases = [
            # Простые адреса
            ("ул. Ленина 10", "Владивосток"),
            ("Светланская 10", "Владивосток"),
            ("проспект 100-летия Владивостока 12", "Владивосток"),

            # Адреса с корпусами и строениями
            ("ул. Ленина 10 к 2", "Владивосток"),
            ("Светланская 10к2", "Владивосток"),
            ("Светланская 10 корпус 2", "Владивосток"),
            ("ул. Пушкинская, строение 5", "Владивосток"),
            ("ул. Адмирала Фокина, стр 3", "Владивосток"),

            # Различные типы улиц
            ("ул. Алеутская 1", "Владивосток"),
            ("пр-кт Красного Знамени 20", "Владивосток"),
            ("набережная Спортивная 5", "Владивосток"),
            ("пер. Павленко 3", "Владивосток"),
            ("проезд Нейбута 7", "Владивосток"),
            ("шоссе Русское 15", "Владивосток"),
            ("бульвар Шевченко 8", "Владивосток"),

            # Нестандартные форматы и сокращения
            ("Ленина д 10", "Владивосток"),
            ("ул Ленина дом 10", "Владивосток"),
            ("улица Ленина 10", "Владивосток"),
            ("пр 100-летия Владивостока 12", "Владивосток"),
            ("наб. Амурская 1", "Владивосток"),
            ("пер. Почтовый 2", "Владивосток"),

            # Сложные и длинные названия
            ("ул. Адмирала Юмашева 22", "Владивосток"),
            ("ул. Всеволода Сибирцева 14", "Владивосток"),
            ("ул. 40 лет ВЛКСМ 1", "Владивосток"),

            # Тест с разными городами
            ("ул. Ленина 10", "Уссурийск"),
            ("ул. Ленина 10", "Артем"),

            # Тест с некорректными данными
            ("", "Владивосток"),
            ("ул. Несуществующая 10", "Владивосток"),
            ("ул. Ленина", "Владивосток"),  # без номера дома
            ("10", "Владивосток"),  # только номер
            ("улица", "Владивосток"), # только тип улицы
        ]

        logger.info("\nНачинаем тестирование find_street_by_name:")
        logger.info("-" * 50)

        for street, city in test_cases:
            logger.info(f"\nТестируем: '{street}' в городе '{city}'")

            # Проверяем формат до обработки
            if street:
                matches_regex = bool(re.match(street_validate_regex, street))
                logger.info(f"Соответствует regex до обработки: {matches_regex}")

            try:
                result = find_street_by_name(street, city)
                logger.info(f"Результат: {result}")

                # Проверяем формат после обработки
                if result:
                    matches_regex = bool(re.match(street_validate_regex, result))
                    logger.info(f"Соответствует regex после обработки: {matches_regex}")

            except Exception as e:
                logger.info(f"Ошибка: {str(e)}")
