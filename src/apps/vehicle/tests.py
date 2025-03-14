import logging

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from datetime import timezone as datetime_timezone
from urllib.parse import quote

from apps.vehicle.models import Vehicle
from apps.trip.models import Trip, City

User = get_user_model()
logger = logging.getLogger(__name__)


class VehicleViewSetTest(APITestCase):
    def setUp(self):
        Vehicle.objects.all().delete()
        Trip.objects.all().delete()
        City.objects.all().delete()
        User.objects.all().delete()

        # Создание пользователей
        self.admin_user = User.objects.create_superuser('+79111111111', 'adminpass')
        self.regular_user = User.objects.create_user('+79111111112', 'userpass')

        # Создание транспортных средств
        self.vehicle1 = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40,
            is_comfort=True,
            air_conditioning=True,
            allows_pets=False
        )

        self.vehicle2 = Vehicle.objects.create(
            vehicle_type='minibus',
            license_plate='В456ВВ',
            total_seats=20,
            is_comfort=False,
            air_conditioning=True,
            allows_pets=True
        )

        # URL для тестов
        self.vehicle_list_url = reverse('vehicle-list')
        self.vehicle_detail_url = reverse('vehicle-detail', args=[self.vehicle1.id])
        self.vehicle_availability_url = reverse('vehicle-availability', args=[self.vehicle1.id])

    def tearDown(self):
        Vehicle.objects.all().delete()
        Trip.objects.all().delete()
        City.objects.all().delete()
        User.objects.all().delete()

    def test_authentication_required(self):
        """Неаутентифицированные пользователи не могут получить доступ к транспортным средствам"""
        response = self.client.get(self.vehicle_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_vehicles(self):
        """Аутентифицированные пользователи могут получить список транспортных средств"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.vehicle_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_vehicle_detail(self):
        """Аутентифицированные пользователи могут получить детальную информацию о транспортном средстве"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.vehicle_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['license_plate'], self.vehicle1.license_plate)

    def test_create_vehicle_admin_only(self):
        """Только администраторы могут создавать транспортные средства"""
        # Попытка создания обычным пользователем
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'vehicle_type': 'car',
            'license_plate': 'Е789ЕЕ',
            'total_seats': 4,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }
        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Создание администратором
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.count(), 3)

    def test_update_vehicle_admin_only(self):
        """Только администраторы могут обновлять транспортные средства"""
        # Попытка обновления обычным пользователем
        self.client.force_authenticate(user=self.regular_user)
        data = {'total_seats': 45}
        response = self.client.patch(self.vehicle_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Обновление администратором
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(self.vehicle_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.total_seats, 45)

    def test_delete_vehicle_admin_only(self):
        """Только администраторы могут удалять транспортные средства"""
        # Попытка удаления обычным пользователем
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(self.vehicle_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Удаление администратором
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.vehicle_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_filter_vehicles(self):
        """Тест фильтрации транспортных средств"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Фильтр по типу транспорта
        response = self.client.get(f"{self.vehicle_list_url}?vehicle_type=bus")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Фильтр по комфорту
        response = self.client.get(f"{self.vehicle_list_url}?is_comfort=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Фильтр по разрешению на перевозку животных
        response = self.client.get(f"{self.vehicle_list_url}?allows_pets=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_vehicles(self):
        """Тест поиска транспортных средств по номеру"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.vehicle_list_url}?search=А123")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_ordering_vehicles(self):
        """Тест сортировки транспортных средств"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Сортировка по количеству мест (по возрастанию)
        response = self.client.get(f"{self.vehicle_list_url}?ordering=total_seats")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['total_seats'], 20)

        # Сортировка по количеству мест (по убыванию)
        response = self.client.get(f"{self.vehicle_list_url}?ordering=-total_seats")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['total_seats'], 40)

    def test_vehicle_availability(self):
        """Тест проверки доступности транспортного средства"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Создаем города для тестовой поездки
        city1 = City.objects.create(name='Москва')
        city2 = City.objects.create(name='Санкт-Петербург')
        
        # Создаем тестовую поездку
        now = timezone.now()
        future_time = now + timedelta(hours=24)  # Увеличиваем запас времени до 24 часов
        
        trip = Trip.objects.create(
            vehicle=self.vehicle1,
            origin=city1,
            destination=city2,
            departure_time=future_time + timedelta(hours=1),
            arrival_time=future_time + timedelta(hours=6),
            default_ticket_price=1000
        )
        
        logger.info(f"\nTrip departure_time: {trip.departure_time}")
        logger.info(f"Trip arrival_time: {trip.arrival_time}")
        
        # Тест 1: Проверка доступности в свободное время
        test1_start = future_time + timedelta(hours=7)
        test1_end = future_time + timedelta(hours=9)
        start_time = quote(test1_start.astimezone(datetime_timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+0000'))
        end_time = quote(test1_end.astimezone(datetime_timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+0000'))
        
        logger.info(f"Test 1 start_time: {test1_start}")
        logger.info(f"Test 1 end_time: {test1_end}")
        
        response = self.client.get(
            f"{self.vehicle_availability_url}?start_time={start_time}&end_time={end_time}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
        
        # Тест 2: Проверка недоступности в занятое время
        test2_start = future_time + timedelta(hours=2)
        test2_end = future_time + timedelta(hours=4)
        start_time = quote(test2_start.astimezone(datetime_timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+0000'))
        end_time = quote(test2_end.astimezone(datetime_timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+0000'))
        
        logger.info(f"Test 2 start_time: {test2_start}")
        logger.info(f"Test 2 end_time: {test2_end}")
        
        response = self.client.get(
            f"{self.vehicle_availability_url}?start_time={start_time}&end_time={end_time}"
        )
        logger.info(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['available'])
