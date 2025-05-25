from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
import re

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.auth.models import User
from apps.vehicle.models import Vehicle, validate_license_plate
from apps.seat.models import Seat, TripSeat
from apps.trip.models import Trip, City


class VehicleLicensePlateValidationTest(TestCase):
    """Тесты для функции валидации номерных знаков"""

    def test_valid_license_plate_without_region(self):
        """Тест валидации корректного номера без региона"""
        # Базовый формат A111AA должен пройти валидацию и получить регион 125
        result = validate_license_plate('А111АА')
        self.assertEqual(result, 'А111АА125')

        # Проверка с различными буквами
        result = validate_license_plate('В234КМ')
        self.assertEqual(result, 'В234КМ125')

    def test_valid_license_plate_with_region(self):
        """Тест валидации корректного номера с регионом"""
        # Формат A111AA 77 должен пройти валидацию и сохранить регион
        result = validate_license_plate('А111АА 77')
        self.assertEqual(result, 'А111АА77')

        # Формат без пробела
        result = validate_license_plate('В234КМ99')
        self.assertEqual(result, 'В234КМ99')

        # Формат с трехзначным регионом
        result = validate_license_plate('Е555МХ178')
        self.assertEqual(result, 'Е555МХ178')

    def test_invalid_license_plate(self):
        """Тест валидации некорректных номеров"""
        # Неправильные буквы (не из русского алфавита)
        with self.assertRaises(ValidationError):
            validate_license_plate('A111AA')

        # Неправильный формат (слишком короткий)
        with self.assertRaises(ValidationError):
            validate_license_plate('А11А')

        # Неправильный формат (слишком длинный)
        with self.assertRaises(ValidationError):
            validate_license_plate('А1111АА')

        # Недопустимые символы
        with self.assertRaises(ValidationError):
            validate_license_plate('А111А!')


class VehicleModelTest(TestCase):
    """Тесты для модели Vehicle"""

    def setUp(self):
        self.bus = Vehicle.objects.create(
            vehicle_type='bus',
            license_plate='А123АА',
            total_seats=40,
            is_comfort=True,
            air_conditioning=True,
            allows_pets=False
        )

        self.car = Vehicle.objects.create(
            vehicle_type='car',
            license_plate='В456ВВ',
            total_seats=4,
            is_comfort=False,
            air_conditioning=False,
            allows_pets=True
        )

        self.premium_car = Vehicle.objects.create(
            vehicle_type='premium_car',
            license_plate='Е789ЕЕ',
            total_seats=4,
            is_comfort=True,  # Обязательно для премиум-авто
            air_conditioning=True,
            allows_pets=False
        )
        
        # Создаем города для тестов с поездками
        self.moscow = City.objects.create(name='Москва')
        self.spb = City.objects.create(name='Санкт-Петербург')

    def test_vehicle_str_representation(self):
        """Тест строкового представления транспорта"""
        expected_bus_str = 'Автобус (Комфорт) - А123АА125'
        expected_car_str = 'Легковой автомобиль  - В456ВВ125'
        expected_premium_car_str = 'Премиум автомобиль (Комфорт) - Е789ЕЕ125'

        self.assertEqual(str(self.bus), expected_bus_str)
        self.assertEqual(str(self.car), expected_car_str)
        self.assertEqual(str(self.premium_car), expected_premium_car_str)

    def test_license_plate_normalization(self):
        """Тест нормализации номерных знаков при сохранении"""
        # Создаем объект с номером без региона
        vehicle = Vehicle.objects.create(
            vehicle_type='car',
            license_plate='Т777ТТ',
            total_seats=4
        )
        # Проверяем, что регион был добавлен
        self.assertEqual(vehicle.license_plate, 'Т777ТТ125')

        # Создаем объект с номером с регионом, но с пробелом
        vehicle = Vehicle.objects.create(
            vehicle_type='car',
            license_plate='М888ММ 77',
            total_seats=4
        )
        # Проверяем, что пробел был удален
        self.assertEqual(vehicle.license_plate, 'М888ММ77')

    def test_premium_car_validation(self):
        """Тест валидации premium_car (должен иметь повышенный уровень комфорта)"""
        # Пытаемся создать премиум автомобиль без повышенного комфорта
        vehicle = Vehicle(
            vehicle_type='premium_car',
            license_plate='Х999ХХ',
            total_seats=4,
            is_comfort=False  # Не соответствует требованиям
        )

        # Проверяем, что валидация не проходит
        with self.assertRaises(ValidationError):
            vehicle.full_clean()

    def test_total_seats_limits(self):
        """Тест ограничений на количество мест для разных типов транспорта"""
        # Пытаемся создать автобус с отрицательным количеством мест
        vehicle = Vehicle(
            vehicle_type='bus',
            license_plate='Р111РР',
            total_seats=-5
        )
        with self.assertRaises(ValidationError):
            vehicle.full_clean()

        # Пытаемся создать автобус с чрезмерно большим количеством мест
        vehicle = Vehicle(
            vehicle_type='bus',
            license_plate='Р222РР',
            total_seats=500
        )
        with self.assertRaises(ValidationError):
            vehicle.full_clean()

        # Пытаемся создать легковой автомобиль с чрезмерно большим количеством мест
        vehicle = Vehicle(
            vehicle_type='car',
            license_plate='Р333РР',
            total_seats=100
        )
        with self.assertRaises(ValidationError):
            vehicle.full_clean()

    def test_seats_created_automatically(self):
        """Тест автоматического создания мест при создании транспортного средства"""
        # Проверяем, что для каждого транспорта созданы места
        bus_seats = Seat.objects.filter(vehicle=self.bus)
        self.assertEqual(bus_seats.count(), self.bus.total_seats)

        car_seats = Seat.objects.filter(vehicle=self.car)
        self.assertEqual(car_seats.count(), self.car.total_seats)

        # Проверяем типы мест
        first_bus_seat = bus_seats.order_by('seat_number').first()
        self.assertEqual(first_bus_seat.price_zone, 'front')

        other_bus_seats = bus_seats.exclude(id=first_bus_seat.id)
        for seat in other_bus_seats:
            self.assertEqual(seat.price_zone, 'back')

    def test_vehicle_update_seats(self):
        """Тест обновления мест при изменении total_seats"""
        # Изначально у автомобиля 4 места
        original_count = self.car.total_seats
        car_seats = Seat.objects.filter(vehicle=self.car)
        self.assertEqual(car_seats.count(), original_count)

        # Увеличиваем количество мест
        self.car.total_seats = 6
        self.car.save()

        # Проверяем, что места были добавлены
        updated_car_seats = Seat.objects.filter(vehicle=self.car)
        self.assertEqual(updated_car_seats.count(), 6)

        # Уменьшаем количество мест
        self.car.total_seats = 3
        self.car.save()

        # Проверяем, что места были удалены
        updated_car_seats = Seat.objects.filter(vehicle=self.car)
        self.assertEqual(updated_car_seats.count(), 3)

    def test_cannot_delete_booked_seats(self):
        """Тест запрета удаления мест, которые забронированы"""
        # Создаем водителя и добавляем его в группу Водитель
        driver = User.objects.create_user('+79111111115', 'driverpass')
        driver_group, _ = Group.objects.get_or_create(name='Водитель')
        driver.groups.add(driver_group)
        
        trip = Trip.objects.create(
            vehicle=self.bus,
            driver=driver,
            from_city=self.moscow,
            to_city=self.spb,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=5),
            front_seat_price=Decimal('1000.00'),
            middle_seat_price=Decimal('1000.00'),
            back_seat_price=Decimal('1000.00')
        )

        # Бронируем последнее место
        last_seat = Seat.objects.filter(vehicle=self.bus).order_by('-seat_number').first()
        trip_seat = TripSeat.objects.get(trip=trip, seat=last_seat)
        trip_seat.is_booked = True
        trip_seat.save()

        # Пытаемся уменьшить количество мест, чтобы удалить забронированное место
        self.bus.total_seats -= 1
        self.bus.save()

        # Проверяем, что количество мест не изменилось из-за блокировки забронированного места
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.total_seats, 40)  # Исходное количество

        # Отменяем бронирование
        trip_seat.is_booked = False
        trip_seat.save()

        # Теперь уменьшаем количество мест
        self.bus.total_seats -= 1
        self.bus.save()

        # Проверяем, что количество мест успешно уменьшилось
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.total_seats, 39)

    def test_vehicle_with_trip_seats(self):
        """Тест создания TripSeats при создании поездки для транспорта"""
        # Создаем водителя и добавляем его в группу Водитель
        driver = User.objects.create_user('+79111111116', 'driverpass')
        driver_group, _ = Group.objects.get_or_create(name='Водитель')
        driver.groups.add(driver_group)
        
        trip = Trip.objects.create(
            vehicle=self.car,
            driver=driver,
            from_city=self.moscow,
            to_city=self.spb,
            departure_time=timezone.now() + timedelta(days=1),
            arrival_time=timezone.now() + timedelta(days=1, hours=3),
            front_seat_price=Decimal('500.00'),
            middle_seat_price=Decimal('500.00'),
            back_seat_price=Decimal('500.00')
        )

        # Проверяем, что для каждого места создан TripSeat
        trip_seats = TripSeat.objects.filter(trip=trip)
        self.assertEqual(trip_seats.count(), self.car.total_seats)

        # Проверяем, что все места изначально не забронированы
        for trip_seat in trip_seats:
            self.assertFalse(trip_seat.is_booked)


class VehicleAPITest(APITestCase):
    """Тесты для API транспортных средств"""

    def setUp(self):
        # Создаем пользователей с разными правами
        self.admin_user = User.objects.create_superuser('+79111111111', 'adminpass')
        self.regular_user = User.objects.create_user('+79222222222', 'userpass')

        # Создаем тестовые транспортные средства
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

        self.vehicle3 = Vehicle.objects.create(
            vehicle_type='car',
            license_plate='Е789ЕЕ',
            total_seats=4,
            is_comfort=False,
            air_conditioning=False,
            allows_pets=True
        )

        # URL для тестов
        self.vehicle_list_url = reverse('vehicle-list')
        self.vehicle1_detail_url = reverse('vehicle-detail', args=[self.vehicle1.id])
        self.vehicle1_availability_url = reverse('vehicle-availability', args=[self.vehicle1.id])

        # Клиент для запросов
        self.client = APIClient()
        self.client.force_authenticate(user=self.regular_user)

    def test_list_vehicles(self):
        """Тест получения списка транспортных средств (доступно всем авторизованным)"""
        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.vehicle_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что в ответе три транспортных средства
        self.assertEqual(len(response.data), 3)

    def test_retrieve_vehicle(self):
        """Тест получения информации о конкретном транспортном средстве"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем основные поля в ответе
        self.assertEqual(response.data['id'], self.vehicle1.id)
        self.assertEqual(response.data['vehicle_type'], 'bus')
        self.assertEqual(response.data['license_plate'], 'А123АА125')
        self.assertEqual(response.data['total_seats'], 40)
        self.assertEqual(response.data['is_comfort'], True)

    def test_create_vehicle_as_admin(self):
        """Тест создания транспортного средства администратором"""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что транспорт действительно создался
        created_vehicle = Vehicle.objects.get(license_plate='Р555РР125')
        self.assertEqual(created_vehicle.vehicle_type, 'car')
        self.assertEqual(created_vehicle.total_seats, 5)

        # Проверяем, что места созданы автоматически
        seats = Seat.objects.filter(vehicle=created_vehicle)
        self.assertEqual(seats.count(), 5)

    def test_create_vehicle_as_regular_user(self):
        """Тест запрета создания транспортного средства обычным пользователем"""
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_vehicle_as_admin(self):
        """Тест обновления транспортного средства администратором"""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'vehicle_type': 'bus',
            'license_plate': 'А123АА',
            'total_seats': 45,  # Изменяем количество мест
            'is_comfort': False,  # Изменяем уровень комфорта
            'air_conditioning': True,
            'allows_pets': True  # Изменяем допустимость животных
        }

        response = self.client.put(self.vehicle1_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные обновились
        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.total_seats, 45)
        self.assertEqual(self.vehicle1.is_comfort, False)
        self.assertEqual(self.vehicle1.allows_pets, True)

        # Проверяем, что места обновились
        seats = Seat.objects.filter(vehicle=self.vehicle1)
        self.assertEqual(seats.count(), 45)

    def test_update_vehicle_as_regular_user(self):
        """Тест запрета обновления транспортного средства обычным пользователем"""
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'vehicle_type': 'bus',
            'license_plate': 'А123АА',
            'total_seats': 45,
            'is_comfort': False
        }

        response = self.client.put(self.vehicle1_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_vehicle_as_admin(self):
        """Тест удаления транспортного средства администратором"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что транспорт удалился
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle1.id).exists())

        # Проверяем, что места тоже удалились (из-за on_delete=CASCADE)
        self.assertEqual(Seat.objects.filter(vehicle_id=self.vehicle1.id).count(), 0)

    def test_delete_vehicle_as_regular_user(self):
        """Тест запрета удаления транспортного средства обычным пользователем"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_vehicles_by_type(self):
        """Тест фильтрации транспортных средств по типу"""
        self.client.force_authenticate(user=self.regular_user)

        # Фильтрация по типу "bus"
        url = f"{self.vehicle_list_url}?vehicle_type=bus"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.vehicle1.id)

        # Фильтрация по типу "car"
        url = f"{self.vehicle_list_url}?vehicle_type=car"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.vehicle3.id)

    def test_filter_vehicles_by_characteristics(self):
        """Тест фильтрации транспортных средств по характеристикам"""
        self.client.force_authenticate(user=self.regular_user)

        # Фильтрация по повышенному комфорту
        url = f"{self.vehicle_list_url}?is_comfort=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.vehicle1.id)

        # Фильтрация по наличию кондиционера
        url = f"{self.vehicle_list_url}?air_conditioning=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        vehicle_ids = [vehicle['id'] for vehicle in response.data]
        self.assertIn(self.vehicle1.id, vehicle_ids)
        self.assertIn(self.vehicle2.id, vehicle_ids)

        # Фильтрация по разрешению животных
        url = f"{self.vehicle_list_url}?allows_pets=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        vehicle_ids = [vehicle['id'] for vehicle in response.data]
        self.assertIn(self.vehicle2.id, vehicle_ids)
        self.assertIn(self.vehicle3.id, vehicle_ids)

    def test_search_vehicles_by_license_plate(self):
        """Тест поиска транспортных средств по номеру"""
        self.client.force_authenticate(user=self.regular_user)

        # Поиск по номеру
        url = f"{self.vehicle_list_url}?search=А123"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.vehicle1.id)

    def test_ordering_vehicles(self):
        """Тест сортировки транспортных средств"""
        self.client.force_authenticate(user=self.regular_user)

        # Сортировка по количеству мест (по убыванию)
        url = f"{self.vehicle_list_url}?ordering=-total_seats"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Проверяем порядок: bus (40), minibus (20), car (4)
        self.assertEqual(response.data[0]['id'], self.vehicle1.id)
        self.assertEqual(response.data[1]['id'], self.vehicle2.id)
        self.assertEqual(response.data[2]['id'], self.vehicle3.id)

        # Сортировка по дате создания (по возрастанию)
        url = f"{self.vehicle_list_url}?ordering=created_at"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем порядок: первый созданный (vehicle1), второй (vehicle2), третий (vehicle3)
        self.assertEqual(response.data[0]['id'], self.vehicle1.id)
        self.assertEqual(response.data[1]['id'], self.vehicle2.id)
        self.assertEqual(response.data[2]['id'], self.vehicle3.id)

    def test_vehicle_availability_checker(self):
        """Тест проверки доступности транспортного средства"""
        self.client.force_authenticate(user=self.admin_user)

        from_city = City.objects.create(name='Москва')
        to_city = City.objects.create(name='Санкт-Петербург')

        # Создаем водителя и добавляем его в группу Водитель
        driver = User.objects.create_user('+79111111115', 'driverpass')
        driver_group, _ = Group.objects.get_or_create(name='Водитель')
        driver.groups.add(driver_group)

        now = timezone.now()
        trip_start = now + timedelta(days=1)
        trip_end = now + timedelta(days=1, hours=5)

        Trip.objects.create(
            vehicle=self.vehicle1,
            driver=driver,  # Добавляем водителя
            from_city=from_city,
            to_city=to_city,
            departure_time=trip_start,
            arrival_time=trip_end,
            front_seat_price=Decimal('1000.00'),
            middle_seat_price=Decimal('1000.00'),
            back_seat_price=Decimal('1000.00')
        )

        # Убираем микросекунды и не добавляем «Z»
        free_time_start = (trip_end + timedelta(hours=1)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')
        free_time_end = (trip_end + timedelta(hours=6)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')

        url = f"{self.vehicle1_availability_url}?start_time={free_time_start}&end_time={free_time_end}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available'], True)


class VehiclePermissionTest(APITestCase):
    """Тесты для проверки разрешений на транспортные средства"""

    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем пользователей с разными ролями
        self.admin_user = User.objects.create_superuser('+79111111111', 'adminpass')
        self.manager_user = User.objects.create_user('+79222222222', 'managerpass')
        self.regular_user = User.objects.create_user('+79333333333', 'userpass')

        # Создаем группу менеджеров с правами на операции с транспортными средствами
        self.manager_group, _ = Group.objects.get_or_create(name='Менеджеры транспорта')

        # Получаем или создаем права для транспортных средств
        content_type = ContentType.objects.get_for_model(Vehicle)

        create_vehicle_perm, _ = Permission.objects.get_or_create(
            codename='can_create_vehicle',
            name='Может создавать транспортные средства',
            content_type=content_type,
        )

        update_vehicle_perm, _ = Permission.objects.get_or_create(
            codename='can_update_vehicle',
            name='Может изменять транспортные средства',
            content_type=content_type,
        )

        delete_vehicle_perm, _ = Permission.objects.get_or_create(
            codename='can_delete_vehicle',
            name='Может удалять транспортные средства',
            content_type=content_type,
        )

        # Добавляем разрешения к группе менеджеров
        self.manager_group.permissions.add(create_vehicle_perm, update_vehicle_perm, delete_vehicle_perm)

        # Добавляем пользователя в группу менеджеров
        self.manager_user.groups.add(self.manager_group)

        # Создаем тестовые транспортные средства
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
        self.vehicle1_detail_url = reverse('vehicle-detail', args=[self.vehicle1.id])
        self.vehicle1_availability_url = reverse('vehicle-availability', args=[self.vehicle1.id])

        # Клиент для запросов
        self.client = APIClient()

    def test_list_vehicles_as_anonymous(self):
        """Тест запрета доступа к списку транспортных средств для анонимного пользователя"""
        response = self.client.get(self.vehicle_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_vehicles_as_authenticated(self):
        """Тест доступа к списку транспортных средств для аутентифицированного пользователя"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.vehicle_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Проверяем, что список содержит оба автомобиля

    def test_retrieve_vehicle_as_anonymous(self):
        """Тест запрета доступа к просмотру детальной информации ТС для анонимного пользователя"""
        response = self.client.get(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_vehicle_as_authenticated(self):
        """Тест доступа к просмотру детальной информации ТС для аутентифицированного пользователя"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.vehicle1.id)
        self.assertEqual(response.data['vehicle_type'], 'bus')

    def test_create_vehicle_as_anonymous(self):
        """Тест запрета создания ТС для анонимного пользователя"""
        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_vehicle_as_regular_user(self):
        """Тест запрета создания ТС для обычного пользователя без прав"""
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_vehicle_as_manager(self):
        """Тест создания ТС менеджером с правами на создание"""
        self.client.force_authenticate(user=self.manager_user)

        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что ТС создалось
        vehicle_id = response.data['id']
        self.assertTrue(Vehicle.objects.filter(id=vehicle_id).exists())

        # Проверяем, что места созданы автоматически
        vehicle = Vehicle.objects.get(id=vehicle_id)
        self.assertEqual(Seat.objects.filter(vehicle=vehicle).count(), 5)

    def test_create_vehicle_as_admin(self):
        """Тест создания ТС администратором"""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что места созданы автоматически
        vehicle_id = response.data['id']
        vehicle = Vehicle.objects.get(id=vehicle_id)
        self.assertEqual(Seat.objects.filter(vehicle=vehicle).count(), 5)

    def test_update_vehicle_as_regular_user(self):
        """Тест запрета обновления ТС обычным пользователем без прав"""
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'vehicle_type': 'bus',
            'license_plate': 'А123АА',
            'total_seats': 45,
            'is_comfort': False,
            'air_conditioning': True,
            'allows_pets': True
        }

        response = self.client.put(self.vehicle1_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что данные не обновились
        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.total_seats, 40)
        self.assertEqual(self.vehicle1.is_comfort, True)
        self.assertEqual(self.vehicle1.allows_pets, False)

    def test_update_vehicle_as_manager(self):
        """Тест обновления ТС менеджером с правами на обновление"""
        self.client.force_authenticate(user=self.manager_user)

        data = {
            'vehicle_type': 'bus',
            'license_plate': 'А123АА',
            'total_seats': 45,
            'is_comfort': False,
            'air_conditioning': True,
            'allows_pets': True
        }

        response = self.client.put(self.vehicle1_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные обновились
        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.total_seats, 45)
        self.assertEqual(self.vehicle1.is_comfort, False)
        self.assertEqual(self.vehicle1.allows_pets, True)

        # Проверяем, что места обновились
        seats = Seat.objects.filter(vehicle=self.vehicle1)
        self.assertEqual(seats.count(), 45)

    def test_update_vehicle_as_admin(self):
        """Тест обновления ТС администратором"""
        self.client.force_authenticate(user=self.admin_user)

        data = {
            'vehicle_type': 'bus',
            'license_plate': 'А123АА',
            'total_seats': 45,
            'is_comfort': False,
            'air_conditioning': True,
            'allows_pets': True
        }

        response = self.client.put(self.vehicle1_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные обновились
        self.vehicle1.refresh_from_db()
        self.assertEqual(self.vehicle1.total_seats, 45)
        self.assertEqual(self.vehicle1.is_comfort, False)
        self.assertEqual(self.vehicle1.allows_pets, True)

    def test_delete_vehicle_as_regular_user(self):
        """Тест запрета удаления ТС обычным пользователем без прав"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что ТС не удалилось
        self.assertTrue(Vehicle.objects.filter(id=self.vehicle1.id).exists())

    def test_delete_vehicle_as_manager(self):
        """Тест удаления ТС менеджером с правами на удаление"""
        self.client.force_authenticate(user=self.manager_user)

        response = self.client.delete(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что ТС удалилось
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle1.id).exists())

        # Проверяем, что места тоже удалились (из-за on_delete=CASCADE)
        self.assertEqual(Seat.objects.filter(vehicle_id=self.vehicle1.id).count(), 0)

    def test_delete_vehicle_as_admin(self):
        """Тест удаления ТС администратором"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(self.vehicle1_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что ТС удалилось
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle1.id).exists())

    def test_availability_checker_as_anonymous(self):
        """Тест запрета доступа к проверке доступности ТС для анонимного пользователя"""
        now = timezone.now()
        free_time_start = (now + timedelta(hours=1)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')
        free_time_end = (now + timedelta(hours=6)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')

        url = f"{self.vehicle1_availability_url}?start_time={free_time_start}&end_time={free_time_end}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_availability_checker_as_authenticated(self):
        """Тест доступа к проверке доступности ТС для аутентифицированного пользователя"""
        self.client.force_authenticate(user=self.regular_user)

        now = timezone.now()
        free_time_start = (now + timedelta(hours=1)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')
        free_time_end = (now + timedelta(hours=6)).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S')

        url = f"{self.vehicle1_availability_url}?start_time={free_time_start}&end_time={free_time_end}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available'], True)

    def test_role_permissions_consistency(self):
        """Тест последовательности назначения и отзыва прав через группы"""
        # Создаем нового пользователя и проверяем отсутствие прав
        test_user = User.objects.create_user('+79555555555', 'testpass')
        self.client.force_authenticate(user=test_user)

        data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 5,
            'is_comfort': True,
            'air_conditioning': True,
            'allows_pets': False
        }

        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Добавляем пользователя в группу менеджеров
        test_user.groups.add(self.manager_group)

        # Теперь пользователь должен иметь право создавать ТС
        response = self.client.post(self.vehicle_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Для обновления ТС нужно получить ID нового транспорта
        vehicle_id = response.data['id']
        vehicle_detail_url = reverse('vehicle-detail', args=[vehicle_id])

        # Проверяем, что пользователь может обновлять свои ТС
        update_data = {
            'vehicle_type': 'car',
            'license_plate': 'Р555РР',
            'total_seats': 6,  # Увеличиваем количество мест
            'is_comfort': False,  # Меняем уровень комфорта
            'air_conditioning': True,
            'allows_pets': True  # Разрешаем животных
        }

        response = self.client.put(vehicle_detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Удаляем пользователя из группы менеджеров
        test_user.groups.remove(self.manager_group)

        # Снова нет права на редактирование
        response = self.client.put(vehicle_detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # И нет права на удаление
        response = self.client.delete(vehicle_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)