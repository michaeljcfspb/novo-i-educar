import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";

import { api, ApiError, type Escola, type Instituicao } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { Table, Td, Th } from "@/components/ui/table";

const POR_PAGINA = 10;

export function EscolasPage() {
  const clienteQuery = useQueryClient();
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [modalAberto, setModalAberto] = useState(false);
  const [instituicao, setInstituicao] = useState("");
  const [nome, setNome] = useState("");
  const [sigla, setSigla] = useState("");
  const [inep, setInep] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const escolas = useQuery({
    queryKey: ["escolas", busca, pagina],
    queryFn: () =>
      api.listar<Escola>("escolas", {
        page: pagina,
        page_size: POR_PAGINA,
        search: busca || undefined,
      }),
  });

  const instituicoes = useQuery({
    queryKey: ["instituicoes"],
    queryFn: () => api.listar<Instituicao>("instituicoes", { page_size: 200 }),
  });

  const criar = useMutation({
    mutationFn: () =>
      api.criar<Escola>("escolas", {
        instituicao: Number(instituicao),
        nome,
        sigla,
        codigo_inep: inep,
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["escolas"] });
      await clienteQuery.invalidateQueries({ queryKey: ["contagens"] });
      setModalAberto(false);
      setNome("");
      setSigla("");
      setInep("");
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao salvar a escola."),
  });

  function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    criar.mutate();
  }

  const totalPaginas = escolas.data ? Math.ceil(escolas.data.count / POR_PAGINA) : 1;
  const semInstituicao = instituicoes.data?.results.length === 0;

  return (
    <>
      <PageHeader
        titulo="Escolas"
        descricao="Unidades escolares vinculadas a uma instituição."
        acoes={
          <Button onClick={() => setModalAberto(true)} disabled={semInstituicao}>
            <Plus className="h-4 w-4" aria-hidden />
            Nova escola
          </Button>
        }
      />

      {semInstituicao && (
        <div className="mb-4">
          <ErroBox mensagem="Cadastre uma instituição no Django Admin antes de criar escolas." />
        </div>
      )}

      <Card>
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
          <div className="relative min-w-64 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <Input
              className="pl-9"
              placeholder="Buscar por nome, sigla ou INEP"
              aria-label="Buscar escolas"
              value={busca}
              onChange={(evento) => {
                setBusca(evento.target.value);
                setPagina(1);
              }}
            />
          </div>
          <span className="text-xs text-slate-500">
            {escolas.data ? `${escolas.data.count} registro(s)` : ""}
          </span>
        </div>

        {escolas.isLoading && <Spinner />}
        {escolas.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar as escolas." />
          </div>
        )}

        {escolas.data && escolas.data.results.length === 0 && (
          <EmptyState titulo="Nenhuma escola" descricao="Cadastre a primeira unidade escolar." />
        )}

        {escolas.data && escolas.data.results.length > 0 && (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Nome</Th>
                  <Th>Sigla</Th>
                  <Th>Instituição</Th>
                  <Th>INEP</Th>
                  <Th>Cidade</Th>
                  <Th>Situação</Th>
                </tr>
              </thead>
              <tbody>
                {escolas.data.results.map((escola) => (
                  <tr key={escola.id}>
                    <Td className="font-medium text-slate-900">{escola.nome}</Td>
                    <Td>{escola.sigla}</Td>
                    <Td>{escola.instituicao_nome}</Td>
                    <Td className="font-mono text-xs">{escola.codigo_inep || "—"}</Td>
                    <Td>{escola.municipio ?? "—"}</Td>
                    <Td>
                      <Badge tom={escola.ativo ? "sucesso" : "neutro"}>
                        {escola.ativo ? "Ativa" : "Inativa"}
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
        titulo="Nova escola"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-escola" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-escola" onSubmit={aoEnviar} className="grid gap-4 sm:grid-cols-2">
          {erro && (
            <div className="sm:col-span-2">
              <ErroBox mensagem={erro} />
            </div>
          )}
          <div className="sm:col-span-2">
            <Campo label="Instituição" obrigatorio>
              {(id) => (
                <Select id={id} required value={instituicao} onChange={(e) => setInstituicao(e.target.value)}>
                  <option value="">Selecione…</option>
                  {instituicoes.data?.results.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome}
                    </option>
                  ))}
                </Select>
              )}
            </Campo>
          </div>
          <Campo label="Nome" obrigatorio>
            {(id) => <Input id={id} required value={nome} onChange={(e) => setNome(e.target.value)} />}
          </Campo>
          <Campo label="Sigla" obrigatorio>
            {(id) => <Input id={id} required value={sigla} onChange={(e) => setSigla(e.target.value)} />}
          </Campo>
          <Campo label="Código INEP">
            {(id) => <Input id={id} value={inep} onChange={(e) => setInep(e.target.value)} />}
          </Campo>
        </form>
      </Modal>
    </>
  );
}
