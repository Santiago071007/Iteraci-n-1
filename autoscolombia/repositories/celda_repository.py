from typing import List, Optional

from ..models import Celda


class CeldaRepository:
    def __init__(self, db):
        self.db = db

    def obtener(self, celda_id: int) -> Optional[Celda]:
        fila = self.db.execute("SELECT * FROM celda WHERE id = ?", (celda_id,)).fetchone()
        return Celda(**fila) if fila else None

    def buscar_por_codigo(self, codigo: str) -> Optional[Celda]:
        fila = self.db.execute("SELECT * FROM celda WHERE codigo = ?", (codigo,)).fetchone()
        return Celda(**fila) if fila else None

    def libres(self, tipo_vehiculo: Optional[str] = None) -> List[Celda]:
        sql = "SELECT * FROM celda WHERE estado = 'LIBRE'"
        parametros = ()
        if tipo_vehiculo:
            sql += " AND tipo_vehiculo = ?"
            parametros = (tipo_vehiculo,)
        return [Celda(**f) for f in self.db.execute(sql + " ORDER BY codigo", parametros)]

    def crear(self, codigo: str, tipo_vehiculo: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO celda (codigo, tipo_vehiculo, estado) VALUES (?, ?, 'LIBRE')", (codigo, tipo_vehiculo)
        )
        return cursor.lastrowid

    def actualizar(self, celda_id: int, codigo: str, tipo_vehiculo: str):
        self.db.execute("UPDATE celda SET codigo = ?, tipo_vehiculo = ? WHERE id = ?", (codigo, tipo_vehiculo, celda_id))

    def cambiar_estado(self, celda_id: int, estado: str, observacion: Optional[str] = None):
        self.db.execute(
            "UPDATE celda SET estado = ?, observacion = ? WHERE id = ?", (estado, observacion, celda_id)
        )

    def eliminar(self, celda_id: int):
        self.db.execute("DELETE FROM celda WHERE id = ?", (celda_id,))

    def total_registros(self, celda_id: int) -> int:
        return self.db.execute("SELECT COUNT(*) FROM registro_parqueo WHERE celda_id = ?", (celda_id,)).fetchone()[0]

    def historial(self, celda_id: int, limite: int = 20):
        return self.db.execute(
            """
            SELECT r.*, v.placa, cl.nombres AS cliente
            FROM registro_parqueo r
            JOIN vehiculo v ON v.id = r.vehiculo_id
            JOIN cliente cl ON cl.id = v.cliente_id
            WHERE r.celda_id = ? ORDER BY r.fecha_entrada DESC LIMIT ?
            """,
            (celda_id, limite),
        ).fetchall()

    def mapa(self):
        return self.db.execute(
            """
            SELECT c.*, v.placa, r.fecha_entrada,
                   (SELECT COUNT(*) FROM registro_parqueo h WHERE h.celda_id = c.id) AS usos
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
