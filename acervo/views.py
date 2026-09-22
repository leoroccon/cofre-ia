from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import IdeiaForm, LinkForm, NomeUsuarioForm, PromptForm, TemaForm, VideoForm
from .models import Ideia, Link, Perfil, Prompt, Video

# Cada área (prompts, ideias, links, vídeos) usa as mesmas telas; só mudam estes dados.
AREAS = {
    'prompts': {'model': Prompt, 'form': PromptForm, 'nome': 'Prompts', 'singular': 'prompt', 'artigo': 'o'},
    'ideias': {'model': Ideia, 'form': IdeiaForm, 'nome': 'Ideias de IA', 'singular': 'ideia', 'artigo': 'a'},
    'links': {'model': Link, 'form': LinkForm, 'nome': 'Links', 'singular': 'link', 'artigo': 'o'},
    'videos': {'model': Video, 'form': VideoForm, 'nome': 'Vídeos', 'singular': 'vídeo', 'artigo': 'o'},
}


class InicioView(LoginRequiredMixin, TemplateView):
    template_name = 'acervo/inicio.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['totais'] = {chave: cfg['model'].objects.count() for chave, cfg in AREAS.items()}
        return ctx


class ContaView(LoginRequiredMixin, TemplateView):
    """Área do usuário: tema, nome de usuário e senha (três formulários, uma página)."""

    template_name = 'acervo/conta.html'

    def _formularios(self, acao=None, dados=None):
        user = self.request.user
        perfil, _ = Perfil.objects.get_or_create(usuario=user)
        return {
            'form_tema': TemaForm(dados if acao == 'tema' else None, instance=perfil),
            # cópia do usuário: um nome inválido não pode vazar para o cabeçalho da página
            'form_nome': NomeUsuarioForm(dados if acao == 'nome' else None,
                                         instance=get_user_model().objects.get(pk=user.pk)),
            'form_senha': PasswordChangeForm(user, dados if acao == 'senha' else None),
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self._formularios())
        return ctx

    def post(self, request, *args, **kwargs):
        acao = request.POST.get('acao')
        formularios = self._formularios(acao, request.POST)
        form = formularios.get(f'form_{acao}')
        if form is not None and form.is_valid():
            form.save()
            if acao == 'senha':
                update_session_auth_hash(request, form.user)  # mantém o login ativo
            messages.success(request, {
                'tema': 'Tema alterado.', 'nome': 'Nome de usuário alterado.', 'senha': 'Senha alterada.',
            }[acao])
            return redirect('conta')
        ctx = self.get_context_data(**kwargs)
        ctx.update(formularios)  # mostra o formulário com os erros
        ctx['acao_com_erro'] = acao
        return self.render_to_response(ctx)


class AreaMixin(LoginRequiredMixin):
    """Descobre a área (prompts/ideias/links) pela URL e a coloca no contexto."""

    @property
    def cfg(self):
        return AREAS[self.kwargs['area']]

    def get_queryset(self):
        return self.cfg['model'].objects.all()

    def get_form_class(self):
        return self.cfg['form']

    def get_success_url(self):
        return reverse_lazy('lista', kwargs={'area': self.kwargs['area']})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(area=self.kwargs['area'], cfg=self.cfg)
        return ctx


def _agrupar_por_texto(itens, texto_de, vazio):
    """Agrupa itens por um texto (sem diferenciar maiúsculas); o grupo sem texto fica por último."""
    grupos = {}
    for item in itens:
        nome = texto_de(item).strip()
        grupo = grupos.setdefault(nome.casefold(), {'nome': (nome[:1].upper() + nome[1:]) or vazio, 'itens': []})
        grupo['itens'].append(item)
    return sorted(grupos.values(), key=lambda g: (g['nome'] == vazio, g['nome'].casefold()))


def agrupar_por_categoria(itens):
    """Prompts: um grupo por categoria."""
    return _agrupar_por_texto(itens, lambda i: i.categoria, 'Sem categoria')


def agrupar_links(itens):
    """Links: um grupo por primeira etiqueta."""
    return _agrupar_por_texto(itens, lambda i: (i.lista_etiquetas() or [''])[0], 'Sem etiqueta')


def agrupar_ideias(itens):
    """Ideias: um grupo por status, na ordem rascunho, em teste, feita."""
    grupos = {}
    for item in itens:
        grupos.setdefault(item.status, {'nome': item.get_status_display(), 'itens': []})['itens'].append(item)
    return [grupos[s.value] for s in Ideia.Status if s.value in grupos]


AGRUPADORES = {
    'prompts': agrupar_por_categoria, 'ideias': agrupar_ideias, 'links': agrupar_links, 'videos': agrupar_links,
}


class ListaView(AreaMixin, ListView):
    template_name = 'acervo/lista.html'
    # Sem páginas: tudo aparece agrupado (por categoria, status ou etiqueta).
    def get_queryset(self):
        qs = super().get_queryset()
        busca = self.request.GET.get('q', '').strip()
        etiqueta = self.request.GET.get('etiqueta', '').strip()
        if busca:
            campos = [f.name for f in qs.model._meta.get_fields()
                      if f.get_internal_type() in ('CharField', 'TextField')]
            filtro = Q()
            for campo in campos:
                filtro |= Q(**{f'{campo}__icontains': busca})
            qs = qs.filter(filtro)
        if etiqueta:
            qs = qs.filter(etiquetas__icontains=etiqueta)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['etiqueta'] = self.request.GET.get('etiqueta', '')
        ctx['grupos'] = AGRUPADORES[self.kwargs['area']](ctx['object_list'])
        return ctx


class PromptDetalheView(LoginRequiredMixin, DetailView):
    model = Prompt
    template_name = 'acervo/prompt_detalhe.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(area='prompts', cfg=AREAS['prompts'])
        return ctx


class VideoDetalheView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'acervo/video_detalhe.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(area='videos', cfg=AREAS['videos'])
        return ctx


class CriarView(AreaMixin, SuccessMessageMixin, CreateView):
    template_name = 'acervo/formulario.html'
    success_message = 'Salvo com sucesso.'

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)


class EditarView(AreaMixin, SuccessMessageMixin, UpdateView):
    template_name = 'acervo/formulario.html'
    success_message = 'Alterações salvas.'


class ExcluirView(AreaMixin, DeleteView):
    template_name = 'acervo/excluir.html'

    def get_form_class(self):
        return Form  # confirmação simples, sem os campos do item
