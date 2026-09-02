"""
Generador de histórico SINTÉTICO (puerto del prototipo de Fase 1),
usado para entrenar/probar el modelo de riesgo mientras no exista
tracking real de campañas (Fase 2). Ver ARCHITECTURE.md — en cuanto
haya datos reales de MensajeCampana.cayo (no nulo), el management
command de entrenamiento debe preferirlos sobre este generador.
"""

import random

import pandas as pd

DEPARTAMENTOS = ["Finanzas", "Ventas", "RH", "Operaciones", "TI", "Atención a Cliente"]
CANALES = ["email", "sms", "whatsapp"]
CATEGORIAS = [
    "sat", "banco", "paqueteria", "oxxo", "prestamo",
    "rh_nomina", "servicio_tecnico", "factura_electronica", "premio_rifa",
]
DIFICULTADES = ["bajo", "medio", "alto"]
HORAS = ["mañana", "tarde", "noche"]
DISPOSITIVOS = ["escritorio", "movil"]

EFECTO_DEPTO = {"Finanzas": -0.12, "TI": -0.15, "RH": -0.05, "Ventas": 0.05, "Operaciones": 0.05, "Atención a Cliente": 0.03}
EFECTO_CANAL = {"email": 0.0, "sms": 0.05, "whatsapp": 0.08}
EFECTO_DIFICULTAD = {"bajo": -0.10, "medio": 0.0, "alto": 0.15}
EFECTO_CATEGORIA = {
    "premio_rifa": 0.05, "oxxo": 0.04, "rh_nomina": -0.03, "sat": 0.0, "banco": 0.0,
    "paqueteria": 0.02, "prestamo": 0.03, "servicio_tecnico": -0.02, "factura_electronica": 0.0,
}
EFECTO_HORA = {"mañana": 0.0, "tarde": 0.03, "noche": 0.07}
EFECTO_DISPOSITIVO = {"escritorio": 0.0, "movil": 0.05}


def _probabilidad(depto, canal, dificultad, categoria, hora, dispositivo, antiguedad_meses, capacitaciones_previas):
    p = 0.35
    p += EFECTO_DEPTO[depto] + EFECTO_CANAL[canal] + EFECTO_DIFICULTAD[dificultad]
    p += EFECTO_CATEGORIA[categoria] + EFECTO_HORA[hora] + EFECTO_DISPOSITIVO[dispositivo]
    p -= min(0.15, 0.15 * (antiguedad_meses / 120))
    p -= min(0.30, 0.06 * capacitaciones_previas)
    return max(0.03, min(0.90, p))


def generar_historico_df(n_empleados=50, envios_por_empleado_rango=(10, 20), seed=7) -> pd.DataFrame:
    rng = random.Random(seed)
    empleados = [{
        "empleado_id": f"SIM{i:03d}",
        "departamento": rng.choice(DEPARTAMENTOS),
        "antiguedad_meses": rng.randint(1, 120),
        "capacitaciones_previas": rng.choices([0, 1, 2, 3, 4, 5], weights=[30, 25, 20, 12, 8, 5])[0],
    } for i in range(1, n_empleados + 1)]

    filas = []
    for emp in empleados:
        for _ in range(rng.randint(*envios_por_empleado_rango)):
            canal, categoria, dificultad = rng.choice(CANALES), rng.choice(CATEGORIAS), rng.choice(DIFICULTADES)
            hora, dispositivo = rng.choice(HORAS), rng.choice(DISPOSITIVOS)
            p = _probabilidad(emp["departamento"], canal, dificultad, categoria, hora, dispositivo,
                               emp["antiguedad_meses"], emp["capacitaciones_previas"])
            filas.append({**emp, "canal": canal, "categoria": categoria, "dificultad": dificultad,
                          "hora_envio": hora, "dispositivo": dispositivo, "cayo": int(rng.random() < p)})
    return pd.DataFrame(filas)
