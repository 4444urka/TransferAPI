from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta

from apps.booking.models import Booking
from apps.seat.models import Seat
from apps.trip.models import Trip, City
from apps.vehicle.models import Vehicle

User = get_user_model()


class BookingViewSetTest(APITestCase):
    def setUp(self):
        # Создание пользователей
        self.admin_user = User.objects.create_superuser('+79111111111', 'adminpass')
        self.regular_user1 = User.objects.create_user('+79111111112', 'user1pass')
        self.regular_user2 = User.objects.create_user('+79111111113', 'user2pass')

        # Создание городов
        self.origin = City.objects.create(name='Origin City')
        self.destination = City.objects.create(name='Destination City')

        # Создание транспортного средства
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=3  # Нам понадобится 3 места для тестов
        )

        # Создание поездки
        self.trip = Trip.objects.create(
            vehicle=self.vehicle,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=2),
            default_ticket_price=100.00
        )

        # Получение мест, созданных сигналом vehicle
        self.seats = Seat.objects.filter(vehicle=self.vehicle)
        self.seat1, self.seat2, self.seat3 = self.seats

        # Отметим первые два места как забронированные
        self.seat1.is_booked = True
        self.seat1.save()
        self.seat2.is_booked = True
        self.seat2.save()

        # Создание бронирований
        self.booking1 = Booking.objects.create(
            user=self.regular_user1,
            trip=self.trip,
            is_active=True
        )
        self.booking1.seats.add(self.seat1)

        self.booking2 = Booking.objects.create(
            user=self.regular_user2,
            trip=self.trip,
            is_active=True
        )
        self.booking2.seats.add(self.seat2)

        self.inactive_booking = Booking.objects.create(
            user=self.regular_user1,
            trip=self.trip,
            is_active=False
        )

        # Определение URL-адресов
        self.booking_list_url = reverse('booking-list')
        self.booking1_detail_url = reverse('booking-detail', args=[self.booking1.id])
        self.booking2_detail_url = reverse('booking-detail', args=[self.booking2.id])
        self.booking1_cancel_url = reverse('booking-cancel', args=[self.booking1.id])
        self.inactive_booking_cancel_url = reverse('booking-cancel', args=[self.inactive_booking.id])

    def test_authentication_required(self):
        """Неаутентифицированные пользователи не могут получить доступ к бронированиям"""
        response = self.client.get(self.booking_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_see_all_bookings(self):
        """Администраторы могут видеть все бронирования"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.booking_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем количество в ответе
        count = len(response.data) if isinstance(response.data, list) else response.data.get('count', 0)
        self.assertEqual(count, 3)  # Всего 3 бронирования

    def test_user_can_only_see_own_bookings(self):
        """Обычные пользователи могут видеть только свои бронирования"""
        # Тест user1
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.get(self.booking_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        count = len(response.data) if isinstance(response.data, list) else response.data.get('count', 0)
        self.assertEqual(count, 2)  # У User1 есть 2 бронирования (1 активное, 1 неактивное)

        # Тест user2
        self.client.force_authenticate(user=self.regular_user2)
        response = self.client.get(self.booking_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        count = len(response.data) if isinstance(response.data, list) else response.data.get('count', 0)
        self.assertEqual(count, 1)  # У User2 есть 1 бронирование

    def test_user_cannot_access_others_booking(self):
        """Пользователи не могут получить доступ к бронированиям других пользователей"""
        self.client.force_authenticate(user=self.regular_user2)
        response = self.client.get(self.booking1_detail_url)  # Booking1 принадлежит user1
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_serializer_class_selection(self):
        """Проверка выбора правильного сериализатора в зависимости от действия"""
        self.client.force_authenticate(user=self.regular_user1)

        # Список должен использовать BookingSerializer
        list_response = self.client.get(self.booking_list_url)

        # Детали должны использовать BookingDetailSerializer
        detail_response = self.client.get(self.booking1_detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

        # Детальный ответ должен иметь больше полей, чем ответ списка
        list_item = list_response.data[0] if isinstance(list_response.data, list) else list_response.data['results'][0]
        detail_item = detail_response.data

        self.assertTrue(len(detail_item) >= len(list_item))

    def test_create_booking_assigns_current_user(self):
        """Проверка автоматического назначения пользователя при создании бронирования"""
        self.client.force_authenticate(user=self.regular_user1)

        data = {
            'trip_id': self.trip.id,  # Используем trip_id на основе сериализатора
            'seats_ids': [self.seat3.id]  # Используем seats_ids на основе сериализатора
        }

        response = self.client.post(self.booking_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем создание бронирования
        booking_id = response.data.get('id')
        booking = Booking.objects.get(id=booking_id)
        
        # Проверяем, правильно ли назначен пользователь
        self.assertEqual(booking.user, self.regular_user1)

    def test_cancel_booking(self):
        """Проверка отмены активного бронирования"""
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.post(self.booking1_cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "Бронирование успешно отменено")

        # Проверяем, что бронирование теперь неактивно
        self.booking1.refresh_from_db()
        self.assertFalse(self.booking1.is_active)

        # Проверяем, что место больше не забронировано
        self.seat1.refresh_from_db()
        self.assertFalse(self.seat1.is_booked)

    def test_cancel_inactive_booking(self):
        """Проверка попытки отмены уже неактивного бронирования"""
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.post(self.inactive_booking_cancel_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Бронирование уже отменено")

    def test_filtering_and_search(self):
        """Проверка функциональности фильтрации и поиска"""
        self.client.force_authenticate(user=self.regular_user1)

        # Проверка фильтрации по is_active
        response = self.client.get(f"{self.booking_list_url}?is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка фильтрации по trip
        response = self.client.get(f"{self.booking_list_url}?trip={self.trip.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка поиска по имени города отправления
        response = self.client.get(f"{self.booking_list_url}?search={self.origin.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering(self):
        """Проверка функциональности сортировки"""
        self.client.force_authenticate(user=self.regular_user1)

        # Сортировка по умолчанию (сначала новые)
        response = self.client.get(self.booking_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Явная сортировка по дате бронирования
        response = self.client.get(f"{self.booking_list_url}?ordering=booking_datetime")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Сортировка по времени отправления рейса
        response = self.client.get(f"{self.booking_list_url}?ordering=trip__departure_time")
        self.assertEqual(response.status_code, status.HTTP_200_OK)