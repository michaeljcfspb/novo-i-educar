from django.contrib import admin

from .models import Frequencia


@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "turma", "data", "presente")
    list_filter = ("presente", "data", "turma")
    search_fields = ("matricula__aluno__pessoa__nome",)
