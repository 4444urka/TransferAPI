from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.auth.models import User
from apps.booking.models import Booking, Payment
from apps.trip.models import Trip, City
from apps.vehicle.models import Vehicle
from apps.seat.models import TripSeat, Seat

User = get_user_model()

class BookingAPITest(APITestCase):
    """
    Проверка эндпоинтов
    """
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем пользователя
        self.user = User.objects.create_user('+79111111111', 'userpass')
        
        # Создаем города
        origin = City.objects.create(name='Москва')
        destination = City.objects.create(name='Санкт-Петербург')
        
        # Создаем транспортное средство
        vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40,
            is_comfort=True
        )
        
        # Создаем поездку
        self.trip = Trip.objects.create(
            vehicle=vehicle,
            origin=origin,
            destination=destination,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=5),
            front_seat_price=Decimal('1000.00'),
            middle_seat_price=Decimal('1000.00'),
            back_seat_price=Decimal('1000.00')
        )
        
        # URL для тестов
        self.booking_list_url = reverse('booking-list')
        
        # Клиент для запросов
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    @patch('utils.address.find_street_by_name')
    def test_create_booking(self, mock_find_street):
        """Тест создания бронирования"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Тестовая, 1"
        
        # Получаем свободное место для бронирования
        available_trip_seat = TripSeat.objects.filter(trip=self.trip, is_booked=False).first()
        
        # Создаем платеж
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            payment_method='card',
        )
        
        data = {
            'trip_id': self.trip.id,
            'seat_numbers': [available_trip_seat.seat.seat_number],
            'payment': {'id': payment.id},
            'pickup_location': 'ул. Тестовая, 1',
            'dropoff_location': 'ул. Тестовая, 2',
        }
        
        response = self.client.post(self.booking_list_url, data, format='json')
        
        # Выводим данные для отладки в случае ошибки
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        # Проверяем успешное создание
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что место отмечено как забронированное
        available_trip_seat.refresh_from_db()
        self.assertTrue(available_trip_seat.is_booked)