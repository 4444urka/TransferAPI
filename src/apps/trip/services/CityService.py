import logging

from apps.trip.models import City


class CityService:
    """
    Сервисный слой для работы с городами.
    """
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        
    def get_all(self):
        """
        Получение списка городов.
        """
        try:
            cities = City.objects.all()
            self.logger.info("Cities list successfully retrieved")
            return cities
        except Exception as e:
            self.logger.error(f"Error while retrieving cities list. Exception: {e}")
            raise
        
    def get_by_id(self, city_id):
        """
        Получение города по ID.
        """
        try:
            city = City.objects.get(id=city_id)
            self.logger.info(f"City successfully retrieved: {city}")
            return city
        except City.DoesNotExist:
            self.logger.error(f"City with id {city_id} does not exist")
            raise
        except Exception as e:
            self.logger.error(f"Error while retrieving city by id. Exception: {e}")
            raise
        
    def get_by_name(self, name):
        """
        Получение города по имени.
        """
        try:
            city = City.objects.get(name=name)
            self.logger.info(f"City successfully retrieved: {city}")
            return city
        except City.DoesNotExist:
            self.logger.error(f"City with name {name} does not exist")
            raise
        except Exception as e:
            self.logger.error(f"Error while retrieving city by name. Exception: {e}")
            raise
    
    