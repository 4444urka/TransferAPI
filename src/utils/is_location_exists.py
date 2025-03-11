import requests


def is_location_exists(street: str, city: str = None) -> bool:
    headers = {
        'User-Agent': 'Armada (contact@example.com)'  # Обязательно укажите свои данные
    }

    params = {
        'format': 'json',
        'city': city,
        'street': street,
        'addressdetails': 1,
        'countrycodes': 'ru',
        'limit': 5,
        'accept-language': 'ru'
    }

    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params=params,
            headers=headers,
            timeout=10
        )
        return True if response.json() else False
    except Exception as e:
        raise e


print(is_location_exists("Шилкинская", "Артём"))