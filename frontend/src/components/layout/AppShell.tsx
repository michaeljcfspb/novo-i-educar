import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  BookOpen,
  CalendarCheck,
  CalendarDays,
  ClipboardList,
  FileClock,
  ScrollText,
  ArrowRightLeft,
  Upload,
  Landmark,
  BarChart3,
  UserCircle,
  FileText,
  GraduationCap,
  Layers,
  LayoutDashboard,
  LogOut,
  Menu,
  School,
  Users,
  UserSquare2,
  X,
} from "lucide-react";

import { useAuth } from "@/lib/auth";
import { cn, iniciais } from "@/lib/utils";

const navegacao = [
  { para: "/", rotulo: "Painel", icone: LayoutDashboard },
  { para: "/alunos", rotulo: "Alunos", icone: Users },
  { para: "/pessoas", rotulo: "Pessoas", icone: UserSquare2 },
  { para: "/escolas", rotulo: "Escolas", icone: School },
  { para: "/servidores", rotulo: "Servidores", icone: UserSquare2 },
  { para: "/turmas", rotulo: "Turmas", icone: BookOpen },
  { para: "/grade", rotulo: "Grade da turma", icone: Layers },
  { para: "/matriculas", rotulo: "Matrículas", icone: GraduationCap },
  { para: "/notas", rotulo: "Notas", icone: ClipboardList },
  { para: "/frequencia", rotulo: "Frequência", icone: CalendarCheck },
  { para: "/boletim", rotulo: "Boletim", icone: FileText },
  { para: "/ano-letivo", rotulo: "Ano letivo", icone: CalendarDays },
  { para: "/historico", rotulo: "Histórico", icone: FileClock },
  { para: "/transferencias", rotulo: "Transferências", icone: ArrowRightLeft },
  { para: "/documentos", rotulo: "Documentos", icone: ScrollText },
  { para: "/censo", rotulo: "Censo", icone: Landmark },
  { para: "/importacao", rotulo: "Importação", icone: Upload },
  { para: "/indicadores", rotulo: "Indicadores", icone: BarChart3 },
  { para: "/portal", rotulo: "Meu portal", icone: UserCircle },
];

export function AppShell() {
  const { usuario, sair } = useAuth();
  const [menuAberto, setMenuAberto] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 border-r border-slate-200 bg-white transition-transform lg:static lg:translate-x-0",
          menuAberto ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center gap-2 border-b border-slate-200 px-5">
          <GraduationCap className="h-6 w-6 text-brand-600" aria-hidden />
          <span className="text-sm font-semibold uppercase tracking-wide text-slate-700">
            i-Educar
          </span>
          <button
            type="button"
            className="ml-auto rounded-md p-1 text-slate-500 lg:hidden"
            onClick={() => setMenuAberto(false)}
            aria-label="Fechar menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex flex-col gap-1 p-3" aria-label="Navegação principal">
          {navegacao.map(({ para, rotulo, icone: Icone }) => (
            <NavLink
              key={para}
              to={para}
              end={para === "/"}
              onClick={() => setMenuAberto(false)}
              className={({ isActive }) =>
                cn(
                  "focus-ring flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                )
              }
            >
              <Icone className="h-4 w-4" aria-hidden />
              {rotulo}
            </NavLink>
          ))}
        </nav>
      </aside>

      {menuAberto && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/30 lg:hidden"
          onClick={() => setMenuAberto(false)}
          aria-hidden
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center gap-3 border-b border-slate-200 bg-white px-4 lg:px-6">
          <button
            type="button"
            className="rounded-md p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
            onClick={() => setMenuAberto(true)}
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-slate-800">{usuario?.nome_completo}</p>
              <p className="text-xs text-slate-500">
                {usuario?.perfil_display}
                {usuario?.escola_nome ? ` · ${usuario.escola_nome}` : ""}
              </p>
            </div>
            <div
              className="grid h-9 w-9 place-items-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700"
              aria-hidden
            >
              {usuario ? iniciais(usuario.nome_completo) : "?"}
            </div>
            <button
              type="button"
              onClick={() => void sair()}
              className="focus-ring rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              aria-label="Sair"
              title="Sair"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
