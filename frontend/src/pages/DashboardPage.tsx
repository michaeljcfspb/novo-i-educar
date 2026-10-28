import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { BookOpen, GraduationCap, School, Users } from "lucide-react";

import { api, type Aluno, type Matricula } from "@/lib/api";
import { formatarData } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { EmptyRow, Table, Td, Th } from "@/components/ui/table";

const atalhos = [
  { chave: "alunos", rotulo: "Alunos", icone: Users, cor: "bg-brand-50 text-brand-700" },
  { chave: "escolas", rotulo: "Escolas", icone: School, cor: "bg-emerald-50 text-emerald-700" },
  { chave: "turmas", rotulo: "Turmas", icone: BookOpen, cor: "bg-amber-50 text-amber-700" },
  { chave: "matriculas", rotulo: "Matrículas", icone: GraduationCap, cor: "bg-purple-50 text-purple-700" },
];

const tons: Record<string, "sucesso" | "atencao" | "erro" | "info" | "neutro"> = {
  cursando: "info",
  aprovado: "sucesso",
  reprovado: "erro",
  transferido: "atencao",
  abandonou: "erro",
  cancelada: "neutro",
  falecido: "neutro",
};

export function DashboardPage() {
  const contagens = useQuery({
    queryKey: ["contagens"],
    queryFn: async () => {
      const [alunos, escolas, turmas, matriculas] = await Promise.all([
        api.listar<Aluno>("alunos", { page_size: 1 }),
        api.listar("escolas", { page_size: 1 }),
        api.listar("turmas", { page_size: 1 }),
        api.listar<Matricula>("matriculas", { page_size: 1 }),
      ]);
      return {
        alunos: alunos.count,
        escolas: escolas.count,
        turmas: turmas.count,
        matriculas: matriculas.count,
      };
    },
  });

  const recentes = useQuery({
    queryKey: ["matriculas", "recentes"],
    queryFn: () => api.listar<Matricula>("matriculas", { page_size: 5, ordering: "-data_matricula" }),
  });

  return (
    <>
      <PageHeader
        titulo="Painel"
        descricao="Visão geral da rede escolar no ano corrente."
      />

      {contagens.isError && <ErroBox mensagem="Não foi possível carregar os indicadores." />}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {atalhos.map(({ chave, rotulo, icone: Icone, cor }) => (
          <Link key={chave} to={`/${chave}`} className="focus-ring rounded-xl">
            <Card className="transition-shadow hover:shadow-md">
              <CardBody className="flex items-center gap-4">
                <div className={`grid h-11 w-11 place-items-center rounded-lg ${cor}`}>
                  <Icone className="h-5 w-5" aria-hidden />
                </div>
                <div>
                  <p className="text-sm text-slate-500">{rotulo}</p>
                  <p className="text-2xl font-semibold text-slate-900">
                    {contagens.isLoading
                      ? "…"
                      : contagens.data
                        ? contagens.data[chave as keyof typeof contagens.data].toLocaleString("pt-BR")
                        : "—"}
                  </p>
                </div>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader
          titulo="Matrículas recentes"
          descricao="Últimos registros lançados no sistema."
          acoes={
            <Link to="/matriculas" className="text-sm font-medium text-brand-700 hover:underline">
              Ver todas
            </Link>
          }
        />
        {recentes.isLoading ? (
          <Spinner />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Aluno</Th>
                <Th>Escola</Th>
                <Th>Ano</Th>
                <Th>Data</Th>
                <Th>Situação</Th>
              </tr>
            </thead>
            <tbody>
              {recentes.data?.results.length === 0 && (
                <EmptyRow colSpan={5} mensagem="Nenhuma matrícula cadastrada ainda." />
              )}
              {recentes.data?.results.map((matricula) => (
                <tr key={matricula.id}>
                  <Td className="font-medium text-slate-900">{matricula.aluno_nome}</Td>
                  <Td>{matricula.escola_nome}</Td>
                  <Td>{matricula.ano}</Td>
                  <Td>{formatarData(matricula.data_matricula)}</Td>
                  <Td>
                    <Badge tom={tons[matricula.situacao] ?? "neutro"}>
                      {matricula.situacao_display}
                    </Badge>
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
