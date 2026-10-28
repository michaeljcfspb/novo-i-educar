/**
 * Cliente HTTP tipado da API do i-Educar.
 *
 * Autenticação por sessão (cookie HttpOnly) + CSRF em métodos de escrita.
 * Em desenvolvimento o Vite faz proxy de /api para o Django, então tudo
 * permanece na mesma origem.
 */

export const API_URL: string = import.meta.env.VITE_API_URL ?? "/api/v1";

export type Perfil = "administrador" | "gestor" | "secretaria" | "professor" | "consulta";

export interface Usuario {
  id: number;
  email: string;
  nome_completo: string;
  perfil: Perfil;
  perfil_display: string;
  escola: number | null;
  escola_nome: string | null;
  is_active: boolean;
  ultimo_acesso: string | null;
}

export interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Instituicao {
  id: number;
  nome: string;
  sigla: string;
  cnpj: string;
  email: string;
  telefone: string;
  municipio: number | null;
  ativo: boolean;
}

export interface Escola {
  id: number;
  instituicao: number;
  instituicao_nome: string;
  nome: string;
  sigla: string;
  codigo_inep: string;
  email: string;
  telefone: string;
  cep: string;
  logradouro: string;
  numero: string;
  bairro: string;
  municipio: number | null;
  ativo: boolean;
}

export interface Curso {
  id: number;
  instituicao: number;
  nome: string;
  sigla: string;
  nivel_ensino: string;
  nivel_ensino_display: string;
  modalidade: string;
  carga_horaria: number;
  ativo: boolean;
}

export interface Serie {
  id: number;
  curso: number;
  curso_nome: string;
  nome: string;
  etapa: number;
  carga_horaria: number;
  idade_inicial: number;
  idade_final: number;
  ativo: boolean;
}

export interface Turma {
  id: number;
  escola: number;
  escola_nome: string;
  serie: number;
  serie_nome: string;
  nome: string;
  sigla: string;
  ano: number;
  turno: string;
  capacidade: number;
  vagas_disponiveis: number;
  ativo: boolean;
}

export interface Pessoa {
  id: number;
  tipo: "fisica" | "juridica";
  tipo_display: string;
  nome: string;
  nome_social: string;
  cpf: string | null;
  cnpj: string | null;
  data_nascimento: string | null;
  sexo: string;
  email: string;
  telefone: string;
  nome_mae: string;
  nome_pai: string;
  nacionalidade: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  municipio: number | null;
  municipio_nome: string | null;
  ativo: boolean;
}

export interface Deficiencia {
  id: number;
  nome: string;
  codigo_censo: string;
}

export interface Aluno {
  id: number;
  codigo: string;
  nome: string;
  pessoa: Pessoa;
  deficiencias: number[];
  deficiencias_detalhe: Deficiencia[];
  ativo: boolean;
  foto: string | null;
  usa_transporte_escolar: boolean;
  recebe_escolarizacao_outro_espaco: boolean;
  observacoes: string;
}

export interface Enturmacao {
  id: number;
  turma: number;
  turma_nome: string;
  data_enturmacao: string;
  ativo: boolean;
  sequencial: number;
}

export interface Servidor {
  id: number;
  matricula_funcional: string;
  nome: string;
  pessoa: Pessoa;
  cargo: string;
  cargo_display: string;
  escola: number;
  escola_nome: string;
  disciplinas: number[];
  disciplinas_detalhe: Deficiencia[];
  data_admissao: string | null;
  ativo: boolean;
}

export interface AnoLetivo {
  id: number;
  instituicao: number;
  instituicao_nome: string;
  ano: number;
  data_inicio: string;
  data_fim: string;
  ativo: boolean;
}

export interface Calendario {
  id: number;
  ano_letivo: number;
  ano: number;
  escola: number | null;
  nome: string;
  ativo: boolean;
  dias_letivos: number;
}

export interface TurmaDisciplina {
  id: number;
  turma: number;
  turma_nome: string;
  disciplina: number;
  disciplina_nome: string;
  professor: number | null;
  professor_nome: string | null;
  carga_horaria: number;
}

export interface RegraAvaliacao {
  id: number;
  nome: string;
  tipo_media: string;
  nota_maxima: string;
  media_aprovacao: string;
  media_recuperacao: string;
  percentual_frequencia: number;
  permite_recuperacao: boolean;
  casas_decimais: number;
}

export interface PeriodoAvaliacao {
  id: number;
  ano_letivo: number;
  ano: number;
  nome: string;
  ordem: number;
  data_inicio: string;
  data_fim: string;
  peso: string;
}

export interface Nota {
  id: number;
  matricula: number;
  aluno_nome: string;
  turma_disciplina: number;
  disciplina_nome: string;
  periodo: number;
  periodo_nome: string;
  tipo: "normal" | "recuperacao";
  valor: string;
  observacao: string;
}

export interface Frequencia {
  id: number;
  matricula: number;
  aluno_nome: string;
  turma: number;
  data: string;
  presente: boolean;
  justificativa: string;
}

export interface BoletimDisciplina {
  turma_disciplina: number;
  disciplina: string;
  professor: string | null;
  notas: Record<string, number>;
  recuperacao: number | null;
  media: number;
}

export interface Boletim {
  matricula: number;
  aluno: string;
  ano: number;
  turma: string | null;
  regra_avaliacao: string | null;
  media_geral: number;
  frequencia: { dias_registrados: number; presencas: number; faltas: number; percentual: number; minimo: number | null };
  situacao_final: string;
  disciplinas: BoletimDisciplina[];
}

export interface HistoricoDisciplina {
  id: number;
  nome_disciplina: string;
  carga_horaria: number;
  media: string;
  frequencia: string;
  situacao: string;
}

export interface HistoricoEscolar {
  id: number;
  aluno: number;
  aluno_nome: string;
  matricula: number | null;
  escola: number;
  escola_nome: string;
  serie: number;
  serie_nome: string;
  ano: number;
  carga_horaria_total: number;
  dias_letivos: number;
  frequencia_percentual: string;
  media_geral: string;
  situacao: string;
  situacao_display: string;
  observacoes: string;
  disciplinas: HistoricoDisciplina[];
}

export interface Transferencia {
  id: number;
  matricula: number;
  aluno_nome: string;
  tipo: string;
  tipo_display: string;
  data: string;
  escola_origem: number | null;
  escola_origem_nome: string | null;
  escola_destino: number | null;
  escola_destino_nome: string | null;
  motivo: string;
  observacao: string;
}

export interface Documento {
  id: number;
  aluno: number;
  aluno_nome: string;
  matricula: number | null;
  tipo: string;
  tipo_display: string;
  numero: string;
  titulo: string;
  corpo: string;
  emitido_em: string;
}

export interface PendenciaCenso {
  entidade: string;
  identificador: string;
  campo: string;
  mensagem: string;
}

export interface ExportacaoCenso {
  id: number;
  escola: number;
  escola_nome: string;
  ano: number;
  versao: number;
  status: string;
  status_display: string;
  total_alunos: number;
  total_turmas: number;
  pendencias: PendenciaCenso[];
  payload: Record<string, unknown>;
  criado_em: string;
}

export interface Importacao {
  id: number;
  tipo: string;
  arquivo_nome: string;
  status: string;
  status_display: string;
  total_linhas: number;
  total_sucessos: number;
  total_erros: number;
  relatorio: { linha: number; nome?: string; erros: string[] }[];
  criado_em: string;
}

export interface Webhook {
  id: number;
  nome: string;
  url: string;
  eventos: string[];
  ativo: boolean;
}

export interface Indicadores {
  ano: number;
  total_matriculas: number;
  matriculas_ativas: number;
  escolas: number;
  turmas: number;
  taxa_aprovacao: number;
  taxa_reprovacao: number;
  taxa_abandono: number;
  taxa_transferencia: number;
  ocupacao_media: number;
  frequencia_media: number;
  media_geral: number;
  situacoes: Record<string, number>;
}

export interface LinhaTurma {
  turma: string;
  escola: string;
  serie: string;
  turno: string;
  capacidade: number;
  alunos: number;
  ocupacao: number;
  media: number;
  frequencia: number;
}

export interface AlunoRisco {
  matricula: number;
  aluno: string;
  escola: string;
  serie: string;
  frequencia: number;
  media: number;
  motivo: string;
}

export interface PortalPerfil {
  aluno: string;
  codigo: string;
  matriculas: { id: number; ano: number; escola: string; serie: string; situacao: string }[];
}

export interface Matricula {
  id: number;
  aluno: number;
  aluno_nome: string;
  escola: number;
  escola_nome: string;
  serie: number;
  serie_nome: string;
  curso: number;
  ano: number;
  data_matricula: string;
  situacao: string;
  situacao_display: string;
  ativo: boolean;
  observacao: string;
  enturmacoes: Enturmacao[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly dados: unknown;

  constructor(status: number, dados: unknown, mensagem: string) {
    super(mensagem);
    this.name = "ApiError";
    this.status = status;
    this.dados = dados;
  }
}

function lerCookie(nome: string): string | null {
  const par = document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${nome}=`));
  return par ? decodeURIComponent(par.split("=").slice(1).join("=")) : null;
}

function mensagemDeErro(status: number, dados: unknown): string {
  if (typeof dados === "string") return dados;
  if (dados && typeof dados === "object") {
    const obj = dados as Record<string, unknown>;
    if (typeof obj.detail === "string") return obj.detail;
    const primeiro = Object.entries(obj)[0];
    if (primeiro) {
      const [campo, valor] = primeiro;
      const texto = Array.isArray(valor) ? String(valor[0]) : String(valor);
      return campo === "non_field_errors" ? texto : `${campo}: ${texto}`;
    }
  }
  return `Erro ${status} ao chamar a API.`;
}

export async function garantirCsrf(): Promise<string> {
  const existente = lerCookie("csrftoken");
  if (existente) return existente;
  const resposta = await fetch(`${API_URL}/auth/csrf/`, { credentials: "include" });
  if (!resposta.ok) throw new ApiError(resposta.status, null, "Não foi possível obter o CSRF.");
  const dados = (await resposta.json()) as { csrfToken: string };
  return dados.csrfToken;
}

type Opcoes = Omit<RequestInit, "body"> & { body?: unknown };

export async function requisitar<T>(caminho: string, opcoes: Opcoes = {}): Promise<T> {
  const metodo = (opcoes.method ?? "GET").toUpperCase();
  const cabecalhos = new Headers(opcoes.headers);
  cabecalhos.set("Accept", "application/json");

  if (opcoes.body !== undefined) {
    cabecalhos.set("Content-Type", "application/json");
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(metodo)) {
    cabecalhos.set("X-CSRFToken", await garantirCsrf());
  }

  const resposta = await fetch(`${API_URL}${caminho}`, {
    ...opcoes,
    method: metodo,
    headers: cabecalhos,
    credentials: "include",
    body: opcoes.body === undefined ? undefined : JSON.stringify(opcoes.body),
  });

  if (resposta.status === 204) return undefined as T;

  const texto = await resposta.text();
  const dados: unknown = texto ? JSON.parse(texto) : null;

  if (!resposta.ok) {
    throw new ApiError(resposta.status, dados, mensagemDeErro(resposta.status, dados));
  }
  return dados as T;
}

function query(params?: Record<string, string | number | boolean | undefined>): string {
  if (!params) return "";
  const busca = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== "") busca.set(chave, String(valor));
  }
  const texto = busca.toString();
  return texto ? `?${texto}` : "";
}

export const api = {
  async login(email: string, password: string): Promise<Usuario> {
    await garantirCsrf();
    return requisitar<Usuario>("/auth/login/", { method: "POST", body: { email, password } });
  },
  logout: () => requisitar<void>("/auth/logout/", { method: "POST" }),
  me: () => requisitar<Usuario>("/auth/me/"),

  /** Lista recursos. Endpoints sem paginação são normalizados para o formato paginado. */
  listar: async <T>(
    recurso: string,
    params?: Record<string, string | number | boolean | undefined>,
  ): Promise<Paginado<T>> => {
    const dados = await requisitar<Paginado<T> | T[]>(`/${recurso}/${query(params)}`);
    if (Array.isArray(dados)) {
      return { count: dados.length, next: null, previous: null, results: dados };
    }
    return dados;
  },
  obter: <T>(recurso: string, id: number) => requisitar<T>(`/${recurso}/${id}/`),
  criar: <T>(recurso: string, corpo: unknown) =>
    requisitar<T>(`/${recurso}/`, { method: "POST", body: corpo }),
  atualizar: <T>(recurso: string, id: number, corpo: unknown) =>
    requisitar<T>(`/${recurso}/${id}/`, { method: "PATCH", body: corpo }),
  remover: (recurso: string, id: number) =>
    requisitar<void>(`/${recurso}/${id}/`, { method: "DELETE" }),

  enturmar: (matriculaId: number, turmaId: number) =>
    requisitar<Enturmacao>(`/matriculas/${matriculaId}/enturmar/`, {
      method: "POST",
      body: { turma: turmaId },
    }),
  indicadores: (ano?: number, escola?: number) =>
    requisitar<Indicadores>(`/relatorios/indicadores/${query({ ano, escola })}`),
  relatorioTurmas: (ano?: number, escola?: number) =>
    requisitar<LinhaTurma[]>(`/relatorios/turmas/${query({ ano, escola })}`),
  alunosRisco: (ano?: number, escola?: number) =>
    requisitar<AlunoRisco[]>(`/relatorios/alunos-risco/${query({ ano, escola })}`),
  portalPerfil: () => requisitar<PortalPerfil>("/portal/perfil/"),
  portalBoletim: () => requisitar<Boletim>("/portal/boletim/"),
  portalFrequencia: () =>
    requisitar<{ dias_registrados: number; presencas: number; faltas: number; percentual: number }>(
      "/portal/frequencia/",
    ),
  portalDocumentos: () => requisitar<Documento[]>("/portal/documentos/"),
  gerarCenso: (escola: number, ano: number) =>
    requisitar<ExportacaoCenso>("/censo/exportacoes/gerar/", { method: "POST", body: { escola, ano } }),
  previewCenso: (escola: number, ano: number) =>
    requisitar<{ totais: { turmas: number; alunos: number; profissionais: number }; pendencias: PendenciaCenso[] }>(
      "/censo/exportacoes/preview/",
      { method: "POST", body: { escola, ano } },
    ),
  importarAlunos: async (arquivo: File) => {
    const form = new FormData();
    form.append("arquivo", arquivo);
    const resposta = await fetch(`${API_URL}/importacoes/`, {
      method: "POST",
      body: form,
      credentials: "include",
      headers: { "X-CSRFToken": await garantirCsrf(), Accept: "application/json" },
    });
    const dados = await resposta.json();
    if (!resposta.ok) throw new ApiError(resposta.status, dados, mensagemDeErro(resposta.status, dados));
    return dados as Importacao;
  },
  gerarHistorico: (matriculaId: number) =>
    requisitar<HistoricoEscolar>("/historicos/gerar/", { method: "POST", body: { matricula: matriculaId } }),
  emitirDocumento: (aluno: number, tipo: string, matricula?: number) =>
    requisitar<Documento>("/documentos/emitir/", {
      method: "POST",
      body: { aluno, tipo, matricula: matricula ?? null },
    }),
  boletim: (matriculaId: number) => requisitar<Boletim>(`/matriculas/${matriculaId}/boletim/`),
  notasLote: (corpo: {
    turma_disciplina: number;
    periodo: number;
    tipo?: "normal" | "recuperacao";
    registros: { matricula: number; valor: string  }[];
  }) => requisitar<{ criadas: Nota[]; erros: { matricula: number; erro: string }[] }>("/notas/lote/", { method: "POST", body: corpo }),
  frequenciaLote: (corpo: {
    turma: number;
    data: string;
    registros: { matricula: number; presente: boolean; justificativa?: string }[];
  }) => requisitar<Frequencia[]>("/frequencias/lote/", { method: "POST", body: corpo }),
  alterarSituacao: (matriculaId: number, situacao: string) =>
    requisitar<Matricula>(`/matriculas/${matriculaId}/situacao/`, {
      method: "PATCH",
      body: { situacao },
    }),
};
