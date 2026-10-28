from rest_framework import serializers

from .models import PerfilUsuario, User


class UsuarioSerializer(serializers.ModelSerializer):
    perfil_display = serializers.CharField(source="get_perfil_display", read_only=True)
    escola_nome = serializers.CharField(source="escola.nome", read_only=True, default=None)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nome_completo",
            "perfil",
            "perfil_display",
            "escola",
            "escola_nome",
            "servidor",
            "aluno",
            "is_active",
            "ultimo_acesso",
        )
        read_only_fields = ("id", "ultimo_acesso", "is_active")


class UsuarioEscritaSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = User
        fields = ("id", "email", "nome_completo", "perfil", "escola", "is_active", "password")

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Informe a senha inicial."})
        return attrs

    def create(self, validated_data):
        senha = validated_data.pop("password")
        return User.objects.create_user(password=senha, **validated_data)

    def update(self, instance, validated_data):
        senha = validated_data.pop("password", None)
        usuario = super().update(instance, validated_data)
        if senha:
            usuario.set_password(senha)
            usuario.save(update_fields=["password"])
        return usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(read_only=True)
    perfil = serializers.ChoiceField(choices=PerfilUsuario.choices, read_only=True)
