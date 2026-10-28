import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/layout/AppShell";
import { Spinner } from "@/components/ui/feedback";
import { AlocacoesPage } from "@/pages/AlocacoesPage";
import { AlunosPage } from "@/pages/AlunosPage";
import { AnoLetivoPage } from "@/pages/AnoLetivoPage";
import { BoletimPage } from "@/pages/BoletimPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { CensoPage } from "@/pages/CensoPage";
import { DocumentosPage } from "@/pages/DocumentosPage";
import { EscolasPage } from "@/pages/EscolasPage";
import { FrequenciaPage } from "@/pages/FrequenciaPage";
import { HistoricoPage } from "@/pages/HistoricoPage";
import { ImportacaoPage } from "@/pages/ImportacaoPage";
import { IndicadoresPage } from "@/pages/IndicadoresPage";
import { PortalPage } from "@/pages/PortalPage";
import { LoginPage } from "@/pages/LoginPage";
import { MatriculasPage } from "@/pages/MatriculasPage";
import { NotasPage } from "@/pages/NotasPage";
import { PessoasPage } from "@/pages/PessoasPage";
import { ServidoresPage } from "@/pages/ServidoresPage";
import { TransferenciasPage } from "@/pages/TransferenciasPage";
import { TurmasPage } from "@/pages/TurmasPage";

function Protegido() {
  const { usuario, carregando } = useAuth();
  if (carregando) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner rotulo="Carregando sessão…" />
      </div>
    );
  }
  if (!usuario) return <Navigate to="/login" replace />;
  return <AppShell />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Protegido />}>
        <Route index element={<DashboardPage />} />
        <Route path="alunos" element={<AlunosPage />} />
        <Route path="pessoas" element={<PessoasPage />} />
        <Route path="escolas" element={<EscolasPage />} />
        <Route path="servidores" element={<ServidoresPage />} />
        <Route path="turmas" element={<TurmasPage />} />
        <Route path="grade" element={<AlocacoesPage />} />
        <Route path="notas" element={<NotasPage />} />
        <Route path="frequencia" element={<FrequenciaPage />} />
        <Route path="boletim" element={<BoletimPage />} />
        <Route path="ano-letivo" element={<AnoLetivoPage />} />
        <Route path="historico" element={<HistoricoPage />} />
        <Route path="transferencias" element={<TransferenciasPage />} />
        <Route path="documentos" element={<DocumentosPage />} />
        <Route path="censo" element={<CensoPage />} />
        <Route path="importacao" element={<ImportacaoPage />} />
        <Route path="indicadores" element={<IndicadoresPage />} />
        <Route path="portal" element={<PortalPage />} />
        <Route path="matriculas" element={<MatriculasPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
