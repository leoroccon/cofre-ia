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
    class Meta:
        model = Video
        fields = ['titulo', 'url', 'descricao', 'resumo', 'etiquetas']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'resumo': forms.Textarea(attrs={'rows': 6}),
        }
