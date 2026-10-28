from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    AdminEscreve,
    EscopoPorEscolaEscrita,
    SomenteLeituraParaConsulta,
    filtrar_por_escola,
)
from .models import (
    AnoLetivo,
    Calendario,
    CalendarioDia,
    Curso,
    Disciplina,
    Escola,
    Instituicao,
    Serie,
    Turma,
    TurmaDisciplina,
)
from .serializers import (
    AnoLetivoSerializer,
    CalendarioDiaSerializer,
    CalendarioSerializer,
    CursoSerializer,
    DisciplinaSerializer,
    EscolaSerializer,
    InstituicaoSerializer,
    SerieSerializer,
    TurmaDisciplinaSerializer,
    TurmaSerializer,
)


class BaseEscolarViewSet(viewsets.ModelViewSet):
    """Estrutura da rede: leitura para todos, escrita apenas para administradores."""

    permission_classes = [permissions.IsAuthenticated, AdminEscreve]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista instituições"),
    retrieve=extend_schema(tags=["Escolas"], summary="Detalha instituição"),
)
class InstituicaoViewSet(BaseEscolarViewSet):
    queryset = Instituicao.objects.select_related("municipio").all()
    serializer_class = InstituicaoSerializer
    filterset_fields = ["ativo"]
    search_fields = ["nome", "sigla"]
    ordering = ["nome"]


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista escolas"),
    retrieve=extend_schema(tags=["Escolas"], summary="Detalha escola"),
    create=extend_schema(tags=["Escolas"], summary="Cria escola"),
    update=extend_schema(tags=["Escolas"], summary="Atualiza escola"),
    destroy=extend_schema(tags=["Escolas"], summary="Remove escola"),
)
class EscolaViewSet(BaseEscolarViewSet):
    queryset = Escola.objects.select_related("instituicao", "municipio").all()
    serializer_class = EscolaSerializer
    filterset_fields = ["ativo", "instituicao", "municipio"]
    search_fields = ["nome", "sigla", "codigo_inep"]
    ordering = ["nome"]

    def get_queryset(self):
        return filtrar_por_escola(super().get_queryset(), self.request.user, campo="id")


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista cursos"),
    retrieve=extend_schema(tags=["Escolas"], summary="Detalha curso"),
)
class CursoViewSet(BaseEscolarViewSet):
    queryset = Curso.objects.select_related("instituicao").all()
    serializer_class = CursoSerializer
    filterset_fields = ["ativo", "instituicao", "nivel_ensino", "modalidade"]
    search_fields = ["nome", "sigla"]
    ordering = ["nome"]


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista séries"),
    retrieve=extend_schema(tags=["Escolas"], summary="Detalha série"),
)
class SerieViewSet(BaseEscolarViewSet):
    queryset = Serie.objects.select_related("curso").all()
    serializer_class = SerieSerializer
    filterset_fields = ["ativo", "curso"]
    search_fields = ["nome"]
    ordering = ["curso__nome", "etapa"]


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista disciplinas"),
    retrieve=extend_schema(tags=["Escolas"], summary="Detalha disciplina"),
)
class DisciplinaViewSet(BaseEscolarViewSet):
    queryset = Disciplina.objects.select_related("instituicao").all()
    serializer_class = DisciplinaSerializer
    filterset_fields = ["ativo", "instituicao"]
    search_fields = ["nome", "sigla", "area_conhecimento"]
    ordering = ["nome"]


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista turmas"),
    retrieve=extend_schema(tags=["Escolas"], summary="Detalha turma"),
    create=extend_schema(tags=["Escolas"], summary="Cria turma"),
    update=extend_schema(tags=["Escolas"], summary="Atualiza turma"),
    destroy=extend_schema(tags=["Escolas"], summary="Remove turma"),
)
class TurmaViewSet(BaseEscolarViewSet):
    queryset = Turma.objects.select_related("escola", "serie").all()
    serializer_class = TurmaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta, EscopoPorEscolaEscrita]
    filterset_fields = ["ativo", "escola", "serie", "ano", "turno"]
    search_fields = ["nome", "sigla"]
    ordering_fields = ["ano", "nome"]
    ordering = ["-ano", "nome"]

    def get_queryset(self):
        return filtrar_por_escola(super().get_queryset(), self.request.user)


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista anos letivos"),
    create=extend_schema(tags=["Escolas"], summary="Cria ano letivo"),
)
class AnoLetivoViewSet(BaseEscolarViewSet):
    queryset = AnoLetivo.objects.select_related("instituicao").all()
    serializer_class = AnoLetivoSerializer
    filterset_fields = ["instituicao", "ano", "ativo"]
    ordering = ["-ano"]


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista calendários"),
    create=extend_schema(tags=["Escolas"], summary="Cria calendário"),
)
class CalendarioViewSet(BaseEscolarViewSet):
    queryset = Calendario.objects.select_related("ano_letivo", "escola").prefetch_related("dias")
    serializer_class = CalendarioSerializer
    filterset_fields = ["ano_letivo", "escola", "ativo"]
    ordering = ["-ano_letivo__ano"]

    @extend_schema(
        tags=["Escolas"],
        summary="Dias do calendário",
        request=CalendarioDiaSerializer(many=True),
        responses={201: CalendarioDiaSerializer(many=True)},
    )
    @action(detail=True, methods=["get", "post"], url_path="dias")
    def dias(self, request, pk=None):
        calendario = self.get_object()
        if request.method == "GET":
            return Response(CalendarioDiaSerializer(calendario.dias.all(), many=True).data)

        muitos = isinstance(request.data, list)
        serializer = CalendarioDiaSerializer(
            data=request.data, many=muitos, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        itens = serializer.validated_data if muitos else [serializer.validated_data]
        criados = [
            CalendarioDia.objects.update_or_create(
                calendario=calendario, data=item["data"],
                defaults={"tipo": item.get("tipo", "letivo"), "descricao": item.get("descricao", "")},
            )[0]
            for item in itens
        ]
        return Response(
            CalendarioDiaSerializer(criados, many=True).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(tags=["Escolas"], summary="Lista disciplinas por turma"),
    create=extend_schema(tags=["Escolas"], summary="Aloca disciplina/professor na turma"),
)
class TurmaDisciplinaViewSet(BaseEscolarViewSet):
    queryset = TurmaDisciplina.objects.select_related(
        "turma", "disciplina", "professor__pessoa"
    ).all()
    serializer_class = TurmaDisciplinaSerializer
    filterset_fields = ["turma", "disciplina", "professor"]
    search_fields = ["disciplina__nome", "professor__pessoa__nome"]
    ordering = ["turma__nome", "disciplina__nome"]

    def get_queryset(self):
        return filtrar_por_escola(
            super().get_queryset(), self.request.user, campo="turma__escola"
        )
