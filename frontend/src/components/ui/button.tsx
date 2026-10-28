import { forwardRef } from "react";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Variante = "primario" | "secundario" | "fantasma" | "perigo";
type Tamanho = "sm" | "md";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante;
  tamanho?: Tamanho;
  carregando?: boolean;
}

const variantes: Record<Variante, string> = {
  primario: "bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-300",
  secundario: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
  fantasma: "text-slate-600 hover:bg-slate-100",
  perigo: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
};

const tamanhos: Record<Tamanho, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variante = "primario", tamanho = "md", carregando, disabled, children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "focus-ring inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed",
        variantes[variante],
        tamanhos[tamanho],
        className,
      )}
      disabled={disabled || carregando}
      {...props}
    >
      {carregando && (
        <span
          aria-hidden
          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
});
