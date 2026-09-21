from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Ideia, Link, Prompt

DADOS = {
    'prompts': {'titulo': 'Render fachada', 'descricao': 'Gera renders de fachadas modernas.',
                'texto': 'Gere uma fachada moderna...', 'etiquetas': 'render, fachada'},
    'ideias': {'titulo': 'Assistente de memorial', 'descricao': 'IA que escreve memoriais.', 'status': 'rascunho'},
    'links': {'titulo': 'Docs Claude', 'url': 'https://docs.claude.com', 'etiquetas': 'docs'},
}
MODELOS = {'prompts': Prompt, 'ideias': Ideia, 'links': Link}


class AcessoTests(TestCase):
    def test_anonimo_e_redirecionado_ao_login(self):
        urls = [reverse('inicio')] + [reverse('lista', args=[a]) for a in DADOS] \
            + [reverse('criar', args=[a]) for a in DADOS]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, url)
            self.assertIn(reverse('login'), resp['Location'])

    def test_anonimo_nao_consegue_criar(self):
        self.client.post(reverse('criar', args=['links']), DADOS['links'])
        self.assertEqual(Link.objects.count(), 0)

    def test_login_com_senha_correta(self):
        get_user_model().objects.create_user('leo', password='senha-bem-forte-123')
        resp = self.client.post(reverse('login'), {'username': 'leo', 'password': 'senha-bem-forte-123'})
        self.assertRedirects(resp, reverse('inicio'))


class CrudTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('leo', password='senha-bem-forte-123')
        self.client.force_login(self.user)

    def test_crud_das_tres_areas(self):
        for area, dados in DADOS.items():
            modelo = MODELOS[area]
            resp = self.client.post(reverse('criar', args=[area]), dados)
            self.assertRedirects(resp, reverse('lista', args=[area]))
            item = modelo.objects.get()
            self.assertEqual(item.criado_por, self.user)

            self.assertContains(self.client.get(reverse('lista', args=[area])), dados['titulo'])

            dados_novos = {**dados, 'titulo': 'Título novo'}
            self.client.post(reverse('editar', args=[area, item.pk]), dados_novos)
            item.refresh_from_db()
            self.assertEqual(item.titulo, 'Título novo')

            self.client.post(reverse('excluir', args=[area, item.pk]))
            self.assertEqual(modelo.objects.count(), 0)

    def test_lista_de_prompts_mostra_descricao_e_nao_o_texto(self):
        p = Prompt.objects.create(titulo='Render', descricao='Serve para renders.', texto='TEXTO-SECRETO-DO-PROMPT')
        resp = self.client.get(reverse('lista', args=['prompts']))
        self.assertContains(resp, 'Serve para renders.')
        self.assertNotContains(resp, '<pre')  # o texto não aparece na tela...
        self.assertContains(resp, 'data-texto="TEXTO-SECRETO-DO-PROMPT"')  # ...só fica guardado no botão Copiar
        self.assertContains(self.client.get(reverse('prompt_detalhe', args=[p.pk])), 'TEXTO-SECRETO-DO-PROMPT')

    def test_prompts_agrupados_por_categoria(self):
        Prompt.objects.create(titulo='P1', descricao='d', texto='t', categoria='Imagem')
        Prompt.objects.create(titulo='P2', descricao='d', texto='t', categoria='imagem ')
        Prompt.objects.create(titulo='P3', descricao='d', texto='t', categoria='Texto')
        Prompt.objects.create(titulo='P4', descricao='d', texto='t')
        grupos = self.client.get(reverse('lista', args=['prompts'])).context['grupos']
        self.assertEqual([g['nome'] for g in grupos], ['Imagem', 'Texto', 'Sem categoria'])
        self.assertEqual([len(g['itens']) for g in grupos], [2, 1, 1])

    def test_detalhe_do_prompt_exige_login(self):
        p = Prompt.objects.create(titulo='X', descricao='d', texto='t')
        self.client.logout()
        self.assertEqual(self.client.get(reverse('prompt_detalhe', args=[p.pk])).status_code, 302)

    def test_ideias_agrupadas_por_status_na_ordem(self):
        Ideia.objects.create(titulo='I1', descricao='d', status='feita')
        Ideia.objects.create(titulo='I2', descricao='d', status='rascunho')
        Ideia.objects.create(titulo='I3', descricao='d', status='teste')
        Ideia.objects.create(titulo='I4', descricao='d', status='rascunho')
        grupos = self.client.get(reverse('lista', args=['ideias'])).context['grupos']
        self.assertEqual([g['nome'] for g in grupos], ['Rascunho', 'Em teste', 'Feita'])
        self.assertEqual([len(g['itens']) for g in grupos], [2, 1, 1])

    def test_links_agrupados_pela_primeira_etiqueta_e_abrem_o_endereco(self):
        Link.objects.create(titulo='L1', url='https://www.exemplo.com/a', etiquetas='claude, docs')
        Link.objects.create(titulo='L2', url='https://exemplo.org', etiquetas='Claude')
        Link.objects.create(titulo='L3', url='https://outro.com', etiquetas='design')
        Link.objects.create(titulo='L4', url='https://sem.com')
        resp = self.client.get(reverse('lista', args=['links']))
        self.assertEqual([g['nome'] for g in resp.context['grupos']], ['Claude', 'Design', 'Sem etiqueta'])
        self.assertContains(resp, 'data-url="https://www.exemplo.com/a"')
        self.assertContains(resp, 'exemplo.com</span>')  # domínio sem "www."

    def test_busca_e_filtro_por_etiqueta(self):
        Prompt.objects.create(titulo='A', texto='chuva', etiquetas='imagem')
        Prompt.objects.create(titulo='B', texto='sol', etiquetas='texto')
        url = reverse('lista', args=['prompts'])
        self.assertEqual(len(self.client.get(url, {'q': 'chuva'}).context['object_list']), 1)
        self.assertEqual(len(self.client.get(url, {'etiqueta': 'texto'}).context['object_list']), 1)

    def test_conteudo_e_compartilhado_entre_usuarios(self):
        Prompt.objects.create(titulo='Do Leo', texto='x', criado_por=self.user)
        irmao = get_user_model().objects.create_user('irmao', password='outra-senha-forte-456')
        self.client.force_login(irmao)
        self.assertContains(self.client.get(reverse('lista', args=['prompts'])), 'Do Leo')
