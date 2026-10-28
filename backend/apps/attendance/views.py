from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    EscopoPorEscolaEscrita,
    SomenteLeituraParaConsulta,
    eh_administrador,
    filtrar_por_escola,
)
from apps.schools.models import Turma
from .models import Frequencia
from .serializers import FrequenciaSerializer, LoteFrequenciaSerializer


@extend_schema_view(
    list=extend_schema(tags=["Frequência"], summary="Lista frequências"),
    create=extend_schema(tags=["Frequência"], summary="Lança frequência individual"),
)
class FrequenciaViewSet(viewsets.ModelViewSet):
    queryset = Frequencia.objects.select_related("matricula__aluno__pessoa", "turma").all()
    serializer_class = FrequenciaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta, EscopoPorEscolaEscrita]
    filterset_fields = ["matricula", "turma", "data", "presente"]
    ordering = ["-data"]

    def get_queryset(self):
        return filtrar_por_escola(
            super().get_queryset(), self.request.user, campo="matricula__escola"
        )

    @extend_schema(
        tags=["Frequência"],
        summary="Lança a chamada da turma em lote",
        request=LoteFrequenciaSerializer,
        responses={201: FrequenciaSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="lote")
    @transaction.atomic
    def lote(self, request):
        entrada = LoteFrequenciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data

        turma = Turma.objects.filter(pk=dados["turma"]).first()
        if turma is None:
            return Response({"turma": ["Turma inexistente."]}, status=status.HTTP_400_BAD_REQUEST)
        if not eh_administrador(request.user) and request.user.escola_id not in (None, turma.escola_id):
            return Response(
                {"detail": "Você só pode lançar frequência da sua escola."},
                status=status.HTTP_403_FORBIDDEN,
            )

        resultados = []
        for registro in dados["registros"]:
            frequencia, _ = Frequencia.objects.update_or_create(
                matricula_id=registro["matricula"],
                data=dados["data"],
                defaults={
                    "turma": turma,
                    "presente": registro["presente"],
                    "justificativa": registro.get("justificativa", ""),
                    "criado_por": request.user,
                },
            )
            resultados.append(frequencia)
        return Response(
            FrequenciaSerializer(resultados, many=True).data, status=status.HTTP_201_CREATED
        )
