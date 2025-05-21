import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from phonenumber_field.phonenumber import PhoneNumber
from apps.auth.models import User
from apps.trip.models import City, Trip
from apps.vehicle.models import Vehicle
from apps.seat.models import Seat, TripSeat
from apps.booking.models import Booking
from apps.payment.models import Payment

class Command(BaseCommand):
    help = 'Генерирует тестовые данные для приложения'

    def add_arguments(self, parser):
        parser.add_argument('--cities', type=int, default=5, help='Количество городов')
        parser.add_argument('--vehicles', type=int, default=10, help='Количество транспортных средств')
        parser.add_argument('--trips', type=int, default=20, help='Количество поездок')
        parser.add_argument('--users', type=int, default=15, help='Количество пользователей')
        parser.add_argument('--bookings', type=int, default=30, help='Количество бронирований')
        parser.add_argument('--clean', action='store_true', help='Очистить существующие данные')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clean']:
            self.clean_data()
            
        city_count = options['cities']
        vehicle_count = options['vehicles']
        trip_count = options['trips']
        user_count = options['users']
        booking_count = options['bookings']
        
        # Создаем города
        cities = self.create_cities(city_count)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(cities)} городов'))
        
        # Создаем транспортные средства
        vehicles = self.create_vehicles(vehicle_count)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(vehicles)} транспортных средств'))
        
        # Создаем поездки
        trips = self.create_trips(trip_count, cities, vehicles)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(trips)} поездок'))
        
        # Создаем пользователей
        users = self.create_users(user_count)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(users)} пользователей'))
        
        # Создаем бронирования
        bookings = self.create_bookings(booking_count, users, trips)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(bookings)} бронирований'))
        
        self.stdout.write(self.style.SUCCESS('Генерация тестовых данных завершена успешно!'))

    def clean_data(self):
        # Удаляем данные в обратном порядке зависимостей
        Booking.objects.all().delete()
        Payment.objects.all().delete()
        TripSeat.objects.all().delete()
        Trip.objects.all().delete()
        Seat.objects.all().delete()
        Vehicle.objects.all().delete()
        City.objects.all().delete()
        User.objects.all().filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Существующие данные очищены'))

    def create_cities(self, count):
        cities = []
        city_names = [
            'Москва', 'Санкт-Петербург', 'Калининград', 'Казань', 'Нижний Новгород', 
            'Сочи', 'Екатеринбург', 'Новосибирск', 'Владивосток', 'Ростов-на-Дону',
            'Краснодар', 'Волгоград', 'Самара', 'Воронеж', 'Уфа'
        ]
        
        existing_cities = set(City.objects.values_list('name', flat=True))
        city_names = [name for name in city_names if name not in existing_cities]
        
        # Если городов достаточно уже в базе, вернуть их
        if len(existing_cities) >= count:
            return list(City.objects.all()[:count])
        
        # Иначе добавить новые города
        for i in range(min(count, len(city_names))):
            city = City.objects.create(name=city_names[i])
            cities.append(city)
        
        return cities + list(City.objects.filter(name__in=existing_cities))[:count]

    def create_vehicles(self, count):
        vehicles = []
        vehicle_types = ['car', 'minibus', 'bus', 'premium_car', 'suv', 'van']
        
        letters = 'АВЕКМНОРСТУХ'
        
        for i in range(count):
            # Генерация случайного номера
            letters_part1 = random.choice(letters)
            numbers = f"{random.randint(100, 999)}"
            letters_part2 = ''.join(random.choices(letters, k=2))
            region = random.randint(1, 199)
            license_plate = f"{letters_part1}{numbers}{letters_part2} {region}"
            
            vehicle_type = random.choice(vehicle_types)
            total_seats = 0
            
            if vehicle_type == 'car':
                total_seats = random.randint(3, 5)
            elif vehicle_type == 'minibus':
                total_seats = random.randint(8, 20)
            elif vehicle_type == 'bus':
                total_seats = random.randint(30, 50)
            elif vehicle_type == 'premium_car':
                total_seats = random.randint(2, 4)
                is_comfort = True
            elif vehicle_type == 'suv':
                total_seats = random.randint(5, 7)
            elif vehicle_type == 'van':
                total_seats = random.randint(6, 8)
                
            is_comfort = vehicle_type == 'premium_car' or random.random() < 0.3
            air_conditioning = random.random() < 0.8
            allows_pets = random.random() < 0.4
            
            vehicle = Vehicle(
                vehicle_type=vehicle_type,
                license_plate=license_plate,
                total_seats=total_seats,
                is_comfort=is_comfort,
                air_conditioning=air_conditioning,
                allows_pets=allows_pets
            )
            
            try:
                vehicle.save()
                vehicles.append(vehicle)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Не удалось создать транспорт: {str(e)}'))
        
        return vehicles

    def create_trips(self, count, cities, vehicles):
        trips = []
        
        for i in range(count):
            # Выбираем случайные города отправления и прибытия
            from_city, to_city = random.sample(cities, 2)
            
            # Выбираем случайное транспортное средство
            vehicle = random.choice(vehicles)
            
            # Генерируем случайные даты в будущем (от 1 до 30 дней)
            now = timezone.now()
            departure_days = random.randint(1, 30)
            departure_time = now + timedelta(days=departure_days, hours=random.randint(0, 23))
            
            # Длительность поездки от 1 до 12 часов
            trip_duration = timedelta(hours=random.randint(1, 12))
            arrival_time = departure_time + trip_duration
            
            # Генерируем случайные цены
            front_seat_price = Decimal(random.randint(500, 2000))
            middle_seat_price = Decimal(random.randint(400, 1800))
            back_seat_price = Decimal(random.randint(300, 1500))
            
            # Доступность для бронирования
            is_bookable = random.random() < 0.9
            
            trip = Trip(
                vehicle=vehicle,
                from_city=from_city,
                to_city=to_city,
                departure_time=departure_time,
                arrival_time=arrival_time,
                front_seat_price=front_seat_price,
                middle_seat_price=middle_seat_price,
                back_seat_price=back_seat_price,
                is_bookable=is_bookable,
                is_active=True,
                booking_cutoff_minutes=random.choice([15, 30, 45, 60])
            )
            
            try:
                trip.save()
                trips.append(trip)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Не удалось создать поездку: {str(e)}'))
        
        return trips

    def create_users(self, count):
        users = []
        first_names = ['Александр', 'Иван', 'Дмитрий', 'Михаил', 'Сергей', 'Андрей', 'Николай', 
                      'Анна', 'Мария', 'Екатерина', 'Елена', 'Ольга', 'Наталья', 'Татьяна']
        last_names = ['Иванов', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Петров', 'Соколов',
                      'Иванова', 'Смирнова', 'Кузнецова', 'Попова', 'Васильева', 'Петрова', 'Соколова']
        
        for i in range(count):
            # Генерируем случайный номер телефона
            phone_number_str = f"+7{random.randint(9000000000, 9999999999)}"
            phone_number = PhoneNumber.from_string(phone_number_str)
            
            # Выбираем случайные имя и фамилию
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            if random.random() < 0.5 and last_name.endswith('ов'):
                last_name = last_name + 'а'
            
            user = User(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
            )
            
            try:
                user.save()
                users.append(user)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Не удалось создать пользователя: {str(e)}'))
        
        return users

    def create_bookings(self, count, users, trips):
        bookings = []
        
        valid_trips = [trip for trip in trips if trip.is_bookable]
        
        if not valid_trips:
            self.stdout.write(self.style.WARNING('Нет доступных поездок для бронирования'))
            return bookings
        
        for i in range(min(count, len(valid_trips) * 3)):  # Ограничиваем количество бронирований
            user = random.choice(users)
            trip = random.choice(valid_trips)
            
            # Случайные адреса
            pickup_location = f"ул. {random.choice(['Ленина', 'Мира', 'Гагарина', 'Пушкина', 'Советская'])}, {random.randint(1, 100)}"
            dropoff_location = f"ул. {random.choice(['Красная', 'Большая', 'Зеленая', 'Московская', 'Центральная'])}, {random.randint(1, 100)}"
            
            # Создаем бронирование без мест (добавим их позже)
            booking = Booking(
                user=user,
                trip=trip,
                pickup_location=pickup_location,
                dropoff_location=dropoff_location,
                is_active=True
            )
            
            try:
                booking.save()
                
                # Выбираем случайные свободные места для бронирования
                available_trip_seats = TripSeat.objects.filter(trip=trip, is_booked=False)
                
                if available_trip_seats.exists():
                    # Выбираем случайное количество мест (от 1 до min(3, доступных мест))
                    num_seats = random.randint(1, min(3, available_trip_seats.count()))
                    seats_to_book = random.sample(list(available_trip_seats), num_seats)
                    
                    # Бронируем места
                    for trip_seat in seats_to_book:
                        trip_seat.is_booked = True
                        trip_seat.save()
                        booking.trip_seats.add(trip_seat)
                
                    booking.save()
                    
                    bookings.append(booking)
                else:
                    booking.delete()
                    self.stdout.write(self.style.WARNING(f'Нет свободных мест для поездки {trip}'))
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Не удалось создать бронирование: {str(e)}'))
        
        return bookings 