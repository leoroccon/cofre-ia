from .models import Perfil


def tema(request):
    """Disponibiliza o tema escolhido pelo usuário em todos os templates."""
    escolhido = Perfil.Tema.CIRCUITO.value
    if request.user.is_authenticated:
        salvo = Perfil.objects.filter(usuario=request.user).values_list('tema', flat=True).first()
        if salvo:
            escolhido = salvo
    return {'tema': escolhido, 'temas': Perfil.Tema.choices}
