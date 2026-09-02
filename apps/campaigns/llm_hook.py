"""
Interfaz de proveedor de generación (igual que en el prototipo Fase 1).
RuleBasedProvider es el default activo hoy. ClaudeProvider queda listo
para cuando haya presupuesto de API — activarlo es cambiar una línea
en la vista/tarea que arma campañas, sin tocar plantillas ni modelos.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from .generator import VariationEngine


class LLMProvider(ABC):
    @abstractmethod
    def generar(
        self, plantilla, perfil_empleado
    ) -> tuple[Optional[str], str, Optional[str]]:
        """Devuelve (asunto, cuerpo, link_falso_visible)."""
        raise NotImplementedError


class RuleBasedProvider(LLMProvider):
    def __init__(
        self, seed: int = None, dominio_links: str = "simulacro-ciberentrena.local"
    ):
        self.engine = VariationEngine(seed=seed, dominio_links=dominio_links)

    def generar(self, plantilla, perfil_empleado):
        return self.engine.generar_variacion(plantilla, perfil_empleado)


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str = None, modelo: str = "claude-sonnet-5"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.modelo = modelo
        if not self.api_key:
            raise ValueError(
                "ClaudeProvider requiere ANTHROPIC_API_KEY. Mientras tanto usa RuleBasedProvider."
            )

    def generar(self, plantilla, perfil_empleado):
        import anthropic

        engine = VariationEngine()
        asunto_base, cuerpo_base, link_falso = engine.generar_variacion(
            plantilla, perfil_empleado
        )

        client = anthropic.Anthropic(api_key=self.api_key)
        prompt = (
            "Reescribe el siguiente mensaje de simulacro de phishing manteniendo el "
            "mismo engaño, canal, urgencia y datos (montos, fechas, links), con "
            f"redacción distinta:\n\nAsunto: {asunto_base}\nCuerpo: {cuerpo_base}"
        )
        respuesta = client.messages.create(
            model=self.modelo,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return asunto_base, respuesta.content[0].text, link_falso
