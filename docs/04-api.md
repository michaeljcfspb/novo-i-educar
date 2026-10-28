# 04 — API REST

Base: `/api/v1/` · Documentação interativa: `/api/docs/` · Schema: `/api/schema/`

## Autenticação

Duas formas, escolhidas pelo cliente:

1. **Sessão (SPA)** — cookie `sessionid` + CSRF.
2. **Token (integrações)** — header `Authorization: Token <chave>`.

### Sessão (passo a passo)

```bash
# 1. obtém o cookie csrftoken
curl -c cookies.txt http://localhost:8080/api/v1/auth/csrf/

# 2. autentica (o token vem do cookie)
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8080/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{"email":"admin@example.com","password":"senha-forte-123"}'

# 3. usa a API
curl -b cookies.txt http://localhost:8080/api/v1/alunos/
```

Em PowerShell, use `Invoke-RestMethod -WebSession $sessao` (o cookie jar é automático).

### Token

```bash
curl -X POST http://localhost:8080/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"senha-forte-123"}'
# {"token": "...", "perfil": "administrador"}
```

## Endpoints

### Autenticação

| Método | Caminho | Permissão | Descrição |
| ------ | ------- | --------- | --------- |
| GET | `/auth/csrf/` | pública | Define/retorna o cookie CSRF. |
| POST | `/auth/login/` | pública + CSRF | Autentica e cria a sessão. |
| POST | `/auth/logout/` | autenticado | Encerra a sessão. |
| GET | `/auth/me/` | autenticado | Usuário, perfil e escola. |
| POST | `/auth/token/` | pública | Emite token DRF. |

### Pessoas e alunos

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET/POST | `/pessoas/` | Lista/cria pessoas (física ou jurídica). |
| GET/PATCH/PUT/DELETE | `/pessoas/{id}/` | Detalhe e manutenção. |
| GET/POST | `/alunos/` | Lista/cria aluno **com pessoa aninhada**. |
| GET/PATCH/PUT/DELETE | `/alunos/{id}/` | Detalhe e manutenção. |
| GET | `/alunos/{id}/matriculas/` | Matrículas do aluno. |
| GET/POST | `/deficiencias/` | Tabela auxiliar (sem paginação). |

Filtros de `/alunos/`: `ativo`, `deficiencias`, `search` (nome, código, CPF), `ordering`.
Filtros de `/pessoas/`: `tipo`, `ativo`, `sexo`, `municipio`, `search`.

### Rede escolar

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET/POST | `/instituicoes/` | Mantenedoras. |
| GET/POST | `/escolas/` | Escolas (escopo por escola para não-admin). |
| GET/POST | `/cursos/` | Cursos. |
| GET/POST | `/series/` | Séries (valida faixa etária). |
| GET/POST | `/disciplinas/` | Disciplinas. |
| GET/POST | `/turmas/` | Turmas (filtro por `ano`, `escola`, `serie`, `turno`). |

### Servidores e estrutura

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET/POST | `/servidores/` | Professores e equipe (escrita apenas admin). |
| GET/POST | `/anos-letivos/` | Anos letivos por instituição. |
| GET/POST | `/calendarios/` | Calendários do ano letivo. |
| GET/POST | `/calendarios/{id}/dias/` | Dias letivos/feriados (aceita lista). |
| GET/POST | `/turma-disciplinas/` | Grade da turma (disciplina, professor, carga). |

### Avaliação e frequência

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET/POST | `/regras-avaliacao/` | Regras de média, recuperação e frequência mínima. |
| GET/POST | `/periodos-avaliacao/` | Bimestres/trimestres com peso. |
| GET/POST | `/notas/` | Notas por matrícula, disciplina e período. |
| POST | `/notas/lote/` | Lançamento em lote (upsert) por turma/disciplina/período. |
| GET/POST | `/frequencias/` | Frequência diária. |
| POST | `/frequencias/lote/` | Chamada da turma em lote. |

### Histórico, transferências e documentos

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET | `/historicos/` | Históricos consolidados (escopo por escola). |
| POST | `/historicos/gerar/` | Gera/atualiza o histórico de uma matrícula. |
| GET/POST | `/transferencias/` | Registra entrada, saída ou movimentação interna. |
| GET | `/documentos/` | Documentos emitidos. |
| POST | `/documentos/emitir/` | Emite declaração/histórico/guia com numeração automática. |

### Relatórios e portal

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET | `/relatorios/indicadores/` | KPIs da rede (aprovação, abandono, ocupação, frequência). |
| GET | `/relatorios/turmas/` | Relatório por turma. |
| GET | `/relatorios/turmas.csv` | Exportação CSV (separador `;`, BOM para Excel). |
| GET | `/relatorios/alunos-risco/` | Alunos com frequência/média abaixo do mínimo. |
| GET | `/portal/perfil/` | Dados do aluno vinculado ao usuário logado. |
| GET | `/portal/boletim/` | Boletim do aluno logado. |
| GET | `/portal/frequencia/` | Resumo de frequência. |
| GET | `/portal/documentos/` | Documentos emitidos para o aluno. |
| GET | `/matriculas/{id}/boletim-pdf/` | Boletim em PDF. |
| GET | `/historicos/{id}/pdf/` | Histórico escolar em PDF. |

### Censo e integrações

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET | `/censo/exportacoes/` | Exportações geradas (escopo por escola). |
| POST | `/censo/exportacoes/gerar/` | Gera pacote do Censo com versão e pendências. |
| POST | `/censo/exportacoes/preview/` | Valida pendências sem gravar. |
| GET | `/importacoes/` | Histórico de importações. |
| POST | `/importacoes/` | Importa alunos via `multipart/form-data` (campo `arquivo`). |
| GET/POST | `/webhooks/` | Cadastro de webhooks (admin). |
| POST | `/webhooks/{id}/testar/` | Dispara evento de teste e registra a entrega. |
| POST | `/matriculas/{id}/remanejar/` | Move o aluno para outra turma. |
| POST | `/matriculas/{id}/reclassificar/` | Muda a série, encerrando a enturmação. |

### Matrículas

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET/POST | `/matriculas/` | Lista/cria matrícula. |
| GET/PATCH | `/matriculas/{id}/` | Detalhe/atualização. |
| DELETE | `/matriculas/{id}/` | Cancelamento **lógico**. |
| POST | `/matriculas/{id}/enturmar/` | Enturma em uma turma. |
| PATCH | `/matriculas/{id}/situacao/` | Altera situação. |
| GET | `/enturmacoes/` | Histórico de enturmações. |
| GET | `/matriculas/{id}/boletim/` | Boletim: notas por período, médias, frequência e situação. |
| GET | `/matriculas/{id}/frequencia/` | Resumo de presenças/faltas e percentual. |

Filtros: `ano`, `escola`, `serie`, `situacao`, `ativo`, `aluno`.

### Infra

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| GET | `/health/` | Healthcheck (banco incluído). |
| GET | `/version/` | Versão da API. |

## Paginação, busca e ordenação

Resposta paginada:

```json
{
  "count": 5,
  "next": "http://localhost:8080/api/v1/alunos/?page=2",
  "previous": null,
  "results": [{ "id": 1, "codigo": "A000001", "nome": "Ana Beatriz Ferreira" }]
}
```

- `?page=2` e `?page_size=50` (máximo 200).
- `?search=maria` — busca textual declarada por viewset.
- `?ordering=-ano` — ordenação (quando exposta).
- `?ano=2026&situacao=cursando` — filtros exatos.

## Erros

Formato padrão:

```json
{ "detail": "Autenticação necessária." }
```

```json
{ "cpf": ["CPF inválido."], "curso": ["O curso deve ser o mesmo da série."] }
```

| Código | Significado |
| ------ | ----------- |
| 400 | Validação de dados. |
| 401/403 | Sem autenticação / sem permissão. |
| 404 | Registro inexistente (ou fora do escopo do usuário). |
| 409/400 | Violação de unicidade (ex.: matrícula ativa duplicada). |

## Exemplos

Criar aluno (pessoa aninhada):

```json
POST /api/v1/alunos/
{
  "pessoa": {
    "nome": "João Pedro Souza",
    "cpf": "11144477735",
    "data_nascimento": "2016-05-20",
    "sexo": "M",
    "municipio": 1
  },
  "deficiencias": [1],
  "usa_transporte_escolar": true
}
```

Enturmar:

```json
POST /api/v1/matriculas/12/enturmar/
{ "turma": 3, "data_enturmacao": "2026-02-05" }
```

Alterar situação:

```json
PATCH /api/v1/matriculas/12/situacao/
{ "situacao": "aprovado" }
```

## Versionamento

A API vive sob `/api/v1/`. Mudanças incompatíveis criam `/api/v2/`; campos novos podem ser
adicionados sem quebra. Erros e formatos são cobertos por testes (`backend/tests`).
