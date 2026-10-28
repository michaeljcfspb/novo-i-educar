from django.contrib import admin

from .models import Curso, Disciplina, Escola, Instituicao, Serie, Turma


@admin.register(Instituicao)
class InstituicaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla", "municipio", "ativo")
    search_fields = ("nome", "sigla")


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla", "instituicao", "codigo_inep", "ativo")
    list_filter = ("instituicao", "ativo")
    search_fields = ("nome", "sigla", "codigo_inep")


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla", "instituicao", "nivel_ensino", "ativo")
    list_filter = ("instituicao", "nivel_ensino", "ativo")


@admin.register(Serie)
class SerieAdmin(admin.ModelAdmin):
    list_display = ("nome", "curso", "etapa", "ativo")
    list_filter = ("curso", "ativo")


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla", "instituicao", "ativo")
    list_filter = ("instituicao", "ativo")


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ano", "escola", "serie", "turno", "capacidade", "ativo")
    list_filter = ("ano", "escola", "turno", "ativo")
    search_fields = ("nome", "sigla")
