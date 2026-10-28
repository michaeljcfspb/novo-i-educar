import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";

import {
  api,
  ApiError,
  type Matricula,
  type Nota,
  type PeriodoAvaliacao,
  type Turma,
  type TurmaDisciplina,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

export function NotasPage() {
  const clienteQuery = useQueryClient();
  const [turmaId, setTurmaId] = useState("");
  const [alocacaoId, setAlocacaoId] = useState("");
  const [periodoId, setPeriodoId] = useState("");
  const [tipo, setTipo] = useState<"normal" | "recuperacao">("normal");
  const [valores, setValores] = useState<Record<number, string>>({});
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const turmas = useQuery({
    queryKey: ["turmas", "opcoes"],
    queryFn: () => api.listar<Turma>("turmas", { page_size: 200, ordering: "-ano" }),
  });
  const alocacoes = useQuery({
    queryKey: ["turma-disciplinas", turmaId],
    queryFn: () => api.listar<TurmaDisciplina>("turma-disciplinas", { turma: turmaId, page_size: 100 }),
    enabled: turmaId !== "",
  });
  const periodos = useQuery({
    queryKey: ["periodos-avaliacao"],
    queryFn: () => api.listar<PeriodoAvaliacao>("periodos-avaliacao", { page_size: 50 }),
  });
  const matriculas = useQuery({
    queryKey: ["matriculas", "turma", turmaId],
    queryFn: () => api.listar<Matricula>("matriculas", { turma: turmaId, page_size: 200 }),
    enabled: turmaId !== "",
  });
  const notas = useQuery({
    queryKey: ["notas", alocacaoId, periodoId, tipo],
    queryFn: () =>
      api.listar<Nota>("notas", {
        turma_disciplina: alocacaoId,
        periodo: periodoId,
        tipo,
        page_size: 200,
      }),
    enabled: alocacaoId !== "" && periodoId !== "",
  });

  useEffect(() => {
    if (!notas.data) return;
    const mapa: Record<number, string> = {};
    for (const nota of notas.data.results) mapa[nota.matricula] = nota.valor;
    setValores(mapa);
  }, [notas.data]);

  const salvar = useMutation({
    mutationFn: () =>
      api.notasLote({
        turma_disciplina: Number(alocacaoId),
        periodo: Number(periodoId),
        tipo,
        registros: Object.entries(valores)
          .filter(([, valor]) => valor !== "")
          .map(([matricula, valor]) => ({ matricula: Number(matricula), valor })),
      }),
    onSuccess: async (dados) => {
      await clienteQuery.invalidateQueries({ queryKey: ["notas"] });
      setErro(null);
      setMensagem(
        `${dados.criadas.length} nota(s) salva(s)${dados.erros.length ? ` · ${dados.erros.length} com erro` : ""}.`,
      );
    },
    onError: (falha) => {
      setMensagem(null);
      setErro(falha instanceof ApiError ? falha.message : "Erro ao salvar as notas.");
    },
  });

  const alunos = useMemo(() => matriculas.data?.results ?? [], [matriculas.data]);
  const podeLancar = alocacaoId !== "" && periodoId !== "";

  return (
    <>
      <PageHeader titulo="Notas" descricao="Lançamento de notas por turma, disciplina e período." />

      <Card className="mb-4">
        <CardBody className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Turma</span>
            <Select value={turmaId} onChange={(e) => { setTurmaId(e.target.value); setAlocacaoId(""); }}>
              <option value="">Selecione…</option>
              {turmas.data?.results.map((turma) => (
                <option key={turma.id} value={turma.id}>
                  {turma.nome} · {turma.ano}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Disciplina</span>
            <Select value={alocacaoId} onChange={(e) => setAlocacaoId(e.target.value)} disabled={!turmaId}>
              <option value="">Selecione…</option>
              {alocacoes.data?.results.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.disciplina_nome}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Período</span>
            <Select value={periodoId} onChange={(e) => setPeriodoId(e.target.value)}>
              <option value="">Selecione…</option>
              {periodos.data?.results.map((periodo) => (
                <option key={periodo.id} value={periodo.id}>
                  {periodo.nome} ({periodo.ano})
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Tipo</span>
            <Select value={tipo} onChange={(e) => setTipo(e.target.value as "normal" | "recuperacao")}>
              <option value="normal">Nota normal</option>
              <option value="recuperacao">Recuperação</option>
            </Select>
          </label>
        </CardBody>
      </Card>

      {!podeLancar && (
        <EmptyState
          titulo="Selecione turma, disciplina e período"
          descricao="A planilha de lançamento aparece aqui."
        />
      )}

      {podeLancar && (
        <Card>
          <CardHeader
            titulo="Planilha de notas"
            descricao="Digite a nota de 0 a 10 por aluno e salve de uma vez."
            acoes={
              <Button onClick={() => salvar.mutate()} carregando={salvar.isPending} disabled={!alunos.length}>
                <Save className="h-4 w-4" aria-hidden />
                Salvar notas
              </Button>
            }
          />
          {mensagem && (
            <div className="mx-4 mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
              {mensagem}
            </div>
          )}
          {erro && (
            <div className="mx-4 mt-4">
              <ErroBox mensagem={erro} />
            </div>
          )}
          {(notas.isLoading || matriculas.isLoading) && <Spinner />}
          {matriculas.data && (
            <Table>
              <thead>
                <tr>
                  <Th>Aluno</Th>
                  <Th className="w-40">Nota</Th>
                </tr>
              </thead>
              <tbody>
                {alunos.length === 0 && (
                  <EmptyRow colSpan={2} mensagem="Nenhum aluno enturmado nesta turma." />
                )}
                {alunos.map((matricula) => (
                  <tr key={matricula.id}>
                    <Td className="font-medium text-slate-900">{matricula.aluno_nome}</Td>
                    <Td>
                      <Input
                        type="number"
                        min={0}
                        max={10}
                        step="0.1"
                        className="h-9 w-28"
                        aria-label={`Nota de ${matricula.aluno_nome}`}
                        value={valores[matricula.id] ?? ""}
                        onChange={(evento) =>
                          setValores((atual) => ({ ...atual, [matricula.id]: evento.target.value }))
                        }
                      />
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      )}
    </>
  );
}
