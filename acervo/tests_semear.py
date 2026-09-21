from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from .management.commands.semear import DADOS
from .models import Ideia, Link, Prompt


class SemearTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('leo', password='senha-bem-forte-123')

    def _semear(self, *args):
        call_command('semear', *args, verbosity=0)

    def test_cria_os_itens_de_exemplo(self):
        self._semear()
        for modelo, area in ((Prompt, 'prompts'), (Ideia, 'ideias'), (Link, 'links')):
            self.assertEqual(modelo.objects.count(), len(DADOS[area]))

    def test_atribui_ao_usuario(self):
        self._semear()
        self.assertEqual(Prompt.objects.exclude(criado_por=self.user).count(), 0)

    def test_usuario_escolhido(self):
        outro = get_user_model().objects.create_user('ana', password='senha-bem-forte-123')
        self._semear('--usuario', 'ana')
        self.assertEqual(Prompt.objects.exclude(criado_por=outro).count(), 0)

    def test_usuario_inexistente_da_erro(self):
        with self.assertRaises(CommandError):
            self._semear('--usuario', 'ninguem')

    def test_sem_usuario_no_banco_da_erro(self):
        get_user_model().objects.all().delete()
        with self.assertRaises(CommandError):
            self._semear()

    def test_rodar_duas_vezes_nao_duplica_nem_sobrescreve(self):
        self._semear()
        prompt = Prompt.objects.first()
        prompt.texto = 'texto que eu editei'
        prompt.save()

        self._semear()

        self.assertEqual(Prompt.objects.count(), len(DADOS['prompts']))
        prompt.refresh_from_db()
        self.assertEqual(prompt.texto, 'texto que eu editei')

    def test_limpar_remove_so_os_exemplos(self):
        self._semear()
        meu = Prompt.objects.create(titulo='Prompt que é meu', texto='...', criado_por=self.user)

        self._semear('--limpar')

        self.assertEqual(list(Prompt.objects.all()), [meu])
        self.assertEqual(Ideia.objects.count(), 0)
        self.assertEqual(Link.objects.count(), 0)
