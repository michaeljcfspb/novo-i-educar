from rest_framework import serializers

from .models import (
    AnoLetivo,
    Calendario,
    CalendarioDia,
    Curso,
    Disciplina,
    Escola,
    Instituicao,
    Serie,
    Turma,
    TurmaDisciplina,
)


class InstituicaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instituicao
        fields = (
            "id", "nome", "sigla", "cnpj", "email", "telefone", "municipio", "ativo",
            "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class EscolaSerializer(serializers.ModelSerializer):
    instituicao_nome = serializers.CharField(source="instituicao.nome", read_only=True)

    class Meta:
        model = Escola
        fields = (
            "id", "instituicao", "instituicao_nome", "nome", "sigla", "codigo_inep", "email",
            "telefone", "cep", "logradouro", "numero", "bairro", "municipio", "ativo",
            "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class CursoSerializer(serializers.ModelSerializer):
    nivel_ensino_display = serializers.CharField(source="get_nivel_ensino_display", read_only=True)

    class Meta:
        model = Curso
        fields = (
            "id", "instituicao", "nome", "sigla", "nivel_ensino", "nivel_ensino_display",
            "modalidade", "carga_horaria", "ativo", "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class SerieSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)

    class Meta:
        model = Serie
        fields = (
            "id", "curso", "curso_nome", "nome", "etapa", "carga_horaria", "regra_avaliacao",
            "idade_inicial", "idade_final", "ativo", "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate(self, attrs):
        inicial = attrs.get("idade_inicial", getattr(self.instance, "idade_inicial", 0))
        final = attrs.get("idade_final", getattr(self.instance, "idade_final", 0))
        if final and inicial and final < inicial:
            raise serializers.ValidationError(
                {"idade_final": "A idade final não pode ser menor que a inicial."}
            )
        return attrs


class DisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplina
        fields = (
            "id", "instituicao", "nome", "sigla", "area_conhecimento", "carga_horaria", "ativo",
            "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class TurmaSerializer(serializers.ModelSerializer):
    escola_nome = serializers.CharField(source="escola.nome", read_only=True)
    serie_nome = serializers.CharField(source="serie.nome", read_only=True)
    vagas_disponiveis = serializers.IntegerField(read_only=True)

    class Meta:
        model = Turma
        fields = (
            "id", "escola", "escola_nome", "serie", "serie_nome", "nome", "sigla", "ano",
            "turno", "capacidade", "vagas_disponiveis", "ativo", "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class AnoLetivoSerializer(serializers.ModelSerializer):
    instituicao_nome = serializers.CharField(source="instituicao.nome", read_only=True)

    class Meta:
        model = AnoLetivo
        fields = (
            "id", "instituicao", "instituicao_nome", "ano", "data_inicio", "data_fim", "ativo",
            "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate(self, attrs):
        inicio = attrs.get("data_inicio", getattr(self.instance, "data_inicio", None))
        fim = attrs.get("data_fim", getattr(self.instance, "data_fim", None))
        if inicio and fim and fim < inicio:
            raise serializers.ValidationError({"data_fim": "O término não pode ser anterior ao início."})
        return attrs


class CalendarioDiaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = CalendarioDia
        fields = ("id", "calendario", "data", "tipo", "tipo_display", "descricao")
        read_only_fields = ("id",)


class CalendarioSerializer(serializers.ModelSerializer):
    dias = CalendarioDiaSerializer(many=True, read_only=True)
    dias_letivos = serializers.IntegerField(read_only=True)
    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)

    class Meta:
        model = Calendario
        fields = ("id", "ano_letivo", "ano", "escola", "nome", "ativo", "dias", "dias_letivos")
        read_only_fields = ("id", "dias", "dias_letivos", "ano")


class TurmaDisciplinaSerializer(serializers.ModelSerializer):
    disciplina_nome = serializers.CharField(source="disciplina.nome", read_only=True)
    professor_nome = serializers.CharField(source="professor.pessoa.nome", read_only=True, default=None)
    turma_nome = serializers.CharField(source="turma.nome", read_only=True)

    class Meta:
        model = TurmaDisciplina
        fields = (
            "id", "turma", "turma_nome", "disciplina", "disciplina_nome", "professor",
            "professor_nome", "carga_horaria", "criado_em", "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate(self, attrs):
        turma = attrs.get("turma", getattr(self.instance, "turma", None))
        professor = attrs.get("professor", getattr(self.instance, "professor", None))
        if turma and professor and professor.escola_id != turma.escola_id:
            raise serializers.ValidationError(
                {"professor": "O professor está lotado em outra escola."}
            )
        return attrs
