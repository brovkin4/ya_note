from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestPages(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь 1')
        cls.another_user = User.objects.create(username='Пользователь 2')
        cls.note = Note.objects.create(
            title='Запись',
            text='Просто текст.',
            slug='Slug',
            author=cls.user
        )
        cls.list_url = reverse('notes:list',)
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.add_url = reverse('notes:add',)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_list_has_note_of_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_list_not_has_notes_of_another_user(self):
        self.client.force_login(self.another_user)
        response = self.client.get(self.list_url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

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
