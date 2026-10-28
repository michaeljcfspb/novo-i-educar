from django.contrib import admin

from .models import Documento, HistoricoDisciplina, HistoricoEscolar, Transferencia


class HistoricoDisciplinaInline(admin.TabularInline):
    model = HistoricoDisciplina
    extra = 0


@admin.register(HistoricoEscolar)
class HistoricoEscolarAdmin(admin.ModelAdmin):
    list_display = ("aluno", "ano", "serie", "situacao", "media_geral", "frequencia_percentual")
    list_filter = ("ano", "situacao", "escola")
    search_fields = ("aluno__pessoa__nome",)
    inlines = [HistoricoDisciplinaInline]


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "tipo", "data", "escola_origem", "escola_destino", "motivo")
    list_filter = ("tipo", "motivo", "data")
    search_fields = ("matricula__aluno__pessoa__nome",)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("numero", "tipo", "aluno", "emitido_em")
    list_filter = ("tipo",)
    search_fields = ("numero", "aluno__pessoa__nome")
