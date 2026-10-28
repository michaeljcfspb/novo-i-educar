import { forwardRef, useId } from "react";
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

interface CampoBase {
  label: string;
  erro?: string;
  ajuda?: string;
  obrigatorio?: boolean;
  children: (id: string, descricaoId: string | undefined) => ReactNode;
}

export function Campo({ label, erro, ajuda, obrigatorio, children }: CampoBase) {
  const id = useId();
  const descricaoId = erro || ajuda ? `${id}-descricao` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label}
        {obrigatorio && <span className="ml-0.5 text-red-600">*</span>}
      </label>
      {children(id, descricaoId)}
      {(erro || ajuda) && (
        <p
          id={descricaoId}
          className={cn("text-xs", erro ? "text-red-600" : "text-slate-500")}
        >
          {erro ?? ajuda}
        </p>
      )}
    </div>
  );
}

const base =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:bg-slate-100";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return <input ref={ref} className={cn(base, "h-10", className)} {...props} />;
  },
);

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...props }, ref) {
    return <textarea ref={ref} className={cn(base, "min-h-24", className)} {...props} />;
  },
);

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, children, ...props }, ref) {
    return (
      <select ref={ref} className={cn(base, "h-10 pr-8", className)} {...props}>
        {children}
      </select>
    );
  },
);
