import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";

import { api, ApiError, type Frequencia, type Matricula, type Turma } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

export function FrequenciaPage() {
  const clienteQuery = useQueryClient();
  const [turmaId, setTurmaId] = useState("");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [presencas, setPresencas] = useState<Record<number, boolean>>({});
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const turmas = useQuery({
    queryKey: ["turmas", "opcoes"],
    queryFn: () => api.listar<Turma>("turmas", { page_size: 200, ordering: "-ano" }),
  });
  const matriculas = useQuery({
    queryKey: ["matriculas", "turma", turmaId],
    queryFn: () => api.listar<Matricula>("matriculas", { turma: turmaId, page_size: 200 }),
    enabled: turmaId !== "",
  });
  const registros = useQuery({
    queryKey: ["frequencias", turmaId, data],
    queryFn: () => api.listar<Frequencia>("frequencias", { turma: turmaId, data, page_size: 200 }),
    enabled: turmaId !== "",
  });

  useEffect(() => {
    const mapa: Record<number, boolean> = {};
    for (const aluno of matriculas.data?.results ?? []) mapa[aluno.id] = true;
    for (const registro of registros.data?.results ?? []) mapa[registro.matricula] = registro.presente;
    setPresencas(mapa);
  }, [matriculas.data, registros.data]);

  const salvar = useMutation({
    mutationFn: () =>
      api.frequenciaLote({
        turma: Number(turmaId),
        data,
        registros: Object.entries(presencas).map(([matricula, presente]) => ({
          matricula: Number(matricula),
          presente,
        })),
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["frequencias"] });
      setErro(null);
      setMensagem("Chamada salva com sucesso.");
    },
    onError: (falha) => {
      setMensagem(null);
      setErro(falha instanceof ApiError ? falha.message : "Erro ao salvar a chamada.");
    },
  });

  const alunos = useMemo(() => matriculas.data?.results ?? [], [matriculas.data]);
  const totalPresentes = Object.values(presencas).filter(Boolean).length;

  return (
    <>
      <PageHeader titulo="Frequência" descricao="Chamada diária por turma." />

      <Card className="mb-4">
        <div className="grid gap-4 px-5 py-4 sm:grid-cols-3">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Turma</span>
            <Select value={turmaId} onChange={(e) => setTurmaId(e.target.value)}>
              <option value="">Selecione…</option>
              {turmas.data?.results.map((turma) => (
                <option key={turma.id} value={turma.id}>
                  {turma.nome} · {turma.ano}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Data</span>
            <Input type="date" value={data} onChange={(e) => setData(e.target.value)} />
          </label>
          <div className="flex items-end text-sm text-slate-600">
            {alunos.length > 0 && `${totalPresentes}/${alunos.length} presente(s)`}
          </div>
        </div>
      </Card>

      {!turmaId && (
        <EmptyState titulo="Selecione uma turma" descricao="A lista de chamada aparece aqui." />
      )}

      {turmaId && (
        <Card>
          <CardHeader
            titulo="Lista de chamada"
            descricao="Marque os ausentes e salve."
            acoes={
              <Button onClick={() => salvar.mutate()} carregando={salvar.isPending} disabled={!alunos.length}>
                <Save className="h-4 w-4" aria-hidden />
                Salvar chamada
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
          {(matriculas.isLoading || registros.isLoading) && <Spinner />}
          {matriculas.data && (
            <Table>
              <thead>
                <tr>
                  <Th>Aluno</Th>
                  <Th className="w-40">Presença</Th>
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
                      <Select
                        className="h-9 w-32"
                        aria-label={`Presença de ${matricula.aluno_nome}`}
                        value={presencas[matricula.id] ? "presente" : "falta"}
                        onChange={(evento) =>
                          setPresencas((atual) => ({
                            ...atual,
                            [matricula.id]: evento.target.value === "presente",
                          }))
                        }
                      >
                        <option value="presente">Presente</option>
                        <option value="falta">Falta</option>
                      </Select>
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
