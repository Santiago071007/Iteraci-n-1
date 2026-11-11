from typing import List, Optional

from ..models import Celda


class CeldaRepository:
    def __init__(self, db):
        self.db = db

    def obtener(self, celda_id: int) -> Optional[Celda]:
        fila = self.db.execute("SELECT * FROM celda WHERE id = ?", (celda_id,)).fetchone()
        return Celda(**fila) if fila else None

    def libres(self, tipo_vehiculo: Optional[str] = None) -> List[Celda]:
        sql = "SELECT * FROM celda WHERE estado = 'LIBRE'"
        parametros = ()
        if tipo_vehiculo:
            sql += " AND tipo_vehiculo = ?"
            parametros = (tipo_vehiculo,)
        return [Celda(**f) for f in self.db.execute(sql + " ORDER BY codigo", parametros)]

    def cambiar_estado(self, celda_id: int, estado: str):
        self.db.execute("UPDATE celda SET estado = ? WHERE id = ?", (estado, celda_id))

    def mapa(self):
        return self.db.execute(
            """
            SELECT c.*, v.placa, r.fecha_entrada
            FROM celda c
            LEFT JOIN registro_parqueo r ON r.celda_id = c.id AND r.fecha_salida IS NULL
            LEFT JOIN vehiculo v ON v.id = r.vehiculo_id
            ORDER BY c.codigo
            """
        ).fetchall()

    def resumen(self):
        return self.db.execute(
            """
            SELECT tipo_vehiculo,
                   COUNT(*) AS total,
                   SUM(estado = 'LIBRE') AS libres,
                   SUM(estado = 'OCUPADA') AS ocupadas,
                   SUM(estado = 'MANTENIMIENTO') AS mantenimiento
            FROM celda GROUP BY tipo_vehiculo ORDER BY tipo_vehiculo
            """
        ).fetchall()
