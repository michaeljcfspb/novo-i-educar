# 03 — Plano de migração

Migrar 231 mil linhas de PHP exige fatiar por **vertical**: cada fase entrega modelo,
API, tela e testes de um conjunto coeso de funcionalidades, sempre com o sistema antigo
ainda operando (estrangulamento gradual).

## Resumo

Todas as fases planejadas foram entregues. O sistema cobre o ciclo escolar completo:
cadastro → rede → matrícula → avaliação/frequência → histórico/documentos → censo →
relatórios e portal.

## Fase 0 — Fundação (concluída)

- [x] Monorepo `backend/` + `frontend/` + `docs/` + Docker.
- [x] Modelo de usuário, perfis e escopo por escola.
- [x] Login por sessão + CSRF (+ token para integrações).
- [x] Pessoas, alunos, deficiências.
- [x] Instituição, escola, curso, série, disciplina, turma.
- [x] Matrícula, enturmação, situação e cancelamento lógico.
- [x] OpenAPI/Swagger, paginação, busca, filtros e ordenação.
- [x] 36 testes de API/permissões/regras + build do frontend.
- [x] Docker, Compose, healthchecks, seed de demonstração.

## Fase 1 — Pessoas e rede escolar (concluída)

| Item | Escopo | Status |
| --- | --- | --- |
| Servidores/professores | `Servidor` ligado a `Pessoa`, lotação, cargo, disciplinas | ✅ feito |
| Turma × disciplina × professor | `TurmaDisciplina` com carga horária | ✅ feito |
| Ano letivo e calendário | `AnoLetivo`, `Calendario`, `CalendarioDia` | ✅ feito |
| Endereço completo | CEP, logradouro, bairro e município em `Pessoa`/`Escola` | ✅ feito |
| Permissões de escrita por escola | `EscopoPorEscolaEscrita` + validação no serializer | ✅ feito |
| Auditoria | `RegistroAuditoria` automático em todos os modelos de domínio | ✅ feito |

## Fase 2 — Avaliação e frequência (concluída)

Origem: módulos `Avaliacao`, `RegraAvaliacao`, `FormulaMedia`, `TabelaArredondamento`,
`ComponenteCurricular`.

- [x] Regra de avaliação (média aritmética/ponderada, nota máxima, recuperação, casas decimais).
- [x] Períodos de avaliação com peso por período.
- [x] Lançamento de notas por disciplina/período, individual e em lote.
- [x] Nota de recuperação substituindo a média quando maior.
- [x] Frequência diária com lançamento em lote (chamada).
- [x] Cálculo de média por disciplina, média geral e situação final (aprovado, recuperação,
      reprovado, reprovado por frequência).
- [x] Boletim na API (`/matriculas/{id}/boletim/`) e tela no SPA.
- [ ] Boletim em PDF e fechamento de período (Fase 5).

## Fase 3 — Histórico e secretaria (concluída)

Origem: módulos `HistoricoEscolar`, `Cadastro`, telas de transferência.

- [x] Histórico escolar consolidado (disciplinas, carga horária, médias, frequência e situação).
- [x] Geração idempotente do histórico a partir das notas/frequência (`/historicos/gerar/`).
- [x] Transferência de entrada/saída/interna com encerramento de matrícula e enturmação.
- [x] Documentos: declaração de matrícula, frequência, conclusão, histórico e guia de transferência.
- [x] Numeração automática de documentos (`DOC-AAAA-000000`) e visualização para impressão.
- [ ] Reclassificação e remanejamento (Fase 4, junto com importações).
- [ ] Certificados em PDF (Fase 5).

## Fase 4 — Censo e integrações (concluída)

Origem: módulo `Educacenso`.

- [x] Códigos INEP em escola, turma e aluno.
- [x] Exportação do Censo por escola/ano com versões, totais e **validação de pendências**
      (`/censo/exportacoes/gerar/` e `/preview/`).
- [x] Payload JSON com escola, turmas, alunos, deficiências e profissionais.
- [x] Importação de alunos por CSV com relatório linha a linha (erros de CPF, data, sexo,
      duplicidade no arquivo e no banco).
- [x] Webhooks com eventos assinados, entrega registrada e endpoint de teste.
- [x] Remanejamento de turma e reclassificação de série com histórico preservado.
- [ ] Importação XLSX e exportação oficial do arquivo INEP (Fase 5).

## Fase 5 — Relatórios e portal (concluída)

Origem: `Reports`, `Modules`, portal do aluno/professor.

- [x] Indicadores da rede: matrículas, aprovação, reprovação, abandono, transferência,
      ocupação média, frequência média e média geral (`/relatorios/indicadores/`).
- [x] Relatório por turma com ocupação, média e frequência + **exportação CSV**.
- [x] Alunos em risco (frequência < 75% ou média < 6) com motivo.
- [x] Portal do aluno/responsável: perfil, boletim, frequência e documentos.
- [x] Boletim e histórico em **PDF** (ReportLab).
- [ ] Notificações por e-mail/push e boletim em lote (evolução futura).

## Estratégia de migração de dados

O schema legado tem 194 tabelas. Não se migra tudo de uma vez:

1. **Catálogo de dados** por módulo (o que a fase precisa).
2. **ETL idempotente** em comando Django (`manage.py importar_legado --fase X`),
   lendo o dump restaurado em um schema `legado` do mesmo PostgreSQL.
3. **Chaves de correlação**: guardar `id_legado` em cada tabela nova (campo indexado e único
   por tipo) para reexecutar sem duplicar.
4. **Validação**: contagens por tabela, amostragem, checksum de campos críticos (CPF, matrícula).
5. **Cutover por módulo**: sistema novo em paralelo, leitura no novo, escrita nos dois até
   validar; depois desligar o antigo.

Sugestão de tabela de correlação (a adicionar na Fase 1):

```python
class IdLegado(models.Model):
    entidade = models.CharField(max_length=50)
    id_legado = models.PositiveBigIntegerField()
    objeto = models.ForeignKey(...)  # ou UUID
    class Meta:
        constraints = [UniqueConstraint(fields=["entidade", "id_legado"], ...)]
```

## Definition of Done por módulo

- Modelos + migrations com constraints.
- Serializers com validação de domínio.
- ViewSet com filtros, busca, ordenação, paginação e escopo.
- Permissões testadas (anônimo, consulta, gestor de outra escola, admin).
- Testes de regra de negócio (não só CRUD).
- Tela no SPA com estados de carregamento, vazio e erro.
- Endpoint no Swagger com resumo e exemplos.
- Documentação atualizada (`docs/04-api.md` e este plano).

## Riscos e mitigação

| Risco | Impacto | Mitigação |
| ----- | ------- | --------- |
| Regras do Censo/INEP mudarem por ano | Alto | Isolar em serviço versionado por ano; testes com fixtures oficiais. |
| Relatórios legados muito específicos | Médio | Reescrever por necessidade real; exportar CSV no início. |
| Volume de dados históricos | Médio | ETL em lotes, índices, `bulk_create`, janela de manutenção. |
| Divergência de regra de arredondamento/média | Alto | Portar tabela de testes do legado (ver `tests/` do PHP) como casos de aceitação. |
| Duas fontes de verdade durante transição | Alto | Escrita única por módulo + feature flag por escola. |
