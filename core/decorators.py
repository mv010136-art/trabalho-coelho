from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """Permite acesso apenas a membros da equipe (is_staff).

    Visitantes anônimos são enviados para o login; usuários logados que não
    são da equipe recebem 403 (evita laço de redirecionamento).
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
