import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileClock, RefreshCw } from "lucide-react";

import { API_URL, api, ApiError, type HistoricoEscolar, type Matricula } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const tons: Record<string, "sucesso" | "atencao" | "erro" | "neutro"> = {
  aprovado: "sucesso",
  reprovado: "erro",
  em_curso: "atencao",
  transferido: "neutro",
  abandonou: "neutro",
};

export function HistoricoPage() {
  const clienteQuery = useQueryClient();
  const [matriculaId, setMatriculaId] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const matriculas = useQuery({
    queryKey: ["matriculas", "historico"],
    queryFn: () => api.listar<Matricula>("matriculas", { page_size: 200, ordering: "-ano" }),
  });
  const historicos = useQuery({
    queryKey: ["historicos"],
    queryFn: () => api.listar<HistoricoEscolar>("historicos", { page_size: 50 }),
  });

  const gerar = useMutation({
    mutationFn: () => api.gerarHistorico(Number(matriculaId)),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["historicos"] });
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao gerar o histórico."),
  });

  const selecionado = historicos.data?.results.find((item) => item.matricula === Number(matriculaId));

  return (
    <>
      <PageHeader
        titulo="Histórico escolar"
        descricao="Consolidação de notas e frequência por ano e série."
      />

      <Card className="mb-4">
        <CardBody className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-72 flex-1 flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Matrícula</span>
            <Select value={matriculaId} onChange={(e) => setMatriculaId(e.target.value)}>
              <option value="">Selecione o aluno…</option>
              {matriculas.data?.results.map((matricula) => (
                <option key={matricula.id} value={matricula.id}>
                  {matricula.aluno_nome} · {matricula.serie_nome} · {matricula.ano}
                </option>
              ))}
            </Select>
          </label>
          <Button
            onClick={() => gerar.mutate()}
            disabled={!matriculaId}
            carregando={gerar.isPending}
          >
            <RefreshCw className="h-4 w-4" aria-hidden />
            Gerar/atualizar
          </Button>
        </CardBody>
      </Card>

      {erro && (
        <div className="mb-4">
          <ErroBox mensagem={erro} />
        </div>
      )}

      {!matriculaId && (
        <EmptyState
          titulo="Selecione uma matrícula"
          descricao="O histórico é gerado a partir das notas e da frequência registradas."
        />
      )}

      {matriculaId && gerar.isPending && <Spinner rotulo="Consolidando histórico…" />}

      {selecionado && (
        <Card className="mb-4">
          <CardHeader
            titulo={`${selecionado.aluno_nome} · ${selecionado.serie_nome} · ${selecionado.ano}`}
            descricao={`${selecionado.escola_nome} · carga horária ${selecionado.carga_horaria_total}h · ${selecionado.dias_letivos} dias letivos`}
            acoes={
              <div className="flex items-center gap-2">
                <Badge tom={tons[selecionado.situacao] ?? "neutro"}>{selecionado.situacao_display}</Badge>
                <a href={`${API_URL}/historicos/${selecionado.id}/pdf/`} target="_blank" rel="noreferrer">
                  <Button variante="secundario" tamanho="sm">PDF</Button>
                </a>
              </div>
            }
          />
          <CardBody className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Média geral</p>
              <p className="text-2xl font-semibold">{Number(selecionado.media_geral).toFixed(1)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Frequência</p>
              <p className="text-2xl font-semibold">{Number(selecionado.frequencia_percentual).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Disciplinas</p>
              <p className="text-2xl font-semibold">{selecionado.disciplinas.length}</p>
            </div>
          </CardBody>
          <Table>
            <thead>
              <tr>
                <Th>Disciplina</Th>
                <Th>Carga horária</Th>
                <Th>Média</Th>
                <Th>Frequência</Th>
                <Th>Situação</Th>
              </tr>
            </thead>
            <tbody>
              {selecionado.disciplinas.length === 0 && (
                <EmptyRow colSpan={5} mensagem="Nenhuma disciplina registrada." />
              )}
              {selecionado.disciplinas.map((disciplina) => (
                <tr key={disciplina.id}>
                  <Td className="font-medium text-slate-900">{disciplina.nome_disciplina}</Td>
                  <Td>{disciplina.carga_horaria}h</Td>
                  <Td>{Number(disciplina.media).toFixed(1)}</Td>
                  <Td>{Number(disciplina.frequencia).toFixed(1)}%</Td>
                  <Td>
                    <Badge tom={tons[disciplina.situacao] ?? "neutro"}>
                      {disciplina.situacao === "aprovado" ? "Aprovado" : "Reprovado"}
                    </Badge>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      <Card>
        <CardHeader
          titulo="Históricos gerados"
          descricao="Registros consolidados da rede."
          acoes={<FileClock className="h-4 w-4 text-slate-400" aria-hidden />}
        />
        {historicos.isLoading && <Spinner />}
        {historicos.data && (
          <Table>
            <thead>
              <tr>
                <Th>Aluno</Th>
                <Th>Ano</Th>
                <Th>Série</Th>
                <Th>Média</Th>
                <Th>Situação</Th>
              </tr>
            </thead>
            <tbody>
              {historicos.data.results.length === 0 && (
                <EmptyRow colSpan={5} mensagem="Nenhum histórico gerado ainda." />
              )}
              {historicos.data.results.map((historico) => (
                <tr key={historico.id}>
                  <Td className="font-medium text-slate-900">{historico.aluno_nome}</Td>
                  <Td>{historico.ano}</Td>
                  <Td>{historico.serie_nome}</Td>
                  <Td>{Number(historico.media_geral).toFixed(1)}</Td>
                  <Td>
                    <Badge tom={tons[historico.situacao] ?? "neutro"}>
                      {historico.situacao_display}
                    </Badge>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}
