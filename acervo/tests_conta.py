from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Perfil

SENHA = 'senha-bem-forte-123'
NOVA = 'outra-senha-mais-forte-456'


class ContaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('leo', password=SENHA)
        self.client.force_login(self.user)
        self.url = reverse('conta')

    def test_exige_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_tema_padrao_e_troca(self):
        self.assertContains(self.client.get(reverse('inicio')), 'tema-circuito')
        resp = self.client.post(self.url, {'acao': 'tema', 'tema': 'paisagismo'})
        self.assertRedirects(resp, self.url)
        self.assertEqual(Perfil.objects.get(usuario=self.user).tema, 'paisagismo')
        self.assertContains(self.client.get(reverse('inicio')), 'tema-paisagismo')

    def test_tema_invalido_e_rejeitado(self):
        self.client.post(self.url, {'acao': 'tema', 'tema': 'inexistente'})
        self.assertNotEqual(getattr(Perfil.objects.filter(usuario=self.user).first(), 'tema', None), 'inexistente')

    def test_tema_e_por_usuario(self):
        self.client.post(self.url, {'acao': 'tema', 'tema': 'paisagismo'})
        irmao = get_user_model().objects.create_user('irmao', password=SENHA)
        self.client.force_login(irmao)
        self.assertContains(self.client.get(reverse('inicio')), 'tema-circuito')

    def test_troca_de_nome(self):
        self.client.post(self.url, {'acao': 'nome', 'username': 'leonardo'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'leonardo')

    def test_nome_repetido_e_rejeitado(self):
        get_user_model().objects.create_user('irmao', password=SENHA)
        resp = self.client.post(self.url, {'acao': 'nome', 'username': 'irmao'})
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'leo')
        self.assertContains(resp, 'leo</a>')  # cabeçalho não mostra o nome recusado

    def test_troca_de_senha_mantem_login(self):
        resp = self.client.post(self.url, {
            'acao': 'senha', 'old_password': SENHA, 'new_password1': NOVA, 'new_password2': NOVA})
        self.assertRedirects(resp, self.url)
        self.assertEqual(self.client.get(self.url).status_code, 200)  # continua logado
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NOVA))

    def test_senha_atual_errada_ou_fraca_e_rejeitada(self):
        self.client.post(self.url, {
            'acao': 'senha', 'old_password': 'errada', 'new_password1': NOVA, 'new_password2': NOVA})
        self.client.post(self.url, {
            'acao': 'senha', 'old_password': SENHA, 'new_password1': '12345', 'new_password2': '12345'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(SENHA))
