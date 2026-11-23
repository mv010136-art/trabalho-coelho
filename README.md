# Online Car Rental System (Django)

Sistema web de aluguel de veículos feito em **Django 5.2 LTS**: clientes se cadastram, buscam veículos por texto e por período livre, reservam com datas de retirada e devolução e acompanham suas reservas; a equipe gerencia frota, reservas e mensagens num painel próprio e no admin do Django.

Este projeto é a atualização completa do *Online-Car-Rental-System-Project-in-Django* original (Django 1.9, que não executava nas versões atuais).

> ✅ **Status de verificação (23/11/2026):** versão final executada em Windows com Python 3.11.9 e Django 5.2.9. `manage.py check`, `makemigrations --check`, migrações, `seed_demo`, `collectstatic` e os **131 testes passaram** (185,7 s; 11 deles são as regras puras). Também foram feitas **80 verificações HTTP** com o servidor no ar (catálogo, filtros, histórico por abas, painel, admin, permissões e estáticos), sem erro de template. As duas correções da revisão anterior continuam aplicadas e cobertas por testes. Veja `RELATORIO_DE_TESTES.md` e `REVISAO_FINAL_FRONTEND.md`.

## Funcionalidades

| Área | O que existe |
|---|---|
| Clientes | Cadastro (com telefone, endereço, CNH), login, logout, edição de perfil |
| Catálogo | Categoria, câmbio e combustível por veículo; busca por texto e **filtros** (categoria, marca, câmbio, lugares mínimos, diária máxima, período livre) com **ordenação** (preço, popularidade, recentes, nome); páginas *Todos / Novidades / Mais curtidos*; contador de resultados; curtir/descurtir |
| Veículos (equipe) | Cadastro, edição, exclusão (com confirmação) e foto |
| Reservas | Datas de retirada e devolução, valor calculado (diárias × valor da diária, congelado no momento da reserva), alterar datas e cancelar |
| Histórico | Abas *Todas / Próximas / Em andamento / Concluídas / Canceladas* com contagens, fase de cada reserva e total em reservas (exceto canceladas) |
| Interface | Página inicial com busca por período e categoria, categorias clicáveis, tabelas que viram cartões e barra fixa de “Reservar” no celular (Bootstrap 3) |
| Regras | Sem reservas sobrepostas para o mesmo veículo; devolução deve ser depois da retirada; retirada não pode ser no passado; veículo fora da frota não pode ser reservado |
| Disponibilidade | Filtro “livre entre duas datas”, selo *Disponível / Alugado agora / Fora da frota*, lista de períodos já reservados na página do veículo |
| Painel da equipe (`/painel/`) | Resumo (veículos, alugados agora, retiradas/devoluções de hoje, receita do mês, vendas dos últimos 7 dias), listas com busca/filtros de veículos, reservas e mensagens, concluir/cancelar reserva |
| Admin do Django (`/admin/`) | Clientes, veículos, reservas (filtros, busca, ações em massa) e mensagens de contato |
| Contato | Formulário público; mensagens aparecem no painel |

### Regra de período (importante)
O período é tratado como **[retirada, devolução)**: o veículo fica ocupado a partir do dia da retirada e volta a ficar livre no dia da devolução. Assim, uma reserva pode **começar no dia em que outra termina**. Reservas *canceladas* não bloqueiam o veículo.

### Cancelamento e alteração
O cliente pode alterar datas ou cancelar **até o dia anterior à retirada**; depois disso, deve contatar a equipe. A equipe pode alterar/cancelar/concluir qualquer reserva confirmada. Cancelar não apaga: a reserva fica no histórico com a situação *Cancelada*.

## Requisitos
- Python 3.10 a 3.13
- Acesso à internet no navegador para carregar o jQuery (usado pelo menu responsivo do Bootstrap 3) a partir de `code.jquery.com`. O Bootstrap CSS/JS e as fontes de ícones já estão em `static/`.

## Atalho (1 clique)
No Windows, dê dois cliques em `iniciar.bat` (cria o ambiente, instala, migra, cria os dados de demonstração, confere o projeto e abre o servidor). Para só rodar os testes: `testar.bat`. No Linux/macOS: `./iniciar.sh` e `./testar.sh`. As contas criadas (`admin` / `admin12345` e `cliente_demo` / `demo12345`) são só para teste local.

## Instalação e execução

```bash
# 1. Ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Dependências
pip install -r requirements.txt

# 3. Banco de dados (SQLite por padrão)
python manage.py migrate

# 4. Usuário administrador (equipe)
python manage.py createsuperuser

# 5. (Opcional) dados de demonstração: 6 veículos e um cliente de teste
python manage.py seed_demo --demo-customer

# 6. Servidor
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ . O superusuário entra por `/contas/entrar/` e é levado ao painel `/painel/`.

> O cliente de demonstração (`cliente_demo` / `demo12345`) existe **só para testes locais**; não use em produção.

## Testes

```bash
python -m unittest reservations.test_rules          # regras puras, sem Django (já executado: OK)
python manage.py check
python manage.py makemigrations --check --dry-run   # garante que modelos e migrações estão em dia
python manage.py test -v 2
```

A suíte cobre cadastro/login/perfil, CRUD e busca de veículos, curtidas, reservas (cálculo de valor, todos os tipos de sobreposição, reservas encostadas, canceladas, permissões), painel da equipe, admin do Django, comando `seed_demo` e verificações de migração. O workflow `.github/workflows/tests.yml` roda tudo no GitHub Actions.

## Estrutura

```
car_rental_app/   configuração (settings, urls, wsgi/asgi)
core/             home, contato, painel da equipe, utilitários e fábricas de teste
accounts/         Customer (OneToOne com User), cadastro, login, perfil
vehicles/         Vehicle, busca/disponibilidade, CRUD, curtidas, comando seed_demo
reservations/     Reservation (FK para Customer e Vehicle), rules.py (regras puras), views
templates/ static/
```

### Modelos e relacionamentos
```
User 1──1 Customer 1──* Reservation *──1 Vehicle
User *──* Vehicle   (curtidas)
```
`Reservation.customer` e `Reservation.vehicle` são `ForeignKey(on_delete=PROTECT)`: não se apaga um cliente/veículo que tenha reservas (para o veículo, desmarque “ativo na frota”). Há ainda um `CheckConstraint` no banco garantindo `devolução > retirada`.

### De onde veio cada parte do projeto original

| Original | Agora |
|---|---|
| `system.Car` | `vehicles.Vehicle` (preço agora `DecimalField`; placa; ativo na frota; curtidas por usuário) |
| `system.Order` (nome do carro e do cliente em texto) | `reservations.Reservation` (FKs reais, datas, valor, situação) |
| `system.PrivateMsg` | `core.ContactMessage` |
| `accounts` (login/registro) | `accounts` (agora com perfil de cliente, confirmação de senha, e-mail único) |
| views de “admin” abertas a qualquer um | painel `/painel/` restrito à equipe (`is_staff`) |
| exclusão por link GET | exclusão/cancelamento só por POST, com confirmação |

Recursos do original **preservados**: lista de carros com busca e paginação, detalhe, “novos”, “populares” (curtidas), contato, painel de carros/pedidos/mensagens e vendas.

> O `db.sqlite3` do original **não foi incluído**: o esquema era incompatível (pedidos guardavam nomes em texto, preços em `CharField`). Ele continha apenas 1 carro, 1 pedido e 2 usuários de teste.

## Configuração por variáveis de ambiente
Veja `.env.example`. Sem variáveis, roda em modo desenvolvimento com SQLite.

| Variável | Uso |
|---|---|
| `DJANGO_DEBUG` | `True` (padrão) / `False` |
| `DJANGO_SECRET_KEY` | **obrigatória** com `DEBUG=False` |
| `DJANGO_ALLOWED_HOSTS` | hosts separados por vírgula |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | origens HTTPS confiáveis |
| `DJANGO_HTTPS` | `True` ativa redirecionamento SSL e cookies seguros |
| `DB_ENGINE` | `sqlite` (padrão) ou `postgresql` (instale `psycopg[binary]`) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | conexão do banco |

## Publicando em produção (resumo)
1. `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e, de preferência, PostgreSQL.
2. `python manage.py migrate` e `python manage.py collectstatic`.
3. Sirva com Gunicorn/uWSGI atrás de Nginx. **Arquivos estáticos (`staticfiles/`) e uploads (`media/`) precisam ser servidos pelo servidor web**: o Django só serve `media/` com `DEBUG=True`.

## Publicando no GitHub
```bash
git init
git add .
git commit -m "Atualiza sistema de aluguel de veículos para Django 5.2"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```
O `.gitignore` já exclui `db.sqlite3`, `media/`, `staticfiles/`, `.env` e ambientes virtuais.

## Limitações conhecidas
- Não há recuperação/troca de senha por e-mail nem pagamento online; o valor é calculado e exibido, mas a cobrança é feita fora do sistema.
- Não há envio de e-mail de confirmação de reserva.
- A trava contra reservas simultâneas usa `select_for_update` (efetiva em PostgreSQL; no SQLite o próprio banco serializa as escritas). No `/admin/` não há essa trava, apenas a validação.
- Tema visual baseado no Bootstrap 3 do projeto original.
