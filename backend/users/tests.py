from django.contrib.auth import get_user
from django.test import TestCase
from users.models import User


class UserViewRegistrationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.email = 'user1@example.com'
        cls.username = 'UserOne'
        cls.password = 'ValidPass123'
        cls.url = '/api/users/register'

    def test_success_registration(self):
        ## Подготавливаем запрос к серверу

        payload = {
            'email': self.email,
            'username': self.username,
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 201)

        self.assertEqual(len(data), 3)
        self.assertIn('email', data)
        self.assertIn('username', data)
        self.assertIn('id', data)

        self.assertEqual(data['email'], self.email)
        self.assertEqual(data['username'], self.username)

        ## Проверяем, что пользователь стал авторизованным
        self.assertIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertTrue(User.objects.filter(pk=user.id).exists())

        ## Проверяем, что для пользователя была создана комната в БД
        self.assertTrue(hasattr(user, 'room'))

        ## Проверяем, что у комнаты правильный владелец
        user_id = user.room.created_by.id
        self.assertEqual(user_id, user.id)

    def test_registration_session_already_exists(self):
        ## Создаём сессию пользователя

        user = User.objects.create_user(
            email='test_'+self.username,
            username='test_'+self.email,
        )
        self.client.force_login(user)

        payload = {
            'email': self.email,
            'username': self.username,
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()

        self.assertEqual(response.status_code, 403)

        self.assertEqual(len(data), 1)
        self.assertIn('error', data)

        self.assertEqual(len(data['error']), 2)
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])

        self.assertEqual(data['error']['code'], 'authenticated')
        self.assertEqual(data['error']['message'], 'Пользователь уже авторизован')

        ## Проверяем, что в тестовой БД не появилась запись о пользователе
        self.assertFalse(User.objects.filter(email=self.email).exists())

    def test_registration_short_password(self):

        payload = {
            'email': self.email,
            'username': self.username,
            'password': '123'
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 422)

        self.assertEqual(len(data), 1)
        self.assertIn('error', data)

        self.assertEqual(len(data['error']), 3)
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])
        self.assertIn('details', data['error'])
        self.assertIn('password', data['error']['details'])

        self.assertEqual(data['error']['code'], 'validation_error')
        self.assertEqual(data['error']['message'], 'Переданные данные не прошли проверку')
        self.assertEqual(data['error']['details']['password'][0], 'Длина пароля должна быть не менее 8 символов')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertNotIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_registration_incorrect_email(self):

        payload = {
            'email': 'example@mail',
            'username': self.username,
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 422)

        self.assertEqual(len(data), 1)
        self.assertIn('error', data)

        self.assertEqual(len(data['error']), 3)
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])
        self.assertIn('details', data['error'])
        self.assertIn('email', data['error']['details'])

        self.assertEqual(data['error']['code'], 'validation_error')
        self.assertEqual(data['error']['message'], 'Переданные данные не прошли проверку')
        self.assertEqual(data['error']['details']['email'][0], 'Почта не соответствует требованиям')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertNotIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_registration_not_all_fields(self):

        payload = {
            'email': self.email,
            'username': self.username
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 500)

        self.assertEqual(len(data), 1)
        self.assertIn('error', data)

        self.assertEqual(len(data['error']), 2)
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])

        self.assertEqual(data['error']['code'], 'internal_error')
        self.assertEqual(data['error']['message'], 'Произошла внутренняя ошибка сервера')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertNotIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_registration_email_already_taken(self):

        ## Регистрируем первого пользователя
        payload = {
            'email': self.email,
            'username': self.username,
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        self.client.logout()
        ## Регистрируем второго пользователя

        new_payload = {
            'email': self.email,
            'username': 'some_username',
            'password': self.password
        }

        new_response = self.client.post(
            self.url,
            data=new_payload,
            content_type='application/json'
        )

        data = new_response.json()
        user = get_user(self.client)

        self.assertEqual(new_response.status_code, 409)

        self.assertEqual(len(data), 1)
        self.assertIn('error', data)

        self.assertEqual(len(data['error']), 3)
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])
        self.assertIn('details', data['error'])
        self.assertIn('email', data['error']['details'])

        self.assertEqual(data['error']['code'], 'account_already_exists')
        self.assertEqual(data['error']['message'], 'Пользователь с такими данными уже существует')
        self.assertEqual(data['error']['details']['email'][0], 'Этот email уже используется')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertNotIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_registration_username_already_taken(self):
        ## Регистрируем первого пользователя
        payload = {
            'email': self.email,
            'username': self.username,
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        self.client.logout()
        ## Регистрируем второго пользователя

        new_payload = {
            'email': 'exam@ya.ru',
            'username': self.username,
            'password': self.password
        }

        new_response = self.client.post(
            self.url,
            data=new_payload,
            content_type='application/json'
        )

        data = new_response.json()
        user = get_user(self.client)

        self.assertEqual(new_response.status_code, 409)

        self.assertEqual(len(data), 1)
        self.assertIn('error', data)

        self.assertEqual(len(data['error']), 3)
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])
        self.assertIn('details', data['error'])
        self.assertIn('username', data['error']['details'])

        self.assertEqual(data['error']['code'], 'account_already_exists')
        self.assertEqual(data['error']['message'], 'Пользователь с такими данными уже существует')
        self.assertEqual(data['error']['details']['username'][0], 'Это имя уже используется')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertNotIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_registration_incorrect_http_method(self):
        payload = {
            'email': self.email,
            'username': self.username,
            'password': self.password
        }

        response = self.client.get(
            self.url,
            data=payload,
            content_type='application/json'
        )
        user = get_user(self.client)

        self.assertEqual(response.status_code, 405)

        ## Проверяем, что тело запроса отсутствует
        self.assertFalse(response.content)

        ## Проверяем, что пользователь не стал авторизованным
        self.assertNotIn('_auth_user_id', self.client.session)

        ## Проверяем, что в тестовой БД появилась запись о пользователе
        self.assertFalse(User.objects.filter(pk=user.id).exists())


class TestUserViewLogin(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.email = 'user1@example.com'
        cls.username = 'UserOne'
        cls.password = 'ValidPass123'

        User.objects.create_user(email='user1@example.com', username='UserOne', password='ValidPass123')
        cls.url = '/api/users/login'

    def test_success_login(self):
        payload = {
            'email': self.email,
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        user = get_user(self.client)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.content)

        ## Проверяем, что пользователь стал авторизованным
        self.assertTrue(user.is_authenticated)

    def test_login_incorrect_email(self):
        payload = {
            'email': 'example@yandex.',
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 422)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])
        self.assertIn('details', data['error'])
        self.assertIn('email', data['error']['details'])

        self.assertEqual(data['error']['code'], 'validation_error')
        self.assertEqual(data['error']['message'], 'Проверьте введенные данные')
        self.assertEqual(data['error']['details']['email'][0], 'Укажите корректный email')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertFalse(user.is_authenticated)

    def test_login_without_email(self):
        payload = {
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 500)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'internal_error')
        self.assertEqual(data['error']['message'], 'Произошла внутренняя ошибка сервера')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertFalse(user.is_authenticated)

    def test_login_without_password(self):
        payload = {
            'email': self.email
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 500)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'internal_error')
        self.assertEqual(data['error']['message'], 'Произошла внутренняя ошибка сервера')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertFalse(user.is_authenticated)

    def test_non_existent_login(self):
        payload = {
            'email': 'example@yandex.ru',
            'password': self.password
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 401)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'invalid_credentials')
        self.assertEqual(data['error']['message'], 'Введен неверный email или пароль')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertFalse(user.is_authenticated)

    def test_login_incorrect_password(self):
        payload = {
            'email': self.email,
            'password': '1234567890'
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 401)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'invalid_credentials')
        self.assertEqual(data['error']['message'], 'Введен неверный email или пароль')

        ## Проверяем, что пользователь не стал авторизованным
        self.assertFalse(user.is_authenticated)

    def test_login_session_already_exists(self):
        payload = {
            'email': self.email,
            'password': self.password
        }

        first_response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        response = self.client.post(
            self.url,
            data=payload,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 403)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'authenticated')
        self.assertEqual(data['error']['message'], 'Пользователь уже авторизован')

        ## Проверяем, что у пользователя не слетела сессия
        self.assertTrue(user.is_authenticated)

    def test_login_incorrect_http_method(self):
        payload = {
            'email': self.email,
            'password': self.password
        }

        response = self.client.get(
            self.url,
            data=payload,
            content_type='application/json'
        )

        user = get_user(self.client)

        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.content)

        ## Проверяем, что у пользователя нет сессии
        self.assertFalse(user.is_authenticated)


class TestUserViewLogout(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.email = 'user1@example.com'
        cls.username = 'UserOne'
        cls.password = 'ValidPass123'

        cls.user = User.objects.create_user(email='user1@example.com', username='UserOne', password='ValidPass123')
        cls.url = '/api/users/logout'

    def test_logout_success(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(data), 1)
        self.assertIn('message', data)

        self.assertEqual(data['message'], 'Выход выполнен')

        self.assertFalse(user.is_authenticated)

    def test_logout_without_session(self):
        response = self.client.post(
            self.url,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 401)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'not_authenticated')
        self.assertEqual(data['error']['message'], 'Пользователь не авторизован')

        self.assertFalse(user.is_authenticated)

    def test_login_incorrect_http_method(self):
        response = self.client.get(
            self.url,
            content_type='application/json'
        )

        user = get_user(self.client)

        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.content)

        ## Проверяем, что у пользователя нет сессии
        self.assertFalse(user.is_authenticated)

    def test_logout_incorrect_cookie(self):
        self.client.force_login(self.user)

        self.client.cookies['sessionid'] = 'incorrect'

        response = self.client.post(
            self.url,
            content_type='application/json'
        )

        data = response.json()
        user = get_user(self.client)

        self.assertEqual(response.status_code, 401)

        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        self.assertIn('message', data['error'])

        self.assertEqual(data['error']['code'], 'not_authenticated')
        self.assertEqual(data['error']['message'], 'Пользователь не авторизован')

        self.assertFalse(user.is_authenticated)
