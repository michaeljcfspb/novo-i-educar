# 02 — Arquitetura da reescrita

## Visão de alto nível

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│  Navegador (SPA)            │        │  Django + DRF                │
│  React 19 + TypeScript      │  HTTP  │  /api/v1/...                 │
│  TanStack Query + Router    │ ─────► │  Sessão + CSRF / Token       │
│  Tailwind + componentes     │        │  OpenAPI (drf-spectacular)   │
└─────────────────────────────┘        └──────────────┬───────────────┘
                                                     │ psycopg 3
                                         ┌───────────▼────────────┐
                                         │ PostgreSQL 17          │
                                         │ (volume persistente)   │
                                         └────────────────────────┘
```

Em produção o Nginx serve o bundle estático e faz proxy de `/api`, `/admin`, `/static` e
`/media` para o Gunicorn. Resultado: **uma única origem**, o que permite cookie de sessão
`HttpOnly` + CSRF sem CORS e sem token no `localStorage`.

## Decisões de arquitetura

| Decisão | Escolha | Por quê |
| ------- | ------- | ------- |
| Autenticação principal | Sessão Django (cookie `HttpOnly`, `SameSite=Lax`) + CSRF | Mais segura que JWT em `localStorage`; funciona naturalmente com SPA na mesma origem. |
| Autenticação para integrações | Token DRF (`/auth/token/`) | Simples para scripts/ETL; pode migrar para JWT/OAuth2 se necessário. |
| Separação de apps Django | `accounts`, `core`, `people`, `schools`, `enrollments` | Cada app tem um domínio e um dono; imports acíclicos. |
| Regras de negócio | Serializers + `clean()` + constraints de banco | Regra perto do dado, testável e válida também no Admin. |
| Escopo por escola | `get_queryset()` + `apps/core/permissions.py` | Impede vazamento de dados entre escolas por padrão (fail-closed). |
| Chaves primárias | `BigAutoField` | Compatível com o volume do legado e simples de migrar. |
| Datas/hora | `USE_TZ=True`, `America/Sao_Paulo`, `pt-br` | Requisito do domínio brasileiro. |
| Documentação | OpenAPI gerado do código | Nunca desatualiza; Swagger UI em `/api/docs/`. |
| Testes | pytest + pytest-django, SQLite em memória | Rápidos no CI; Postgres é usado em Docker/staging. |
| Configuração | 12-factor (variáveis de ambiente) | Mesmo artefato em dev/staging/produção; sem segredo no Git. |

## Modelo de domínio implementado

```
Pessoa 1───1 Aluno ──M:N── Deficiencia
                │
                │ 1:N
             Matricula ──1:N── MatriculaTurma ──N:1── Turma
                │                                        │
                ├── N:1 Escola ──N:1 Instituicao          ├── N:1 Escola
                ├── N:1 Serie  ──N:1 Curso                └── N:1 Serie
                └── N:1 Curso
```

Regras garantidas por constraint/validação:

- CPF válido (dígitos verificadores) e único quando informado.
- Uma única matrícula **ativa** por aluno/ano (`UniqueConstraint` condicional).
- Uma única enturmação **ativa** por matrícula.
- Série pertence ao curso informado na matrícula.
- Enturmação só em turma da mesma escola, mesma série e mesmo ano da matrícula.
- Enturmação respeita a capacidade da turma (`vagas_disponiveis`).
- Cancelamento de matrícula é **lógico** (`ativo=False`, `situacao=cancelada`) para preservar histórico.

## Fluxo de autenticação

```
SPA                          Django
 │  GET /auth/csrf/            │  set-cookie: csrftoken (não HttpOnly)
 │ ──────────────────────────► │
 │  POST /auth/login/          │  SessionAuthentication estendida:
 │   {email, password}         │  enforce_csrf → authenticate → login()
 │   X-CSRFToken: <cookie>     │  set-cookie: sessionid (HttpOnly)
 │ ──────────────────────────► │
 │  GET /auth/me/              │  retorna usuário, perfil e escola
 │ ──────────────────────────► │
```

- A classe `CsrfObrigatorio` (`apps/accounts/authentication.py`) valida CSRF **também para
  visitantes**, fechando a brecha de *login CSRF* que o DRF deixa por padrão.
- Senhas passam pelos validadores do Django (mínimo 8 caracteres, senha comum, similaridade).
- `registrar_acesso()` grava o último login.

## Matriz de permissões

| Recurso | Administrador | Gestor/Secretaria | Professor | Consulta |
| ------- | ------------- | ----------------- | --------- | -------- |
| Ler qualquer escola | ✅ | só a própria | só a própria | só a própria |
| Criar/editar alunos, escolas, turmas, matrículas | ✅ | ✅ (na própria escola) | ✅ | ❌ |
| Excluir (cancelar) | ✅ | ✅ | ✅ | ❌ |

Implementação: `IsAuthenticated` como padrão global; `SomenteLeituraParaConsulta` nos
viewsets; filtro de escola em `EscolaViewSet`, `TurmaViewSet`, `MatriculaViewSet` e
`MatriculaTurmaViewSet`.

> Ainda não há permissões por objeto (ex.: gestor editar apenas alunos da própria escola na
> escrita). Está no roadmap da Fase 1 junto com `django-guardian` ou validação no serializer.

## Mapeamento legado → novo

| Legado | Novo | Observação |
| ------ | ---- | ---------- |
| `cadastro.pessoa` + `cadastro.fisica` | `people.Pessoa` | Campos de endereço e documentos unificados. |
| `pmieducar.aluno` | `people.Aluno` | `codigo` gerado (`A000001`). |
| `pmieducar.instituicao` | `schools.Instituicao` | — |
| `pmieducar.escola` | `schools.Escola` | Bloco Censo/INEP fica para a fase 4. |
| `pmieducar.curso` | `schools.Curso` | `nivel_ensino` e `modalidade` como choices. |
| `pmieducar.serie` | `schools.Serie` | Faixa etária validada. |
| `modules.componente_curricular` | `schools.Disciplina` | — |
| `pmieducar.turma` | `schools.Turma` | Capacidade + vagas calculadas. |
| `pmieducar.matricula` | `enrollments.Matricula` | Situação como `TextChoices`. |
| `pmieducar.matricula_turma` | `enrollments.MatriculaTurma` | Histórico de enturmações preservado. |
| `pmieducar.usuario` + `tipo_usuario` | `accounts.User` + `perfil` | Perfil + escola opcional. |

## Segurança

Já implementado:

- CSRF em login e em toda escrita; cookie de sessão `HttpOnly`.
- `SECRET_KEY` por ambiente; `DEBUG=False` em produção; `ALLOWED_HOSTS` e
  `CSRF_TRUSTED_ORIGINS` explícitos; `SECURE_PROXY_SSL_HEADER` para HTTPS atrás do proxy.
- Validação de CPF, unicidade de matrícula ativa e escopo por escola.
- Erros de API sem stack trace; mensagens em português.

Pendências planejadas:

- Throttling (`DEFAULT_THROTTLE_CLASSES`) no login e na API.
- Trilha de auditoria (quem alterou o quê) — hoje só `criado_por`/datas.
- Política de backup/restauração documentada e testada.
- Revisão de uploads (`foto` de aluno) com validação de tipo/tamanho.

## Testes

36 testes em `backend/tests`, divididos em:

- `test_auth.py` — login, logout, sessão, token, CSRF e healthcheck.
- `test_permissions.py` — anônimo, perfil consulta, escopo por escola.
- `test_alunos.py` — criação aninhada, CPF inválido/duplicado, busca, atualização.
- `test_matriculas.py` — criação, curso incompatível, duplicidade ativa, enturmação,
  capacidade, escola divergente, situação e cancelamento lógico.
- `test_escolas.py` — CRUD, unicidade, validação de faixa etária e filtros.
- `test_schema.py` — geração do OpenAPI e disponibilidade do Swagger.

Frontend verificado com `tsc --noEmit` (TypeScript estrito) e `vite build`.
