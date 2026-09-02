"""
Modelo baseline de scoring de riesgo (puerto directo del prototipo de
Fase 1 — misma Regresión Logística, ahora reutilizable dentro de
Django). No depende de Django directamente: recibe/entrega DataFrames,
así que también se puede probar con pytest sin necesidad de una BD.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

COLUMNAS_CATEGORICAS = ["departamento", "canal", "categoria", "dificultad", "hora_envio", "dispositivo"]
COLUMNAS_NUMERICAS = ["antiguedad_meses", "capacitaciones_previas"]
COLUMNA_OBJETIVO = "cayo"


class RiskScorer:
    def __init__(self):
        preprocesador = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), COLUMNAS_CATEGORICAS),
                ("num", StandardScaler(), COLUMNAS_NUMERICAS),
            ]
        )
        self.pipeline = Pipeline(steps=[
            ("preprocesador", preprocesador),
            ("clasificador", LogisticRegression(max_iter=1000)),
        ])
        self._entrenado = False

    def entrenar_desde_dataframe(self, df: pd.DataFrame, test_size: float = 0.25, random_state: int = 42) -> dict:
        X = df[COLUMNAS_CATEGORICAS + COLUMNAS_NUMERICAS]
        y = df[COLUMNA_OBJETIVO]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        self.pipeline.fit(X_train, y_train)
        self._entrenado = True

        y_pred = self.pipeline.predict(X_test)
        y_proba = self.pipeline.predict_proba(X_test)[:, 1]

        return {
            "n_train": len(X_train),
            "n_test": len(X_test),
            "accuracy": accuracy_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "reporte": classification_report(y_test, y_pred, zero_division=0),
        }

    def predecir_proba(self, df: pd.DataFrame) -> pd.Series:
        if not self._entrenado:
            raise RuntimeError("El modelo aún no ha sido entrenado.")
        return pd.Series(self.pipeline.predict_proba(df)[:, 1], index=df.index)

    def guardar(self, ruta: str):
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, ruta)

    @staticmethod
    def cargar(ruta: str) -> "RiskScorer":
        return joblib.load(ruta)
