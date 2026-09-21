from urllib.parse import urlparse

from django.conf import settings
from django.db import models


class Perfil(models.Model):
    """Preferências de cada usuário (por enquanto, só o tema visual)."""

    class Tema(models.TextChoices):
        CIRCUITO = 'circuito', 'Circuito'
        PAISAGISMO = 'paisagismo', 'Paisagismo'

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    tema = models.CharField(max_length=20, choices=Tema.choices, default=Tema.CIRCUITO)

    def __str__(self):
        return f'Perfil de {self.usuario}'


class ItemBase(models.Model):
    titulo = models.CharField('título', max_length=200)
    etiquetas = models.CharField(
        max_length=200, blank=True, help_text='Separe por vírgulas. Ex.: arquitetura, imagem, render'
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name='criado por',
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-atualizado_em']

    def __str__(self):
        return self.titulo

    def lista_etiquetas(self):
        return [e.strip() for e in self.etiquetas.split(',') if e.strip()]


class Prompt(ItemBase):
    descricao = models.TextField(
        'descrição', blank=True, help_text='Para que serve este prompt? É isto que aparece no card.'
    )
    texto = models.TextField('texto do prompt')
    ferramenta = models.CharField(
        'ferramenta / modelo', max_length=100, blank=True, help_text='Ex.: Claude, Midjourney, ChatGPT'
    )
    categoria = models.CharField(max_length=100, blank=True)
    favorito = models.BooleanField(default=False)

    class Meta(ItemBase.Meta):
        verbose_name = 'prompt'
        verbose_name_plural = 'prompts'


class Ideia(ItemBase):
    class Status(models.TextChoices):
        RASCUNHO = 'rascunho', 'Rascunho'
        TESTE = 'teste', 'Em teste'
        FEITA = 'feita', 'Feita'

    descricao = models.TextField('descrição')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RASCUNHO)

    class Meta(ItemBase.Meta):
        verbose_name = 'ideia'
        verbose_name_plural = 'ideias'


class Link(ItemBase):
    url = models.URLField('endereço (URL)', max_length=500)
    descricao = models.TextField('descrição', blank=True)

    @property
    def dominio(self):
        return urlparse(self.url).netloc.removeprefix('www.')

    class Meta(ItemBase.Meta):
        verbose_name = 'link'
        verbose_name_plural = 'links'
