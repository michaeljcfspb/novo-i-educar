import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";

import { api, ApiError, type Pessoa } from "@/lib/api";
import { formatarCpf, formatarData } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input } from "@/components/ui/field";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const POR_PAGINA = 10;

export function PessoasPage() {
  const clienteQuery = useQueryClient();
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [modalAberto, setModalAberto] = useState(false);
  const [nome, setNome] = useState("");
  const [cpf, setCpf] = useState("");
  const [email, setEmail] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const pessoas = useQuery({
    queryKey: ["pessoas", busca, pagina],
    queryFn: () =>
      api.listar<Pessoa>("pessoas", {
        page: pagina,
        page_size: POR_PAGINA,
        search: busca || undefined,
      }),
  });

  const criar = useMutation({
    mutationFn: () =>
      api.criar<Pessoa>("pessoas", { nome, cpf: cpf || null, email, tipo: "fisica" }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["pessoas"] });
      setModalAberto(false);
      setNome("");
      setCpf("");
      setEmail("");
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao salvar a pessoa."),
  });

  function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    criar.mutate();
  }

  const totalPaginas = pessoas.data ? Math.ceil(pessoas.data.count / POR_PAGINA) : 1;

  return (
    <>
      <PageHeader
        titulo="Pessoas"
        descricao="Base única de pessoas físicas e jurídicas."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Nova pessoa
          </Button>
        }
      />

      <Card>
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
          <div className="relative min-w-64 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <Input
              className="pl-9"
              placeholder="Buscar por nome, CPF ou e-mail"
              aria-label="Buscar pessoas"
              value={busca}
              onChange={(evento) => {
                setBusca(evento.target.value);
                setPagina(1);
              }}
            />
          </div>
          <span className="text-xs text-slate-500">
            {pessoas.data ? `${pessoas.data.count} registro(s)` : ""}
          </span>
        </div>

        {pessoas.isLoading && <Spinner />}
        {pessoas.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar as pessoas." />
          </div>
        )}

        {pessoas.data && (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Nome</Th>
                  <Th>Tipo</Th>
                  <Th>CPF</Th>
                  <Th>Nascimento</Th>
                  <Th>E-mail</Th>
                  <Th>Situação</Th>
                </tr>
              </thead>
              <tbody>
                {pessoas.data.results.length === 0 && (
                  <EmptyRow colSpan={6} mensagem="Nenhuma pessoa encontrada." />
                )}
                {pessoas.data.results.map((pessoa) => (
                  <tr key={pessoa.id}>
                    <Td className="font-medium text-slate-900">{pessoa.nome}</Td>
                    <Td>{pessoa.tipo_display}</Td>
                    <Td>{formatarCpf(pessoa.cpf)}</Td>
                    <Td>{formatarData(pessoa.data_nascimento)}</Td>
                    <Td>{pessoa.email || "—"}</Td>
                    <Td>
                      <Badge tom={pessoa.ativo ? "sucesso" : "neutro"}>
                        {pessoa.ativo ? "Ativa" : "Inativa"}
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
        titulo="Nova pessoa"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-pessoa" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-pessoa" onSubmit={aoEnviar} className="grid gap-4">
          {erro && <ErroBox mensagem={erro} />}
          <Campo label="Nome" obrigatorio>
            {(id) => (
              <Input id={id} required value={nome} onChange={(e) => setNome(e.target.value)} />
            )}
          </Campo>
          <Campo label="CPF">
            {(id) => (
              <Input id={id} value={cpf} onChange={(e) => setCpf(e.target.value)} placeholder="000.000.000-00" />
            )}
          </Campo>
          <Campo label="E-mail">
            {(id) => (
              <Input id={id} type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            )}
          </Campo>
        </form>
      </Modal>
    </>
  );
}
