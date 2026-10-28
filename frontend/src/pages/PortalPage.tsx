import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

export function PortalPage() {
  const perfil = useQuery({ queryKey: ["portal", "perfil"], queryFn: () => api.portalPerfil() });
  const boletim = useQuery({
    queryKey: ["portal", "boletim"],
    queryFn: () => api.portalBoletim(),
    retry: false,
  });
  const frequencia = useQuery({
    queryKey: ["portal", "frequencia"],
    queryFn: () => api.portalFrequencia(),
    retry: false,
  });
  const documentos = useQuery({
    queryKey: ["portal", "documentos"],
    queryFn: () => api.portalDocumentos(),
    retry: false,
  });

  const semVinculo = perfil.isError;
  const periodos = Array.from(
    new Set((boletim.data?.disciplinas ?? []).flatMap((disciplina) => Object.keys(disciplina.notas))),
  );

  return (
    <>
      <PageHeader titulo="Meu portal" descricao="Notas, frequência e documentos do aluno." />

      {semVinculo && (
        <ErroBox mensagem="Seu usuário não está vinculado a um aluno. Peça à secretaria para vincular seu login ao cadastro do aluno." />
      )}

      {perfil.isLoading && <Spinner />}

      {perfil.data && (
        <>
          <Card className="mb-4">
            <CardBody className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-lg font-semibold text-slate-900">{perfil.data.aluno}</p>
                <p className="text-sm text-slate-500">Código {perfil.data.codigo}</p>
              </div>
              <div className="flex gap-2">
                {perfil.data.matriculas.map((matricula) => (
                  <Badge key={matricula.id} tom="info">
                    {matricula.ano} · {matricula.serie}
                  </Badge>
                ))}
              </div>
            </CardBody>
          </Card>

          {frequencia.data && (
            <div className="mb-4 grid gap-4 sm:grid-cols-3">
              <Card>
                <CardBody>
                  <p className="text-xs uppercase text-slate-500">Frequência</p>
                  <p className="text-2xl font-semibold">{frequencia.data.percentual.toFixed(1)}%</p>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <p className="text-xs uppercase text-slate-500">Presenças</p>
                  <p className="text-2xl font-semibold">{frequencia.data.presencas}</p>
                </CardBody>
              </Card>
              <Card>
                <CardBody>
                  <p className="text-xs uppercase text-slate-500">Faltas</p>
                  <p className="text-2xl font-semibold">{frequencia.data.faltas}</p>
                </CardBody>
              </Card>
            </div>
          )}

          {boletim.data && (
            <Card className="mb-4">
              <CardHeader
                titulo="Boletim"
                descricao={`${boletim.data.turma ?? "Sem turma"} · média ${boletim.data.media_geral.toFixed(1)}`}
                acoes={
                  <Badge tom={boletim.data.situacao_final === "aprovado" ? "sucesso" : "atencao"}>
                    {boletim.data.situacao_final.replace("_", " ")}
                  </Badge>
                }
              />
              <Table>
                <thead>
                  <tr>
                    <Th>Disciplina</Th>
                    {periodos.map((periodo) => (
                      <Th key={periodo}>{periodo}</Th>
                    ))}
                    <Th>Média</Th>
                  </tr>
                </thead>
                <tbody>
                  {boletim.data.disciplinas.length === 0 && (
                    <EmptyRow colSpan={periodos.length + 2} mensagem="Sem notas lançadas." />
                  )}
                  {boletim.data.disciplinas.map((disciplina) => (
                    <tr key={disciplina.turma_disciplina}>
                      <Td className="font-medium text-slate-900">{disciplina.disciplina}</Td>
                      {periodos.map((periodo) => (
                        <Td key={periodo}>{disciplina.notas[periodo] ?? "—"}</Td>
                      ))}
                      <Td className="font-semibold">{disciplina.media.toFixed(1)}</Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card>
          )}

          <Card>
            <CardHeader titulo="Documentos" descricao="Declarações e históricos emitidos." />
            {documentos.data && documentos.data.length === 0 && (
              <CardBody className="text-sm text-slate-500">Nenhum documento emitido.</CardBody>
            )}
            {documentos.data && documentos.data.length > 0 && (
              <Table>
                <thead>
                  <tr>
                    <Th>Número</Th>
                    <Th>Tipo</Th>
                    <Th>Emitido em</Th>
                  </tr>
                </thead>
                <tbody>
                  {documentos.data.map((documento) => (
                    <tr key={documento.id}>
                      <Td className="font-mono text-xs">{documento.numero}</Td>
                      <Td>
                        <span className="inline-flex items-center gap-2">
                          <FileText className="h-4 w-4 text-slate-400" aria-hidden />
                          {documento.tipo_display}
                        </span>
                      </Td>
                      <Td>{new Date(documento.emitido_em).toLocaleDateString("pt-BR")}</Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>
        </>
      )}
    </>
  );
}
