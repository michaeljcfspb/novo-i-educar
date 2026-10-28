from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import AdminEscreve, SomenteLeituraParaConsulta
from .models import Importacao, Webhook
from .serializers import ImportacaoSerializer, WebhookSerializer
from .services import disparar_webhook, importar_alunos


@extend_schema_view(
    list=extend_schema(tags=["Integrações"], summary="Lista importações"),
    retrieve=extend_schema(tags=["Integrações"], summary="Detalha importação"),
)
class ImportacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Importacao.objects.all()
    serializer_class = ImportacaoSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    filterset_fields = ["tipo", "status"]
    ordering = ["-criado_em"]

    @extend_schema(
        tags=["Integrações"],
        summary="Importa alunos de um CSV",
        request={"multipart/form-data": {"type": "object", "properties": {"arquivo": {"type": "string", "format": "binary"}}}},
        responses={201: ImportacaoSerializer},
    )
    def create(self, request):
        arquivo = request.FILES.get("arquivo")
        if arquivo is None:
            return Response(
                {"arquivo": ["Envie o arquivo CSV no campo 'arquivo'."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        importacao = importar_alunos(
            conteudo=arquivo.read(), nome_arquivo=arquivo.name, usuario=request.user
        )
        return Response(ImportacaoSerializer(importacao).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(tags=["Integrações"], summary="Lista webhooks"),
    create=extend_schema(tags=["Integrações"], summary="Cria webhook"),
)
class WebhookViewSet(viewsets.ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated, AdminEscreve]
    ordering = ["nome"]

    @extend_schema(tags=["Integrações"], summary="Dispara um evento de teste")
    @action(detail=True, methods=["post"], url_path="testar")
    def testar(self, request, pk=None):
        webhook = self.get_object()
        entrega = disparar_webhook(
            webhook, evento="teste", payload={"mensagem": "Evento de teste do i-Educar"}
        )
        return Response(
            {
                "sucesso": entrega.sucesso,
                "status_code": entrega.status_code,
                "erro": entrega.erro,
            }
        )
