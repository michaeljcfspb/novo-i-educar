from django.contrib import admin

from .models import Estado, Municipio


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla", "codigo_ibge")
    search_fields = ("nome", "sigla")


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ("nome", "estado", "codigo_ibge")
    list_filter = ("estado",)
    search_fields = ("nome",)
