from django.urls import path, register_converter

from . import views


class AreaConverter:
    regex = 'prompts|ideias|links|videos'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(AreaConverter, 'area')

urlpatterns = [
    path('', views.InicioView.as_view(), name='inicio'),
    path('conta/', views.ContaView.as_view(), name='conta'),
    path('prompts/<int:pk>/', views.PromptDetalheView.as_view(), name='prompt_detalhe'),
    path('videos/<int:pk>/', views.VideoDetalheView.as_view(), name='video_detalhe'),
    path('<area:area>/', views.ListaView.as_view(), name='lista'),
    path('<area:area>/novo/', views.CriarView.as_view(), name='criar'),
    path('<area:area>/<int:pk>/editar/', views.EditarView.as_view(), name='editar'),
    path('<area:area>/<int:pk>/excluir/', views.ExcluirView.as_view(), name='excluir'),
]
