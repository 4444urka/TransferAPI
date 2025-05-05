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
            config.ACTIVE_BOOKINGS_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json() if response.ok else None
    
    @staticmethod
    def get_trips(access_token):
        response = requests.get(
            config.TRIPS_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json() if response.ok else None
    
    @staticmethod
    def update_chat_id(access_token, user_id, chat_id=''):
        data={
            "chat_id": chat_id
        }
        response = requests.patch(
            config.USER_UPDATE_URL(user_id=user_id),
            data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json() if response.ok else None
    
    @staticmethod
    def get_user_info(access_token):
        response = requests.get(
            config.GET_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return response.json() if response.ok else None

    