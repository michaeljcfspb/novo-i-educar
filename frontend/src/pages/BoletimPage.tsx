import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { API_URL, api, type Matricula } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const rotulos: Record<string, { texto: string; tom: "sucesso" | "atencao" | "erro" | "neutro" }> = {
  aprovado: { texto: "Aprovado", tom: "sucesso" },
  recuperacao: { texto: "Em recuperação", tom: "atencao" },
  reprovado: { texto: "Reprovado", tom: "erro" },
  reprovado_frequencia: { texto: "Reprovado por frequência", tom: "erro" },
  sem_regra: { texto: "Sem regra de avaliação", tom: "neutro" },
};

export function BoletimPage() {
  const [matriculaId, setMatriculaId] = useState("");

  const matriculas = useQuery({
    queryKey: ["matriculas", "boletim"],
    queryFn: () => api.listar<Matricula>("matriculas", { page_size: 200, ordering: "-ano" }),
  });

  const boletim = useQuery({
    queryKey: ["boletim", matriculaId],
    queryFn: () => api.boletim(Number(matriculaId)),
    enabled: matriculaId !== "",
  });

  const periodos = useMemo(() => {
    const nomes = new Set<string>();
    for (const disciplina of boletim.data?.disciplinas ?? []) {
      for (const nome of Object.keys(disciplina.notas)) nomes.add(nome);
    }
    return Array.from(nomes);
  }, [boletim.data]);

  const situacao = boletim.data ? rotulos[boletim.data.situacao_final] ?? { texto: boletim.data.situacao_final, tom: "neutro" as const } : null;

  return (
    <>
      <PageHeader
        titulo="Boletim"
        descricao="Notas, médias, frequência e situação final do aluno."
        acoes={
          matriculaId ? (
            <a href={`${API_URL}/matriculas/${matriculaId}/boletim-pdf/`} target="_blank" rel="noreferrer">
              <Button variante="secundario">Baixar PDF</Button>
            </a>
          ) : undefined
        }
      />

      <Card className="mb-4">
        <CardBody>
          <label className="flex flex-col gap-1.5 text-sm sm:max-w-xl">
            <span className="font-medium text-slate-700">Matrícula</span>
            <Select value={matriculaId} onChange={(e) => setMatriculaId(e.target.value)}>
              <option value="">Selecione o aluno…</option>
              {matriculas.data?.results.map((matricula) => (
                <option key={matricula.id} value={matricula.id}>
                  {matricula.aluno_nome} · {matricula.escola_nome} · {matricula.ano}
                </option>
              ))}
            </Select>
          </label>
        </CardBody>
      </Card>

      {!matriculaId && (
        <EmptyState titulo="Selecione uma matrícula" descricao="O boletim é montado a partir das notas e da frequência." />
      )}
      {boletim.isLoading && <Spinner />}
      {boletim.isError && <ErroBox mensagem="Não foi possível carregar o boletim." />}

      {boletim.data && (
        <div className="space-y-4">
          <Card>
            <CardBody className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Aluno</p>
                <p className="text-lg font-semibold text-slate-900">{boletim.data.aluno}</p>
                <p className="text-sm text-slate-500">
                  {boletim.data.turma ?? "Sem turma"} · {boletim.data.ano} ·{" "}
                  {boletim.data.regra_avaliacao ?? "sem regra"}
                </p>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Média geral</p>
                  <p className="text-2xl font-semibold text-slate-900">{boletim.data.media_geral.toFixed(1)}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Frequência</p>
                  <p className="text-2xl font-semibold text-slate-900">
                    {boletim.data.frequencia.percentual.toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-500">
                    mínimo {boletim.data.frequencia.minimo ?? "—"}%
                  </p>
                </div>
                {situacao && <Badge tom={situacao.tom}>{situacao.texto}</Badge>}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader titulo="Desempenho por disciplina" />
            <Table>
              <thead>
                <tr>
                  <Th>Disciplina</Th>
                  {periodos.map((periodo) => (
                    <Th key={periodo}>{periodo}</Th>
                  ))}
                  <Th>Recuperação</Th>
                  <Th>Média</Th>
                </tr>
              </thead>
              <tbody>
                {boletim.data.disciplinas.length === 0 && (
                  <EmptyRow colSpan={periodos.length + 3} mensagem="Sem disciplinas alocadas na turma." />
                )}
                {boletim.data.disciplinas.map((disciplina) => (
                  <tr key={disciplina.turma_disciplina}>
                    <Td className="font-medium text-slate-900">{disciplina.disciplina}</Td>
                    {periodos.map((periodo) => (
                      <Td key={periodo}>{disciplina.notas[periodo] ?? "—"}</Td>
                    ))}
                    <Td>{disciplina.recuperacao ?? "—"}</Td>
                    <Td className="font-semibold">{disciplina.media.toFixed(1)}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
        </div>
      )}
    </>
  );
}
