# Guia de teste manual — Online Car Rental

Este guia é para você abrir o sistema no navegador e conferir o funcionamento com as próprias mãos. Leva de **15 a 25 minutos** se você seguir na ordem.

> Este guia é para o seu computador: ele pressupõe o projeto instalado e o servidor rodando (`python manage.py runserver`). As contas de teste abaixo não vão dentro do ZIP; crie-as conforme a seção 5.

## 1. Antes de começar

**Endereço:** http://127.0.0.1:8000/

Rode antes, na pasta do `manage.py`: `python manage.py migrate` e `python manage.py seed_demo --demo-customer`. Deixe o servidor aberto e use o navegador normalmente (Chrome, Edge ou Firefox).

### Contas para o teste

| Perfil | Usuário | Senha | Onde entra |
|---|---|---|---|
| Equipe / administrador | crie com `python manage.py createsuperuser` | a que você escolher | `/contas/entrar/` → cai em `/painel/` |
| Cliente de demonstração | `cliente_demo` | `demo12345` | `/contas/entrar/` → cai em `/veiculos/` |

> Essas contas são **só para teste local**. O `db.sqlite3` não vai no ZIP.

### O que o `seed_demo` cria

- 6 veículos: Honda Amaze (sedã), Fiat Mobi e Chevrolet Onix (econômicos), Toyota Corolla (sedã automático híbrido), Jeep Compass (SUV) e Renault Master (van de 15 lugares).
- O cliente `cliente_demo` com telefone e endereço preenchidos.
- Nenhuma reserva — você vai criar as primeiras.

## 2. Roteiro rápido (o essencial)

### A. Visitante (sem login)

1. Abra http://127.0.0.1:8000/.
   - **Esperado:** home com imagem de capa, menu superior, formulário de datas e quatro veículos recentes.
2. Clique em **Veículos**.
   - **Esperado:** os 6 veículos, com foto/placeholder, marca, lugares, curtidas, diária e selo “Disponível”.
3. No campo **Buscar**, digite `honda` e clique em Buscar.
   - **Esperado:** só o Honda Amaze.
4. Teste a busca por placa: `DEM1A01`.
   - **Esperado:** o mesmo Honda.
5. Teste a busca por lugares: `15`.
   - **Esperado:** Renault Master.
6. Preencha **Retirada** e **Devolução** com datas futuras (ex.: 01/12/2026 a 04/12/2026) e clique em Buscar.
   - **Esperado:** a lista continua mostrando os veículos livres no período; aparece o aviso “Mostrando apenas veículos livres...”.
7. Clique em **Detalhes** de um veículo.
   - **Esperado:** foto, marca, placa, lugares, situação, curtidas, descrição, botão **Reservar**, lista “Períodos já reservados” e, se estiver logado, Curtir.
8. Clique em **Reservar** sem estar logado.
   - **Esperado:** redireciona para o login com `?next=/reservas/veiculo/.../reservar/`.
9. Abra **Contato** (`/contato/`), preencha nome, e-mail e mensagem e envie.
   - **Esperado:** mensagem “Mensagem enviada! Responderemos em breve.”.
10. Acesse uma URL inexistente, por exemplo `http://127.0.0.1:8000/pagina-inexistente/`.
    - **Esperado:** página 404 com o visual do site, não o erro técnico do Django.
11. Abra **Cadastrar** (`/contas/cadastro/`) e crie um cliente novo de teste (`maria_teste`, e-mail diferente, telefone válido, senha com pelo menos 8 caracteres).
    - **Esperado:** cadastro aceito, login automático e redirecionamento para `/veiculos/`.
    - Esse usuário serve para testar o isolamento das reservas: ele não deve ver as reservas do `cliente_demo`.

### B. Cliente

> Se você acabou de cadastrar o cliente novo, clique em **Sair** antes de continuar (ou faça o cadastro em uma janela anônima).

1. Entre com `cliente_demo` / `demo12345`.
   - **Esperado:** redireciona para `/veiculos/` (cliente não vai para o painel).
2. Abra um veículo e clique em **Curtir**.
   - **Esperado:** o contador aumenta e o botão vira “Descurtir”. Clique de novo para descurtir.
3. Clique em **Reservar** no Honda Amaze.
4. Escolha **Retirada** e **Devolução** (ex.: 01/12/2026 a 04/12/2026).
   - **Esperado:** abaixo do veículo aparece a estimativa “3 diária(s) — total estimado: R$ 389,70” (129,90 × 3).
5. Confirme a reserva.
   - **Esperado:** página da reserva com situação **Confirmada**, 3 diárias, diária de R$ 129,90 e total de R$ 389,70.
6. Abra **Minhas reservas** no menu (a página se chama **Histórico de reservas**).
   - **Esperado:** abas Todas / Próximas / Em andamento / Concluídas / Canceladas com contagem, o total em reservas (sem as canceladas) e só a sua reserva, com a situação **Próxima** e botões de detalhes, alterar e cancelar.
7. Clique em **Alterar datas**, mude a devolução para 05/12/2026 e salve.
   - **Esperado:** total recalculado para 4 diárias (R$ 519,60).
8. Tente reservar o **mesmo veículo** em um período que cruze o existente.
   - **Esperado:** erro “Este veículo já está reservado em pelo menos um dia do período escolhido.” e nenhuma reserva nova.
9. Tente reservar com retirada no passado.
   - **Esperado:** erro “A data de retirada não pode estar no passado.”.
10. Tente reservar com devolução igual ou anterior à retirada.
    - **Esperado:** erro “A data de devolução deve ser posterior à data de retirada.”.
11. Volte em **Minhas reservas** e **cancele** a reserva.
    - **Esperado:** confirmação, depois a reserva fica **Cancelada** e o veículo volta a ficar disponível no período.
12. Abra **Meu perfil** (nome no canto direito), altere telefone/endereço e salve.
    - **Esperado:** “Dados atualizados com sucesso.”.

### C. Regra de período encostado (opcional, mas bom de mostrar)

O sistema trata o período como **[retirada, devolução)**: o carro fica ocupado da retirada até a véspera da devolução.

1. Crie uma reserva para 10/12/2026 a 13/12/2026.
2. Crie outra para o **mesmo veículo** de 13/12/2026 a 15/12/2026.
   - **Esperado:** permitido, porque uma começa no dia em que a outra termina.
3. Crie uma de 12/12/2026 a 14/12/2026.
   - **Esperado:** bloqueada por sobreposição.

### D. Equipe / painel

1. Saia e entre com o superusuário que você criou.
   - **Esperado:** redireciona para `/painel/`.
2. Confira o **Resumo**: veículos ativos/total, alugados agora, reservas confirmadas, receita do mês, retiradas/devoluções de hoje e vendas dos últimos 7 dias.
3. Abra **Veículos** no painel.
   - **Esperado:** lista com todos, inclusive fora da frota, busca e ações.
4. Clique em **Novo veículo**, cadastre um carro de teste (pode enviar uma foto `.jpg`/`.png`), salve.
   - **Esperado:** volta ao painel com “cadastrado”.
5. Edite esse veículo, troque a diária e salve.
6. Tente excluir um veículo **que já tem reserva**.
   - **Esperado:** mensagem “possui reservas e não pode ser excluído. Desmarque ‘ativo na frota’...”.
7. Exclua o veículo de teste que não tem reserva.
8. Abra **Reservas** no painel.
   - **Esperado:** filtros por situação e busca por cliente/veículo/placa; ações de ver, alterar, concluir e cancelar.
9. Marque uma reserva confirmada como **concluída**.
   - **Esperado:** situação **Concluída**.
10. Abra **Mensagens** no painel.
    - **Esperado:** a mensagem enviada no passo A.9; exclua-a e confirme que some.
11. Abra **Admin do Django** (`/admin/`).
    - **Esperado:** telas de Clientes, Veículos, Reservas e Mensagens de contato.

### E. Segurança e permissões

1. Logado como `cliente_demo`, tente abrir `/painel/`.
   - **Esperado:** página **403** “Você não tem permissão...”.
2. Sem login, tente abrir `/reservas/`.
   - **Esperado:** redireciona para o login.
3. Logado como cliente, tente abrir `/veiculos/novo/`.
   - **Esperado:** 403.
4. Tente sair por GET: abra `http://127.0.0.1:8000/contas/sair/` diretamente.
   - **Esperado:** 405 (o logout só aceita POST; o botão “Sair” do menu funciona).
5. Confira que excluir/cancelar/curtir não funcionam por link GET, só por formulário POST (os botões do site já fazem certo).

### F. Responsivo (opcional)

1. Aperte `F12` → ícone de celular (modo responsivo) → largura 375 px.
2. Recarregue a home.
   - **Esperado:** menu vira “hambúrguer”, cards empilham e o formulário de datas se ajusta.
   - O menu depende do jQuery carregado de `code.jquery.com`; **é preciso estar com internet** para o botão abrir/fechar.

### G. Novidades desta versão (catálogo, histórico e painel)

1. Na **home**, confira a faixa de números (veículos na frota, marcas, categorias) e os cartões de **categoria**; clique em “SUV”.
   - **Esperado:** abre `/veiculos/?category=suv` só com o Jeep Compass.
2. Em **Veículos**, combine filtros: categoria **Sedã** + câmbio **Automático**.
   - **Esperado:** só o Toyota Corolla; o contador mostra “1 veículo encontrado” e aparece **Limpar filtros**.
3. Teste **Diária até** (ex.: 100) e **Lugares (mín.)** (ex.: 5), e a **ordenação** (menor preço, maior preço, mais curtidos, mais recentes, nome).
   - **Esperado:** a lista respeita filtros e ordem.
4. Abra o detalhe de um veículo.
   - **Esperado:** categoria, câmbio, combustível, marca, lugares e placa em grade; no celular, barra fixa “Reservar” no rodapé.
5. Em **Minhas reservas**, clique nas abas.
   - **Esperado:** cada aba mostra só a situação correspondente; uma reserva com retirada hoje ou antes e devolução futura aparece em **Em andamento**; uma confirmada com devolução vencida aparece como **Encerrada** em *Concluídas*.
6. No **painel** e no **celular (375 px)**, abra as tabelas de veículos e reservas.
   - **Esperado:** as tabelas viram cartões com o rótulo de cada coluna.

## 3. Testando especificamente as duas correções

### Correção 1 — equipe edita reserva em andamento

Esse era o bug: reserva com retirada no passado não podia ser salva pela equipe.

1. Entre com o superusuário.
2. Vá em `/admin/reservations/reservation/add/`.
3. Escolha `cliente_demo`, um veículo livre (ex.: Renault Master), retirada **ontem**, devolução **amanhã**, situação **Confirmada**, salve.
4. Abra `/painel/reservas/`, localize a reserva e clique no lápis (**Alterar datas**).
5. Mude só as observações (ou a devolução) e clique em **Salvar alterações**.
   - **Esperado:** “Reserva atualizada.” e volta para o detalhe.
   - **Antes da correção:** aparecia “A data de retirada não pode estar no passado.”.

### Correção 2 — admin não cancela reserva concluída em massa

Esse era o bug: a ação em massa cancelava reservas já concluídas.

1. Como `admin`, abra `/admin/reservations/reservation/`.
2. Tenha uma reserva **Concluída** (você pode concluir uma pela ação “Marcar reservas selecionadas como concluídas”).
3. Marque essa reserva concluída, escolha a ação **“Cancelar reservas selecionadas”** e confirme.
   - **Esperado:** a reserva continua **Concluída** e a mensagem informa “0 reserva(s) cancelada(s).”.
   - **Antes da correção:** ela virava **Cancelada**.

## 4. Checklist rápido

Marque conforme for testando:

- [ ] Home carrega com capa, menu, faixa de números, categorias e 4 veículos.
- [ ] Filtros do catálogo (categoria, marca, câmbio, lugares, diária) e ordenação funcionam.
- [ ] Histórico de reservas mostra as abas e o total corretamente.
- [ ] Tabelas viram cartões no celular.
- [ ] Busca por texto, placa e lugares funciona.
- [ ] Filtro por período esconde veículo ocupado.
- [ ] Detalhe mostra foto, dados, curtidas e períodos reservados.
- [ ] Curtir/descurtir funciona logado.
- [ ] Cadastro de cliente novo funciona.
- [ ] Login de cliente vai para `/veiculos/`.
- [ ] Login de admin vai para `/painel/`.
- [ ] Reserva calcula diárias e total corretos.
- [ ] Reserva sobreposta é bloqueada.
- [ ] Retirada no passado é bloqueada.
- [ ] Devolução anterior à retirada é bloqueada.
- [ ] Reserva encostada (fim = início da outra) é permitida.
- [ ] Alterar datas recalcula o total.
- [ ] Cancelar libera o veículo.
- [ ] Perfil salva nome, e-mail, telefone e endereço.
- [ ] Painel mostra números e listas.
- [ ] Criar/editar/excluir veículo funciona (com foto).
- [ ] Veículo com reserva não pode ser excluído.
- [ ] Reserva pode ser concluída pela equipe.
- [ ] Mensagem de contato aparece no painel e pode ser excluída.
- [ ] Admin do Django abre Clientes, Veículos, Reservas e Mensagens.
- [ ] Cliente recebe 403 no painel.
- [ ] Logout por GET retorna 405.
- [ ] Layout responsivo (menu hambúrguer) funciona com internet.

## 5. Criar ou reiniciar o ambiente

Primeira vez (na pasta do `manage.py`):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo --demo-customer
python manage.py runserver
```

Para parar o servidor, use `Ctrl+C` na janela dele. Para recriar o banco do zero (apaga reservas e usuários de teste):

```powershell
Remove-Item db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo --demo-customer
```

## 6. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Página sem CSS/JS | Servidor parado ou aberto em outro endereço | Confirme `http://127.0.0.1:8000/` e se o servidor está rodando |
| Menu hambúrguer não abre | Sem internet para o jQuery do CDN | Conecte à internet ou troque o jQuery por uma cópia local |
| “Usuário ou senha incorretos” | Banco recriado | Use `cliente_demo` / `demo12345` ou crie um superusuário com `createsuperuser` |
| Datas não aceitas | Data no passado ou devolução ≤ retirada | Escolha datas futuras e devolução depois da retirada |
| Erro ao enviar foto | Arquivo não é imagem ou é muito grande | Use um `.jpg`/`.png` pequeno |
| Porta 8000 em uso | Outro servidor rodando | Pare o processo da porta ou use `runserver 8001` |

> Observação: a conferência visual (cores, imagens, alinhamento e menu no celular) só se faz no navegador. Abra as telas uma vez no seu PC e no celular.
