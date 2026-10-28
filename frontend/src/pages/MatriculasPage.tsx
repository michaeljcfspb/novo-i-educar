import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GraduationCap, Plus } from "lucide-react";

import { api, ApiError, type Aluno, type Escola, type Matricula, type Serie, type Turma } from "@/lib/api";
import { anosLetivos, formatarData } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Campo, Input, Select } from "@/components/ui/field";
import { EmptyState, ErroBox, PageHeader, Spinner } from "@/components/ui/feedback";
import { Modal } from "@/components/ui/modal";
import { Pagination } from "@/components/ui/pagination";
import { Table, Td, Th } from "@/components/ui/table";

const POR_PAGINA = 10;

const SITUACOES = [
  { valor: "cursando", rotulo: "Cursando" },
  { valor: "aprovado", rotulo: "Aprovado" },
  { valor: "reprovado", rotulo: "Reprovado" },
  { valor: "transferido", rotulo: "Transferido" },
  { valor: "abandonou", rotulo: "Abandonou" },
  { valor: "cancelada", rotulo: "Cancelada" },
];

export function MatriculasPage() {
  const clienteQuery = useQueryClient();
  const [ano, setAno] = useState(String(new Date().getFullYear()));
  const [situacao, setSituacao] = useState("");
  const [pagina, setPagina] = useState(1);
  const [modalAberto, setModalAberto] = useState(false);
  const [enturmarAberto, setEnturmarAberto] = useState<Matricula | null>(null);
  const [turmaSelecionada, setTurmaSelecionada] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [erroEnturmar, setErroEnturmar] = useState<string | null>(null);

  const [aluno, setAluno] = useState("");
  const [escola, setEscola] = useState("");
  const [serie, setSerie] = useState("");
  const [dataMatricula, setDataMatricula] = useState(new Date().toISOString().slice(0, 10));

  const matriculas = useQuery({
    queryKey: ["matriculas", ano, situacao, pagina],
    queryFn: () =>
      api.listar<Matricula>("matriculas", {
        page: pagina,
        page_size: POR_PAGINA,
        ano: ano || undefined,
        situacao: situacao || undefined,
      }),
  });

  const opcoesAlunos = useQuery({
    queryKey: ["alunos", "opcoes"],
    queryFn: () => api.listar<Aluno>("alunos", { page_size: 200 }),
  });
  const opcoesEscolas = useQuery({
    queryKey: ["escolas", "opcoes"],
    queryFn: () => api.listar<Escola>("escolas", { page_size: 200 }),
  });
  const opcoesSeries = useQuery({
    queryKey: ["series", "opcoes"],
    queryFn: () => api.listar<Serie>("series", { page_size: 200 }),
  });
  const opcoesTurmas = useQuery({
    queryKey: ["turmas", "opcoes"],
    queryFn: () => api.listar<Turma>("turmas", { page_size: 200, ano }),
  });

  const serieSelecionada = useMemo(
    () => opcoesSeries.data?.results.find((item) => String(item.id) === serie),
    [opcoesSeries.data, serie],
  );

  const turmasCompativeis = useMemo(() => {
    if (!enturmarAberto) return [];
    return (opcoesTurmas.data?.results ?? []).filter(
      (turma) =>
        turma.escola === enturmarAberto.escola &&
        turma.serie === enturmarAberto.serie &&
        turma.ano === enturmarAberto.ano &&
        turma.ativo &&
        turma.vagas_disponiveis > 0,
    );
  }, [opcoesTurmas.data, enturmarAberto]);

  const criar = useMutation({
    mutationFn: () =>
      api.criar<Matricula>("matriculas", {
        aluno: Number(aluno),
        escola: Number(escola),
        serie: Number(serie),
        curso: serieSelecionada?.curso,
        ano: Number(ano),
        data_matricula: dataMatricula,
      }),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["matriculas"] });
      await clienteQuery.invalidateQueries({ queryKey: ["contagens"] });
      setModalAberto(false);
      setAluno("");
      setErro(null);
    },
    onError: (falha) =>
      setErro(falha instanceof ApiError ? falha.message : "Erro ao criar a matrícula."),
  });

  const enturmar = useMutation({
    mutationFn: () => api.enturmar(enturmarAberto!.id, Number(turmaSelecionada)),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["matriculas"] });
      await clienteQuery.invalidateQueries({ queryKey: ["turmas"] });
      setEnturmarAberto(null);
      setTurmaSelecionada("");
      setErroEnturmar(null);
    },
    onError: (falha) =>
      setErroEnturmar(falha instanceof ApiError ? falha.message : "Erro ao enturmar."),
  });

  const alterarSituacao = useMutation({
    mutationFn: ({ id, valor }: { id: number; valor: string }) => api.alterarSituacao(id, valor),
    onSuccess: async () => {
      await clienteQuery.invalidateQueries({ queryKey: ["matriculas"] });
      await clienteQuery.invalidateQueries({ queryKey: ["contagens"] });
    },
  });

  const totalPaginas = matriculas.data ? Math.ceil(matriculas.data.count / POR_PAGINA) : 1;

  return (
    <>
      <PageHeader
        titulo="Matrículas"
        descricao="Vínculo do aluno com escola, série e turma."
        acoes={
          <Button onClick={() => setModalAberto(true)}>
            <Plus className="h-4 w-4" aria-hidden />
            Nova matrícula
          </Button>
        }
      />

      <Card>
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-4 py-3">
          <label className="text-sm text-slate-600" htmlFor="filtro-ano-matricula">
            Ano
          </label>
          <Select
            id="filtro-ano-matricula"
            className="w-32"
            value={ano}
            onChange={(evento) => {
              setAno(evento.target.value);
              setPagina(1);
            }}
          >
            <option value="">Todos</option>
            {anosLetivos().map((valor) => (
              <option key={valor} value={valor}>
                {valor}
              </option>
            ))}
          </Select>

          <label className="text-sm text-slate-600" htmlFor="filtro-situacao">
            Situação
          </label>
          <Select
            id="filtro-situacao"
            className="w-40"
            value={situacao}
            onChange={(evento) => {
              setSituacao(evento.target.value);
              setPagina(1);
            }}
          >
            <option value="">Todas</option>
            {SITUACOES.map((item) => (
              <option key={item.valor} value={item.valor}>
                {item.rotulo}
              </option>
            ))}
          </Select>

          <span className="ml-auto text-xs text-slate-500">
            {matriculas.data ? `${matriculas.data.count} matrícula(s)` : ""}
          </span>
        </div>

        {matriculas.isLoading && <Spinner />}
        {matriculas.isError && (
          <div className="p-4">
            <ErroBox mensagem="Não foi possível carregar as matrículas." />
          </div>
        )}

        {matriculas.data && matriculas.data.results.length === 0 && (
          <EmptyState titulo="Nenhuma matrícula" descricao="Crie a primeira matrícula do ano letivo." />
        )}

        {matriculas.data && matriculas.data.results.length > 0 && (
          <>
            <Table>
              <thead>
                <tr>
                  <Th>Aluno</Th>
                  <Th>Escola</Th>
                  <Th>Série</Th>
                  <Th>Ano</Th>
                  <Th>Data</Th>
                  <Th>Turma</Th>
                  <Th>Situação</Th>
                  <Th>Ações</Th>
                </tr>
              </thead>
              <tbody>
                {matriculas.data.results.map((matricula) => {
                  const ativa = matricula.enturmacoes.find((item) => item.ativo);
                  return (
                    <tr key={matricula.id}>
                      <Td className="font-medium text-slate-900">{matricula.aluno_nome}</Td>
                      <Td>{matricula.escola_nome}</Td>
                      <Td>{matricula.serie_nome}</Td>
                      <Td>{matricula.ano}</Td>
                      <Td>{formatarData(matricula.data_matricula)}</Td>
                      <Td>{ativa ? ativa.turma_nome : <span className="text-slate-400">Sem turma</span>}</Td>
                      <Td>
                        <div className="flex items-center gap-2">
                          <Select
                            className="h-8 w-32 text-xs"
                            aria-label={`Situação da matrícula de ${matricula.aluno_nome}`}
                            value={matricula.situacao}
                            onChange={(evento) =>
                              alterarSituacao.mutate({ id: matricula.id, valor: evento.target.value })
                            }
                          >
                            {SITUACOES.map((item) => (
                              <option key={item.valor} value={item.valor}>
                                {item.rotulo}
                              </option>
                            ))}
                          </Select>
                        </div>
                      </Td>
                      <Td>
                        <Button
                          variante="secundario"
                          tamanho="sm"
                          onClick={() => {
                            setEnturmarAberto(matricula);
                            setErroEnturmar(null);
                          }}
                          disabled={!!ativa || !matricula.ativo}
                        >
                          <GraduationCap className="h-3.5 w-3.5" aria-hidden />
                          {ativa ? "Enturmado" : "Enturmar"}
                        </Button>
                      </Td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
            <Pagination pagina={pagina} totalPaginas={totalPaginas} aoMudar={setPagina} />
          </>
        )}
      </Card>

      <Modal
        aberto={modalAberto}
        titulo="Nova matrícula"
        onFechar={() => setModalAberto(false)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setModalAberto(false)}>
              Cancelar
            </Button>
            <Button form="form-matricula" type="submit" carregando={criar.isPending}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-matricula" onSubmit={(e: FormEvent) => { e.preventDefault(); criar.mutate(); }} className="grid gap-4 sm:grid-cols-2">
          {erro && (
            <div className="sm:col-span-2">
              <ErroBox mensagem={erro} />
            </div>
          )}
          <div className="sm:col-span-2">
            <Campo label="Aluno" obrigatorio>
              {(id) => (
                <Select id={id} required value={aluno} onChange={(e) => setAluno(e.target.value)}>
                  <option value="">Selecione…</option>
                  {opcoesAlunos.data?.results.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nome} ({item.codigo})
                    </option>
                  ))}
                </Select>
              )}
            </Campo>
          </div>
          <Campo label="Escola" obrigatorio>
            {(id) => (
              <Select id={id} required value={escola} onChange={(e) => setEscola(e.target.value)}>
                <option value="">Selecione…</option>
                {opcoesEscolas.data?.results.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nome}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <Campo label="Série" obrigatorio>
            {(id) => (
              <Select id={id} required value={serie} onChange={(e) => setSerie(e.target.value)}>
                <option value="">Selecione…</option>
                {opcoesSeries.data?.results.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nome} — {item.curso_nome}
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          <Campo label="Ano letivo" obrigatorio>
            {(id) => <Input id={id} type="number" value={ano} onChange={(e) => setAno(e.target.value)} />}
          </Campo>
          <Campo label="Data da matrícula" obrigatorio>
            {(id) => (
              <Input id={id} type="date" required value={dataMatricula} onChange={(e) => setDataMatricula(e.target.value)} />
            )}
          </Campo>
        </form>
      </Modal>

      <Modal
        aberto={enturmarAberto !== null}
        titulo={`Enturmar ${enturmarAberto?.aluno_nome ?? ""}`}
        onFechar={() => setEnturmarAberto(null)}
        rodape={
          <>
            <Button variante="secundario" onClick={() => setEnturmarAberto(null)}>
              Cancelar
            </Button>
            <Button
              onClick={() => enturmar.mutate()}
              carregando={enturmar.isPending}
              disabled={!turmaSelecionada}
            >
              Enturmar
            </Button>
          </>
        }
      >
        <div className="grid gap-4">
          {erroEnturmar && <ErroBox mensagem={erroEnturmar} />}
          <Campo label="Turma disponível" obrigatorio ajuda="Somente turmas da mesma escola, série e ano com vagas.">
            {(id) => (
              <Select id={id} value={turmaSelecionada} onChange={(e) => setTurmaSelecionada(e.target.value)}>
                <option value="">Selecione…</option>
                {turmasCompativeis.map((turma) => (
                  <option key={turma.id} value={turma.id}>
                    {turma.nome} · {turma.turno} · {turma.vagas_disponiveis} vaga(s)
                  </option>
                ))}
              </Select>
            )}
          </Campo>
          {turmasCompativeis.length === 0 && (
            <p className="text-sm text-slate-500">
              Nenhuma turma compatível com vagas. Ajuste a capacidade ou crie uma nova turma.
            </p>
          )}
        </div>
      </Modal>
    </>
  );
}
