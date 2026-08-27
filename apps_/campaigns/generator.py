"""
Motor de variación de plantillas — puerto del prototipo de Fase 1
(ver el proyecto original `ciberentrena/src/generator.py`) para
trabajar directamente contra los modelos de Django (PlantillaPhishing,
PerfilEmpleado) en vez de JSON/dataclasses sueltos.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional


class VariationEngine:
    BANCOS = ["BBVA", "Banorte", "Santander", "Banamex", "HSBC", "Banco Azteca"]
    PAQUETERIAS = ["DHL", "Estafeta", "Correos de México", "FedEx", "Paquetexpress"]
    AGENTES_FALSOS = ["Carlos Ramírez", "Ana Torres", "Luis Mendoza", "Sofía Herrera"]

    URGENCIA_SINONIMOS = {
        "de inmediato": ["ahora mismo", "sin demora", "a la brevedad"],
        "urgente": ["prioritario", "inmediato", "de carácter urgente"],
        "antes de que expire": ["antes de que venza", "antes de que se agote"],
    }

    def __init__(self, seed: int = None, dominio_links: str = "simulacro-ciberentrena.local"):
        self._rng = random.Random(seed)
        self.dominio_links = dominio_links

    def _monto(self) -> str:
        return f"{self._rng.randint(800, 45000):,}"

    def _fecha_futura(self) -> str:
        dias = self._rng.randint(1, 10)
        return (datetime.now() + timedelta(days=dias)).strftime("%d/%m/%Y")

    def _link_falso(self, categoria: str) -> str:
        dominios = [
            f"{self.dominio_links}/{categoria}",
            f"verificacion-{categoria}.{self.dominio_links}",
            f"portal-{categoria}-mx.{self.dominio_links}",
        ]
        return "https://" + self._rng.choice(dominios) + f"/{self._rng.randint(1000, 9999)}"

    def _guia(self) -> str:
        return "".join(self._rng.choices("0123456789", k=10))

    def _folio(self) -> str:
        return "".join(self._rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))

    def _aplicar_sinonimos(self, texto: str) -> str:
        for frase, alternativas in self.URGENCIA_SINONIMOS.items():
            if frase in texto and self._rng.random() < 0.6:
                texto = texto.replace(frase, self._rng.choice(alternativas), 1)
        return texto

    def rellenar_variables(self, plantilla, perfil_empleado) -> dict:
        categoria = plantilla.categoria
        return {
            "nombre": perfil_empleado.usuario.get_full_name() or perfil_empleado.usuario.username,
            "empresa": getattr(perfil_empleado.usuario, "empresa_nombre", "tu empresa"),
            "departamento": perfil_empleado.departamento or "General",
            "monto": self._monto(),
            "anio": str(datetime.now().year - 1),
            "fecha": self._fecha_futura(),
            "link_falso": self._link_falso(categoria),
            "banco": self._rng.choice(self.BANCOS),
            "paqueteria": self._rng.choice(self.PAQUETERIAS),
            "agente_falso": self._rng.choice(self.AGENTES_FALSOS),
            "guia": self._guia(),
            "folio": self._folio(),
        }

    def generar_variacion(self, plantilla, perfil_empleado) -> tuple[Optional[str], str]:
        valores = self.rellenar_variables(plantilla, perfil_empleado)

        def render(texto: Optional[str]) -> Optional[str]:
            if not texto:
                return texto
            out = texto
            for var, val in valores.items():
                out = out.replace("{" + var + "}", str(val))
            return self._aplicar_sinonimos(out)

        return render(plantilla.asunto), render(plantilla.cuerpo)
