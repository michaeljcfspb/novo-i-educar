from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    AdminEscreve,
    EscopoPorEscolaEscrita,
    SomenteLeituraParaConsulta,
    eh_administrador,
    filtrar_por_escola,
)
from apps.enrollments.models import Matricula
from apps.schools.models import TurmaDisciplina
from .models import Nota, PeriodoAvaliacao, RegraAvaliacao
from .serializers import (
    LoteNotasSerializer,
    NotaSerializer,
    PeriodoAvaliacaoSerializer,
    RegraAvaliacaoSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Avaliação"], summary="Lista regras de avaliação"),
    create=extend_schema(tags=["Avaliação"], summary="Cria regra de avaliação"),
)
class RegraAvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = RegraAvaliacao.objects.all()
    serializer_class = RegraAvaliacaoSerializer
    permission_classes = [permissions.IsAuthenticated, AdminEscreve]
    search_fields = ["nome"]
    pagination_class = None


@extend_schema_view(
    list=extend_schema(tags=["Avaliação"], summary="Lista períodos de avaliação"),
    create=extend_schema(tags=["Avaliação"], summary="Cria período de avaliação"),
)
class PeriodoAvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = PeriodoAvaliacao.objects.select_related("ano_letivo").all()
    serializer_class = PeriodoAvaliacaoSerializer
    permission_classes = [permissions.IsAuthenticated, AdminEscreve]
    filterset_fields = ["ano_letivo"]
    ordering = ["-ano_letivo__ano", "ordem"]
    pagination_class = None


@extend_schema_view(
    list=extend_schema(tags=["Avaliação"], summary="Lista notas"),
    create=extend_schema(tags=["Avaliação"], summary="Lança nota"),
    retrieve=extend_schema(tags=["Avaliação"], summary="Detalha nota"),
    update=extend_schema(tags=["Avaliação"], summary="Atualiza nota"),
    destroy=extend_schema(tags=["Avaliação"], summary="Remove nota"),
)
class NotaViewSet(viewsets.ModelViewSet):
    queryset = Nota.objects.select_related(
        "matricula__aluno__pessoa", "turma_disciplina__disciplina", "periodo"
    ).all()
    serializer_class = NotaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta, EscopoPorEscolaEscrita]
    filterset_fields = ["matricula", "turma_disciplina", "periodo", "tipo"]
    ordering = ["matricula__aluno__pessoa__nome", "periodo__ordem"]

    def get_queryset(self):
        qs = filtrar_por_escola(super().get_queryset(), self.request.user, campo="matricula__escola")
        user = self.request.user
        if getattr(user, "perfil", None) == "professor" and user.servidor_id:
            qs = qs.filter(turma_disciplina__professor_id=user.servidor_id)
        return qs

    @extend_schema(
        tags=["Avaliação"],
        summary="Lança notas da turma/disciplina em lote",
        request=LoteNotasSerializer,
        responses={201: NotaSerializer(many=True)},
    )
    @action(detail=False, methods=["post"], url_path="lote")
    @transaction.atomic
    def lote(self, request):
        entrada = LoteNotasSerializer(data=request.data, context={"request": request})
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data

        turma_disciplina = TurmaDisciplina.objects.filter(pk=dados["turma_disciplina"]).first()
        if turma_disciplina is None:
            return Response(
                {"turma_disciplina": ["Disciplina da turma inexistente."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not eh_administrador(request.user) and request.user.escola_id not in (
            None, turma_disciplina.turma.escola_id,
        ):
            return Response(
                {"detail": "Você só pode lançar notas da sua escola."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if getattr(request.user, "perfil", None) == "professor" and request.user.servidor_id:
            if turma_disciplina.professor_id != request.user.servidor_id:
                return Response(
                    {"detail": "Você só pode lançar notas das suas turmas."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        from apps.assessment.models import PeriodoAvaliacao as Periodo
        from apps.assessment.services import validar_nota

        periodo = Periodo.objects.filter(pk=dados["periodo"]).first()
        if periodo is None:
            return Response(
                {"periodo": ["Período inexistente."]}, status=status.HTTP_400_BAD_REQUEST
            )

        criadas = []
        erros = []
        for registro in dados["registros"]:
            matricula = Matricula.objects.filter(pk=registro["matricula"]).first()
            if matricula is None:
                erros.append({"matricula": registro["matricula"], "erro": "Matrícula inexistente."})
                continue
            erro = validar_nota(matricula, turma_disciplina, periodo, registro["valor"])
            if erro:
                erros.append({"matricula": matricula.id, "erro": erro})
                continue
            nota, _ = Nota.objects.update_or_create(
                matricula=matricula,
                turma_disciplina=turma_disciplina,
                periodo_id=dados["periodo"],
                tipo=dados["tipo"],
                defaults={
                    "valor": registro["valor"],
                    "observacao": registro.get("observacao", ""),
                    "criado_por": request.user,
                },
            )
            criadas.append(nota)
        if erros and not criadas:
            return Response({"erros": erros}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"criadas": NotaSerializer(criadas, many=True).data, "erros": erros},
            status=status.HTTP_201_CREATED,
        )
