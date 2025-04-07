from django.core.cache import cache

class Config:
    BOT_TOKEN='7553600402:AAFvb8DvJQXpCsrmoABNtw0qw-q8R6izMNw'
    API_BASE = "http://web:8000"
    
    TOKEN_URL = f"{API_BASE}/auth/token/"
    REFRESH_URL = f"{API_BASE}/auth/token/refresh/"
    GET_USER_INFO_URL = f"{API_BASE}/auth/users/get_user_info/"

    BOOKINGS_URL = f"{API_BASE}/api/bookings/"

    def USER_UPDATE_URL(self, user_id):
        return f"{self.API_BASE}/auth/users/{user_id}/update/"
    
    @staticmethod
    def store_user_data(chat_id, data):
        cache.set(f"user:{chat_id}", data)
    
    @staticmethod
    def get_user_data(chat_id):
        return cache.get(f"user:{chat_id}")
    
    @staticmethod
    def delete_user_data(chat_id):
        cache.delete(f"user:{chat_id}")

config = Config()