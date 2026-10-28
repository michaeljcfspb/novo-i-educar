from rest_framework import serializers

from apps.core.permissions import validar_escola_do_usuario
from .models import Frequencia


class FrequenciaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source="matricula.aluno.pessoa.nome", read_only=True)

    class Meta:
        model = Frequencia
        fields = ("id", "matricula", "aluno_nome", "turma", "data", "presente", "justificativa")
        read_only_fields = ("id",)

    def validate(self, attrs):
        matricula = attrs.get("matricula", getattr(self.instance, "matricula", None))
        turma = attrs.get("turma", getattr(self.instance, "turma", None))
        if matricula and turma and matricula.escola_id != turma.escola_id:
            raise serializers.ValidationError({"turma": "A turma pertence a outra escola."})
        if matricula:
            request = self.context.get("request")
            if request:
                validar_escola_do_usuario(request.user, matricula.escola_id)
        return attrs


class RegistroFrequenciaSerializer(serializers.Serializer):
    matricula = serializers.IntegerField()
    presente = serializers.BooleanField(default=True)
    justificativa = serializers.CharField(required=False, allow_blank=True, default="")


class LoteFrequenciaSerializer(serializers.Serializer):
    turma = serializers.IntegerField()
    data = serializers.DateField()
    registros = RegistroFrequenciaSerializer(many=True)
