# 01 — Reconhecimento do projeto original

Levantamento feito diretamente no fork `michaeljcfspb/i-educar` (clone raso em `i-educar/`),
sem suposições: todos os números abaixo foram medidos no código.

## Números gerais

| Métrica                                   | Valor |
| ----------------------------------------- | ----- |
| Arquivos PHP                              | 2.983 |
| Linhas de PHP                             | 231.421 |
| Linhas em `app/` (Laravel moderno)        | 44.376 |
| Linhas em `ieducar/` (legado procedural)  | 98.855 |
| Linhas em `src/` (pacotes internos)       | 8.769 |
| Linhas em `tests/`                        | 34.412 |
| Models Eloquent (`app/Models`)            | 170 |
| Migrations                                | 700 (316 delas em SQL cru, schema legado) |
| Tabelas no banco                          | 194 em 6 schemas |
| Rotas web (`routes/web.php`)              | 17,9 KB de definições |
| Endpoints REST (`routes/api.php`)         | ~31 |

## Stack original

- **PHP 8.3 + Laravel 13**, Blade, Vite, Yarn.
- **PostgreSQL** com schemas `cadastro`, `modules`, `pmieducar`, `portal`, `relatorio`, `public`.
- **Redis + Horizon** para filas; **Sanctum** para tokens; **Socialite** para login social.
- Domínio legado em `ieducar/` (controladores procedurais, bibliotecas e views Smarty/Blade),
  convivendo com models Eloquent novos (`app/Models/Legacy*`).
- Testes em PHPUnit (**443 arquivos**) cobrindo controllers, services e regras.

## Modelo de dados (essencial)

O schema é fortemente normalizado e cheio de tabelas de domínio. As entidades centrais:

| Tabela legada                | Função                                            | Colunas |
| ---------------------------- | ------------------------------------------------- | ------- |
| `cadastro.pessoa`            | base única de pessoas (física/jurídica)           | 13      |
| `cadastro.fisica`            | atributos de pessoa física (CPF, nascimento, etc.)| 52      |
| `pmieducar.aluno`            | aluno vinculado a uma pessoa                      | 34      |
| `pmieducar.escola`           | unidade escolar                                   | 170     |
| `pmieducar.instituicao`      | mantenedora / secretaria                          | 53      |
| `pmieducar.curso`            | curso (nível, modalidade, carga horária)          | 23      |
| `pmieducar.serie`            | série/etapa do curso                              | 24      |
| `pmieducar.turma`            | turma (ano, turno, capacidade, AEE etc.)          | 64      |
| `pmieducar.matricula`        | vínculo aluno ↔ escola/série/ano                  | 29      |
| `pmieducar.matricula_turma`  | enturmação do aluno                               | 22      |
| `pmieducar.usuario`          | usuário do sistema                                | 9       |
| `modules.componente_curricular` | disciplina                                     | 10      |

Observações relevantes para a reescrita:

1. **Pessoa é separada de Aluno.** Uma pessoa pode ser aluno, responsável, funcionário ou
   fornecedor. A nova modelagem preserva essa separação (`Pessoa` 1—1 `Aluno`).
2. **Matrícula e enturmação são entidades distintas.** A matrícula fixa escola/série/ano;
   a enturmação diz em qual turma o aluno está, com histórico (transferência, remanejamento).
3. **Escola tem 170 colunas** por concentrar dados do Censo/INEP, infraestrutura e
   acessibilidade. Na reescrita isso foi dividido em campos de endereço + cadastro da escola,
   deixando o bloco de Censo para a fase de integração com o INEP.
4. **Turma tem 64 colunas**, incluindo AEE, atividades complementares e etapas do Censo.
5. **Usuário legado tem tipo** (`tipo_usuario`) e vínculo opcional com escola — origem das
   regras de permissão por escola implementadas no novo backend.

## Autenticação e autorização no original

- Login por sessão Laravel (guard `web`) + Sanctum para a API.
- `pmieducar.usuario` + `pmieducar.tipo_usuario` definem perfis (admin, escola, professor…).
- Permissões granulares em tabelas de menu/recurso (`pmieducar.menu_tipo_usuario`).
- Escopo por escola aplicado em consultas e controllers — nem sempre de forma consistente.

Na reescrita: usuário único com `perfil` + `escola` (FK opcional), permissões declarativas
(`apps/core/permissions.py`) e escopo aplicado no `get_queryset()` de cada viewset.

## Funcionalidades mapeadas (módulos legados)

`AreaConhecimento`, `Avaliacao`, `Cadastro`, `Calendario`, `ComponenteCurricular`,
`Configuracao`, `Educacenso`, `FormulaMedia`, `HistoricoEscolar`, `RegraAvaliacao`,
`TabelaArredondamento`, `Usuario`, `Api`, além de `Reports` e `Modules` em `src/`.

Isso define as fases do plano de migração em [`03-plano-de-migracao.md`](03-plano-de-migracao.md).

## O que foi descartado de propósito

- Views Blade e bibliotecas JavaScript legadas (substituídas por SPA React).
- Menu/permissões em tabelas (`menu_tipo_usuario`) → permissões em código, versionadas.
- Funções de banco e triggers de auditoria → `RegistroAuditavel` + futura trilha de auditoria.
- Regras de negócio embutidas em controllers → `clean()`/serializers/services no Django.
