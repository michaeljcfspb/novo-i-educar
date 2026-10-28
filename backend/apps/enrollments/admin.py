from django.contrib import admin

from .models import Matricula, MatriculaTurma


class MatriculaTurmaInline(admin.TabularInline):
    model = MatriculaTurma
    extra = 0


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "escola", "serie", "ano", "situacao", "ativo")
    list_filter = ("ano", "escola", "situacao", "ativo")
    search_fields = ("aluno__pessoa__nome", "aluno__codigo")
    inlines = [MatriculaTurmaInline]


@admin.register(MatriculaTurma)
class MatriculaTurmaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "turma", "data_enturmacao", "ativo")
    list_filter = ("ativo", "turma")
