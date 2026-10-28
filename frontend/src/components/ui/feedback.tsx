import type { ReactNode } from "react";

export function Spinner({ rotulo = "Carregando…" }: { rotulo?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-sm text-slate-500" role="status">
      <span
        aria-hidden
        className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent"
      />
      {rotulo}
    </div>
  );
}

export function ErroBox({ mensagem }: { mensagem: string }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {mensagem}
    </div>
  );
}

export function EmptyState({ titulo, descricao, acao }: { titulo: string; descricao?: string; acao?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      <p className="text-sm font-medium text-slate-700">{titulo}</p>
      {descricao && <p className="max-w-md text-sm text-slate-500">{descricao}</p>}
      {acao}
    </div>
  );
}

export function PageHeader({
  titulo,
  descricao,
  acoes,
}: {
  titulo: string;
  descricao?: string;
  acoes?: ReactNode;
}) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{titulo}</h1>
        {descricao && <p className="mt-1 text-sm text-slate-500">{descricao}</p>}
      </div>
      <div className="flex gap-2">{acoes}</div>
    </header>
  );
}
