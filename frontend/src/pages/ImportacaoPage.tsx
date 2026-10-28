import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";

import { api, ApiError, type Importacao } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const tons: Record<string, "sucesso" | "atencao" | "erro" | "info" | "neutro"> = {
  concluida: "sucesso",
  com_erros: "atencao",
  falhou: "erro",
  processando: "info",
};

export function ImportacaoPage() {
  const clienteQuery = useQueryClient();
  const entrada = useRef<HTMLInputElement>(null);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [resultado, setResultado] = useState<Importacao | null>(null);

  const importacoes = useQuery({
    queryKey: ["importacoes"],
    queryFn: () => api.listar<Importacao>("importacoes", { page_size: 30 }),
  });

  const enviar = useMutation({
    mutationFn: (file: File) => api.importarAlunos(file),
    onSuccess: async (dados) => {
      await clienteQuery.invalidateQueries({ queryKey: ["importacoes"] });
      setResultado(dados);
      setArquivo(null);
      setErro(null);
      if (entrada.current) entrada.current.value = "";
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao importar o arquivo."),
  });

  return (
    <>
      <PageHeader
        titulo="Importação de alunos"
        descricao="Planilha CSV com nome, CPF, data de nascimento, sexo, e-mail e telefone."
      />

      <Card className="mb-4">
        <CardHeader
          titulo="Enviar arquivo"
          descricao="Separador vírgula ou ponto e vírgula; codificação UTF-8. A primeira linha deve conter o cabeçalho."
        />
        <CardBody className="space-y-3">
          <input
            ref={entrada}
            type="file"
            accept=".csv,text/csv"
            className="block w-full cursor-pointer rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            onChange={(evento) => setArquivo(evento.target.files?.[0] ?? null)}
            aria-label="Arquivo CSV"
          />
          <div className="flex items-center gap-2">
            <Button
              onClick={() => arquivo && enviar.mutate(arquivo)}
              disabled={!arquivo}
              carregando={enviar.isPending}
            >
              <Upload className="h-4 w-4" aria-hidden />
              Importar
            </Button>
            <span className="text-xs text-slate-500">
              {arquivo ? arquivo.name : "Nenhum arquivo selecionado"}
            </span>
          </div>
          {erro && <ErroBox mensagem={erro} />}
        </CardBody>
      </Card>

      {resultado && (
        <Card className="mb-4">
          <CardHeader
            titulo={`Resultado: ${resultado.arquivo_nome}`}
            descricao={`${resultado.total_linhas} linha(s) · ${resultado.total_sucessos} importada(s) · ${resultado.total_erros} com erro`}
            acoes={<Badge tom={tons[resultado.status] ?? "neutro"}>{resultado.status_display}</Badge>}
          />
          {resultado.relatorio.length > 0 && (
            <Table>
              <thead>
                <tr>
                  <Th>Linha</Th>
                  <Th>Nome</Th>
                  <Th>Erros</Th>
                </tr>
              </thead>
              <tbody>
                {resultado.relatorio.map((item) => (
                  <tr key={item.linha}>
                    <Td>{item.linha}</Td>
                    <Td>{item.nome ?? "—"}</Td>
                    <Td className="text-red-700">{item.erros.join(" ")}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      )}

      <Card>
        <CardHeader titulo="Histórico de importações" />
        {importacoes.isLoading && <Spinner />}
        {importacoes.data && (
          <Table>
            <thead>
              <tr>
                <Th>Arquivo</Th>
                <Th>Status</Th>
                <Th>Linhas</Th>
                <Th>Sucessos</Th>
                <Th>Erros</Th>
                <Th>Data</Th>
              </tr>
            </thead>
            <tbody>
              {importacoes.data.results.length === 0 && (
                <EmptyRow colSpan={6} mensagem="Nenhuma importação realizada." />
              )}
              {importacoes.data.results.map((item) => (
                <tr key={item.id}>
                  <Td className="font-medium text-slate-900">{item.arquivo_nome}</Td>
                  <Td>
                    <Badge tom={tons[item.status] ?? "neutro"}>{item.status_display}</Badge>
                  </Td>
                  <Td>{item.total_linhas}</Td>
                  <Td>{item.total_sucessos}</Td>
                  <Td>{item.total_erros}</Td>
                  <Td>{new Date(item.criado_em).toLocaleString("pt-BR")}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}
