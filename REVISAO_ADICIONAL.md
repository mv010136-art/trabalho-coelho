# Revisão adicional do pacote — 21/11/2026

> **Registro histórico da versão base.** Esta nota descreve a revisão anterior à ampliação do projeto; os números de testes valem para a versão base.
>
> **Atualização (22/11/2026):** a execução real foi feita posteriormente em Windows com Python 3.11.9 e Django 5.2.9. `manage.py check`, `makemigrations --check` e os **105 testes** passaram, e os fluxos principais foram validados com o servidor rodando. Assim, a ressalva abaixo sobre “testes sem execução” está resolvida; as recomendações de produção continuam válidas. Detalhes em `CORRECOES_REALIZADAS.md` e `RELATORIO_DE_TESTES.md`.
>
> **Atualização final (23/11/2026):** a versão com o frontend novo foi executada: **131 testes OK**, `check`, `makemigrations --check`, migrações, `seed_demo`, `collectstatic` e 80 verificações HTTP, sem erro de template. Veja `REVISAO_FINAL_FRONTEND.md`.

## Resultado

O ZIP foi extraído sem erro e os arquivos Python foram compilados novamente com `python -m compileall -q .` (resultado: OK). A suíte continha 103 métodos `test_*` naquela revisão: 15 em `accounts/tests.py`, 31 em `vehicles/tests.py`, 37 em `reservations/tests.py` e 20 em `core/tests.py`. Após as correções desta revisão são 105 (dois testes de regressão).

**Na data desta revisão, os testes Django continuavam sem execução.** O ambiente desta revisão usava Python 3.13.5, mas não tinha Django instalado. A tentativa de `pip install -r requirements.txt` falhou porque o ambiente não conseguiu resolver o endereço do PyPI (sem acesso à rede). Por isso não havia resultado para `manage.py check`, `makemigrations --check` ou `manage.py test`. Isso foi resolvido na atualização de 22/11/2026, no topo deste arquivo.

## Pontos confirmados na leitura do código

- O projeto está dividido nos apps `core`, `accounts`, `vehicles` e `reservations`.
- O SQLite é o banco padrão; PostgreSQL é opcional por variáveis de ambiente.
- O cadastro de veículos e a alteração aceitam upload de imagem (`request.FILES`).
- As ações de curtir, concluir reserva e excluir mensagem exigem POST; o logout também é enviado por formulário POST.
- As rotas de painel usam a proteção de equipe; as reservas de clientes são filtradas pelo usuário autenticado.
- A regra de conflito usa intervalos semiabertos: `start_date < outra_end_date` e `end_date > outra_start_date`.
- O projeto não inclui `db.sqlite3`, então o banco deve ser criado com `migrate`.

## Atenções antes de publicar ou demonstrar

1. **Menu responsivo depende de internet:** `templates/base.html` carrega jQuery 1.12.4 de `code.jquery.com`. Sem conexão, o menu recolhível e os componentes JavaScript do Bootstrap podem não funcionar. O projeto já documenta essa dependência. Para uso offline, será necessário incluir uma cópia local compatível do jQuery e alterar a referência do script.
2. **PostgreSQL é opcional, mas exige dependência extra:** `requirements.txt` instala Django e Pillow. Se for usar PostgreSQL, instale também `psycopg[binary]`, conforme o README.
3. **Servidor de produção:** o README cita Gunicorn/uWSGI como opções, mas eles não fazem parte do `requirements.txt`. Instale o servidor escolhido separadamente ao publicar.
4. **Segurança de produção:** não publique com `DJANGO_DEBUG=True` nem com a chave de desenvolvimento. Configure `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e HTTPS conforme o README.
5. **Concorrência de reservas:** a trava `select_for_update` depende de banco com suporte adequado; o próprio projeto ressalta a limitação do SQLite e a ausência da mesma trava no admin.
6. **Validação visual ainda necessária:** abrir em navegador/Android as telas de início, cadastro, login, listagem, detalhe, reserva, perfil, painel e admin. A revisão estática não comprova comportamento de CSS/JavaScript.

## Comandos obrigatórios na máquina com internet

Na pasta que contém `manage.py`:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Se `makemigrations --check` apontar diferenças, não apague migrações de um banco já utilizado. Gere e revise uma nova migração com `python manage.py makemigrations` e aplique-a com `python manage.py migrate`.

## Conclusão

A revisão adicional não encontrou erro de sintaxe Python nem falha de integridade do ZIP. Não alterei a lógica do sistema sem conseguir executar Django, pois uma correção especulativa poderia introduzir regressões. O pacote está pronto para a etapa de instalação e validação funcional, mas **ainda não deve ser apresentado como testado ou comprovadamente funcional** até os comandos acima terminarem sem erros e as telas serem verificadas.

> **Nota posterior (22/11/2026):** os comandos acima foram executados com sucesso (105 testes OK), o servidor foi colocado no ar e os fluxos principais foram validados. Esta ressalva estava correta na data da revisão, mas foi superada pela execução real. Veja `CORRECOES_REALIZADAS.md` e `RELATORIO_DE_TESTES.md`.
