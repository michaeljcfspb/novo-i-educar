import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";

import { api, ApiError, type Deficiencia, type Escola, type Servidor } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const CARGOS = [
  { valor: "professor", rotulo: "Professor" },
  { valor: "pedagogo", rotulo: "Pedagogo" },
  { valor: "diretor", rotulo: "Diretor" },
  { valor: "secretario_escolar", rotulo: "Secretário escolar" },
  { valor: "auxiliar", rotulo: "Auxiliar" },
  { valor: "outro", rotulo: "Outro" },
];

export function ServidoresPage() {
  const clienteQuery = useQueryClient();
  const [busca, setBusca] = useState("");
  const [modalAberto, setModalAberto] = useState(false);
  const [nome, setNome] = useState("");
  const [cpf, setCpf] = useState("");
  const [cargo, setCargo] = useState("professor");
  const [escola, setEscola] = useState("");
  const [disciplinas, setDisciplinas] = useState<number[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  const servidores = useQuery({
    queryKey: ["servidores", busca],
    queryFn: () => api.listar<Servidor>("servidores", { search: busca || undefined, page_size: 50 }),
  });
  const escolas = useQuery({
    queryKey: ["escolas", "opcoes"],
    queryFn: () => api.listar<Escola>("escolas", { page_size: 200 }),
  });
  const disciplinasDisponiveis = useQuery({
    queryKey: ["disciplinas", "opcoes"],
    queryFn: () => api.listar<Deficiencia>("disciplinas", { page_size: 200 }),
  });

  const criar = useMutation({
    mutationFn: () =>
      api.criar<Servidor>("servidores", {
        pessoa: { nome, cpf: cpf || null },
        cargo,
        escola: Number(escola),
        disciplinas,
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["servidores"] });
      setModalAberto(false);
      setNome("");
      setCpf("");
      setDisciplinas([]);
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao salvar o servidor."),
  });

  function alternarDisciplina(id: number) {
    setDisciplinas((atual) =>
      atual.includes(id) ? atual.filter((item) => item !== id) : [...atual, id],
    );
  }

  return (
    <>
      <PageHeader
        titulo="Servidores"
        descricao="Professores e equipe escolar lotados nas unidades."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Novo servidor
          </Button>
        }
      />

      <Card>
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
          <div className="relative min-w-64 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <Input
              className="pl-9"
              placeholder="Buscar por nome ou matrícula"
              aria-label="Buscar servidores"
              value={busca}
              onChange={(evento) => setBusca(evento.target.value)}
            />
          </div>
          <span className="text-xs text-slate-500">
            {servidores.data ? `${servidores.data.count} servidor(es)` : ""}
          </span>
        </div>

        {servidores.isLoading && <Spinner />}
        {servidores.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar os servidores." />
          </div>
        )}

        {servidores.data && (
          <Table>
            <thead>
              <tr>
                <Th>Matrícula</Th>
                <Th>Nome</Th>
                <Th>Cargo</Th>
                <Th>Escola</Th>
                <Th>Disciplinas</Th>
                <Th>Situação</Th>
              </tr>
            </thead>
            <tbody>
              {servidores.data.results.length === 0 && (
                <EmptyRow colSpan={6} mensagem="Nenhum servidor cadastrado." />
              )}
              {servidores.data.results.map((servidor) => (
                <tr key={servidor.id}>
                  <Td className="font-mono text-xs">{servidor.matricula_funcional}</Td>
                  <Td className="font-medium text-slate-900">{servidor.nome}</Td>
                  <Td>{servidor.cargo_display}</Td>
                  <Td>{servidor.escola_nome}</Td>
                  <Td>
                    {servidor.disciplinas_detalhe.length
                      ? servidor.disciplinas_detalhe.map((d) => d.nome).join(", ")
                      : "—"}
                  </Td>
                  <Td>
                    <Badge tom={servidor.ativo ? "sucesso" : "neutro"}>
                      {servidor.ativo ? "Ativo" : "Inativo"}
                    </Badge>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Modal
        aberto={modalAberto}
        titulo="Novo servidor"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-servidor" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form
          id="form-servidor"
          onSubmit={(evento: FormEvent) => {
            evento.preventDefault();
            criar.mutate();
          }}
          className="grid gap-4 sm:grid-cols-2"
        >
          {erro && (
            <div className="sm:col-span-2">
              <ErroBox mensagem={erro} />
            </div>
          )}
          <div className="sm:col-span-2">
            <Campo label="Nome completo" obrigatorio>
              {(id) => <Input id={id} required value={nome} onChange={(e) => setNome(e.target.value)} />}
            </Campo>
          </div>
          <Campo label="CPF">
            {(id) => <Input id={id} value={cpf} onChange={(e) => setCpf(e.target.value)} />}
          </Campo>
          <Campo label="Cargo" obrigatorio>
            {(id) => (
              <Select id={id} value={cargo} onChange={(e) => setCargo(e.target.value)}>
                {CARGOS.map((item) => (
                  <option key={item.valor} value={item.valor}>
                    {item.rotulo}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <div className="sm:col-span-2">
            <Campo label="Escola de lotação" obrigatorio>
              {(id) => (
                <Select id={id} required value={escola} onChange={(e) => setEscola(e.target.value)}>
                  <option value="">Selecione…</option>
                  {escolas.data?.results.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome}
                    </option>
                  ))}
                </Select>
              )}
            </Campo>
          </div>
          <div className="sm:col-span-2">
            <Campo label="Disciplinas que leciona">
              {() => (
                <div className="flex flex-wrap gap-2">
                  {disciplinasDisponiveis.data?.results.map((item) => (
                    <label
                      key={item.id}
                      className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-sm"
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300"
                        checked={disciplinas.includes(item.id)}
                        onChange={() => alternarDisciplina(item.id)}
                      />
                      {item.nome}
                    </label>
                  ))}
                </div>
              )}
            </Campo>
          </div>
        </form>
      </Modal>
    </>
  );
}
