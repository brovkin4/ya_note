from django.contrib.auth import get_user_model
from django.test import TestCase
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestPages(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь 1')
        cls.all_notes = [
            Note(
                title=f'Запись {index}',
                text='Просто текст.',
                slug=f'Slug_{index}',
                author=cls.user
            )
            for index in range(3)
        ]
        Note.objects.bulk_create(cls.all_notes)
        cls.list_url = reverse('notes:list',)
        cls.detail_url = reverse('notes:detail', args=(cls.all_notes[0].slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.all_notes[1].slug,))
        cls.add_url = reverse('notes:add',)
        cls.edit_url = reverse('notes:edit', args=(cls.all_notes[2].slug,))

    def test_notes_order(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        object_list = response.context['object_list']
        # Получаем даты новостей в том порядке, как они выведены на странице.
        all_notes = [note.id for note in object_list]
        # Сортируем полученный список по убыванию.
        sorted_nodes = sorted(all_notes)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_notes, sorted_nodes)
        self.assertEqual(object_list.count(), len(all_notes))

    def test_detail_delete_has_no_form(self):
        self.client.force_login(self.user)
        for name in (self.detail_url, self.delete_url):
            with self.subTest(name=name):
                response = self.client.get(path=name)
                self.assertNotIn('form', response.context)

    def test_add_edit_has_form(self):
        self.client.force_login(self.user)
        for name in (self.add_url, self.edit_url):
            with self.subTest(name=name):
                response = self.client.get(path=name)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
