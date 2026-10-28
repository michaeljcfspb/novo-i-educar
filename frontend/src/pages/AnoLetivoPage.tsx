import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, Plus } from "lucide-react";

import { api, ApiError, type AnoLetivo, type Calendario, type Instituicao } from "@/lib/api";
import { formatarData } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

export function AnoLetivoPage() {
  const clienteQuery = useQueryClient();
  const [anoSelecionado, setAnoSelecionado] = useState("");
  const [modalAno, setModalAno] = useState(false);
  const [modalCalendario, setModalCalendario] = useState(false);
  const [instituicao, setInstituicao] = useState("");
  const [ano, setAno] = useState(String(new Date().getFullYear() + 1));
  const [inicio, setInicio] = useState("");
  const [fim, setFim] = useState("");
  const [nomeCalendario, setNomeCalendario] = useState("Calendário escolar");
  const [erro, setErro] = useState<string | null>(null);

  const anos = useQuery({
    queryKey: ["anos-letivos"],
    queryFn: () => api.listar<AnoLetivo>("anos-letivos", { page_size: 50, ordering: "-ano" }),
  });
  const instituicoes = useQuery({
    queryKey: ["instituicoes", "opcoes"],
    queryFn: () => api.listar<Instituicao>("instituicoes", { page_size: 50 }),
  });
  const calendarios = useQuery({
    queryKey: ["calendarios", anoSelecionado],
    queryFn: () => api.listar<Calendario>("calendarios", { ano_letivo: anoSelecionado, page_size: 50 }),
    enabled: anoSelecionado !== "",
  });

  const criarAno = useMutation({
    mutationFn: () =>
      api.criar<AnoLetivo>("anos-letivos", {
        instituicao: Number(instituicao),
        ano: Number(ano),
        data_inicio: inicio,
        data_fim: fim,
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["anos-letivos"] });
      setModalAno(false);
      setErro(null);
    },
    onError: (falha) => setErro(falha instanceof ApiError ? falha.message : "Erro ao criar ano letivo."),
  });

  const criarCalendario = useMutation({
    mutationFn: () =>
      api.criar<Calendario>("calendarios", {
        ano_letivo: Number(anoSelecionado),
        nome: nomeCalendario,
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["calendarios"] });
      setModalCalendario(false);
      setErro(null);
    },
    onError: (falha) => setErro(falha instanceof ApiError ? falha.message : "Erro ao criar calendário."),
  });

  return (
    <>
      <PageHeader
        titulo="Ano letivo"
        descricao="Anos letivos e calendários escolares."
        acoes={
          <Button onClick={() => setModalAno(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Novo ano letivo
          </Button>
        }
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader titulo="Anos letivos" />
          {anos.isLoading && <Spinner />}
          {anos.isError && (
            <div className="p-4">
              <ErroBox mensagem="Não foi possível carregar os anos letivos." />
            </div>
          )}
          {anos.data && (
            <Table>
              <thead>
                <tr>
                  <Th>Ano</Th>
                  <Th>Instituição</Th>
                  <Th>Início</Th>
                  <Th>Término</Th>
                  <Th />
                </tr>
              </thead>
              <tbody>
                {anos.data.results.length === 0 && (
                  <EmptyRow colSpan={5} mensagem="Nenhum ano letivo cadastrado." />
                )}
                {anos.data.results.map((item) => (
                  <tr key={item.id} className={item.id === Number(anoSelecionado) ? "bg-brand-50/50" : ""}>
                    <Td className="font-semibold">{item.ano}</Td>
                    <Td>{item.instituicao_nome}</Td>
                    <Td>{formatarData(item.data_inicio)}</Td>
                    <Td>{formatarData(item.data_fim)}</Td>
                    <Td>
                      <Button variante="fantasma" tamanho="sm" onClick={() => setAnoSelecionado(String(item.id))}>
                        Calendários
                      </Button>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>

        <Card>
          <CardHeader
            titulo="Calendários"
            descricao={anoSelecionado ? "Dias letivos por calendário." : "Selecione um ano letivo."}
            acoes={
              <Button
                tamanho="sm"
                variante="secundario"
                onClick={() => setModalCalendario(true)}
                disabled={!anoSelecionado}
              >
                <CalendarDays className="h-4 w-4" aria-hidden />
                Novo calendário
              </Button>
            }
          />
          {!anoSelecionado && (
            <EmptyState titulo="Nenhum ano selecionado" descricao="Clique em “Calendários” na lista ao lado." />
          )}
          {anoSelecionado && calendarios.isLoading && <Spinner />}
          {anoSelecionado && calendarios.data && (
            <CardBody className="space-y-3">
              {calendarios.data.results.length === 0 && (
                <p className="text-sm text-slate-500">Nenhum calendário para este ano letivo.</p>
              )}
              {calendarios.data.results.map((calendario) => (
                <div
                  key={calendario.id}
                  className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">{calendario.nome}</p>
                    <p className="text-xs text-slate-500">
                      {calendario.escola ? "Calendário da escola" : "Calendário da rede"}
                    </p>
                  </div>
                  <Badge tom="info">{calendario.dias_letivos} dias letivos</Badge>
                </div>
              ))}
            </CardBody>
          )}
        </Card>
      </div>

      <Modal
        aberto={modalAno}
        titulo="Novo ano letivo"
        onFechar={() => setModalAno(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAno(false)}>
              Cancelar
            </Button>
            <Button form="form-ano" type="submit" carregando={criarAno.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form
          id="form-ano"
          onSubmit={(evento: FormEvent) => {
            evento.preventDefault();
            criarAno.mutate();
          }}
          className="grid gap-4 sm:grid-cols-2"
        >
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
          <Campo label="Ano" obrigatorio>
            {(id) => <Input id={id} type="number" required value={ano} onChange={(e) => setAno(e.target.value)} />}
          </Campo>
          <Campo label="Início" obrigatorio>
            {(id) => <Input id={id} type="date" required value={inicio} onChange={(e) => setInicio(e.target.value)} />}
          </Campo>
          <Campo label="Término" obrigatorio>
            {(id) => <Input id={id} type="date" required value={fim} onChange={(e) => setFim(e.target.value)} />}
          </Campo>
        </form>
      </Modal>

      <Modal
        aberto={modalCalendario}
        titulo="Novo calendário"
        onFechar={() => setModalCalendario(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalCalendario(false)}>
              Cancelar
            </Button>
            <Button form="form-calendario" type="submit" carregando={criarCalendario.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form
          id="form-calendario"
          onSubmit={(evento: FormEvent) => {
            evento.preventDefault();
            criarCalendario.mutate();
          }}
          className="grid gap-4"
        >
          {erro && <ErroBox mensagem={erro} />}
          <Campo label="Nome" obrigatorio>
            {(id) => (
              <Input id={id} required value={nomeCalendario} onChange={(e) => setNomeCalendario(e.target.value)} />
            )}
          </Campo>
        </form>
      </Modal>
    </>
  );
}
