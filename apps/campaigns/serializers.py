from rest_framework import serializers

from .models import Campana, MensajeCampana


class MensajeCampanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensajeCampana
        # Deliberadamente NO se expone cuerpo_final completo por API salvo
        # a admin_pyme/superadmin — para un endpoint de solo-lectura de
        # progreso, basta con el estado.
        fields = ["id", "empleado", "plantilla", "enviado_en", "abierto", "cayo"]


class CampanaSerializer(serializers.ModelSerializer):
    mensajes = MensajeCampanaSerializer(many=True, read_only=True)

    class Meta:
        model = Campana
        fields = ["id", "nombre", "consentimiento_explicito", "fecha_creacion", "fecha_envio", "mensajes"]
        read_only_fields = ["fecha_creacion", "fecha_envio"]
