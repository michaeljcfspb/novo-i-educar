from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    AdminEscreve,
    EscopoPorEscolaEscrita,
    SomenteLeituraParaConsulta,
    filtrar_por_escola,
)
from .models import Aluno, Deficiencia, Pessoa, Servidor
from .serializers import (
    AlunoSerializer,
    DeficienciaSerializer,
    PessoaSerializer,
    ServidorSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Pessoas"], summary="Lista pessoas"),
    retrieve=extend_schema(tags=["Pessoas"], summary="Detalha uma pessoa"),
    create=extend_schema(tags=["Pessoas"], summary="Cria uma pessoa"),
    update=extend_schema(tags=["Pessoas"], summary="Atualiza uma pessoa"),
    partial_update=extend_schema(tags=["Pessoas"], summary="Atualiza parcialmente"),
    destroy=extend_schema(tags=["Pessoas"], summary="Remove uma pessoa"),
)
class PessoaViewSet(viewsets.ModelViewSet):
    queryset = Pessoa.objects.select_related("municipio").all()
    serializer_class = PessoaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    filterset_fields = ["tipo", "ativo", "sexo", "municipio"]
    search_fields = ["nome", "nome_social", "cpf", "email"]
    ordering_fields = ["nome", "criado_em"]
    ordering = ["nome"]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


@extend_schema_view(
    list=extend_schema(tags=["Alunos"], summary="Lista alunos"),
    retrieve=extend_schema(tags=["Alunos"], summary="Detalha um aluno"),
    create=extend_schema(tags=["Alunos"], summary="Cria aluno e pessoa"),
    update=extend_schema(tags=["Alunos"], summary="Atualiza aluno"),
    partial_update=extend_schema(tags=["Alunos"], summary="Atualiza parcialmente"),
    destroy=extend_schema(tags=["Alunos"], summary="Remove um aluno"),
)
class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.select_related("pessoa").prefetch_related("deficiencias")
    serializer_class = AlunoSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    filterset_fields = ["ativo", "deficiencias"]
    search_fields = ["pessoa__nome", "codigo", "pessoa__cpf"]
    ordering_fields = ["pessoa__nome", "codigo", "criado_em"]
    ordering = ["pessoa__nome"]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    @extend_schema(tags=["Alunos"], summary="Matrículas do aluno")
    @action(detail=True, methods=["get"], url_path="matriculas")
    def matriculas(self, request, pk=None):
        from apps.enrollments.serializers import MatriculaSerializer

        aluno = self.get_object()
        dados = MatriculaSerializer(aluno.matriculas.all(), many=True).data
        return Response(dados)


@extend_schema_view(
    list=extend_schema(tags=["Cadastros"], summary="Lista deficiências"),
    create=extend_schema(tags=["Cadastros"], summary="Cria deficiência"),
)
class DeficienciaViewSet(viewsets.ModelViewSet):
    queryset = Deficiencia.objects.all()
    serializer_class = DeficienciaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    search_fields = ["nome"]
    pagination_class = None


@extend_schema_view(
    list=extend_schema(tags=["Pessoas"], summary="Lista servidores"),
    create=extend_schema(tags=["Pessoas"], summary="Cria servidor (professor/gestor)"),
    retrieve=extend_schema(tags=["Pessoas"], summary="Detalha servidor"),
    update=extend_schema(tags=["Pessoas"], summary="Atualiza servidor"),
    destroy=extend_schema(tags=["Pessoas"], summary="Remove servidor"),
)
class ServidorViewSet(viewsets.ModelViewSet):
    queryset = Servidor.objects.select_related("pessoa", "escola").prefetch_related("disciplinas")
    serializer_class = ServidorSerializer
    permission_classes = [permissions.IsAuthenticated, AdminEscreve, EscopoPorEscolaEscrita]
    filterset_fields = ["cargo", "escola", "ativo"]
    search_fields = ["pessoa__nome", "matricula_funcional"]
    ordering = ["pessoa__nome"]

    def get_queryset(self):
        return filtrar_por_escola(super().get_queryset(), self.request.user)

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)
