import requests
from bot.setup import config

class ApiClient:
    @staticmethod
    def authenticate(phone, password):
        data = {
            "phone_number": phone,
            "password": password
        }
        response = requests.post(config.TOKEN_URL, data)

        return response.json() if response.ok else None

    @staticmethod
    def refresh_tokens(refresh_token):
        data = {
            "refresh": refresh_token
        }
        response = requests.post(config.REFRESH_URL, data) 
        return response.json() if response.ok else None
    
    @staticmethod
    def get_bookings(access_token):
        response = requests.get(
            config.BOOKINGS_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json() if response.ok else None
    
    