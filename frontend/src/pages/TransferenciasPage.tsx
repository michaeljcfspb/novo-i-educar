import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRightLeft, Plus } from "lucide-react";

import { api, ApiError, type Escola, type Matricula, type Transferencia } from "@/lib/api";
import { formatarData } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select, Textarea } from "@/components/ui/field";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const MOTIVOS = [
  { valor: "mudanca_endereco", rotulo: "Mudança de endereço" },
  { valor: "pedido_responsavel", rotulo: "Pedido do responsável" },
  { valor: "saude", rotulo: "Motivo de saúde" },
  { valor: "transferencia_escola", rotulo: "Transferência de escola" },
  { valor: "outro", rotulo: "Outro" },
];

export function TransferenciasPage() {
  const clienteQuery = useQueryClient();
  const [modalAberto, setModalAberto] = useState(false);
  const [matricula, setMatricula] = useState("");
  const [tipo, setTipo] = useState("saida");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [destino, setDestino] = useState("");
  const [motivo, setMotivo] = useState("pedido_responsavel");
  const [observacao, setObservacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  const transferencias = useQuery({
    queryKey: ["transferencias"],
    queryFn: () => api.listar<Transferencia>("transferencias", { page_size: 50 }),
  });
  const matriculas = useQuery({
    queryKey: ["matriculas", "transferencia"],
    queryFn: () => api.listar<Matricula>("matriculas", { page_size: 200, ordering: "-ano" }),
  });
  const escolas = useQuery({
    queryKey: ["escolas", "opcoes"],
    queryFn: () => api.listar<Escola>("escolas", { page_size: 200 }),
  });

  const criar = useMutation({
    mutationFn: () =>
      api.criar<Transferencia>("transferencias", {
        matricula: Number(matricula),
        tipo,
        data,
        escola_destino: destino ? Number(destino) : null,
        motivo,
        observacao,
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["transferencias"] });
      await clienteQuery.invalidateQueries({ queryKey: ["matriculas"] });
      setModalAberto(false);
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao registrar a transferência."),
  });

  return (
    <>
      <PageHeader
        titulo="Transferências"
        descricao="Entradas, saídas e movimentações internas de alunos."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Nova transferência
          </Button>
        }
      />

      <Card>
        {transferencias.isLoading && <Spinner />}
        {transferencias.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar as transferências." />
          </div>
        )}
        {transferencias.data && (
          <Table>
            <thead>
              <tr>
                <Th>Aluno</Th>
                <Th>Tipo</Th>
                <Th>Data</Th>
                <Th>Origem</Th>
                <Th>Destino</Th>
                <Th>Motivo</Th>
              </tr>
            </thead>
            <tbody>
              {transferencias.data.results.length === 0 && (
                <EmptyRow colSpan={6} mensagem="Nenhuma transferência registrada." />
              )}
              {transferencias.data.results.map((item) => (
                <tr key={item.id}>
                  <Td className="font-medium text-slate-900">{item.aluno_nome}</Td>
                  <Td>
                    <Badge tom={item.tipo === "saida" ? "atencao" : "info"}>{item.tipo_display}</Badge>
                  </Td>
                  <Td>{formatarData(item.data)}</Td>
                  <Td>{item.escola_origem_nome ?? "—"}</Td>
                  <Td>{item.escola_destino_nome ?? "—"}</Td>
                  <Td className="capitalize">{item.motivo.replace(/_/g, " ")}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Modal
        aberto={modalAberto}
        titulo="Nova transferência"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-transferencia" type="submit" carregando={criar.isPending}>
              <ArrowRightLeft className="h-4 w-4" aria-hidden />
              Registrar
            </Button>
          </>
        }
      >
        <form
          id="form-transferencia"
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
            <Campo label="Matrícula" obrigatorio ajuda="A saída encerra a matrícula e a enturmação.">
              {(id) => (
                <Select id={id} required value={matricula} onChange={(e) => setMatricula(e.target.value)}>
                  <option value="">Selecione…</option>
                  {matriculas.data?.results.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.aluno_nome} · {item.escola_nome} · {item.ano}
                    </option>
                  ))}
                </Select>
              )}
            </Campo>
          </div>
          <Campo label="Tipo" obrigatorio>
            {(id) => (
              <Select id={id} value={tipo} onChange={(e) => setTipo(e.target.value)}>
                <option value="saida">Saída</option>
                <option value="entrada">Entrada</option>
                <option value="interna">Interna</option>
              </Select>
            )}
          </Campo>
          <Campo label="Data" obrigatorio>
            {(id) => <Input id={id} type="date" required value={data} onChange={(e) => setData(e.target.value)} />}
          </Campo>
          <div className="sm:col-span-2">
            <Campo label="Escola de destino">
              {(id) => (
                <Select id={id} value={destino} onChange={(e) => setDestino(e.target.value)}>
                  <option value="">Não se aplica</option>
                  {escolas.data?.results.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome}
                    </option>
                  ))}
                </Select>
              )}
            </Campo>
          </div>
          <Campo label="Motivo">
            {(id) => (
              <Select id={id} value={motivo} onChange={(e) => setMotivo(e.target.value)}>
                {MOTIVOS.map((item) => (
                  <option key={item.valor} value={item.valor}>
                    {item.rotulo}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <div className="sm:col-span-2">
            <Campo label="Observação">
              {(id) => (
                <Textarea id={id} value={observacao} onChange={(e) => setObservacao(e.target.value)} />
              )}
            </Campo>
          </div>
        </form>
      </Modal>
    </>
  );
}
