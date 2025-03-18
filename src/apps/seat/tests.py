from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.auth.models import User
from apps.seat.models import Seat, TripSeat
from apps.trip.models import Trip, City
from apps.vehicle.models import Vehicle


class SeatModelTest(TestCase):
    """Тесты для модели Seat"""

    def setUp(self):
        # Создаем транспортное средство
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40,
            is_comfort=True,
            air_conditioning=True
        )

        # Получаем места, созданные сигналом manage_seats
        self.seats = Seat.objects.filter(vehicle=self.vehicle)

    def test_seat_creation_by_signal(self):
        """Тест автоматического создания мест при создании транспортного средства"""
        # Проверяем, что создано правильное количество мест
        self.assertEqual(self.seats.count(), self.vehicle.total_seats)

        # Проверяем, что первое место имеет тип "front"
        first_seat = self.seats.order_by('seat_number').first()
        self.assertEqual(first_seat.seat_type, "front")

        # Проверяем, что остальные места имеют тип "back"
        back_seats = self.seats.filter(seat_number__gt=1)
        for seat in back_seats:
            self.assertEqual(seat.seat_type, "back")

    def test_seat_str_representation(self):
        """Тест строкового представления места"""
        seat = self.seats.first()
        expected_str = f"{self.vehicle} - Место {seat.seat_number} ({seat.get_seat_type_display()})"
        self.assertEqual(str(seat), expected_str)

    def test_seat_unique_constraint(self):
        """Тест уникальности комбинации vehicle + seat_number"""
        existing_seat = self.seats.first()

        # Пробуем создать место с тем же номером для того же транспортного средства
        with self.assertRaises(Exception):
            Seat.objects.create(
                vehicle=self.vehicle,
                seat_number=existing_seat.seat_number,
                seat_type="back"
            )

    def test_seat_number_validation(self):
        """Тест валидации номера места"""
        # Попытка создать место с отрицательным номером
        seat = Seat(vehicle=self.vehicle, seat_number=-1, seat_type="back")
        with self.assertRaises(ValidationError):
            seat.full_clean()

        # Попытка создать место с номером больше, чем общее количество мест
        seat = Seat(vehicle=self.vehicle, seat_number=self.vehicle.total_seats + 1, seat_type="back")
        with self.assertRaises(ValidationError):
            seat.full_clean()

    def test_seat_deletion_restriction(self):
        """Тест запрета на удаление отдельного места"""
        seat = self.seats.first()

        # Попытка удалить место должна вызывать ValidationError
        with self.assertRaises(ValidationError):
            seat.delete()

    def test_vehicle_update_seats_count(self):
        """Тест обновления количества мест при изменении транспортного средства"""
        # Исходное количество мест
        original_count = self.vehicle.total_seats

        # Увеличиваем количество мест
        self.vehicle.total_seats += 5
        self.vehicle.save()

        # Проверяем, что места добавились
        updated_seats_count = Seat.objects.filter(vehicle=self.vehicle).count()
        self.assertEqual(updated_seats_count, original_count + 5)

        # Уменьшаем количество мест (до изначального)
        self.vehicle.total_seats = original_count
        self.vehicle.save()

        # Проверяем, что количество мест вернулось к исходному
        updated_seats_count = Seat.objects.filter(vehicle=self.vehicle).count()
        self.assertEqual(updated_seats_count, original_count)


class TripSeatModelTest(TestCase):
    """Тесты для модели TripSeat"""

    def setUp(self):
        # Создаем города
        self.origin = City.objects.create(name='Москва')
        self.destination = City.objects.create(name='Санкт-Петербург')

        # Создаем транспортное средство
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40
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

        # Получаем места для транспортного средства
        self.seats = Seat.objects.filter(vehicle=self.vehicle)

    def test_trip_seat_creation_by_signal(self):
        """Тест автоматического создания TripSeat при создании поездки"""
        # Проверяем, что для каждого места в транспортном средстве создан TripSeat
        trip_seats = TripSeat.objects.filter(trip=self.trip)
        self.assertEqual(trip_seats.count(), self.seats.count())

        # Проверяем, что все места изначально не забронированы
        for trip_seat in trip_seats:
            self.assertFalse(trip_seat.is_booked)

    def test_trip_seat_booking_status(self):
        """Тест установки статуса бронирования для TripSeat"""
        # Берем первый TripSeat
        trip_seat = TripSeat.objects.filter(trip=self.trip).first()

        # Бронируем место
        trip_seat.is_booked = True
        trip_seat.save()

        # Проверяем, что место действительно забронировано
        refreshed_trip_seat = TripSeat.objects.get(pk=trip_seat.pk)
        self.assertTrue(refreshed_trip_seat.is_booked)

        # Проверяем работу метода is_booked_for_trip
        seat = trip_seat.seat
        self.assertTrue(seat.is_booked_for_trip(self.trip))

    def test_trip_seat_str_representation(self):
        """Тест строкового представления TripSeat"""
        trip_seat = TripSeat.objects.filter(trip=self.trip).first()
        expected_str = f"{self.trip} - {trip_seat.seat} - Свободно"
        self.assertEqual(str(trip_seat), expected_str)

        # Бронируем место и проверяем изменение строки
        trip_seat.is_booked = True
        trip_seat.save()
        expected_str = f"{self.trip} - {trip_seat.seat} - Забронировано"
        self.assertEqual(str(trip_seat), expected_str)

    def test_multiple_trips_same_seat(self):
        """Тест возможности использования одного и того же места на разных поездках"""
        # Создаем вторую поездку
        trip2 = Trip.objects.create(
            vehicle=self.vehicle,
            origin=self.origin,
            destination=self.destination,
            departure_time=timezone.now() + timedelta(days=2),
            arrival_time=timezone.now() + timedelta(days=2, hours=5),
            default_ticket_price=Decimal('1000.00')
        )

        # Выбираем одно место для тестов
        test_seat = self.seats.first()

        # Получаем TripSeat для этого места в разных поездках
        trip_seat1 = TripSeat.objects.get(trip=self.trip, seat=test_seat)
        trip_seat2 = TripSeat.objects.get(trip=trip2, seat=test_seat)

        # Бронируем место в первой поездке
        trip_seat1.is_booked = True
        trip_seat1.save()

        # Проверяем, что место забронировано только для первой поездки
        self.assertTrue(test_seat.is_booked_for_trip(self.trip))
        self.assertFalse(test_seat.is_booked_for_trip(trip2))

        # Бронируем место и во второй поездке
        trip_seat2.is_booked = True
        trip_seat2.save()

        # Проверяем, что место теперь забронировано для обеих поездок
        self.assertTrue(test_seat.is_booked_for_trip(self.trip))
        self.assertTrue(test_seat.is_booked_for_trip(trip2))


class SeatAPITest(APITestCase):
    """Тесты для API мест"""

    def setUp(self):
        # Создаем пользователей
        self.admin_user = User.objects.create_superuser('+79111111111', 'adminpass')
        self.regular_user = User.objects.create_user('+79111111112', 'userpass')

        # Создаем транспортное средство с местами
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=10
        )

        # Получаем все места
        self.seats = Seat.objects.filter(vehicle=self.vehicle)
        self.seat1 = self.seats.order_by('seat_number').first()
        self.seat2 = self.seats.order_by('seat_number')[1]

        # Создаем поездки
        self.trip = Trip.objects.create(
            vehicle=self.vehicle,
            origin=City.objects.create(name='Москва'),
            destination=City.objects.create(name='Санкт-Петербург'),
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=5),
            default_ticket_price=Decimal('1000.00')
        )

        # Получаем TripSeat
        self.trip_seats = TripSeat.objects.filter(trip=self.trip)

        # URL для тестов
        self.seat_list_url = reverse('seat-list')
        self.seat_detail_url = reverse('seat-detail', args=[self.seat1.id])
        self.seats_by_vehicle_url = reverse('seat-get-seats-by-vehicle', args=[self.vehicle.id])

        # Клиент для авторизованных запросов
        self.client = APIClient()

    def test_list_seats(self):
        """Тест получения списка всех мест"""
        response = self.client.get(self.seat_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем наличие всех мест, учитывая возможную пагинацию
        if 'results' in response.data:
            # Если включена пагинация
            self.assertEqual(response.data['count'], self.seats.count())
        else:
            # Если пагинация отключена
            self.assertEqual(len(response.data), self.seats.count())

    def test_retrieve_seat(self):
        """Тест получения информации о конкретном месте"""
        response = self.client.get(self.seat_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.seat1.id)
        self.assertEqual(response.data['vehicle'], self.vehicle.id)
        self.assertEqual(response.data['seat_number'], self.seat1.seat_number)
        self.assertEqual(response.data['seat_type'], self.seat1.seat_type)

    def test_create_seat_forbidden(self):
        """Тест запрета создания мест через API"""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            "vehicle": self.vehicle.id,
            "seat_number": 100,
            "seat_type": "back"
        }

        response = self.client.post(self.seat_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_seat_forbidden(self):
        """Тест запрета удаления мест через API"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.seat_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_seat_as_admin(self):
        """Тест обновления типа места администратором"""
        self.client.force_authenticate(user=self.admin_user)

        # Меняем тип места с "back" на "middle"
        data = {"seat_type": "middle"}
        response = self.client.patch(self.seat_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что тип места действительно изменился
        self.seat1.refresh_from_db()
        self.assertEqual(self.seat1.seat_type, "middle")

    def test_update_seat_as_regular_user(self):
        """Тест обновления типа места обычным пользователем (без права доступа)"""
        self.client.force_authenticate(user=self.regular_user)

        # Обычный пользователь не должен иметь прав на изменение мест
        data = {"seat_type": "middle"}
        response = self.client.patch(self.seat_detail_url, data)
        # Проверка на отказ зависит от настроек разрешений в SeatViewSet
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_get_seats_by_vehicle(self):
        """Тест получения списка мест для конкретного транспортного средства"""
        response = self.client.get(self.seats_by_vehicle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что получены все места для указанного транспорта
        self.assertEqual(len(response.data), self.seats.count())

        # Проверяем, что все места относятся к правильному транспортному средству
        vehicle_ids = set(seat['vehicle'] for seat in response.data)
        self.assertEqual(len(vehicle_ids), 1)
        self.assertEqual(list(vehicle_ids)[0], self.vehicle.id)

    def test_get_seats_by_nonexistent_vehicle(self):
        """Тест получения мест для несуществующего транспортного средства"""
        nonexistent_vehicle_url = reverse('seat-get-seats-by-vehicle', args=[999])
        response = self.client.get(nonexistent_vehicle_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TripSeatBookingTest(APITestCase):
    """Тесты бронирования мест для поездки"""

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user('+79111111112', 'userpass')

        # Создаем транспортное средство с местами
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=3
        )

        # Получаем все места
        self.seats = list(Seat.objects.filter(vehicle=self.vehicle).order_by('seat_number'))

        # Создаем поездки
        self.trip1 = Trip.objects.create(
            vehicle=self.vehicle,
            origin=City.objects.create(name='Москва'),
            destination=City.objects.create(name='Санкт-Петербург'),
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=5),
            default_ticket_price=Decimal('1000.00')
        )

        self.trip2 = Trip.objects.create(
            vehicle=self.vehicle,
            origin=City.objects.get(name='Москва'),
            destination=City.objects.get(name='Санкт-Петербург'),
            departure_time=timezone.now() + timedelta(days=2),
            arrival_time=timezone.now() + timedelta(days=2, hours=5),
            default_ticket_price=Decimal('1000.00')
        )

        # Получаем TripSeat
        self.trip1_seats = list(TripSeat.objects.filter(trip=self.trip1).order_by('seat__seat_number'))
        self.trip2_seats = list(TripSeat.objects.filter(trip=self.trip2).order_by('seat__seat_number'))

        self.client.force_authenticate(user=self.user)

    def test_book_same_seat_for_different_trips(self):
        """Тест возможности бронирования одного и того же места на разные поездки"""
        # Бронируем место 1 для поездки 1
        self.trip1_seats[0].is_booked = True
        self.trip1_seats[0].save()

        # Проверяем, что место забронировано для поездки 1
        self.assertTrue(self.seats[0].is_booked_for_trip(self.trip1))

        # Бронируем то же самое место для поездки 2
        self.trip2_seats[0].is_booked = True
        self.trip2_seats[0].save()

        # Проверяем, что место забронировано и для поездки 2
        self.assertTrue(self.seats[0].is_booked_for_trip(self.trip2))

    def test_booking_seats_for_trip(self):
        """Тест бронирования нескольких мест для поездки"""
        # Бронируем места 1 и 2 для поездки 1
        self.trip1_seats[0].is_booked = True
        self.trip1_seats[0].save()
        self.trip1_seats[1].is_booked = True
        self.trip1_seats[1].save()

        # Проверяем, что места забронированы
        self.assertTrue(self.seats[0].is_booked_for_trip(self.trip1))
        self.assertTrue(self.seats[1].is_booked_for_trip(self.trip1))
        self.assertFalse(self.seats[2].is_booked_for_trip(self.trip1))

        # Проверяем, что места не забронированы для другой поездки
        self.assertFalse(self.seats[0].is_booked_for_trip(self.trip2))
        self.assertFalse(self.seats[1].is_booked_for_trip(self.trip2))

    def test_release_seats_for_trip(self):
        """Тест освобождения забронированных мест"""
        # Бронируем все места для поездки 1
        for trip_seat in self.trip1_seats:
            trip_seat.is_booked = True
            trip_seat.save()

        # Проверяем, что все места забронированы
        for seat in self.seats:
            self.assertTrue(seat.is_booked_for_trip(self.trip1))

        # Освобождаем места
        for trip_seat in self.trip1_seats:
            trip_seat.is_booked = False
            trip_seat.save()

        # Проверяем, что все места свободны
        for seat in self.seats:
            self.assertFalse(seat.is_booked_for_trip(self.trip1))


class SeatTypeConstraintTest(TestCase):
    """Тесты для проверки ограничений типов мест"""

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=3
        )

        self.seats = list(Seat.objects.filter(vehicle=self.vehicle))

    def test_first_seat_is_front(self):
        """Проверка, что первое место имеет тип 'front'"""
        first_seat = self.seats[0]
        self.assertEqual(first_seat.seat_number, 1)
        self.assertEqual(first_seat.seat_type, 'front')

    def test_change_seat_type(self):
        """Тест изменения типа места"""
        seat = self.seats[1]
        self.assertEqual(seat.seat_type, 'back')  # Изначально

        # Меняем тип на middle
        seat.seat_type = 'middle'
        seat.save()
        seat.refresh_from_db()
        self.assertEqual(seat.seat_type, 'middle')