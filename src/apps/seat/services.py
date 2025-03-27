import logging
from typing import List, Optional

from django.core.exceptions import ValidationError
from .models import Seat
from apps.vehicle.models import Vehicle

class SeatService:
    """
    Сервис для работы с моделью Seat.
    Предоставляет методы для выполнения операций с местами.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_all_seats(self) -> List[Seat]:
        """
        Получить список всех мест.
        """
        self.logger.debug("Получение списка всех мест")
        try:
            seats = Seat.objects.all()
            self.logger.info(f"Найдено мест: {seats.count()}")
            return list(seats)
        except Exception as e:
            self.logger.error(f"Ошибка при получении мест: {e}")
            raise

    def get_seat_by_id(self, seat_id: int) -> Optional[Seat]:
        """
        Получить место по его идентификатору.
        """
        self.logger.debug(f"Получение места с id: {seat_id}")
        try:
            seat = Seat.objects.get(id=seat_id)
            self.logger.info(f"Место с id {seat_id} найдено")
            return seat
        except Seat.DoesNotExist:
            self.logger.error(f"Место с id {seat_id} не найдено")
            raise
        except Exception as e:
            self.logger.error(f"Ошибка при получении места: {e}")
            raise

    def update_seat(self, seat_id: int, data: dict) -> Seat:
        """
        Обновить данные места.
        Выполняется обновление только разрешенных полей (например, is_booked, seat_type).
        """
        self.logger.debug(f"Обновление места с id {seat_id}")
        try:
            seat = self.get_seat_by_id(seat_id)
            
            # Обновляем только разрешенные поля
            allowed_fields = ['seat_type']
            updated_fields = []
            for field in allowed_fields:
                if field in data:
                    setattr(seat, field, data[field])
                    updated_fields.append(field)
            
            if updated_fields:
                seat.save(update_fields=updated_fields)
                self.logger.info(f"Место с id {seat_id} обновлено: {', '.join(updated_fields)}")
            return seat
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении места с id {seat_id}: {e}")
            raise ValidationError(f"Ошибка обновления места: {str(e)}")

    def get_seats_by_vehicle(self, vehicle_id: int) -> List[Seat]:
        """
        Получить список мест для конкретного транспортного средства.
        """
        self.logger.debug(f"Получение мест для транспортного средства с id: {vehicle_id}")
        try:
            # Проверяем, существует ли транспортное средство
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            seats = Seat.objects.filter(vehicle=vehicle)
            self.logger.info(f"Найдено мест для транспортного средства {vehicle_id}: {seats.count()}")
            return list(seats)
        except Vehicle.DoesNotExist:
            self.logger.error(f"Транспортное средство с id {vehicle_id} не найдено")
            raise
        except Exception as e:
            self.logger.error(f"Ошибка при получении мест для транспортного средства: {e}")
            raise