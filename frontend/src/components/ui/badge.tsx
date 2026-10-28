import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type Tom = "neutro" | "sucesso" | "atencao" | "erro" | "info";

const tons: Record<Tom, string> = {
  neutro: "bg-slate-100 text-slate-700",
  sucesso: "bg-emerald-50 text-emerald-700",
  atencao: "bg-amber-50 text-amber-700",
  erro: "bg-red-50 text-red-700",
  info: "bg-brand-50 text-brand-700",
};

export function Badge({
  children,
  tom = "neutro",
  className,
}: {
  children: ReactNode;
  tom?: Tom;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        tons[tom],
        className,
      )}
    >
      {children}
    </span>
  );
}
