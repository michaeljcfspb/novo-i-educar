"""Portal do aluno/responsável: consulta dos próprios dados."""
from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessment.services import gerar_boletim
from apps.attendance.services import resumo_frequencia
from apps.people.models import Aluno
from apps.records.models import Documento
from apps.records.serializers import DocumentoSerializer


class BasePortalView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(parameters=[OpenApiParameter("aluno", int, description="Somente para equipe escolar")])
    def obter_aluno(self, request, exigir: bool = True) -> Aluno | None:
        aluno = getattr(request.user, "aluno", None)
        if aluno is not None:
            return aluno

        parametro = request.query_params.get("aluno")
        if parametro and (
            request.user.is_superuser
            or getattr(request.user, "perfil", None) in {"administrador", "gestor", "secretaria"}
        ):
            return Aluno.objects.filter(pk=parametro).first()

        if exigir:
            return None
        return None


@extend_schema(tags=["Portal"], summary="Perfil do aluno logado", responses={200: OpenApiTypes.OBJECT})
class PerfilView(BasePortalView):
    def get(self, request):
        aluno = self.obter_aluno(request)
        if aluno is None:
            return Response(
                {"detail": "Este usuário não está vinculado a um aluno."},
                status=status.HTTP_404_NOT_FOUND,
            )
        matriculas = aluno.matriculas.select_related("escola", "serie").order_by("-ano")
        return Response(
            {
                "aluno": aluno.pessoa.nome,
                "codigo": aluno.codigo,
                "matriculas": [
                    {
                        "id": matricula.id,
                        "ano": matricula.ano,
                        "escola": matricula.escola.nome,
                        "serie": matricula.serie.nome,
                        "situacao": matricula.situacao,
                    }
                    for matricula in matriculas
                ],
            }
        )


@extend_schema(tags=["Portal"], summary="Boletim do aluno logado", responses={200: OpenApiTypes.OBJECT})
class BoletimView(BasePortalView):
    def get(self, request):
        aluno = self.obter_aluno(request)
        if aluno is None:
            return Response(
                {"detail": "Este usuário não está vinculado a um aluno."},
                status=status.HTTP_404_NOT_FOUND,
            )
        matricula = aluno.matriculas.order_by("-ano").first()
        if matricula is None:
            return Response({"detail": "Nenhuma matrícula encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(gerar_boletim(matricula))


@extend_schema(tags=["Portal"], summary="Frequência do aluno logado", responses={200: OpenApiTypes.OBJECT})
class FrequenciaView(BasePortalView):
    def get(self, request):
        aluno = self.obter_aluno(request)
        if aluno is None:
            return Response(
                {"detail": "Este usuário não está vinculado a um aluno."},
                status=status.HTTP_404_NOT_FOUND,
            )
        matricula = aluno.matriculas.order_by("-ano").first()
        if matricula is None:
            return Response({"detail": "Nenhuma matrícula encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(resumo_frequencia(matricula))


@extend_schema(tags=["Portal"], summary="Documentos do aluno logado", responses={200: OpenApiTypes.OBJECT})
class DocumentosView(BasePortalView):
    def get(self, request):
        aluno = self.obter_aluno(request)
        if aluno is None:
            return Response(
                {"detail": "Este usuário não está vinculado a um aluno."},
                status=status.HTTP_404_NOT_FOUND,
            )
        documentos = Documento.objects.filter(aluno=aluno).order_by("-emitido_em")
        return Response(DocumentoSerializer(documentos, many=True).data)
