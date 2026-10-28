import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";

import { API_URL, api, type AlunoRisco, type Escola, type Indicadores, type LinhaTurma } from "@/lib/api";
import { anosLetivos } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Select } from "@/components/ui/field";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

function Kpi({ rotulo, valor, detalhe }: { rotulo: string; valor: string; detalhe?: string }) {
  return (
    <Card>
      <div className="px-5 py-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">{rotulo}</p>
        <p className="mt-1 text-2xl font-semibold text-slate-900">{valor}</p>
        {detalhe && <p className="mt-1 text-xs text-slate-500">{detalhe}</p>}
      </div>
    </Card>
  );
}

export function IndicadoresPage() {
  const [ano, setAno] = useState(String(new Date().getFullYear()));
  const [escola, setEscola] = useState("");

  const escolas = useQuery({
    queryKey: ["escolas", "opcoes"],
    queryFn: () => api.listar<Escola>("escolas", { page_size: 200 }),
  });
  const indicadores = useQuery({
    queryKey: ["indicadores", ano, escola],
    queryFn: () => api.indicadores(Number(ano), escola ? Number(escola) : undefined),
  });
  const turmas = useQuery({
    queryKey: ["relatorio-turmas", ano, escola],
    queryFn: () => api.relatorioTurmas(Number(ano), escola ? Number(escola) : undefined),
  });
  const risco = useQuery({
    queryKey: ["alunos-risco", ano, escola],
    queryFn: () => api.alunosRisco(Number(ano), escola ? Number(escola) : undefined),
  });

  const dados: Indicadores | undefined = indicadores.data;
  const urlCsv = `${API_URL}/relatorios/turmas.csv?ano=${ano}${escola ? `&escola=${escola}` : ""}`;

  return (
    <>
      <PageHeader
        titulo="Indicadores"
        descricao="Aprovação, evasão, ocupação e frequência da rede."
        acoes={
          <a href={urlCsv} target="_blank" rel="noreferrer">
            <Button variante="secundario">
              <Download className="h-4 w-4" aria-hidden />
              Exportar CSV
            </Button>
          </a>
        }
      />

      <Card className="mb-4">
        <div className="grid gap-3 px-5 py-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Ano letivo</span>
            <Select value={ano} onChange={(e) => setAno(e.target.value)}>
              {anosLetivos().map((valor) => (
                <option key={valor} value={valor}>
                  {valor}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="font-medium text-slate-700">Escola</span>
            <Select value={escola} onChange={(e) => setEscola(e.target.value)}>
              <option value="">Toda a rede</option>
              {escolas.data?.results.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                </option>
              ))}
            </Select>
          </label>
        </div>
      </Card>

      {indicadores.isError && (
        <div className="mb-4">
          <ErroBox mensagem="Não foi possível carregar os indicadores." />
        </div>
      )}
      {indicadores.isLoading && <Spinner />}

      {dados && (
        <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi rotulo="Matrículas" valor={String(dados.total_matriculas)} detalhe={`${dados.matriculas_ativas} ativas`} />
          <Kpi rotulo="Taxa de aprovação" valor={`${dados.taxa_aprovacao}%`} detalhe={`${dados.turmas} turma(s)`} />
          <Kpi rotulo="Taxa de abandono" valor={`${dados.taxa_abandono}%`} detalhe={`${dados.taxa_transferencia}% transferidos`} />
          <Kpi rotulo="Média geral" valor={dados.media_geral.toFixed(1)} detalhe={`frequência ${dados.frequencia_media}%`} />
        </div>
      )}

      <Card className="mb-6">
        <CardHeader titulo="Ocupação por turma" descricao="Vagas preenchidas, média e frequência." />
        {turmas.isLoading && <Spinner />}
        {turmas.data && (
          <Table>
            <thead>
              <tr>
                <Th>Turma</Th>
                <Th>Escola</Th>
                <Th>Série</Th>
                <Th>Alunos</Th>
                <Th>Ocupação</Th>
                <Th>Média</Th>
                <Th>Frequência</Th>
              </tr>
            </thead>
            <tbody>
              {turmas.data.length === 0 && <EmptyRow colSpan={7} mensagem="Nenhuma turma no ano selecionado." />}
              {turmas.data.map((linha: LinhaTurma) => (
                <tr key={`${linha.escola}-${linha.turma}`}>
                  <Td className="font-medium text-slate-900">{linha.turma}</Td>
                  <Td>{linha.escola}</Td>
                  <Td>{linha.serie}</Td>
                  <Td>
                    {linha.alunos}/{linha.capacidade}
                  </Td>
                  <Td>
                    <Badge tom={linha.ocupacao >= 80 ? "sucesso" : linha.ocupacao >= 50 ? "info" : "atencao"}>
                      {linha.ocupacao}%
                    </Badge>
                  </Td>
                  <Td>{linha.media.toFixed(1)}</Td>
                  <Td>{linha.frequencia}%</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <Card>
        <CardHeader titulo="Alunos em risco" descricao="Frequência abaixo de 75% ou média abaixo de 6." />
        {risco.isLoading && <Spinner />}
        {risco.data && (
          <Table>
            <thead>
              <tr>
                <Th>Aluno</Th>
                <Th>Escola</Th>
                <Th>Série</Th>
                <Th>Frequência</Th>
                <Th>Média</Th>
                <Th>Motivo</Th>
              </tr>
            </thead>
            <tbody>
              {risco.data.length === 0 && <EmptyRow colSpan={6} mensagem="Nenhum aluno em risco." />}
              {risco.data.map((item: AlunoRisco) => (
                <tr key={item.matricula}>
                  <Td className="font-medium text-slate-900">{item.aluno}</Td>
                  <Td>{item.escola}</Td>
                  <Td>{item.serie}</Td>
                  <Td>{item.frequencia}%</Td>
                  <Td>{item.media.toFixed(1)}</Td>
                  <Td>
                    <Badge tom="erro">{item.motivo}</Badge>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </>
  );
}
