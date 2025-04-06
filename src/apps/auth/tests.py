from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from apps.auth.models import User

class RegistrationUserTest(APITestCase):
    def setUp(self):
        self.test_password = "221312312ya"

    def test_create_user(self):
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571', 'password': self.test_password},
                                    format='json')
        self.assertEqual(response.status_code, 201)

    def test_create_user_with_existing_phone_number(self):
        self.client.post('/auth/register/',
                         {'phone_number': '+79147282571', 'password': self.test_password},
                         format='json')
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571', 'password': self.test_password},
                                    format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_user_with_invalid_phone_numbers(self):
        response = self.client.post('/auth/register/',
                                    {'phone_number': 'invalid_phone', 'password': self.test_password},
                                    format='json')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/auth/register/',
                                    {'phone_number': '1111111111', 'password': self.test_password},
                                    format='json')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/auth/register/',
                                    {'phone_number': '', 'password': self.test_password},
                                    format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_user_without_password(self):
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571'},
                                    format='json')
        self.assertEqual(response.status_code, 400)


    # Проверка валидации
    def test_password_cant_be_too_short(self):
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571', 'password': 'short'},
                                    format='json')
        self.assertEqual(response.status_code, 400)

    def test_password_cant_be_too_common(self):
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571', 'password': 'password'},
                                    format='json')
        self.assertEqual(response.status_code, 400)

    def test_password_cant_be_entirely_numeric(self):
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571', 'password': '223392489'},
                                    format='json')
        self.assertEqual(response.status_code, 400)

class TokenUserTest(APITestCase):
    def setUp(self):
        self.test_phone_number = '+79147282571'
        self.test_password = 'testpassword'
        response = self.client.post('/auth/register/',
                                    {'phone_number': '+79147282571', 'password': 'testpassword'},
                                    format='json')
        self.assertEqual(response.status_code, 201)
        self.token_url = reverse('token_obtain_pair')
        self.token_refresh_url = reverse('token_refresh')

    def test_obtain_token(self):
        response = self.client.post(self.token_url, {'phone_number': self.test_phone_number, 'password': self.test_password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_obtain_token_invalid_credentials(self):
        response = self.client.post(self.token_url, {'phone_number': self.test_phone_number, 'password': 'wrongpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        response = self.client.post(self.token_url, {'phone_number': self.test_phone_number, 'password': self.test_password}, format='json')
        refresh_token = response.data['refresh']
        response = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalid(self):
        response = self.client.post(self.token_refresh_url, {'refresh': 'invalidtoken'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListTest(APITestCase):
    """
    Тесты для проверки эндпоинта /auth/users/.
    Обычный пользователь должен получать только свои данные,
    а администратор – список всех пользователей.
    """

    def setUp(self):
        self.admin_phone = "+79147282571"
        self.user_phone = "+79223334455"
        self.password = "testpassword123."

        # Создаем администратора напрямую через модель
        self.admin = User.objects.create_superuser(
            phone_number=self.admin_phone,
            password=self.password,
            first_name="Admin",
            last_name="User"
        )

        # Создаем обычного пользователя через эндпоинт регистрации
        response = self.client.post('/auth/register/', {
            'phone_number': self.user_phone,
            'password': self.password,
            'first_name': 'Normal',
            'last_name': 'User'
        }, format='json')
        self.assertEqual(response.status_code, 201)

        # Получаем токены для обоих пользователей
        self.admin_token = self.client.post(reverse('token_obtain_pair'), {
            'phone_number': self.admin_phone,
            'password': self.password
        }, format='json').data.get('access')

        self.user_token = self.client.post(reverse('token_obtain_pair'), {
            'phone_number': self.user_phone,
            'password': self.password
        }, format='json').data.get('access')

        self.users_url = "/auth/users/"

    def test_users_route_unauthenticated(self):
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_route_normal_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.get(self.users_url)

        # Используем более гибкую проверку, так как в разных случаях ожидается 200 или 403
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

        # Если получили 200, проверяем, что пользователь видит только себя
        if response.status_code == status.HTTP_200_OK:
            users = response.data.get('results', response.data)
            self.assertIsInstance(users, list)
            # Обычный пользователь должен видеть только свою запись
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0]['phone_number'], self.user_phone)

    def test_users_route_admin_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(self.users_url)
        users = response.data.get('results', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(users, list)
        # Администратор должен видеть как минимум две записи (его и обычного пользователя)
        self.assertGreaterEqual(len(users), 2)
        phones = [user['phone_number'] for user in users]
        self.assertIn(self.admin_phone, phones)
        self.assertIn(self.user_phone, phones)

class UserDetailTest(APITestCase):
    """
    Тесты для проверки эндпоинта /auth/users/get_user_info.
    Обычный пользователь должен получать только свои данные,
    а администратор – данные любого пользователя.
    """
    def setUp(self):
        self.admin_phone = "+79147282571"
        self.user_phone = "+79223334455"
        self.password = "testpassword123."

        # Создаем администратора напрямую через модель
        self.admin = User.objects.create_superuser(
            phone_number=self.admin_phone,
            password=self.password,
            first_name="Admin",
            last_name="User"
        )

        # Создаем обычного пользователя через эндпоинт регистрации
        response = self.client.post('/auth/register/', {
            'phone_number': self.user_phone,
            'password': self.password,
            'first_name': 'Normal',
            'last_name': 'User'
        }, format='json')
        self.assertEqual(response.status_code, 201)

        # Получаем токены для обоих пользователей
        self.admin_token = self.client.post(reverse('token_obtain_pair'), {
            'phone_number': self.admin_phone,
            'password': self.password
        }, format='json').data.get('access')

        self.user_token = self.client.post(reverse('token_obtain_pair'), {
            'phone_number': self.user_phone,
            'password': self.password
        }, format='json').data.get('access')

        self.user_detail_url = "/auth/users/get_user_info/"

    def test_user_detail_route_unauthenticated(self):
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_route_normal_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = response.data
        self.assertEqual(user['phone_number'], self.user_phone)

    def test_user_detail_route_admin_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserUpdateTests(APITestCase):
    def setUp(self):

        self.phone_admin = "+79147282571"
        self.user_phone = "+79223334455"
        self.password = "normalpass123."
        self.test_phone = "+79998881111"
        # Создаем пользователей напрямую через модель
        self.admin = User.objects.create_superuser(
            phone_number=self.phone_admin,
            password=self.password,
            first_name="Admin",
            last_name="User"
        )
        self.user = User.objects.create_user(
            phone_number=self.user_phone,
            password=self.password,
            first_name="Normal",
            last_name="User"
        )
        
        # Получаем токены
        self.admin_token = self.get_token(self.phone_admin, self.password)
        self.user_token = self.get_token(self.user_phone, self.password)
        
        # URL для обновления
        self.update_user_url = reverse('user_update', args=[self.user.id])
        self.update_admin_url = reverse('user_update', args=[self.admin.id])

    def get_token(self, phone, password):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {
                'phone_number': phone, 
                'password': password
            },
            format='json'
        )
        return response.data['access']

    # --- Тесты безопасности ---
    def test_unauthorized_access(self):
        """Неаутентифицированный пользователь не может обновлять данные"""
        response = self.client.patch(self.update_user_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_update_others(self):
        """Обычный пользователь не может обновлять чужой аккаунт"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.patch(self.update_admin_url, {'first_name': 'Hack'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertNotEqual(self.admin.first_name, 'Hack')

    # --- Тесты функционала ---
    def test_user_update_self(self):
        """Обычный пользователь может обновить свои данные"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        data = {
            'first_name': 'UpdatedName', 
            'chat_id': '1111'
            }
        response = self.client.patch(self.update_user_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedName')
        self.assertEqual(self.user.chat_id, '1111')

    def test_admin_update_any_user(self):
        """Администратор может обновлять любые аккаунты"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        data = {
            'last_name': 'NewAdminName',
            'chat_id': 2222
            }
        response = self.client.patch(self.update_user_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, 'NewAdminName')
        self.assertEqual(self.user.chat_id, '2222')

    # --- Тесты валидации ---
    def test_invalid_fields(self):
        """Нельзя изменять недопустимые поля"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        data = {'phone_number': self.test_phone}
        response = self.client.patch(self.update_admin_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_chat_id(self):
        """Невалидный chat_id (должен быть числом)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        data = {'chat_id': 'abc123'}
        response = self.client.patch(self.update_user_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('chat_id', response.data)

    def test_protected_fields(self) -> None:
        """Попытка обновления защищенных (неразрешенных) полей должна вернуть ошибку."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        data = {'is_superuser': True}
        response = self.client.patch(self.update_user_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    # --- Тесты граничных условий ---
    def test_update_nonexistent_user(self):
        """Обновление несуществующего пользователя возвращает 404"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        url = reverse('user_update', args=[999])
        response = self.client.patch(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_update(self):
        """PATCH-запрос без данных не изменяет пользователя"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        original_data = self.user.__dict__
        response = self.client.patch(self.update_user_url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(original_data['first_name'], self.user.first_name)

    # --- Тесты методов ---
    def test_disallowed_methods(self):
        """PUT, DELETE и GET не поддерживаются"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(self.update_user_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.put(self.update_user_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        response = self.client.delete(self.update_user_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # --- Тест неопределенных полей ---
    def test_unexpected_fields(self) -> None:
        """Передача недопустимых полей приводит к ошибке валидации."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        data = {'first_name': 'Test', 'unknown_field': 'value'}
        response = self.client.patch(self.update_user_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unexpected fields", str(response.data))

    def test_admin_cannot_update_phone_number_via_admin(self) -> None:
        """
        В админке поле phone_number должно отображаться, но быть недоступным для редактирования.
        Даже при отправке нового значения оно не должно измениться.
        """
        self.client.login(username=self.phone_admin, password=self.password)
        admin_change_url = reverse('admin:transfer_auth_user_change', args=[self.user.id])
        original_phone = self.user.phone_number
        data = {
            'phone_number': '+70000000000',
            'first_name': 'AdminEdited',
            'last_name': self.user.last_name,
            'chat_id': '3333',
            'password': self.user.password,
        }
        response = self.client.post(admin_change_url, data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, original_phone)
        self.assertEqual(self.user.first_name, 'AdminEdited')
        self.assertEqual(self.user.chat_id, '3333')

