import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";

import { api, ApiError, type Aluno } from "@/lib/api";
import { formatarCpf, formatarData } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { Table, Td, Th } from "@/components/ui/table";

const POR_PAGINA = 10;

interface Formulario {
  nome: string;
  cpf: string;
  data_nascimento: string;
  sexo: string;
  nome_mae: string;
  telefone: string;
}

const formularioInicial: Formulario = {
  nome: "",
  cpf: "",
  data_nascimento: "",
  sexo: "",
  nome_mae: "",
  telefone: "",
};

export function AlunosPage() {
  const clienteQuery = useQueryClient();
  const [busca, setBusca] = useState("");
  const [pagina, setPagina] = useState(1);
  const [modalAberto, setModalAberto] = useState(false);
  const [formulario, setFormulario] = useState<Formulario>(formularioInicial);
  const [erroFormulario, setErroFormulario] = useState<string | null>(null);

  const alunos = useQuery({
    queryKey: ["alunos", busca, pagina],
    queryFn: () =>
      api.listar<Aluno>("alunos", {
        page: pagina,
        page_size: POR_PAGINA,
        search: busca || undefined,
      }),
  });

  const criar = useMutation({
    mutationFn: (dados: Formulario) =>
      api.criar<Aluno>("alunos", {
        pessoa: {
          nome: dados.nome,
          cpf: dados.cpf || null,
          data_nascimento: dados.data_nascimento || null,
          sexo: dados.sexo || "",
          nome_mae: dados.nome_mae,
          telefone: dados.telefone,
        },
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["alunos"] });
      await clienteQuery.invalidateQueries({ queryKey: ["contagens"] });
      setModalAberto(false);
      setFormulario(formularioInicial);
      setErroFormulario(null);
    },
    onError: (erro) => {
      setErroFormulario(erro instanceof ApiError ? erro.message : "Erro ao salvar o aluno.");
    },
  });

  function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    setErroFormulario(null);
    criar.mutate(formulario);
  }

  const totalPaginas = alunos.data ? Math.ceil(alunos.data.count / POR_PAGINA) : 1;

  return (
    <>
      <PageHeader
        titulo="Alunos"
        descricao="Cadastro de estudantes da rede."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Novo aluno
          </Button>
        }
      />

      <Card>
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 px-4 py-3">
          <div className="relative min-w-64 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <Input
              className="pl-9"
              placeholder="Buscar por nome, código ou CPF"
              aria-label="Buscar alunos"
              value={busca}
              onChange={(evento) => {
                setBusca(evento.target.value);
                setPagina(1);
              }}
            />
          </div>
          <span className="text-xs text-slate-500">
            {alunos.data ? `${alunos.data.count} registro(s)` : ""}
          </span>
        </div>

        {alunos.isLoading && <Spinner />}
        {alunos.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar os alunos." />
          </div>
        )}

        {alunos.data && alunos.data.results.length === 0 && busca === "" && (
          <EmptyState
            titulo="Nenhum aluno cadastrado"
            descricao="Comece cadastrando o primeiro estudante da rede."
            acao={<Button className="mt-2" onClick={() => setModalAberto(true)}>Cadastrar aluno</Button>}
          />
        )}

        {alunos.data && alunos.data.results.length > 0 && (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Código</Th>
                  <Th>Nome</Th>
                  <Th>CPF</Th>
                  <Th>Nascimento</Th>
                  <Th>Deficiências</Th>
                  <Th>Situação</Th>
                </tr>
              </thead>
              <tbody>
                {alunos.data.results.map((aluno) => (
                  <tr key={aluno.id}>
                    <Td className="font-mono text-xs">{aluno.codigo}</Td>
                    <Td className="font-medium text-slate-900">{aluno.nome}</Td>
                    <Td>{formatarCpf(aluno.pessoa.cpf)}</Td>
                    <Td>{formatarData(aluno.pessoa.data_nascimento)}</Td>
                    <Td>
                      {aluno.deficiencias_detalhe.length > 0
                        ? aluno.deficiencias_detalhe.map((d) => d.nome).join(", ")
                        : "—"}
                    </Td>
                    <Td>
                      <Badge tom={aluno.ativo ? "sucesso" : "neutro"}>
                        {aluno.ativo ? "Ativo" : "Inativo"}
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
        titulo="Novo aluno"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-aluno" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-aluno" onSubmit={aoEnviar} className="grid gap-4 sm:grid-cols-2">
          {erroFormulario && (
            <div className="sm:col-span-2">
              <ErroBox mensagem={erroFormulario} />
            </div>
          )}
          <div className="sm:col-span-2">
            <Campo label="Nome completo" obrigatorio>
              {(id) => (
                <Input
                  id={id}
                  required
                  minLength={3}
                  value={formulario.nome}
                  onChange={(e) => setFormulario({ ...formulario, nome: e.target.value })}
                />
              )}
            </Campo>
          </div>
          <Campo label="CPF" ajuda="Opcional, mas único no sistema.">
            {(id) => (
              <Input
                id={id}
                inputMode="numeric"
                placeholder="000.000.000-00"
                value={formulario.cpf}
                onChange={(e) => setFormulario({ ...formulario, cpf: e.target.value })}
              />
            )}
          </Campo>
          <Campo label="Data de nascimento">
            {(id) => (
              <Input
                id={id}
                type="date"
                value={formulario.data_nascimento}
                onChange={(e) =>
                  setFormulario({ ...formulario, data_nascimento: e.target.value })
                }
              />
            )}
          </Campo>
          <Campo label="Sexo">
            {(id) => (
              <Select
                id={id}
                value={formulario.sexo}
                onChange={(e) => setFormulario({ ...formulario, sexo: e.target.value })}
              >
                <option value="">Não informado</option>
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
              </Select>
            )}
          </Campo>
          <Campo label="Telefone">
            {(id) => (
              <Input
                id={id}
                value={formulario.telefone}
                onChange={(e) => setFormulario({ ...formulario, telefone: e.target.value })}
              />
            )}
          </Campo>
          <div className="sm:col-span-2">
            <Campo label="Nome da mãe">
              {(id) => (
                <Input
                  id={id}
                  value={formulario.nome_mae}
                  onChange={(e) => setFormulario({ ...formulario, nome_mae: e.target.value })}
                />
              )}
            </Campo>
          </div>
        </form>
      </Modal>
    </>
  );
}
