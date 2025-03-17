from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

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