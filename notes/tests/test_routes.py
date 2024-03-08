from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create(username='Лев Толстой')
        cls.anonymous = User.is_anonymous
        cls.user_2 = User.objects.create(username='Александр Пушкин')
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст',
            slug='slug', author=cls.user_1
        )

    def test_pages_availability_all(self):
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_auth_user(self):
        names = (
            'notes:list',
            'notes:add',
            'notes:success',
        )
        # Логиним пользователя в клиенте:
        self.client.force_login(self.user_2)
        # Для каждой пары "пользователь - ожидаемый ответ"
        # перебираем имена тестируемых страниц:
        for name in names:
            with self.subTest(user=self.user_2, name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_pages_edit_delete_detail(self):
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        users_statuses = (
            (self.user_1, HTTPStatus.OK),
            (self.user_2, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name, args in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:success', None),
        )
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                # Получаем ожидаемый адрес страницы логина,
                # на который будет перенаправлен пользователь.
                # Учитываем, что в адресе будет параметр next,
                # в котором передаётся
                # адрес страницы, с которой пользователь был переадресован.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
