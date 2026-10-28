from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import SomenteLeituraParaConsulta, filtrar_por_escola
from .models import Matricula, MatriculaTurma
from .serializers import (
    AlterarSituacaoSerializer,
    EnturmarSerializer,
    MatriculaSerializer,
    MatriculaTurmaSerializer,
    ReclassificarSerializer,
    RemanejarSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Matrículas"], summary="Lista matrículas"),
    retrieve=extend_schema(tags=["Matrículas"], summary="Detalha matrícula"),
    create=extend_schema(tags=["Matrículas"], summary="Cria matrícula"),
    update=extend_schema(tags=["Matrículas"], summary="Atualiza matrícula"),
    partial_update=extend_schema(tags=["Matrículas"], summary="Atualiza parcialmente"),
    destroy=extend_schema(tags=["Matrículas"], summary="Cancela matrícula"),
)
class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = (
        Matricula.objects.select_related("aluno__pessoa", "escola", "serie", "curso")
        .prefetch_related("enturmacoes__turma")
        .all()
    )
    serializer_class = MatriculaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    filterset_fields = ["ano", "escola", "serie", "situacao", "ativo", "aluno"]
    search_fields = ["aluno__pessoa__nome", "aluno__codigo"]
    ordering_fields = ["ano", "data_matricula"]
    ordering = ["-ano"]

    def get_queryset(self):
        qs = filtrar_por_escola(super().get_queryset(), self.request.user)
        turma = self.request.query_params.get("turma")
        if turma:
            qs = qs.filter(enturmacoes__turma_id=turma, enturmacoes__ativo=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.situacao = "cancelada"
        instance.save(update_fields=["ativo", "situacao", "atualizado_em"])

    @extend_schema(
        tags=["Matrículas"],
        summary="Enturma a matrícula em uma turma",
        request=EnturmarSerializer,
        responses={201: MatriculaTurmaSerializer},
    )
    @action(detail=True, methods=["post"], url_path="enturmar")
    def enturmar(self, request, pk=None):
        matricula = self.get_object()
        serializer = EnturmarSerializer(data=request.data, context={"matricula": matricula})
        serializer.is_valid(raise_exception=True)
        enturmacao = serializer.save()
        return Response(MatriculaTurmaSerializer(enturmacao).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Matrículas"],
        summary="Remaneja o aluno para outra turma",
        request=RemanejarSerializer,
        responses={201: MatriculaTurmaSerializer},
    )
    @action(detail=True, methods=["post"], url_path="remanejar")
    def remanejar(self, request, pk=None):
        matricula = self.get_object()
        serializer = RemanejarSerializer(data=request.data, context={"matricula": matricula})
        serializer.is_valid(raise_exception=True)
        enturmacao = serializer.save()
        return Response(MatriculaTurmaSerializer(enturmacao).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Matrículas"],
        summary="Reclassifica o aluno para outra série",
        request=ReclassificarSerializer,
        responses={200: MatriculaSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reclassificar")
    def reclassificar(self, request, pk=None):
        matricula = self.get_object()
        serializer = ReclassificarSerializer(data=request.data, context={"matricula": matricula})
        serializer.is_valid(raise_exception=True)
        matricula = serializer.save()
        return Response(MatriculaSerializer(matricula).data)

    @extend_schema(tags=["Matrículas"], summary="Boletim do aluno (notas, médias e frequência)")
    @action(detail=True, methods=["get"], url_path="boletim")
    def boletim(self, request, pk=None):
        from apps.assessment.services import gerar_boletim

        return Response(gerar_boletim(self.get_object()))

    @extend_schema(tags=["Matrículas"], summary="Boletim em PDF")
    @action(detail=True, methods=["get"], url_path="boletim-pdf")
    def boletim_pdf(self, request, pk=None):
        from django.http import HttpResponse

        from apps.reports.pdf import boletim_pdf

        matricula = self.get_object()
        conteudo = boletim_pdf(matricula)
        resposta = HttpResponse(conteudo, content_type="application/pdf")
        resposta["Content-Disposition"] = f'inline; filename="boletim-{matricula.id}.pdf"'
        return resposta

    @extend_schema(tags=["Matrículas"], summary="Resumo de frequência da matrícula")
    @action(detail=True, methods=["get"], url_path="frequencia")
    def frequencia(self, request, pk=None):
        from apps.attendance.services import resumo_frequencia

        return Response(resumo_frequencia(self.get_object()))

    @extend_schema(
        tags=["Matrículas"],
        summary="Altera a situação da matrícula",
        request=AlterarSituacaoSerializer,
        responses={200: MatriculaSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="situacao")
    def alterar_situacao(self, request, pk=None):
        matricula = self.get_object()
        serializer = AlterarSituacaoSerializer(
            data=request.data, context={"matricula": matricula}
        )
        serializer.is_valid(raise_exception=True)
        matricula.situacao = serializer.validated_data["situacao"]
        matricula.save(update_fields=["situacao", "atualizado_em"])
        return Response(MatriculaSerializer(matricula).data)


@extend_schema_view(
    list=extend_schema(tags=["Matrículas"], summary="Lista enturmações"),
    destroy=extend_schema(tags=["Matrículas"], summary="Encerra enturmação"),
)
class MatriculaTurmaViewSet(viewsets.ModelViewSet):
    queryset = MatriculaTurma.objects.select_related("matricula__aluno__pessoa", "turma").all()
    serializer_class = MatriculaTurmaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    filterset_fields = ["ativo", "turma", "matricula"]
    ordering = ["-data_enturmacao"]

    def get_queryset(self):
        return filtrar_por_escola(
            super().get_queryset(), self.request.user, campo="matricula__escola"
        )

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save(update_fields=["ativo", "atualizado_em"])
