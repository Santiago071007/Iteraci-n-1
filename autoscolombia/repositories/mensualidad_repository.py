from datetime import date
from typing import Optional

from ..models import Mensualidad


class MensualidadRepository:
    def __init__(self, db):
        self.db = db

    def vigente(self, vehiculo_id: int, hoy: date) -> Optional[Mensualidad]:
        fila = self.db.execute(
            """
            SELECT * FROM mensualidad
            WHERE vehiculo_id = ? AND fecha_inicio <= ? AND fecha_fin >= ?
            ORDER BY fecha_fin DESC LIMIT 1
            """,
            (vehiculo_id, hoy.isoformat(), hoy.isoformat()),
        ).fetchone()
        return Mensualidad(**fila) if fila else None

    def crear(self, vehiculo_id, fecha_inicio, fecha_fin, valor) -> int:
        cursor = self.db.execute(
            "INSERT INTO mensualidad (vehiculo_id, fecha_inicio, fecha_fin, valor) VALUES (?, ?, ?, ?)",
            (vehiculo_id, fecha_inicio, fecha_fin, valor),
        )
        return cursor.lastrowid
