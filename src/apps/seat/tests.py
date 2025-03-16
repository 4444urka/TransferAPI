from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.vehicle.models import Vehicle
from apps.seat.models import Seat


class SeatViewSetTest(APITestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=3
        )
        self.seats = list(Seat.objects.filter(vehicle=self.vehicle))
        self.seat1 = self.seats[0]
        self.seat2 = self.seats[1]
        self.seat3 = self.seats[2]

        # Определяем URL-адреса, предполагая, что роутер зарегистрировал имена 'seat-list' и 'seat-detail'
        self.list_url = reverse('seat-list')
        self.detail_url = reverse('seat-detail', args=[self.seat1.id])

    def test_list_seats(self):
        """Проверка получения списка мест через API."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Исправляем ожидаемое количество мест с 3 на 4
        self.assertEqual(len(response.data), 4)

    def test_retrieve_seat(self):
        """Проверка получения деталей конкретного места."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.seat1.id)
    
    def test_create_seat_forbidden(self):
        """Проверка запрета создания места через API."""
        data = {
            "vehicle": self.vehicle.id,
            "seat_number": 4,
            "seat_type": "back",
            "is_booked": False
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_seat_forbidden(self):
        """Проверка запрета удаления места через API."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_seat_allowed_field_patch(self):
        """Проверка редактирования разрешенных полей через PATCH (например, изменение статуса бронирования)."""
        data = {
            "is_booked": True,
            "seat_type": "middle"
        }
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seat1.refresh_from_db()
        self.assertTrue(self.seat1.is_booked)
    
    def test_update_seat_forbidden_fields_patch(self):
        """
        Проверка, что попытка изменить запрещенные поля (vehicle и seat_number)
        через PATCH не приводит к их изменению.
        """
        data = {
            "vehicle": self.vehicle.id + 1,  
            "seat_number": 99,               
            "is_booked": True
        }
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seat1.refresh_from_db()
        # Проверяем, что запрещенные поля не изменились
        self.assertEqual(self.seat1.vehicle, self.vehicle)
        self.assertNotEqual(self.seat1.seat_number, 99)
    
    def test_put_update_forbidden_fields(self):
        """
        (1) Проверка, что при полном обновлении (PUT) запрещенные поля не изменяются.
        Даже если клиент попытается передать новые значения для 'vehicle' и 'seat_number',
        они должны остаться прежними.
        """
        original_vehicle = self.seat1.vehicle
        original_seat_number = self.seat1.seat_number
        original_is_booked = self.seat1.is_booked

        data = {
            "seat_type": self.seat1.seat_type,       
            "is_booked": not original_is_booked,       
            "vehicle": self.vehicle.id + 100,          
            "seat_number": 999                         
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seat1.refresh_from_db()
        # Запрещенные поля не изменились
        self.assertEqual(self.seat1.vehicle, original_vehicle)
        self.assertEqual(self.seat1.seat_number, original_seat_number)
        # Разрешенное поле изменилось
        self.assertEqual(self.seat1.is_booked, not original_is_booked)

    def test_put_update_allowed_fields(self):
        """
        (4) Проверка корректного обновления разрешенных полей через PUT.
        Обновляем поля 'seat_type' и 'is_booked' и проверяем, что изменения применены.
        """
        data = {
            "seat_type": "middle",
            "is_booked": True,
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.seat1.refresh_from_db()
        self.assertEqual(self.seat1.seat_type, "middle")
        self.assertEqual(self.seat1.is_booked, True)
    
    def test_retrieve_nonexistent_seat(self):
        """
        (3) Проверка обращения к несуществующему месту.
        Запрос деталей места с несуществующим id должен возвращать 404.
        """
        nonexistent_url = reverse('seat-detail', args=[10])
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    

