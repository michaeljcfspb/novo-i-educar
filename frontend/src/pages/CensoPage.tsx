import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Download } from "lucide-react";

import { api, ApiError, type Escola, type ExportacaoCenso, type PendenciaCenso } from "@/lib/api";
import { anosLetivos } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Select } from "@/components/ui/field";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const tons: Record<string, "sucesso" | "atencao" | "erro" | "info" | "neutro"> = {
  gerado: "atencao",
  validado: "sucesso",
  enviado: "info",
};

export function CensoPage() {
  const clienteQuery = useQueryClient();
  const [escolaId, setEscolaId] = useState("");
  const [ano, setAno] = useState(String(new Date().getFullYear()));
  const [pendencias, setPendencias] = useState<PendenciaCenso[] | null>(null);
  const [totais, setTotais] = useState<{ turmas: number; alunos: number; profissionais: number } | null>(null);
  const [detalhe, setDetalhe] = useState<ExportacaoCenso | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const escolas = useQuery({
    queryKey: ["escolas", "opcoes"],
    queryFn: () => api.listar<Escola>("escolas", { page_size: 200 }),
  });
  const exportacoes = useQuery({
    queryKey: ["censo", escolaId],
    queryFn: () =>
      api.listar<ExportacaoCenso>("censo/exportacoes", {
        escola: escolaId || undefined,
        page_size: 50,
      }),
  });

  const preview = useMutation({
    mutationFn: () => api.previewCenso(Number(escolaId), Number(ano)),
    onSuccess: (dados) => {
      setPendencias(dados.pendencias);
      setTotais(dados.totais);
      setErro(null);
    },
    onError: (falha) => setErro(falha instanceof ApiError ? falha.message : "Erro na pré-visualização."),
  });

  const gerar = useMutation({
    mutationFn: () => api.gerarCenso(Number(escolaId), Number(ano)),
    onSuccess: async (dados) => {
      await clienteQuery.invalidateQueries({ queryKey: ["censo"] });
      setDetalhe(dados);
      setPendencias(dados.pendencias);
      setErro(null);
    },
    onError: (falha) => setErro(falha instanceof ApiError ? falha.message : "Erro ao gerar exportação."),
  });

  return (
    <>
      <PageHeader
        titulo="Censo escolar"
        descricao="Exportação INEP por escola e ano, com validação de pendências."
      />

      <Card className="mb-4">
        <CardBody className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-72 flex-1 flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Escola</span>
            <Select value={escolaId} onChange={(e) => setEscolaId(e.target.value)}>
              <option value="">Todas as escolas</option>
              {escolas.data?.results.map((escola) => (
                <option key={escola.id} value={escola.id}>
                  {escola.nome} — INEP {escola.codigo_inep || "não informado"}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex w-32 flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Ano</span>
            <Select value={ano} onChange={(e) => setAno(e.target.value)}>
              {anosLetivos().map((valor) => (
                <option key={valor} value={valor}>
                  {valor}
                </option>
              ))}
            </Select>
          </label>
          <Button
            variante="secundario"
            onClick={() => preview.mutate()}
            disabled={!escolaId}
            carregando={preview.isPending}
          >
            Pré-visualizar
          </Button>
          <Button onClick={() => gerar.mutate()} disabled={!escolaId} carregando={gerar.isPending}>
            <Download className="h-4 w-4" aria-hidden />
            Gerar exportação
          </Button>
        </CardBody>
      </Card>

      {erro && (
        <div className="mb-4">
          <ErroBox mensagem={erro} />
        </div>
      )}

      {(totais || pendencias) && (
        <Card className="mb-4">
          <CardHeader
            titulo="Validação"
            descricao={totais ? `${totais.turmas} turma(s) · ${totais.alunos} aluno(s) · ${totais.profissionais} profissional(is)` : undefined}
            acoes={
              <Badge tom={pendencias && pendencias.length ? "atencao" : "sucesso"}>
                {pendencias && pendencias.length ? `${pendencias.length} pendência(s)` : "Sem pendências"}
              </Badge>
            }
          />
          {pendencias && pendencias.length > 0 ? (
            <Table>
              <thead>
                <tr>
                  <Th>Entidade</Th>
                  <Th>Registro</Th>
                  <Th>Campo</Th>
                  <Th>Mensagem</Th>
                </tr>
              </thead>
              <tbody>
                {pendencias.map((item, indice) => (
                  <tr key={`${item.entidade}-${indice}`}>
                    <Td className="capitalize">{item.entidade}</Td>
                    <Td>{item.identificador}</Td>
                    <Td className="font-mono text-xs">{item.campo}</Td>
                    <Td>{item.mensagem}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <CardBody className="flex items-center gap-2 text-sm text-emerald-700">
              <AlertTriangle className="h-4 w-4" aria-hidden />
              Todos os códigos obrigatórios estão preenchidos.
            </CardBody>
          )}
        </Card>
      )}

      <Card>
        <CardHeader titulo="Exportações geradas" />
        {exportacoes.isLoading && <Spinner />}
        {exportacoes.data && (
          <Table>
            <thead>
              <tr>
                <Th>Escola</Th>
                <Th>Ano</Th>
                <Th>Versão</Th>
                <Th>Alunos</Th>
                <Th>Turmas</Th>
                <Th>Status</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {exportacoes.data.results.length === 0 && (
                <EmptyRow colSpan={7} mensagem="Nenhuma exportação gerada." />
              )}
              {exportacoes.data.results.map((item) => (
                <tr key={item.id}>
                  <Td className="font-medium text-slate-900">{item.escola_nome}</Td>
                  <Td>{item.ano}</Td>
                  <Td>v{item.versao}</Td>
                  <Td>{item.total_alunos}</Td>
                  <Td>{item.total_turmas}</Td>
                  <Td>
                    <Badge tom={tons[item.status] ?? "neutro"}>{item.status_display}</Badge>
                  </Td>
                  <Td>
                    <Button variante="fantasma" tamanho="sm" onClick={() => setDetalhe(item)}>
                      Ver payload
                    </Button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Modal
        aberto={detalhe !== null}
        titulo={`Exportação censo ${detalhe?.ano ?? ""} · v${detalhe?.versao ?? ""}`}
        onFechar={() => setDetalhe(null)}
        rodape={<Button onClick={() => setDetalhe(null)}>Fechar</Button>}
      >
        <pre className="max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
          {JSON.stringify(detalhe?.payload ?? {}, null, 2)}
        </pre>
      </Modal>
    </>
  );
}
