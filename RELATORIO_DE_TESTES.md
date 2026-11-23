# Relatório de testes e verificação

## Status: versão final executada

Este relatório foi atualizado em **23/11/2026**, na verificação da versão com o frontend novo (categoria/câmbio/combustível, filtros e ordenação, histórico por abas e visual reformulado).

**Resumo:** `manage.py check`, `makemigrations --check`, migrações, `seed_demo`, `collectstatic` e **131 testes** passaram. Também foram executadas **80 verificações HTTP** com o servidor no ar, cobrindo as páginas novas, filtros, abas do histórico, painel, admin, permissões e arquivos estáticos. Nenhum erro de template ou 500 apareceu.

## Ambiente da execução

| Item | Versão |
|---|---|
| Sistema | Windows 11 |
| Python | 3.11.9 |
| Django | 5.2.9 |
| Pillow | 12.3.0 |
| tzdata | 2026.6 (Django declara essa dependência no Windows) |
| Banco | SQLite |

As dependências foram instaladas a partir de wheels baixados com o próprio Python porque o cliente `pip` do ambiente de revisão travava ao acessar o PyPI. Em uma máquina com internet, `pip install -r requirements.txt` é o caminho normal.

## Comandos e resultados

| Comando | Resultado |
|---|---|
| `python manage.py check` | System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python manage.py migrate` | Migrações `0001` e `0002` aplicadas sem erro (banco novo) |
| `python manage.py seed_demo --demo-customer` | 6 veículos + `cliente_demo` / `demo12345` |
| `python -m unittest reservations.test_rules` | 11 testes puros, OK |
| `python manage.py test -v 2` | **131 testes, todos OK, em 185,7 s** |
| `python manage.py collectstatic --noinput` | 138 arquivos copiados |
| `python manage.py runserver` | Servidor no ar em `http://127.0.0.1:8000/` |
| `python -m compileall` | OK |
| `python manage.py check --deploy` | Apenas os avisos esperados de configuração de desenvolvimento (DEBUG/HSTS/cookies/chave) |

A suíte tem 15 testes em `accounts`, 40 em `vehicles`, 43 em `reservations`, 22 em `core` e 11 em `reservations/test_rules.py`.

## O que foi validado no frontend novo

- **Home:** capa, faixa de números, cartões de categoria, formulário de busca, veículos recentes e CTA.
- **Catálogo:** busca por texto/placa/lugares; filtros de categoria, marca, câmbio, lugares e diária; filtro por período; ordenação por preço/popularidade/recentes/nome; contador de resultados e “Limpar filtros”.
- **Detalhe:** foto/placeholder, categoria, câmbio, combustível, lugares, placa, situação, curtidas, períodos reservados e barra fixa de “Reservar”.
- **Histórico:** abas Todas / Próximas / Em andamento / Concluídas / Canceladas, contagens, fase da reserva e total em reservas.
- **Painel e admin:** tabelas que viram cartões no celular, formulário de veículo com os campos novos, listas e telas de alteração.
- **Segurança:** cliente recebe 403 no painel, rotas protegidas redirecionam para login, logout por GET retorna 405.
- **Estáticos:** CSS, JS, fontes dos ícones e imagens responderam 200; todos os caminhos `{% static %}` e `{{ vehicle.image.url }}` renderizaram corretamente.

As **80 verificações HTTP** foram divididas em 37 (fluxos principais e novas funcionalidades) + 43 (todas as páginas, filtros inválidos, abas, telas de edição/exclusão, admin e estáticos). Todas passaram.

## Correções da revisão anterior (mantidas nesta versão)

1. **Reserva em andamento editável pela equipe** — `ReservationForm.clean_start_date` aceita a data original de uma reserva existente; novas reservas continuam exigindo hoje/futuro. Teste: `test_staff_can_edit_in_progress_reservation_without_changing_start`.
2. **Admin não cancela reserva concluída em massa** — `ReservationAdmin.mark_cancelled` atua só em reservas confirmadas. Teste: `test_admin_cancel_action_does_not_reopen_completed_reservations`.

## Riscos e limitações

1. **Conferência visual:** o ambiente de revisão não abriu navegador gráfico (sandbox bloqueia o Edge headless). A validação foi por renderização de todos os templates, HTTP 200, caminhos de CSS/imagem e classes CSS; vale abrir as telas uma vez no PC/celular para conferir alinhamento e o menu.
2. **jQuery via CDN:** o menu responsivo e os alertas do Bootstrap dependem de `code.jquery.com`; sem internet, o menu pode não abrir.
3. **Banco e mídia não vão no ZIP:** rode `migrate`; `seed_demo --demo-customer` é opcional.
4. **Concorrência:** `select_for_update` só tem efeito real no PostgreSQL; no SQLite as escritas são serializadas pelo banco.
5. **Produção:** `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY` forte, `DJANGO_ALLOWED_HOSTS`, HTTPS e servidor WSGI/ASGI.
6. **Upgrade de banco antigo:** a migração `0002` dá categoria/câmbio/combustível padrão aos veículos já cadastrados; ajuste-os no painel se necessário.
7. **Sem e-mail, pagamento ou recuperação de senha:** limitações já assumidas no README.

## Problemas do projeto original corrigidos (histórico)

- Django 1.9 → 5.2: `url()` removido, `{% load staticfiles %}`, `USE_L10N`, `SessionAuthenticationMiddleware`, `django.conf.urls` etc.
- App `accounts` sem `INSTALLED_APPS`; `crispy_forms` obrigatório mas sem `requirements`.
- `order_list` filtrava por `movie_name` (campo inexistente → erro 500 na busca).
- Pedido guardava carro e cliente como texto (sem ForeignKey); preço como `CharField`.
- Qualquer visitante acessava `/` e podia excluir carros/pedidos por link GET.
- Cadastro sem confirmação de senha e sem e-mail único; `login_view` testava o usuário errado.
- Botão “Book” só para staff e formulário sem veículo; contato da home sem `<form>`.
- `car_update` não aceitava imagem; “like” sem limite e por GET.
- `STATIC_ROOT`/`MEDIA_ROOT` fora do projeto; `SECRET_KEY` fixa; HTML sem `<head>` fechado; scripts por HTTP.
