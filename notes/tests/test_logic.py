from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestAddNote(TestCase):
    TITLE = 'Тестовый заголовок'
    TEXT = 'Просто текст'
    SLUG = 'note'

    @classmethod
    def setUpTestData(cls):
        cls.add_url = reverse('notes:add')
        cls.done_url = reverse('notes:success')
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {
            'title': cls.TITLE, 'text': cls.TEXT, 'slug': cls.SLUG
        }

    def test_anonymous_user_cant_add_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(self.add_url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_add_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.add_url, data=self.form_data)
        # Проверяем, что редирект привёл на страницу Done.
        self.assertRedirects(response, self.done_url)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна заметка.
        self.assertEqual(notes_count, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.title, self.TITLE)
        self.assertEqual(note.text, self.TEXT)
        self.assertEqual(note.slug, self.SLUG)
        self.assertEqual(note.author, self.user)

    def test_user_can_add_note_without_slug(self):
        self.form_data.pop('slug')
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.slug, slugify(self.TITLE))

    def test_user_cant_add_note_with_not_uniq_slug(self):
        self.note = Note.objects.create(
            title=self.TITLE, text=self.TEXT,
            slug=self.SLUG, author=self.user,
        )
        response = self.auth_client.post(self.add_url, data=self.form_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.SLUG}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestEditDeleteNote(TestCase):
    TITLE = 'Тестовый заголовок'
    TEXT = 'Просто текст'
    SLUG = 'note'
    NEW_TITLE = 'Новый заголовок'
    NEW_TEXT = 'Новый текст'
    NEW_SLUG = 'note_new'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Пользователь 1')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_user = User.objects.create(username='Пользователь 2')
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)
        cls.note = Note.objects.create(
            title=cls.TITLE, text=cls.TEXT,
            slug=cls.SLUG, author=cls.author,
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.done_url = reverse('notes:success')
        # Формируем данные для POST-запроса по обновлению записи.
        cls.form_data = {
            'title': cls.NEW_TITLE, 'text': cls.NEW_TEXT, 'slug': cls.NEW_SLUG
        }

    def test_author_can_delete_note(self):
        # От имени автора записи отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл на страницу Done.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.done_url)
        # Считаем количество заметок в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль заметок в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от другого пользователя.
        response = self.another_user_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что запись по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора заметки.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.done_url)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст заметки соответствует обновленному.
        self.assertEqual(
            (self.note.title, self.note.text, self.note.slug,),
            (self.NEW_TITLE, self.NEW_TEXT, self.NEW_SLUG,)
        )

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.another_user_client.post(
            self.edit_url, data=self.form_data
        )
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что данные заметки остались теми же, что и были.
        self.assertEqual(
            (self.note.title, self.note.text, self.note.slug,),
            (self.TITLE, self.TEXT, self.SLUG,)
        )
