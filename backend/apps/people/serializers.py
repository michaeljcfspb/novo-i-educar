from rest_framework import serializers

from .models import Aluno, Deficiencia, Pessoa, Servidor


class DeficienciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deficiencia
        fields = ("id", "nome", "codigo_censo")


class PessoaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    municipio_nome = serializers.CharField(source="municipio.nome", read_only=True, default=None)

    class Meta:
        model = Pessoa
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "nome",
            "nome_social",
            "cpf",
            "cnpj",
            "data_nascimento",
            "sexo",
            "email",
            "telefone",
            "nome_mae",
            "nome_pai",
            "nacionalidade",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "municipio",
            "municipio_nome",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate(self, attrs):
        tipo = attrs.get("tipo", getattr(self.instance, "tipo", None))
        if tipo == "fisica" and attrs.get("cnpj"):
            raise serializers.ValidationError({"cnpj": "Pessoa física não deve ter CNPJ."})
        if tipo == "juridica" and attrs.get("cpf"):
            raise serializers.ValidationError({"cpf": "Pessoa jurídica não deve ter CPF."})
        return attrs


class AlunoSerializer(serializers.ModelSerializer):
    pessoa = PessoaSerializer()
    deficiencias = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Deficiencia.objects.all(), required=False
    )
    deficiencias_detalhe = DeficienciaSerializer(source="deficiencias", many=True, read_only=True)
    nome = serializers.CharField(source="pessoa.nome", read_only=True)

    class Meta:
        model = Aluno
        fields = (
            "id",
            "codigo",
            "nome",
            "pessoa",
            "deficiencias",
            "deficiencias_detalhe",
            "ativo",
            "foto",
            "usa_transporte_escolar",
            "recebe_escolarizacao_outro_espaco",
            "observacoes",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("id", "codigo", "criado_em", "atualizado_em")

    def create(self, validated_data):
        pessoa_data = validated_data.pop("pessoa")
        deficiencias = validated_data.pop("deficiencias", [])
        pessoa = Pessoa.objects.create(**pessoa_data)
        aluno = Aluno.objects.create(pessoa=pessoa, **validated_data)
        aluno.deficiencias.set(deficiencias)
        return aluno

    def update(self, instance, validated_data):
        pessoa_data = validated_data.pop("pessoa", None)
        deficiencias = validated_data.pop("deficiencias", None)
        if pessoa_data:
            for campo, valor in pessoa_data.items():
                setattr(instance.pessoa, campo, valor)
            instance.pessoa.save()
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()
        if deficiencias is not None:
            instance.deficiencias.set(deficiencias)
        return instance


class ServidorSerializer(serializers.ModelSerializer):
    pessoa = PessoaSerializer()
    cargo_display = serializers.CharField(source="get_cargo_display", read_only=True)
    escola_nome = serializers.CharField(source="escola.nome", read_only=True)
    disciplinas_detalhe = DeficienciaSerializer(source="disciplinas", many=True, read_only=True)
    nome = serializers.CharField(source="pessoa.nome", read_only=True)

    class Meta:
        model = Servidor
        fields = (
            "id", "matricula_funcional", "nome", "pessoa", "cargo", "cargo_display", "escola",
            "escola_nome", "disciplinas", "disciplinas_detalhe", "data_admissao", "ativo",
            "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "matricula_funcional", "criado_em", "atualizado_em")

    def validate(self, attrs):
        request = self.context.get("request")
        escola = attrs.get("escola", getattr(self.instance, "escola", None))
        if request and escola:
            from apps.core.permissions import validar_escola_do_usuario

            validar_escola_do_usuario(request.user, escola.id)
        return attrs

    def create(self, validated_data):
        pessoa_data = validated_data.pop("pessoa")
        disciplinas = validated_data.pop("disciplinas", [])
        pessoa = Pessoa.objects.create(**pessoa_data)
        servidor = Servidor.objects.create(pessoa=pessoa, **validated_data)
        servidor.disciplinas.set(disciplinas)
        return servidor

    def update(self, instance, validated_data):
        pessoa_data = validated_data.pop("pessoa", None)
        disciplinas = validated_data.pop("disciplinas", None)
        if pessoa_data:
            for campo, valor in pessoa_data.items():
                setattr(instance.pessoa, campo, valor)
            instance.pessoa.save()
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()
        if disciplinas is not None:
            instance.disciplinas.set(disciplinas)
        return instance
