import csv

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import filtrar_por_escola
from apps.schools.models import Escola
from .services import alunos_em_risco, indicadores_rede, relatorio_turmas


class BaseRelatorioView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    def escola_do_pedido(self, request):
        escola_id = request.query_params.get("escola")
        if not escola_id:
            return None
        escola = Escola.objects.filter(pk=escola_id).first()
        if escola is None:
            return None
        if not request.user.is_superuser and request.user.escola_id not in (None, escola.id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Você só pode consultar relatórios da sua escola.")
        return escola

    def ano_do_pedido(self, request) -> int:
        from django.utils import timezone

        ano = request.query_params.get("ano")
        try:
            return int(ano) if ano else timezone.localdate().year
        except ValueError:
            return timezone.localdate().year


@extend_schema(
    tags=["Relatórios"],
    summary="Indicadores da rede",
    responses={200: OpenApiTypes.OBJECT},
    parameters=[
        OpenApiParameter("ano", int, description="Ano letivo (padrão: ano atual)"),
        OpenApiParameter("escola", int, description="Restringe a uma escola"),
    ],
)
class IndicadoresView(BaseRelatorioView):
    def get(self, request):
        return Response(indicadores_rede(self.ano_do_pedido(request), self.escola_do_pedido(request)))


@extend_schema(
    tags=["Relatórios"],
    summary="Relatório por turma",
    responses={200: OpenApiTypes.OBJECT},
    parameters=[
        OpenApiParameter("ano", int, description="Ano letivo"),
        OpenApiParameter("escola", int, description="Restringe a uma escola"),
    ],
)
class TurmasRelatorioView(BaseRelatorioView):
    def get(self, request):
        return Response(relatorio_turmas(self.ano_do_pedido(request), self.escola_do_pedido(request)))


@extend_schema(
    tags=["Relatórios"],
    summary="Exporta o relatório de turmas em CSV",
    responses={(200, "text/csv"): OpenApiTypes.BINARY},
    parameters=[OpenApiParameter("ano", int), OpenApiParameter("escola", int)],
)
class TurmasRelatorioCSVView(BaseRelatorioView):
    def get(self, request):
        linhas = relatorio_turmas(self.ano_do_pedido(request), self.escola_do_pedido(request))
        resposta = HttpResponse(content_type="text/csv; charset=utf-8")
        resposta["Content-Disposition"] = 'attachment; filename="relatorio-turmas.csv"'
        resposta.write("\ufeff")
        escritor = csv.writer(resposta, delimiter=";")
        escritor.writerow(
            ["Turma", "Escola", "Série", "Turno", "Capacidade", "Alunos", "Ocupação %", "Média", "Frequência %"]
        )
        for linha in linhas:
            escritor.writerow(
                [
                    linha["turma"], linha["escola"], linha["serie"], linha["turno"],
                    linha["capacidade"], linha["alunos"], linha["ocupacao"],
                    linha["media"], linha["frequencia"],
                ]
            )
        return resposta


@extend_schema(
    tags=["Relatórios"],
    summary="Alunos em risco (frequência ou média baixa)",
    responses={200: OpenApiTypes.OBJECT},
    parameters=[
        OpenApiParameter("ano", int),
        OpenApiParameter("escola", int),
        OpenApiParameter("frequencia_minima", int),
        OpenApiParameter("media_minima", float),
    ],
)
class AlunosRiscoView(BaseRelatorioView):
    def get(self, request):
        try:
            frequencia = int(request.query_params.get("frequencia_minima", 75))
            media = float(request.query_params.get("media_minima", 6))
        except ValueError:
            frequencia, media = 75, 6.0
        return Response(
            alunos_em_risco(self.ano_do_pedido(request), self.escola_do_pedido(request), frequencia, media)
        )
