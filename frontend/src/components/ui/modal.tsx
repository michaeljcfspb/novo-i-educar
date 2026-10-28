import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

export function Modal({
  aberto,
  titulo,
  onFechar,
  children,
  rodape,
}: {
  aberto: boolean;
  titulo: string;
  onFechar: () => void;
  children: ReactNode;
  rodape?: ReactNode;
}) {
  const referencia = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!aberto) return;
    const aoTeclar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") onFechar();
    };
    document.addEventListener("keydown", aoTeclar);
    referencia.current?.focus();
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [aberto, onFechar]);

  if (!aberto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onFechar}
        aria-hidden
      />
      <div
        ref={referencia}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        tabIndex={-1}
        className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white shadow-xl focus:outline-none"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-800">{titulo}</h2>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="focus-ring rounded-md p-1 text-slate-500 hover:bg-slate-100"
          >
            ✕
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
        {rodape && (
          <div className="flex justify-end gap-2 border-t border-slate-200 px-5 py-3">{rodape}</div>
        )}
      </div>
    </div>
  );
}
