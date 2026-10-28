from django.urls import path

from .views import AlunosRiscoView, IndicadoresView, TurmasRelatorioCSVView, TurmasRelatorioView

urlpatterns = [
    path("relatorios/indicadores/", IndicadoresView.as_view(), name="relatorio-indicadores"),
    path("relatorios/turmas/", TurmasRelatorioView.as_view(), name="relatorio-turmas"),
    path("relatorios/turmas.csv", TurmasRelatorioCSVView.as_view(), name="relatorio-turmas-csv"),
    path("relatorios/alunos-risco/", AlunosRiscoView.as_view(), name="relatorio-risco"),
]
