from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import (
    EscopoPorEscolaEscrita,
    SomenteLeituraParaConsulta,
    filtrar_por_escola,
)
from apps.enrollments.models import Matricula
from apps.people.models import Aluno
from .models import Documento, HistoricoEscolar, Transferencia
from .serializers import (
    DocumentoSerializer,
    EmitirDocumentoSerializer,
    HistoricoEscolarSerializer,
    TransferenciaSerializer,
)
from .services import emitir_documento, gerar_historico, registrar_transferencia


@extend_schema_view(
    list=extend_schema(tags=["Histórico"], summary="Lista históricos escolares"),
    retrieve=extend_schema(tags=["Histórico"], summary="Detalha histórico"),
)
class HistoricoViewSet(viewsets.ModelViewSet):
    queryset = HistoricoEscolar.objects.select_related(
        "aluno__pessoa", "escola", "serie"
    ).prefetch_related("disciplinas")
    serializer_class = HistoricoEscolarSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta, EscopoPorEscolaEscrita]
    filterset_fields = ["aluno", "ano", "escola", "serie", "situacao"]
    search_fields = ["aluno__pessoa__nome"]
    ordering = ["-ano"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return filtrar_por_escola(super().get_queryset(), self.request.user)

    @extend_schema(tags=["Histórico"], summary="Histórico escolar em PDF")
    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        from django.http import HttpResponse

        from apps.reports.pdf import historico_pdf

        historico = self.get_object()
        conteudo = historico_pdf(historico)
        resposta = HttpResponse(conteudo, content_type="application/pdf")
        resposta["Content-Disposition"] = f'inline; filename="historico-{historico.id}.pdf"'
        return resposta

    @extend_schema(
        tags=["Histórico"],
        summary="Gera/atualiza o histórico de uma matrícula",
        request={"application/json": {"type": "object", "properties": {"matricula": {"type": "integer"}}}},
        responses={201: HistoricoEscolarSerializer},
    )
    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request):
        matricula_id = request.data.get("matricula")
        matricula = Matricula.objects.filter(pk=matricula_id).first()
        if matricula is None:
            return Response({"matricula": ["Matrícula inexistente."]}, status=status.HTTP_400_BAD_REQUEST)
        from apps.core.permissions import eh_administrador

        if not eh_administrador(request.user) and request.user.escola_id not in (
            None, matricula.escola_id,
        ):
            return Response(
                {"detail": "Você só pode gerar histórico da sua escola."},
                status=status.HTTP_403_FORBIDDEN,
            )
        historico = gerar_historico(matricula, usuario=request.user)
        return Response(
            HistoricoEscolarSerializer(historico).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(tags=["Histórico"], summary="Lista transferências"),
    create=extend_schema(tags=["Histórico"], summary="Registra transferência"),
)
class TransferenciaViewSet(viewsets.ModelViewSet):
    queryset = Transferencia.objects.select_related(
        "matricula__aluno__pessoa", "escola_origem", "escola_destino"
    ).all()
    serializer_class = TransferenciaSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta, EscopoPorEscolaEscrita]
    filterset_fields = ["matricula", "tipo", "motivo"]
    ordering = ["-data"]

    def get_queryset(self):
        return filtrar_por_escola(
            super().get_queryset(), self.request.user, campo="matricula__escola"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        matricula = dados["matricula"]
        if matricula.transferencias.filter(tipo="saida").exists() and dados["tipo"] == "saida":
            return Response(
                {"detail": "Esta matrícula já possui transferência de saída registrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transferencia = registrar_transferencia(
            matricula=matricula,
            tipo=dados["tipo"],
            data_movimento=dados["data"],
            escola_destino=dados.get("escola_destino"),
            motivo=dados.get("motivo", "pedido_responsavel"),
            observacao=dados.get("observacao", ""),
            usuario=request.user,
        )
        return Response(
            TransferenciaSerializer(transferencia).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(tags=["Documentos"], summary="Lista documentos emitidos"),
    retrieve=extend_schema(tags=["Documentos"], summary="Detalha documento"),
)
class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.select_related("aluno__pessoa", "matricula").all()
    serializer_class = DocumentoSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta, EscopoPorEscolaEscrita]
    filterset_fields = ["aluno", "matricula", "tipo"]
    search_fields = ["aluno__pessoa__nome", "numero"]
    ordering = ["-emitido_em"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return filtrar_por_escola(
            super().get_queryset(), self.request.user, campo="matricula__escola"
        )

    @extend_schema(
        tags=["Documentos"],
        summary="Emite declaração/histórico/guia de transferência",
        request=EmitirDocumentoSerializer,
        responses={201: DocumentoSerializer},
    )
    @action(detail=False, methods=["post"], url_path="emitir")
    def emitir(self, request):
        entrada = EmitirDocumentoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        aluno = Aluno.objects.filter(pk=entrada.validated_data["aluno"]).first()
        if aluno is None:
            return Response({"aluno": ["Aluno inexistente."]}, status=status.HTTP_400_BAD_REQUEST)
        matricula = None
        if entrada.validated_data.get("matricula"):
            matricula = Matricula.objects.filter(pk=entrada.validated_data["matricula"]).first()
        documento = emitir_documento(
            aluno=aluno,
            tipo=entrada.validated_data["tipo"],
            matricula=matricula,
            usuario=request.user,
        )
        return Response(DocumentoSerializer(documento).data, status=status.HTTP_201_CREATED)
