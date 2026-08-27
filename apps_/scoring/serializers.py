from rest_framework import serializers

from .models import ScoreRiesgo


class ScoreRiesgoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="empleado.usuario.get_full_name", read_only=True)
    departamento = serializers.CharField(source="empleado.departamento", read_only=True)

    class Meta:
        model = ScoreRiesgo
        fields = ["id", "empleado_nombre", "departamento", "probabilidad", "calculado_en", "version_modelo"]
