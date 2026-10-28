from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import SomenteLeituraParaConsulta, eh_administrador, filtrar_por_escola
from apps.schools.models import Escola

from .models import ExportacaoCenso
from .serializers import ExportacaoCensoSerializer, GerarCensoSerializer
from .services import gerar_exportacao, montar_payload


@extend_schema_view(
    list=extend_schema(tags=["Censo"], summary="Lista exportações do censo"),
    retrieve=extend_schema(tags=["Censo"], summary="Detalha exportação"),
)
class ExportacaoCensoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExportacaoCenso.objects.select_related("escola").all()
    serializer_class = ExportacaoCensoSerializer
    permission_classes = [permissions.IsAuthenticated, SomenteLeituraParaConsulta]
    filterset_fields = ["escola", "ano", "status"]
    ordering = ["-ano", "-versao"]

    def get_queryset(self):
        return filtrar_por_escola(super().get_queryset(), self.request.user)

    def _escola_do_pedido(self, escola_id):
        escola = Escola.objects.filter(pk=escola_id).first()
        if escola is None:
            return None, Response(
                {"escola": ["Escola inexistente."]}, status=status.HTTP_400_BAD_REQUEST
            )
        if not eh_administrador(self.request.user) and self.request.user.escola_id not in (
            None, escola.id,
        ):
            return None, Response(
                {"detail": "Você só pode exportar o censo da sua escola."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return escola, None

    @extend_schema(
        tags=["Censo"],
        summary="Gera o pacote de exportação do censo",
        request=GerarCensoSerializer,
        responses={201: ExportacaoCensoSerializer},
    )
    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request):
        entrada = GerarCensoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        escola, erro = self._escola_do_pedido(entrada.validated_data["escola"])
        if erro:
            return erro
        exportacao = gerar_exportacao(
            escola, entrada.validated_data["ano"], usuario=request.user
        )
        return Response(
            ExportacaoCensoSerializer(exportacao).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=["Censo"],
        summary="Pré-visualiza pendências sem gerar arquivo",
        request=GerarCensoSerializer,
    )
    @action(detail=False, methods=["post"], url_path="preview")
    def preview(self, request):
        entrada = GerarCensoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        escola, erro = self._escola_do_pedido(entrada.validated_data["escola"])
        if erro:
            return erro
        payload, pendencias = montar_payload(escola, entrada.validated_data["ano"])
        return Response({"totais": payload["totais"], "pendencias": pendencias})
