import re

from django import forms
from django.contrib.auth import get_user_model

from .models import Ideia, Link, Perfil, Prompt, Video


class TemaForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['tema']
        widgets = {'tema': forms.RadioSelect}


class NomeUsuarioForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username']
        labels = {'username': 'Nome de usuário'}
        help_texts = {'username': 'É o nome que você digita para entrar. Letras, números e @/./+/-/_'}


class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ['titulo', 'descricao', 'texto', 'ferramenta', 'categoria', 'etiquetas', 'favorito']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'texto': forms.Textarea(attrs={'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = True


class IdeiaForm(forms.ModelForm):
    class Meta:
        model = Ideia
        fields = ['titulo', 'descricao', 'status', 'etiquetas']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 8})}


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['titulo', 'url', 'descricao', 'etiquetas']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 4})}


class VideoForm(forms.ModelForm):
    # CharField (não URLField): assim aceita quem cola o código <iframe> de incorporar do YouTube;
    # a extração do endereço e a validação do formato ficam por conta de clean_url, abaixo.
    url = forms.CharField(
        label='endereço do vídeo', max_length=500,
        widget=forms.TextInput(attrs={'placeholder': 'Cole aqui o link do vídeo (ou o código de incorporar)'}),
    )

    class Meta:
        model = Video
        fields = ['titulo', 'url', 'descricao', 'resumo', 'etiquetas']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'resumo': forms.Textarea(attrs={'rows': 6}),
        }

    def clean_url(self):
        valor = self.cleaned_data['url'].strip()
        # quem cola o <iframe> inteiro do YouTube: pega só o endereço do src
        trecho = re.search(r'src=[\'"]([^\'"]+)[\'"]', valor)
        if trecho:
            valor = trecho.group(1).strip()
        if valor.startswith('//'):
            valor = 'https:' + valor
        return forms.URLField().clean(valor)  # valida o formato (levanta erro se não for uma URL válida)
