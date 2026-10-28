from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("nome_completo",)
    list_display = ("email", "nome_completo", "perfil", "escola", "is_active", "is_staff")
    list_filter = ("perfil", "is_active", "is_staff", "escola")
    search_fields = ("email", "nome_completo")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("nome_completo", "perfil", "escola")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("ultimo_acesso", "criado_em", "atualizado_em")}),
    )
    readonly_fields = ("criado_em", "atualizado_em", "ultimo_acesso")
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "nome_completo", "perfil", "escola", "password1", "password2")}),
    )
