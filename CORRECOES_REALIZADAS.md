# Correções e validação funcional — 22/11/2026

> **Nota sobre esta versão do projeto:** as duas correções abaixo foram feitas e validadas sobre a versão base (105 testes, executados em 22/11/2026) e foram **reaplicadas** nesta versão ampliada (categoria/câmbio/combustível, filtros, histórico por abas, visual novo). A versão final foi executada em 23/11/2026: `check`, `makemigrations --check`, migrações, `seed_demo`, `collectstatic` e **131 testes passaram** (185,7 s), além de **80 verificações HTTP** sem erro de template. Os números de 105 testes e 30 verificações citados abaixo referem-se à versão base; o resultado final está em `RELATORIO_DE_TESTES.md` e `REVISAO_FINAL_FRONTEND.md`.

## Resumo

O projeto foi **executado de verdade** nesta revisão (não apenas analisado estaticamente):

- `python manage.py check` → sem problemas.
- `python manage.py makemigrations --check --dry-run` → nenhuma migração pendente.
- `python manage.py test -v 2` → **105 testes, todos OK** (tempo: 271 s, cerca de 4 min 31 s).
- `python manage.py migrate` → OK em banco novo.
- `python manage.py seed_demo --demo-customer` → 6 veículos + cliente de demonstração.
- `python manage.py runserver` → servidor no ar e 30 verificações HTTP manuais aprovadas.
- `python manage.py collectstatic --noinput` → 138 arquivos copiados.
- `python manage.py check` com `DJANGO_DEBUG=False` e chave de produção → sem problemas.

Foram feitas **2 correções de código** e a **documentação de status foi atualizada**. A estrutura de apps, rotas, templates, modelos e migrações **não foi alterada**, e nenhuma dependência nova foi adicionada ao projeto.

## Ambiente usado na revisão

| Item | Versão / observação |
|---|---|
| Sistema | Windows 11 |
| Python | 3.11.9 |
| Django | 5.2.9 |
| Pillow | 12.3.0 |
| tzdata | 2026.6 (dependência do Django no Windows) |
| Banco | SQLite |
| Navegador | não foi possível abrir navegador com interface gráfica no ambiente de revisão; a validação visual foi feita pela renderização dos templates e pelos arquivos estáticos servidos (CSS, JS, fontes e imagens com HTTP 200) |

> O `pip` do ambiente de revisão não conseguia falar com o PyPI (o cliente travava), então as dependências foram baixadas com o próprio Python e instaladas a partir de arquivos `.whl` locais. Isso é uma limitação **do ambiente de revisão**, não do projeto: em uma máquina com internet, `pip install -r requirements.txt` funciona normalmente.

## Correções de código

### 1. Equipe não conseguia salvar uma reserva em andamento

**Sintoma:** uma reserva cuja retirada já tinha acontecido (por exemplo, começou ontem e termina amanhã) ficava presa. Ao abrir “Alterar datas” no painel e salvar — mesmo mudando só as observações ou a devolução — o formulário respondia:

> “A data de retirada não pode estar no passado.”

**Causa:** `ReservationForm.clean_start_date` (`reservations/forms.py`) rejeitava qualquer data de retirada anterior a hoje. A regra existe para **novas** reservas, mas também era aplicada ao editar uma reserva já existente, cuja data original legitimamente está no passado.

**Correção:** a data original de uma reserva existente passou a ser aceita; uma **nova** data de retirada continua tendo de ser hoje ou no futuro. Também foi adicionado um teste de regressão.

**Arquivos:**
- `reservations/forms.py` — `ReservationForm.clean_start_date`.
- `reservations/tests.py` — `test_staff_can_edit_in_progress_reservation_without_changing_start`.

### 2. Ação “Cancelar reservas selecionadas” do admin cancelava reservas concluídas

**Sintoma:** no `/admin/`, a ação em massa “Cancelar reservas selecionadas” mudava para *Cancelada* até reservas já **concluídas**, apagando o histórico de uma locação finalizada. O painel da equipe e as views do site só permitem cancelar reservas **confirmadas**.

**Causa:** `ReservationAdmin.mark_cancelled` (`reservations/admin.py`) usava `queryset.exclude(status=CANCELLED)`, o que incluía as concluídas.

**Correção:** a ação agora atua somente em reservas com situação **Confirmada**, igual ao restante do sistema. Foi adicionado um teste de regressão.

**Arquivos:**
- `reservations/admin.py` — `mark_cancelled`.
- `core/tests.py` — `test_admin_cancel_action_does_not_reopen_completed_reservations`.

## Documentação atualizada

- `README.md`: o aviso “testes não executados” foi substituído pelo status real da verificação (105 testes passando, servidor e fluxos testados) e a contagem de testes foi atualizada.
- `RELATORIO_DE_TESTES.md`: reescrito com os comandos, resultados e verificações manuais desta execução.
- `REVISAO_ADICIONAL.md`: recebeu uma nota de atualização no topo; o conteúdo original foi preservado como registro histórico da revisão anterior.

## Validação manual (HTTP, com o servidor rodando)

Além da suíte automática, foram feitas 30 verificações em sequência real de requisições:

**Páginas e arquivos estáticos**
- `/`, `/veiculos/`, `/veiculos/?q=honda`, `/veiculos/novos/`, `/veiculos/populares/`, `/veiculos/1/`, `/contato/`, `/contas/cadastro/`, `/contas/entrar/` → 200.
- `/static/css/style.css`, `bootstrap.min.css`, `bootstrap.min.js`, imagens, fontes dos ícones e `/media/...` → 200.
- Rota inexistente → 404 com o template do site.
- `/painel/` e `/reservas/` sem login → redirecionam para o login; `/painel/` com cliente comum → 403.

**Cliente**
- Cadastro de novo cliente, login, edição de perfil e logout.
- Criação de reserva, bloqueio de reserva sobreposta, alteração de datas e cancelamento.
- “Minhas reservas” mostrando apenas as reservas do próprio cliente.
- Formulário de contato gravando a mensagem.

**Equipe**
- Login de superusuário caindo no painel.
- Painel (resumo, veículos, reservas, mensagens) e admin do Django.
- Conclusão de reserva, criação/edição/exclusão de veículo e exclusão de mensagem.
- Reserva em andamento editada pela equipe após a correção nº 1 (teste específico via HTTP).

## O que não foi alterado

- Estrutura de pastas e apps (`core`, `accounts`, `vehicles`, `reservations`).
- Rotas, templates, CSS, modelos e migrações.
- Regras de negócio de período, sobreposição, cancelamento e cálculo de valor.
- Dependências do `requirements.txt`.

## Limitações conhecidas (não são defeitos desta revisão)

- O menu responsivo e os componentes JavaScript do Bootstrap dependem do jQuery carregado de `code.jquery.com`; sem internet, o menu recolhível pode não funcionar. O README já documenta isso. Para uso totalmente offline, seria necessário baixar uma cópia local do jQuery e trocar a referência em `templates/base.html`.
- O banco `db.sqlite3` e a pasta `media/` não vão no ZIP: rode `migrate` e, se quiser os dados de demonstração, `seed_demo --demo-customer`.
- `select_for_update` só tem efeito real no PostgreSQL; no SQLite o próprio banco serializa as escritas. O README já explica.
- Não há recuperação de senha por e-mail, pagamento online nem envio de e-mail de confirmação — limitações já documentadas no projeto.
- Em produção: usar `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY` forte, `DJANGO_ALLOWED_HOSTS`, HTTPS e um servidor WSGI/ASGI. O `check --deploy` só aponta os avisos esperados de configuração de desenvolvimento.

## Como rodar na máquina do seu amigo

Na pasta que contém `manage.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo --demo-customer   # opcional: 6 veículos + cliente_demo/demo12345
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`. O superusuário entra em `/contas/entrar/` e cai no painel; o cliente de demonstração usa `cliente_demo` / `demo12345`.
