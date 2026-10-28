import { Button } from "./button";

export function Pagination({
  pagina,
  totalPaginas,
  aoMudar,
}: {
  pagina: number;
  totalPaginas: number;
  aoMudar: (pagina: number) => void;
}) {
  if (totalPaginas <= 1) return null;
  return (
    <div className="flex items-center justify-between gap-2 px-4 py-3">
      <span className="text-xs text-slate-500">
        Página {pagina} de {totalPaginas}
      </span>
      <div className="flex gap-2">
        <Button
          variante="secundario"
          tamanho="sm"
          onClick={() => aoMudar(pagina - 1)}
          disabled={pagina <= 1}
        >
          Anterior
        </Button>
        <Button
          variante="secundario"
          tamanho="sm"
          onClick={() => aoMudar(pagina + 1)}
          disabled={pagina >= totalPaginas}
        >
          Próxima
        </Button>
      </div>
    </div>
  );
}
