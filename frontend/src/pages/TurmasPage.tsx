import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import { api, ApiError, type Escola, type Serie, type Turma } from "@/lib/api";
import { anosLetivos } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { Table, Td, Th } from "@/components/ui/table";

const POR_PAGINA = 10;

export function TurmasPage() {
  const clienteQuery = useQueryClient();
  const [ano, setAno] = useState<string>(String(new Date().getFullYear()));
  const [pagina, setPagina] = useState(1);
  const [modalAberto, setModalAberto] = useState(false);
  const [escola, setEscola] = useState("");
  const [serie, setSerie] = useState("");
  const [nome, setNome] = useState("");
  const [turno, setTurno] = useState("matutino");
  const [capacidade, setCapacidade] = useState("30");
  const [erro, setErro] = useState<string | null>(null);

  const turmas = useQuery({
    queryKey: ["turmas", ano, pagina],
    queryFn: () =>
      api.listar<Turma>("turmas", {
        page: pagina,
        page_size: POR_PAGINA,
        ano: ano || undefined,
        ordering: "nome",
      }),
  });

  const escolas = useQuery({
    queryKey: ["escolas", "opcoes"],
    queryFn: () => api.listar<Escola>("escolas", { page_size: 200 }),
  });

  const series = useQuery({
    queryKey: ["series", "opcoes"],
    queryFn: () => api.listar<Serie>("series", { page_size: 200 }),
  });

  const criar = useMutation({
    mutationFn: () =>
      api.criar<Turma>("turmas", {
        escola: Number(escola),
        serie: Number(serie),
        nome,
        ano: Number(ano),
        turno,
        capacidade: Number(capacidade),
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["turmas"] });
      await clienteQuery.invalidateQueries({ queryKey: ["contagens"] });
      setModalAberto(false);
      setNome("");
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao salvar a turma."),
  });

  function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    criar.mutate();
  }

  const totalPaginas = turmas.data ? Math.ceil(turmas.data.count / POR_PAGINA) : 1;

  return (
    <>
      <PageHeader
        titulo="Turmas"
        descricao="Turmas por escola, série e ano letivo."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Nova turma
          </Button>
        }
      />

      <Card>
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-4 py-3">
          <label className="text-sm text-slate-600" htmlFor="filtro-ano">
            Ano letivo
          </label>
          <Select
            id="filtro-ano"
            className="w-32"
            value={ano}
            onChange={(evento) => {
              setAno(evento.target.value);
              setPagina(1);
            }}
          >
            <option value="">Todos</option>
            {anosLetivos().map((valor) => (
              <option key={valor} value={valor}>
                {valor}
              </option>
            ))}
          </Select>
          <span className="ml-auto text-xs text-slate-500">
            {turmas.data ? `${turmas.data.count} turma(s)` : ""}
          </span>
        </div>

        {turmas.isLoading && <Spinner />}
        {turmas.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar as turmas." />
          </div>
        )}

        {turmas.data && turmas.data.results.length === 0 && (
          <EmptyState titulo="Nenhuma turma" descricao="Cadastre uma turma para o ano selecionado." />
        )}

        {turmas.data && turmas.data.results.length > 0 && (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Turma</Th>
                  <Th>Escola</Th>
                  <Th>Série</Th>
                  <Th>Ano</Th>
                  <Th>Turno</Th>
                  <Th>Vagas</Th>
                  <Th>Situação</Th>
                </tr>
              </thead>
              <tbody>
                {turmas.data.results.map((turma) => (
                  <tr key={turma.id}>
                    <Td className="font-medium text-slate-900">{turma.nome}</Td>
                    <Td>{turma.escola_nome}</Td>
                    <Td>{turma.serie_nome}</Td>
                    <Td>{turma.ano}</Td>
                    <Td className="capitalize">{turma.turno}</Td>
                    <Td>
                      {turma.vagas_disponiveis}/{turma.capacidade}
                    </Td>
                    <Td>
                      <Badge tom={turma.ativo ? "sucesso" : "neutro"}>
                        {turma.ativo ? "Ativa" : "Inativa"}
                      </Badge>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
            <Pagination pagina={pagina} totalPaginas={totalPaginas} aoMudar={setPagina} />
          </>
        )}
      </Card>

      <Modal
        aberto={modalAberto}
        titulo="Nova turma"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-turma" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-turma" onSubmit={aoEnviar} className="grid gap-4 sm:grid-cols-2">
          {erro && (
            <div className="sm:col-span-2">
              <ErroBox mensagem={erro} />
            </div>
          )}
          <div className="sm:col-span-2">
            <Campo label="Escola" obrigatorio>
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
            <Campo label="Série" obrigatorio>
              {(id) => (
                <Select id={id} required value={serie} onChange={(e) => setSerie(e.target.value)}>
                  <option value="">Selecione…</option>
                  {series.data?.results.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome} — {item.curso_nome}
                    </option>
                  ))}
                </Select>
              )}
            </Campo>
          </div>
          <Campo label="Nome da turma" obrigatorio>
            {(id) => <Input id={id} required value={nome} onChange={(e) => setNome(e.target.value)} placeholder="1º Ano A" />}
          </Campo>
          <Campo label="Capacidade" obrigatorio>
            {(id) => (
              <Input
                id={id}
                type="number"
                min={1}
                required
                value={capacidade}
                onChange={(e) => setCapacidade(e.target.value)}
              />
            )}
          </Campo>
          <Campo label="Turno" obrigatorio>
            {(id) => (
              <Select id={id} value={turno} onChange={(e) => setTurno(e.target.value)}>
                <option value="matutino">Matutino</option>
                <option value="vespertino">Vespertino</option>
                <option value="noturno">Noturno</option>
                <option value="integral">Integral</option>
              </Select>
            )}
          </Campo>
          <Campo label="Ano letivo" obrigatorio>
            {(id) => (
              <Input id={id} type="number" value={ano} onChange={(e) => setAno(e.target.value)} />
            )}
          </Campo>
        </form>
      </Modal>
    </>
  );
}
