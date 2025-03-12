from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta

from apps.trip.models import Trip, City
from apps.vehicle.models import Vehicle
from apps.seat.models import Seat


class TripViewSetTest(APITestCase):
    def setUp(self):
        # Создание городов
        self.origin = City.objects.create(name='Владивосток')
        self.destination = City.objects.create(name='Уссурийск')
        self.another_city = City.objects.create(name='Арсеньев')

        # Создание транспортного средства
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=10
        )

        # Создание поездок
        self.trip = Trip.objects.create(
            vehicle=self.vehicle,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=2),  # 2 часа до Уссурийска
            default_ticket_price=1000.00
        )

        self.future_trip = Trip.objects.create(
            vehicle=self.vehicle,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + timedelta(days=2),
            arrival_time=timezone.now() + timedelta(days=2, hours=2),
            default_ticket_price=1000.00
        )

        # URL для тестов
        self.trip_list_url = reverse('trip-list')
        self.trip_detail_url = reverse('trip-detail', args=[self.trip.id])

    def test_list_trips(self):
        """Тест получения списка поездок"""
        response = self.client.get(self.trip_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что все будущие поездки включены в список
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['id'], self.trip.id)

    def test_trip_detail(self):
        """Тест получения детальной информации о поездке"""
        response = self.client.get(self.trip_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверка основных полей
        self.assertEqual(response.data['id'], self.trip.id)
        self.assertEqual(response.data['origin']['name'], self.origin.name)
        self.assertEqual(response.data['destination']['name'], self.destination.name)
        self.assertEqual(response.data['vehicle']['license_plate'], self.vehicle.license_plate)
        
        # Проверка наличия информации о местах
        self.assertIn('seats', response.data)
        self.assertEqual(len(response.data['seats']), self.vehicle.total_seats)

    def test_filter_by_cities(self):
        """Тест фильтрации поездок по городам"""
        # Фильтр по городу отправления
        response = self.client.get(f"{self.trip_list_url}?origin={self.origin.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Фильтр по городу назначения
        response = self.client.get(f"{self.trip_list_url}?destination={self.destination.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # Фильтр по несуществующему маршруту
        response = self.client.get(
            f"{self.trip_list_url}?origin={self.origin.id}&destination={self.another_city.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_by_date(self):
        """Тест фильтрации поездок по дате"""
        tomorrow = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f"{self.trip_list_url}?date={tomorrow}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Проверка фильтрации по будущей дате
        day_after_tomorrow = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.get(f"{self.trip_list_url}?date={day_after_tomorrow}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_available_seats_calculation(self):
        """Тест расчета доступных мест"""
        # Бронируем несколько мест
        seats = Seat.objects.filter(vehicle=self.vehicle)[:2]
        for seat in seats:
            seat.is_booked = True
            seat.save()

        response = self.client.get(self.trip_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available_seats'], self.vehicle.total_seats - 2)

    def test_duration_calculation(self):
        """Тест расчета длительности поездки"""
        response = self.client.get(self.trip_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['duration'], "2ч 0мин")


class TripPaginationTest(APITestCase):
    def setUp(self):
        # Создаем город и транспортное средство
        self.city = City.objects.create(name="Test City")
        self.vehicle = Vehicle.objects.create(
            vehicle_type="bus",
            license_plate="Т123ТТ",
            total_seats=40
        )
        # Создаем 30 поездок
        for i in range(30):
            Trip.objects.create(
                vehicle=self.vehicle,
                origin=self.city,
                destination=self.city,
                departure_time=timezone.now() + timedelta(days=1+i),
                arrival_time=timezone.now() + timedelta(days=1+i, hours=2),
                default_ticket_price=100.00
            )
        self.trips_url = reverse("trip-list") 

    def test_trip_pagination(self):
        response = self.client.get(self.trips_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Проверяем, что на странице максимум 20 записей
        self.assertLessEqual(len(data.get("results", [])), 20)
        # Проверяем наличие ключей пагинации
        self.assertIn("count", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
