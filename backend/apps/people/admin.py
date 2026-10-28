from django.contrib import admin

from .models import Aluno, Deficiencia, Pessoa, Servidor


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "cpf", "email", "municipio", "ativo")
    list_filter = ("tipo", "ativo", "sexo")
    search_fields = ("nome", "cpf", "email")


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "pessoa", "ativo")
    list_filter = ("ativo",)
    search_fields = ("codigo", "pessoa__nome")
    filter_horizontal = ("deficiencias",)


@admin.register(Deficiencia)
class DeficienciaAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo_censo")
    search_fields = ("nome",)


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ("matricula_funcional", "pessoa", "cargo", "escola", "ativo")
    list_filter = ("cargo", "escola", "ativo")
    search_fields = ("pessoa__nome", "matricula_funcional")
    filter_horizontal = ("disciplinas",)
