from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def paginate(request, queryset, per_page=12):
    """Pagina um queryset; páginas inválidas caem na primeira/última."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def redirect_back(request, default, *args):
    """Redireciona para o parâmetro ``next`` (POST/GET) se for seguro."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(target)
    return redirect(default, *args)
