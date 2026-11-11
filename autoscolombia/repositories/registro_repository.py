from typing import Optional

from ..models import RegistroParqueo

_CONSULTA_DETALLE = """
    SELECT r.*, v.placa, v.tipo, v.marca, v.color, c.codigo AS celda,
           cl.nombres AS cliente, ue.nombre AS operador_entrada, us.nombre AS operador_salida
    FROM registro_parqueo r
    JOIN vehiculo v ON v.id = r.vehiculo_id
    JOIN cliente cl ON cl.id = v.cliente_id
    JOIN celda c ON c.id = r.celda_id
    JOIN usuario ue ON ue.id = r.usuario_entrada_id
    LEFT JOIN usuario us ON us.id = r.usuario_salida_id
"""


class RegistroRepository:
    def __init__(self, db):
        self.db = db

    def obtener(self, registro_id: int) -> Optional[RegistroParqueo]:
        fila = self.db.execute("SELECT * FROM registro_parqueo WHERE id = ?", (registro_id,)).fetchone()
        return RegistroParqueo(**fila) if fila else None

    def abierto_por_vehiculo(self, vehiculo_id: int) -> Optional[RegistroParqueo]:
        fila = self.db.execute(
            "SELECT * FROM registro_parqueo WHERE vehiculo_id = ? AND fecha_salida IS NULL",
            (vehiculo_id,),
        ).fetchone()
        return RegistroParqueo(**fila) if fila else None

    def crear_entrada(self, vehiculo_id, celda_id, fecha_entrada, usuario_id) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO registro_parqueo (vehiculo_id, celda_id, fecha_entrada, usuario_entrada_id)
            VALUES (?, ?, ?, ?)
            """,
            (vehiculo_id, celda_id, fecha_entrada, usuario_id),
        )
        return cursor.lastrowid

    def cerrar(self, registro_id, fecha_salida, usuario_id):
        self.db.execute(
            "UPDATE registro_parqueo SET fecha_salida = ?, usuario_salida_id = ? WHERE id = ?",
            (fecha_salida, usuario_id, registro_id),
        )

    def detalle(self, registro_id: int):
        return self.db.execute(_CONSULTA_DETALLE + " WHERE r.id = ?", (registro_id,)).fetchone()

    def activos(self):
        return self.db.execute(
            _CONSULTA_DETALLE + " WHERE r.fecha_salida IS NULL ORDER BY r.fecha_entrada"
        ).fetchall()

    def historial(self, placa: str = "", fecha: str = "", limite: int = 200):
        condiciones, parametros = [], []
        if placa:
            condiciones.append("v.placa LIKE ?")
            parametros.append(f"%{placa}%")
        if fecha:
            condiciones.append("(date(r.fecha_entrada) = ? OR date(r.fecha_salida) = ?)")
            parametros += [fecha, fecha]
        donde = " WHERE " + " AND ".join(condiciones) if condiciones else ""
        return self.db.execute(
            _CONSULTA_DETALLE + donde + " ORDER BY r.fecha_entrada DESC LIMIT ?",
            (*parametros, limite),
        ).fetchall()

    def ultimos_movimientos(self, limite: int = 6):
        return self.db.execute(
            _CONSULTA_DETALLE + " ORDER BY COALESCE(r.fecha_salida, r.fecha_entrada) DESC LIMIT ?", (limite,)
        ).fetchall()

    def movimientos_del_dia(self, fecha: str):
        return self.db.execute(
            """
            SELECT SUM(date(fecha_entrada) = ?) AS entradas,
                   SUM(date(fecha_salida) = ?) AS salidas
            FROM registro_parqueo
            """,
            (fecha, fecha),
        ).fetchone()
