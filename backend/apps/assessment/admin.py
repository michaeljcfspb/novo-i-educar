from django.contrib import admin

from .models import Nota, PeriodoAvaliacao, RegraAvaliacao


@admin.register(RegraAvaliacao)
class RegraAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_media", "nota_maxima", "media_aprovacao", "percentual_frequencia")


@admin.register(PeriodoAvaliacao)
class PeriodoAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ano_letivo", "ordem", "data_inicio", "data_fim")
    list_filter = ("ano_letivo",)


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "turma_disciplina", "periodo", "tipo", "valor")
    list_filter = ("periodo", "tipo", "turma_disciplina")
    search_fields = ("matricula__aluno__pessoa__nome",)
