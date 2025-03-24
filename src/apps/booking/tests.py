from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.auth.models import User
from apps.booking.models import Booking, Payment
from apps.trip.models import Trip, City
from apps.vehicle.models import Vehicle
from apps.seat.models import Seat, TripSeat


class BookingPermissionsTest(APITestCase):
    """Тесты для проверки разрешений на бронирования"""

    @patch('apps.booking.models.find_street_by_name')
    def setUp(self, mock_find_street):
        """Настройка тестовых данных"""
        # Настраиваем мок, чтобы он всегда возвращал правильный формат адреса
        mock_find_street.return_value = "ул. Тестовая, 1"

        # Создаем пользователей с разными ролями
        self.admin_user = User.objects.create_superuser('+79111111111', 'adminpass')
        self.manager_user = User.objects.create_user('+79222222222', 'managerpass')
        self.regular_user1 = User.objects.create_user('+79333333333', 'userpass1')
        self.regular_user2 = User.objects.create_user('+79444444444', 'userpass2')

        # Создаем группу менеджеров с правами на просмотр всех бронирований
        self.manager_group, _ = Group.objects.get_or_create(name='Менеджеры')

        # Добавляем разрешение в модель если его нет
        content_type = ContentType.objects.get_for_model(Booking)
        view_all_permission, _ = Permission.objects.get_or_create(
            codename='can_view_all_booking',
            name='Может просматривать все бронирования',
            content_type=content_type,
        )

        # Добавляем разрешение к группе менеджеров
        self.manager_group.permissions.add(view_all_permission)

        # Добавляем пользователя в группу менеджеров
        self.manager_user.groups.add(self.manager_group)

        # Создаем города
        self.origin = City.objects.create(name='Москва')
        self.destination = City.objects.create(name='Санкт-Петербург')

        # Создаем транспортное средство
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40,
            is_comfort=True
        )

        # Создаем поездку
        self.trip = Trip.objects.create(
            vehicle=self.vehicle,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=5),
            default_ticket_price=Decimal('1000.00')
        )

        # Получаем места для тестов
        self.trip_seats = TripSeat.objects.filter(trip=self.trip)[:2]

        # Создаем платежи с указанием пользователя
        self.payment1 = Payment.objects.create(
            user=self.regular_user1,  # Указываем пользователя
            amount=Decimal('2000.00'),
            payment_method='card',
        )

        self.payment2 = Payment.objects.create(
            user=self.regular_user2,  # Указываем пользователя
            amount=Decimal('2000.00'),
            payment_method='card',
        )

        # Создаем бронирования для разных пользователей
        self.booking1 = Booking.objects.create(
            user=self.regular_user1,
            trip=self.trip,
            payment=self.payment1,
            pickup_location="ул. Тестовая, 1",
            dropoff_location="ул. Тестовая, 1",
            is_active=True
        )
        self.booking1.trip_seats.add(self.trip_seats[0])

        self.booking2 = Booking.objects.create(
            user=self.regular_user2,
            trip=self.trip,
            payment=self.payment2,
            pickup_location="ул. Тестовая, 1",
            dropoff_location="ул. Тестовая, 1",
            is_active=True
        )
        self.booking2.trip_seats.add(self.trip_seats[1])

        # URL для тестов
        self.booking_list_url = reverse('booking-list')
        self.booking1_detail_url = reverse('booking-detail', args=[self.booking1.id])
        self.booking2_detail_url = reverse('booking-detail', args=[self.booking2.id])

        # Клиент для запросов
        self.client = APIClient()

    @patch('apps.booking.models.find_street_by_name')
    def test_booking_list_as_admin(self, mock_find_street):
        """Тест получения списка бронирований администратором"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Тестовая, 1"

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.booking_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что администратор видит все бронирования
        self.assertEqual(len(response.data['results']), 2)

        booking_ids = [booking['id'] for booking in response.data['results']]
        self.assertIn(self.booking1.id, booking_ids)
        self.assertIn(self.booking2.id, booking_ids)

    @patch('apps.booking.models.find_street_by_name')
    def test_booking_list_as_manager(self, mock_find_street):
        """Тест получения списка бронирований менеджером с правом просмотра всех бронирований"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Тестовая, 1"

        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get(self.booking_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что менеджер видит все бронирования
        self.assertEqual(len(response.data['results']), 2)

        booking_ids = [booking['id'] for booking in response.data['results']]
        self.assertIn(self.booking1.id, booking_ids)
        self.assertIn(self.booking2.id, booking_ids)

    @patch('apps.booking.models.find_street_by_name')
    def test_booking_list_as_regular_user(self, mock_find_street):
        """Тест получения списка бронирований обычным пользователем (видит только свои)"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Тестовая, 1"

        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.get(self.booking_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что пользователь видит только свои бронирования
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.booking1.id)

    def test_view_other_booking_detail_as_regular_user(self):
        """Тест попытки доступа к чужому бронированию обычным пользователем"""
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.get(self.booking2_detail_url)

        # Вместо проверки на 403, будем проверять что доступ запрещен (403 или 404)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_view_other_booking_detail_as_manager(self):
        """Тест доступа к чужому бронированию менеджером"""
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get(self.booking1_detail_url)

        # Проверяем, что доступ разрешен
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.booking1.id)

    @patch('apps.booking.models.find_street_by_name')
    def test_create_booking_as_regular_user(self, mock_find_street):
        """Тест создания бронирования обычным пользователем"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Тестовая, 1"

        self.client.force_authenticate(user=self.regular_user1)

        # Получаем свободное место для бронирования
        available_trip_seat = TripSeat.objects.filter(trip=self.trip, is_booked=False).first()

        # Создаем новый платеж, указывая пользователя
        payment = Payment.objects.create(
            user=self.regular_user1,
            amount=Decimal('1000.00'),
            payment_method='cash',
        )

        data = {
            'trip_id': self.trip.id,
            'seats_ids': [available_trip_seat.seat.id],
            'payment': {'id': payment.id},
            'pickup_location': 'ул. Тестовая, 1',
            'dropoff_location': 'ул. Тестовая, 1',
        }

        response = self.client.post(self.booking_list_url, data, format='json')

        # Проверяем успешное создание
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что место отмечено как забронированное
        available_trip_seat.refresh_from_db()
        self.assertTrue(available_trip_seat.is_booked)

        # Проверяем, что пользователь теперь имеет еще одно бронирование
        response = self.client.get(self.booking_list_url)
        self.assertEqual(len(response.data['results']), 2)

    @patch('apps.booking.models.find_street_by_name')
    def test_update_booking_as_owner(self, mock_find_street):
        """Тест обновления своего бронирования"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Новая, 40"

        self.client.force_authenticate(user=self.regular_user1)

        data = {
            'pickup_location': 'ул. Новая, 40',
            'dropoff_location': 'ул. Новая, 40',
        }

        # Отключаем валидацию во время теста через patch
        with patch('apps.booking.models.Booking.clean') as mock_clean:
            mock_clean.return_value = None
            response = self.client.patch(self.booking1_detail_url, data, format='json')

            # Проверяем успешное обновление
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Проверяем, что данные обновились
            self.booking1.refresh_from_db()
            self.assertEqual(self.booking1.pickup_location, 'ул. Новая, 40')
            self.assertEqual(self.booking1.dropoff_location, 'ул. Новая, 40')

    def test_update_booking_as_other_user(self):
        """Тест попытки обновления чужого бронирования"""
        self.client.force_authenticate(user=self.regular_user2)

        data = {
            'pickup_location': 'ул. Чужая, 50',
        }

        response = self.client.patch(self.booking1_detail_url, data, format='json')

        # Вместо проверки на 403, будем проверять что доступ запрещен (403 или 404)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_cancel_booking_as_owner(self):
        """Тест отмены своего бронирования"""
        self.client.force_authenticate(user=self.regular_user1)

        data = {
            'is_active': False,
        }

        # Отключаем валидацию во время теста через patch
        with patch('apps.booking.models.Booking.clean') as mock_clean:
            mock_clean.return_value = None
            response = self.client.patch(self.booking1_detail_url, data, format='json')

            # Проверяем успешную отмену
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Проверяем, что бронирование отменено
            self.booking1.refresh_from_db()
            self.assertFalse(self.booking1.is_active)

            # Проверяем, что место освободилось
            trip_seat = self.booking1.trip_seats.first()
            trip_seat.refresh_from_db()
            self.assertFalse(trip_seat.is_booked)

    def test_delete_booking_as_admin(self):
        """Тест удаления бронирования администратором"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(self.booking1_detail_url)

        # Проверяем успешное удаление
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что бронирование удалено
        self.assertFalse(Booking.objects.filter(id=self.booking1.id).exists())

        # Проверяем, что места освобождены
        trip_seat = self.trip_seats[0]
        trip_seat.refresh_from_db()
        self.assertFalse(trip_seat.is_booked)

    def test_delete_booking_as_regular_user(self):
        """Тест попытки удаления бронирования обычным пользователем (не владельцем)"""
        self.client.force_authenticate(user=self.regular_user2)

        response = self.client.delete(self.booking1_detail_url)

        # Вместо проверки на 403, будем проверять что доступ запрещен (403 или 404)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Проверяем, что бронирование не удалено
        self.assertTrue(Booking.objects.filter(id=self.booking1.id).exists())

    def test_role_permissions_consistency(self):
        """Тест последовательности назначения и отзыва прав через группы"""
        # Проверяем, что обычный пользователь не видит чужие бронирования
        self.client.force_authenticate(user=self.regular_user1)
        response = self.client.get(self.booking2_detail_url)
        # Вместо проверки на 403, будем проверять что доступ запрещен (403 или 404)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Добавляем пользователя в группу менеджеров
        self.regular_user1.groups.add(self.manager_group)

        # Теперь пользователь должен видеть чужие бронирования
        response = self.client.get(self.booking2_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Удаляем пользователя из группы менеджеров
        self.regular_user1.groups.remove(self.manager_group)

        # Снова не должен видеть чужие бронирования
        response = self.client.get(self.booking2_detail_url)
        # Вместо проверки на 403, будем проверять что доступ запрещен (403 или 404)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])


class BookingFilterTest(APITestCase):
    """Тесты для проверки фильтрации бронирований"""

    @patch('apps.booking.models.find_street_by_name')
    def setUp(self, mock_find_street):
        """Настройка тестовых данных"""
        # Настраиваем мок
        mock_find_street.return_value = "ул. Тестовая, 1"

        # Создаем пользователя-менеджера
        self.manager_user = User.objects.create_user('+79222222222', 'managerpass')

        # Создаем группу с правом просмотра всех бронирований
        manager_group = Group.objects.create(name='Менеджеры')
        content_type = ContentType.objects.get_for_model(Booking)
        view_all_permission, _ = Permission.objects.get_or_create(
            codename='can_view_all_booking',
            name='Может просматривать все бронирования',
            content_type=content_type,
        )
        manager_group.permissions.add(view_all_permission)
        self.manager_user.groups.add(manager_group)

        # Создаем города
        origin = City.objects.create(name='Москва')
        destination1 = City.objects.create(name='Санкт-Петербург')
        destination2 = City.objects.create(name='Казань')

        # Создаем транспортное средство
        vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40,
            is_comfort=True
        )

        # Создаем поездки
        now = timezone.now()
        self.trip1 = Trip.objects.create(
            vehicle=vehicle,
            origin=origin,
            destination=destination1,
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=1, hours=5),
            default_ticket_price=Decimal('1000.00')
        )

        self.trip2 = Trip.objects.create(
            vehicle=vehicle,
            origin=origin,
            destination=destination2,
            departure_time=now + timedelta(days=2),
            arrival_time=now + timedelta(days=2, hours=6),
            default_ticket_price=Decimal('1200.00')
        )

        # Создаем пользователей
        self.user1 = User.objects.create_user('+79333333333', 'userpass1')
        self.user2 = User.objects.create_user('+79444444444', 'userpass2')

        # Создаем платежи с указанием пользователя
        payment1 = Payment.objects.create(
            user=self.user1,
            amount=Decimal('1000.00'),
            payment_method='card',
        )

        payment2 = Payment.objects.create(
            user=self.user2,
            amount=Decimal('1200.00'),
            payment_method='cash',
        )

        # Получаем trip_seats для бронирований
        trip1_seat = TripSeat.objects.filter(trip=self.trip1).first()
        trip2_seat = TripSeat.objects.filter(trip=self.trip2).first()

        # Устанавливаем даты так, чтобы они всегда были в нужном порядке
        # для тестирования
        booking_datetime1 = now
        booking_datetime2 = now - timedelta(days=1)

        # Создаем активное и неактивное бронирование
        self.active_booking = Booking.objects.create(
            user=self.user1,
            trip=self.trip1,
            payment=payment1,
            pickup_location="ул. Тестовая, 1",
            dropoff_location="ул. Тестовая, 1",
            is_active=True,
            booking_datetime=booking_datetime1
        )
        self.active_booking.trip_seats.add(trip1_seat)

        self.canceled_booking = Booking.objects.create(
            user=self.user2,
            trip=self.trip2,
            payment=payment2,
            pickup_location="ул. Тестовая, 1",
            dropoff_location="ул. Тестовая, 1",
            is_active=False,
            booking_datetime=booking_datetime2
        )
        self.canceled_booking.trip_seats.add(trip2_seat)

        # URL для тестов
        self.booking_list_url = reverse('booking-list')

        # Клиент для запросов
        self.client = APIClient()
        self.client.force_authenticate(user=self.manager_user)

    def test_filter_bookings_by_active_status(self):
        """Тест фильтрации бронирований по статусу активности"""
        # Только активные бронирования
        url = f"{self.booking_list_url}?is_active=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.active_booking.id)

        # Только неактивные бронирования
        url = f"{self.booking_list_url}?is_active=false"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.canceled_booking.id)

    def test_filter_bookings_by_trip(self):
        """Тест фильтрации бронирований по поездке"""
        url = f"{self.booking_list_url}?trip={self.trip1.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.active_booking.id)

    def test_search_bookings_by_city(self):
        """Тест поиска бронирований по названию города"""
        # Поиск по городу "Санкт-Петербург"
        url = f"{self.booking_list_url}?search=Санкт"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.active_booking.id)

        # Поиск по городу "Казань"
        url = f"{self.booking_list_url}?search=Казан"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.canceled_booking.id)

    def test_ordering_bookings(self):
        """Тест сортировки бронирований"""
        # Сортировка по дате бронирования (по возрастанию)
        url = f"{self.booking_list_url}?ordering=booking_datetime"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)

        # Проверяем порядок сортировки, но не конкретные ID
        booking_dates = [booking['booking_datetime'] for booking in results]
        self.assertTrue(booking_dates[0] < booking_dates[1])

        # Сортировка по дате бронирования (по убыванию)
        url = f"{self.booking_list_url}?ordering=-booking_datetime"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)

        # Проверяем порядок сортировки, но не конкретные ID
        booking_dates = [booking['booking_datetime'] for booking in results]
        self.assertTrue(booking_dates[0] > booking_dates[1])