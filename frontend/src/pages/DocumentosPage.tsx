import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Plus } from "lucide-react";

import { api, ApiError, type Aluno, type Documento, type Matricula } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Select } from "@/components/ui/field";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const TIPOS = [
  { valor: "declaracao_matricula", rotulo: "Declaração de matrícula" },
  { valor: "declaracao_frequencia", rotulo: "Declaração de frequência" },
  { valor: "declaracao_conclusao", rotulo: "Declaração de conclusão" },
  { valor: "historico_escolar", rotulo: "Histórico escolar" },
  { valor: "transferencia", rotulo: "Guia de transferência" },
];

export function DocumentosPage() {
  const clienteQuery = useQueryClient();
  const [modalAberto, setModalAberto] = useState(false);
  const [aluno, setAluno] = useState("");
  const [matricula, setMatricula] = useState("");
  const [tipo, setTipo] = useState("declaracao_matricula");
  const [erro, setErro] = useState<string | null>(null);
  const [visualizando, setVisualizando] = useState<Documento | null>(null);

  const documentos = useQuery({
    queryKey: ["documentos"],
    queryFn: () => api.listar<Documento>("documentos", { page_size: 50 }),
  });
  const alunos = useQuery({
    queryKey: ["alunos", "opcoes"],
    queryFn: () => api.listar<Aluno>("alunos", { page_size: 200 }),
  });
  const matriculas = useQuery({
    queryKey: ["matriculas", "documento"],
    queryFn: () => api.listar<Matricula>("matriculas", { page_size: 200, ordering: "-ano" }),
  });

  const emitir = useMutation({
    mutationFn: () =>
      api.emitirDocumento(Number(aluno), tipo, matricula ? Number(matricula) : undefined),
    onSuccess: async (documento) => {
      await clienteQuery.invalidateQueries({ queryKey: ["documentos"] });
      setModalAberto(false);
      setErro(null);
      setVisualizando(documento);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao emitir o documento."),
  });

  return (
    <>
      <PageHeader
        titulo="Documentos"
        descricao="Declarações, históricos e guias de transferência."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Emitir documento
          </Button>
        }
      />

      <Card>
        {documentos.isLoading && <Spinner />}
        {documentos.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar os documentos." />
          </div>
        )}
        {documentos.data && (
          <Table>
            <thead>
              <tr>
                <Th>Número</Th>
                <Th>Tipo</Th>
                <Th>Aluno</Th>
                <Th>Emitido em</Th>
                <Th />
              </tr>
            </thead>
            <tbody>
              {documentos.data.results.length === 0 && (
                <EmptyRow colSpan={5} mensagem="Nenhum documento emitido." />
              )}
              {documentos.data.results.map((documento) => (
                <tr key={documento.id}>
                  <Td className="font-mono text-xs">{documento.numero}</Td>
                  <Td>
                    <Badge tom="info">{documento.tipo_display}</Badge>
                  </Td>
                  <Td className="font-medium text-slate-900">{documento.aluno_nome}</Td>
                  <Td>{new Date(documento.emitido_em).toLocaleString("pt-BR")}</Td>
                  <Td>
                    <Button variante="fantasma" tamanho="sm" onClick={() => setVisualizando(documento)}>
                      <FileText className="h-4 w-4" aria-hidden />
                      Ver
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
        titulo="Emitir documento"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-documento" type="submit" carregando={emitir.isPending}>
              Emitir
            </Button>
          </>
        }
      >
        <form
          id="form-documento"
          onSubmit={(evento: FormEvent) => {
            evento.preventDefault();
            emitir.mutate();
          }}
          className="grid gap-4"
        >
          {erro && <ErroBox mensagem={erro} />}
          <Campo label="Aluno" obrigatorio>
            {(id) => (
              <Select id={id} required value={aluno} onChange={(e) => setAluno(e.target.value)}>
                <option value="">Selecione…</option>
                {alunos.data?.results.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nome} ({item.codigo})
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <Campo label="Matrícula" ajuda="Opcional; usada para dados de escola, série e frequência.">
            {(id) => (
              <Select id={id} value={matricula} onChange={(e) => setMatricula(e.target.value)}>
                <option value="">Não vincular</option>
                {matriculas.data?.results.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.aluno_nome} · {item.ano}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <Campo label="Tipo" obrigatorio>
            {(id) => (
              <Select id={id} value={tipo} onChange={(e) => setTipo(e.target.value)}>
                {TIPOS.map((item) => (
                  <option key={item.valor} value={item.valor}>
                    {item.rotulo}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
        </form>
      </Modal>

      <Modal
        aberto={visualizando !== null}
        titulo={visualizando?.titulo ?? ""}
        onFechar={() => setVisualizando(null)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => window.print()}>
              Imprimir
            </Button>
            <Button onClick={() => setVisualizando(null)}>Fechar</Button>
          </>
        }
      >
        {visualizando && (
          <article className="space-y-4">
            <p className="text-xs text-slate-500">
              Documento nº <span className="font-mono">{visualizando.numero}</span>
            </p>
            <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
              {visualizando.corpo}
            </p>
          </article>
        )}
      </Modal>
    </>
  );
}
