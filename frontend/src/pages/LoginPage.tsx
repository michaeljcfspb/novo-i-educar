import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { GraduationCap } from "lucide-react";

import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Campo, Input } from "@/components/ui/field";

export function LoginPage() {
  const { usuario, entrar } = useAuth();
  const [email, setEmail] = useState("admin@example.com");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (usuario) return <Navigate to="/" replace />;

  async function aoEnviar(evento: FormEvent) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await entrar(email, senha);
    } catch (falha) {
      setErro(
        falha instanceof ApiError
          ? falha.message
          : "Não foi possível entrar. Verifique sua conexão.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-brand-700 p-10 text-white lg:flex">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-8 w-8" aria-hidden />
          <span className="text-lg font-semibold">i-Educar</span>
        </div>
        <div>
          <h1 className="max-w-md text-3xl font-semibold leading-tight">
            Gestão escolar completa, agora em React + Django.
          </h1>
          <p className="mt-4 max-w-md text-brand-100">
            Alunos, escolas, turmas e matrículas em um único lugar — com API documentada,
            permissões por escola e testes automatizados.
          </p>
        </div>
        <p className="text-xs text-brand-200">
          Software livre de gestão escolar · reescrita moderna do i-Educar
        </p>
      </div>

      <div className="flex items-center justify-center p-6">
        <form onSubmit={aoEnviar} className="w-full max-w-sm space-y-5">
          <div className="lg:hidden">
            <div className="flex items-center gap-2 text-brand-700">
              <GraduationCap className="h-7 w-7" aria-hidden />
              <span className="text-lg font-semibold">i-Educar</span>
            </div>
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">Entrar</h2>
            <p className="mt-1 text-sm text-slate-500">Use seu e-mail institucional.</p>
          </div>

          {erro && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {erro}
            </div>
          )}

          <Campo label="E-mail" obrigatorio>
            {(id) => (
              <Input
                id={id}
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="voce@escola.gov.br"
              />
            )}
          </Campo>

          <Campo label="Senha" obrigatorio>
            {(id) => (
              <Input
                id={id}
                type="password"
                autoComplete="current-password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="••••••••"
              />
            )}
          </Campo>

          <Button type="submit" className="w-full" carregando={enviando}>
            Entrar
          </Button>

          <p className="text-xs text-slate-500">
            Ambiente de desenvolvimento: crie um usuário com{" "}
            <code className="rounded bg-slate-100 px-1 py-0.5">python manage.py createsuperuser</code>.
          </p>
        </form>
      </div>
    </div>
  );
}
