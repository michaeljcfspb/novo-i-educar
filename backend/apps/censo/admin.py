from django.contrib import admin

from .models import ExportacaoCenso


@admin.register(ExportacaoCenso)
class ExportacaoCensoAdmin(admin.ModelAdmin):
    list_display = ("escola", "ano", "versao", "status", "total_alunos", "total_turmas", "criado_em")
    list_filter = ("ano", "status", "escola")
