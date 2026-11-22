from typing import Optional

from ..models import Pago, Tarifa

_CONSULTA_DETALLE = """
    SELECT p.*, v.placa, v.tipo, v.marca, v.color, c.id AS cliente_id, c.nombres AS cliente, c.documento,
           u.nombre AS cajero, a.nombre AS anulador
    FROM pago p
    JOIN vehiculo v ON v.id = p.vehiculo_id
    JOIN cliente c ON c.id = v.cliente_id
    JOIN usuario u ON u.id = p.usuario_id
    LEFT JOIN usuario a ON a.id = p.anulado_por
"""


class TarifaRepository:
    def __init__(self, db):
        self.db = db

    def obtener(self, tipo_vehiculo: str) -> Optional[Tarifa]:
        fila = self.db.execute("SELECT * FROM tarifa WHERE tipo_vehiculo = ?", (tipo_vehiculo,)).fetchone()
        return Tarifa(**fila) if fila else None

    def listar(self):
        return self.db.execute(
            """
            SELECT t.*, u.nombre AS usuario,
                   (SELECT COUNT(*) FROM vehiculo v WHERE v.tipo = t.tipo_vehiculo) AS vehiculos
            FROM tarifa t LEFT JOIN usuario u ON u.id = t.usuario_id ORDER BY t.tipo_vehiculo
            """
        ).fetchall()

    def actualizar(self, tipo_vehiculo: str, valor: float, fecha: str, usuario_id: int):
        self.db.execute(
            "UPDATE tarifa SET valor_mensual = ?, actualizado_en = ?, usuario_id = ? WHERE tipo_vehiculo = ?",
            (valor, fecha, usuario_id, tipo_vehiculo),
        )


class PagoRepository:
    def __init__(self, db):
        self.db = db

    def obtener(self, pago_id: int) -> Optional[Pago]:
        fila = self.db.execute("SELECT * FROM pago WHERE id = ?", (pago_id,)).fetchone()
        return Pago(**fila) if fila else None

    def detalle(self, pago_id: int):
        return self.db.execute(_CONSULTA_DETALLE + " WHERE p.id = ?", (pago_id,)).fetchone()

    def crear(self, mensualidad_id, vehiculo_id, fecha, meses, periodo_inicio, periodo_fin, valor, medio,
              referencia, usuario_id) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO pago (mensualidad_id, vehiculo_id, fecha, meses, periodo_inicio, periodo_fin, valor,
                              medio, referencia, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (mensualidad_id, vehiculo_id, fecha, meses, periodo_inicio, periodo_fin, valor, medio, referencia,
             usuario_id),
        )
        return cursor.lastrowid

    def anular(self, pago_id: int, fecha: str, usuario_id: int, motivo: str):
        self.db.execute(
            "UPDATE pago SET estado = 'ANULADO', anulado_en = ?, anulado_por = ?, motivo_anulacion = ? WHERE id = ?",
            (fecha, usuario_id, motivo, pago_id),
        )

    def referencia_en_uso(self, medio: str, referencia: str) -> Optional[Pago]:
        fila = self.db.execute(
            "SELECT * FROM pago WHERE medio = ? AND referencia = ? AND estado = 'VIGENTE'", (medio, referencia)
        ).fetchone()
        return Pago(**fila) if fila else None

    def posterior_vigente(self, vehiculo_id: int, periodo_fin: str) -> Optional[Pago]:
        """Pago vigente del mismo vehículo que cubre un período posterior al indicado."""
        fila = self.db.execute(
            """
            SELECT * FROM pago WHERE vehiculo_id = ? AND estado = 'VIGENTE' AND periodo_inicio > ?
            ORDER BY periodo_inicio DESC LIMIT 1
            """,
            (vehiculo_id, periodo_fin),
        ).fetchone()
        return Pago(**fila) if fila else None

    @staticmethod
    def _filtros(desde="", hasta="", medio="", estado="", texto="", usuario_id=None):
        condiciones, parametros = [], []
        if desde:
            condiciones.append("date(p.fecha) >= ?")
            parametros.append(desde)
        if hasta:
            condiciones.append("date(p.fecha) <= ?")
            parametros.append(hasta)
        if medio:
            condiciones.append("p.medio = ?")
            parametros.append(medio)
        if estado:
            condiciones.append("p.estado = ?")
            parametros.append(estado)
        if texto:
            condiciones.append("(v.placa LIKE ? OR c.nombres LIKE ? OR c.documento LIKE ? OR p.referencia LIKE ?)")
            parametros += [f"%{texto}%"] * 4
        if usuario_id:
            condiciones.append("p.usuario_id = ?")
            parametros.append(usuario_id)
        return (" WHERE " + " AND ".join(condiciones) if condiciones else ""), parametros

    def listar(self, limite: int = 300, **filtros):
        donde, parametros = self._filtros(**filtros)
        return self.db.execute(
            _CONSULTA_DETALLE + donde + " ORDER BY p.fecha DESC, p.id DESC LIMIT ?", (*parametros, limite)
        ).fetchall()

    def por_cliente(self, cliente_id: int, limite: int = 12):
        return self.db.execute(
            _CONSULTA_DETALLE + " WHERE c.id = ? ORDER BY p.fecha DESC, p.id DESC LIMIT ?", (cliente_id, limite)
        ).fetchall()

    def totales_por_medio(self, desde: str, hasta: str, usuario_id: Optional[int] = None):
        donde, parametros = self._filtros(desde=desde, hasta=hasta, estado="VIGENTE", usuario_id=usuario_id)
        return self.db.execute(
            "SELECT p.medio, COUNT(*) AS cantidad, SUM(p.valor) AS total FROM pago p" + donde + " GROUP BY p.medio",
            parametros,
        ).fetchall()

    def totales_por_usuario(self, desde: str, hasta: str):
        return self.db.execute(
            """
            SELECT u.nombre AS cajero, COUNT(*) AS cantidad, SUM(p.valor) AS total,
                   SUM(CASE WHEN p.medio = 'EFECTIVO' THEN p.valor ELSE 0 END) AS efectivo
            FROM pago p JOIN usuario u ON u.id = p.usuario_id
            WHERE p.estado = 'VIGENTE' AND date(p.fecha) BETWEEN ? AND ?
            GROUP BY u.id ORDER BY total DESC
            """,
            (desde, hasta),
        ).fetchall()

    def estado_de_vehiculos(self):
        """Un renglón por vehículo de cliente activo con el fin de su última mensualidad y su tarifa."""
        return self.db.execute(
            """
            SELECT v.id AS vehiculo_id, v.placa, v.tipo, v.marca, c.id AS cliente_id, c.nombres AS cliente,
                   c.telefono, t.valor_mensual AS tarifa,
                   (SELECT MAX(m.fecha_fin) FROM mensualidad m WHERE m.vehiculo_id = v.id) AS vence,
                   (SELECT MAX(p.fecha) FROM pago p WHERE p.vehiculo_id = v.id AND p.estado = 'VIGENTE') AS ultimo_pago,
                   EXISTS (SELECT 1 FROM registro_parqueo r
                           WHERE r.vehiculo_id = v.id AND r.fecha_salida IS NULL) AS dentro
            FROM vehiculo v
            JOIN cliente c ON c.id = v.cliente_id
            JOIN tarifa t ON t.tipo_vehiculo = v.tipo
            WHERE c.activo = 1
            ORDER BY vence IS NOT NULL, vence, v.placa
            """
        ).fetchall()
