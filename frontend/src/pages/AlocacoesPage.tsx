import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";

import {
  api,
  ApiError,
  type Deficiencia,
  type Servidor,
  type Turma,
  type TurmaDisciplina,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

export function AlocacoesPage() {
  const clienteQuery = useQueryClient();
  const [turmaId, setTurmaId] = useState("");
  const [modalAberto, setModalAberto] = useState(false);
  const [disciplina, setDisciplina] = useState("");
  const [professor, setProfessor] = useState("");
  const [carga, setCarga] = useState("200");
  const [erro, setErro] = useState<string | null>(null);

  const turmas = useQuery({
    queryKey: ["turmas", "opcoes"],
    queryFn: () => api.listar<Turma>("turmas", { page_size: 200, ordering: "-ano" }),
  });
  const disciplinas = useQuery({
    queryKey: ["disciplinas", "opcoes"],
    queryFn: () => api.listar<Deficiencia>("disciplinas", { page_size: 200 }),
  });
  const professores = useQuery({
    queryKey: ["servidores", "professores"],
    queryFn: () => api.listar<Servidor>("servidores", { cargo: "professor", page_size: 200 }),
  });
  const alocacoes = useQuery({
    queryKey: ["turma-disciplinas", turmaId],
    queryFn: () => api.listar<TurmaDisciplina>("turma-disciplinas", { turma: turmaId, page_size: 100 }),
    enabled: turmaId !== "",
  });

  const criar = useMutation({
    mutationFn: () =>
      api.criar<TurmaDisciplina>("turma-disciplinas", {
        turma: Number(turmaId),
        disciplina: Number(disciplina),
        professor: professor ? Number(professor) : null,
        carga_horaria: Number(carga),
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["turma-disciplinas"] });
      setModalAberto(false);
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao alocar disciplina."),
  });

  const remover = useMutation({
    mutationFn: (id: number) => api.remover("turma-disciplinas", id),
    onSuccess: async () => clienteQuery.invalidateQueries({ queryKey: ["turma-disciplinas"] }),
  });

  return (
    <>
      <PageHeader
        titulo="Grade da turma"
        descricao="Disciplinas, professores e carga horária de cada turma."
        acoes={
          <Button onClick={() => setModalAberto(true)} disabled={!turmaId}>
            <Plus className="h-4 w-4" aria-hidden />
            Alocar disciplina
          </Button>
        }
      />

      <Card>
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-4 py-3">
          <label className="text-sm text-slate-600" htmlFor="turma-select">
            Turma
          </label>
          <Select
            id="turma-select"
            className="w-72"
            value={turmaId}
            onChange={(evento) => setTurmaId(evento.target.value)}
          >
            <option value="">Selecione uma turma…</option>
            {turmas.data?.results.map((turma) => (
              <option key={turma.id} value={turma.id}>
                {turma.nome} · {turma.escola_nome} · {turma.ano}
              </option>
            ))}
          </Select>
        </div>

        {!turmaId && (
          <EmptyState titulo="Escolha uma turma" descricao="A grade curricular aparece aqui." />
        )}
        {turmaId && alocacoes.isLoading && <Spinner />}
        {turmaId && alocacoes.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar a grade da turma." />
          </div>
        )}

        {turmaId && alocacoes.data && (
          <Table>
            <thead>
              <tr>
                <Th>Disciplina</Th>
                <Th>Professor</Th>
                <Th>Carga horária</Th>
                <Th>Ações</Th>
              </tr>
            </thead>
            <tbody>
              {alocacoes.data.results.length === 0 && (
                <EmptyRow colSpan={4} mensagem="Nenhuma disciplina alocada nesta turma." />
              )}
              {alocacoes.data.results.map((alocacao) => (
                <tr key={alocacao.id}>
                  <Td className="font-medium text-slate-900">{alocacao.disciplina_nome}</Td>
                  <Td>{alocacao.professor_nome ?? "Sem professor"}</Td>
                  <Td>{alocacao.carga_horaria}h</Td>
                  <Td>
                    <Button
                      variante="fantasma"
                      tamanho="sm"
                      aria-label={`Remover ${alocacao.disciplina_nome}`}
                      onClick={() => remover.mutate(alocacao.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Modal
        aberto={modalAberto}
        titulo="Alocar disciplina"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-alocacao" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form
          id="form-alocacao"
          onSubmit={(evento: FormEvent) => {
            evento.preventDefault();
            criar.mutate();
          }}
          className="grid gap-4"
        >
          {erro && <ErroBox mensagem={erro} />}
          <Campo label="Disciplina" obrigatorio>
            {(id) => (
              <Select id={id} required value={disciplina} onChange={(e) => setDisciplina(e.target.value)}>
                <option value="">Selecione…</option>
                {disciplinas.data?.results.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nome}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <Campo label="Professor">
            {(id) => (
              <Select id={id} value={professor} onChange={(e) => setProfessor(e.target.value)}>
                <option value="">Sem professor definido</option>
                {professores.data?.results.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nome}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <Campo label="Carga horária (h)">
            {(id) => (
              <Input id={id} type="number" min={0} value={carga} onChange={(e) => setCarga(e.target.value)} />
            )}
          </Campo>
        </form>
      </Modal>
    </>
  );
}
