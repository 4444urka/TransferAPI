import os
import sys
import django
import logging

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from utils.find_street_by_name import find_street_by_name
from utils.street_validate_regex import street_validate_regex
import re

def test_find_street():
    # Тестовые случаи
    test_cases = [
        # Простые адреса
        ("ул. Ленина 10", "Владивосток"),
        ("Светланская 10", "Владивосток"),
        ("проспект 100-летия Владивостока 12", "Владивосток"),
        
        # Адреса с корпусами
        ("ул. Ленина 10 к 2", "Владивосток"),
        ("Светланская 10к2", "Владивосток"),
        ("Светланская 10 корпус 2", "Владивосток"),
        
        # Нестандартные форматы
        ("Ленина д 10", "Владивосток"),
        ("ул Ленина дом 10", "Владивосток"),
        ("улица Ленина 10", "Владивосток"),
        
        # Сложные случаи
        ("100-летия Владивостока 12", "Владивосток"),
        ("Океанский проспект 10", "Владивосток"),
        ("Океанский пр-т 10", "Владивосток"),
        ("пр-т 100-летия Владивостока 12", "Владивосток"),
        
        # Тест с разными городами
        ("ул. Ленина 10", "Уссурийск"),
        ("ул. Ленина 10", "Артем"),
        
        # Тест с некорректными данными
        ("", "Владивосток"),
        ("ул. Несуществующая 10", "Владивосток"),
        ("ул. Ленина", "Владивосток"),  # без номера дома
        ("10", "Владивосток"),  # только номер
    ]

    print("\nНачинаем тестирование find_street_by_name:")
    print("-" * 50)

    for street, city in test_cases:
        print(f"\nТестируем: '{street}' в городе '{city}'")
        
        # Проверяем формат до обработки
        if street:
            matches_regex = bool(re.match(street_validate_regex, street))
            print(f"Соответствует regex до обработки: {matches_regex}")
        
        try:
            result = find_street_by_name(street, city)
            print(f"Результат: {result}")
            
            # Проверяем формат после обработки
            if result:
                matches_regex = bool(re.match(street_validate_regex, result))
                print(f"Соответствует regex после обработки: {matches_regex}")
            
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    print("\nТестирование завершено")

if __name__ == "__main__":
    test_find_street() 