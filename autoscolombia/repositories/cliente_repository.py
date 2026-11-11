from typing import Optional

from ..models import Cliente


class ClienteRepository:
    def __init__(self, db):
        self.db = db

    def obtener(self, cliente_id: int) -> Optional[Cliente]:
        fila = self.db.execute("SELECT * FROM cliente WHERE id = ?", (cliente_id,)).fetchone()
        return Cliente(**fila) if fila else None

    def buscar_por_documento(self, documento: str) -> Optional[Cliente]:
        fila = self.db.execute("SELECT * FROM cliente WHERE documento = ?", (documento,)).fetchone()
        return Cliente(**fila) if fila else None

    def crear(self, documento, nombres, telefono, email) -> int:
        cursor = self.db.execute(
            "INSERT INTO cliente (documento, nombres, telefono, email) VALUES (?, ?, ?, ?)",
            (documento, nombres, telefono, email),
        )
        return cursor.lastrowid

    def actualizar(self, cliente_id, documento, nombres, telefono, email):
        self.db.execute(
            "UPDATE cliente SET documento = ?, nombres = ?, telefono = ?, email = ? WHERE id = ?",
            (documento, nombres, telefono, email, cliente_id),
        )

    def cambiar_estado(self, cliente_id: int, activo: bool):
        self.db.execute("UPDATE cliente SET activo = ? WHERE id = ?", (int(activo), cliente_id))

    def listar(self, hoy: str):
        return self.db.execute(
            """
            SELECT c.*,
                   COUNT(v.id) AS vehiculos,
                   SUM((SELECT MAX(m.fecha_fin) FROM mensualidad m WHERE m.vehiculo_id = v.id) >= ?) AS vigentes,
                   SUM(EXISTS (SELECT 1 FROM registro_parqueo r
                               WHERE r.vehiculo_id = v.id AND r.fecha_salida IS NULL)) AS dentro
            FROM cliente c LEFT JOIN vehiculo v ON v.cliente_id = c.id
            GROUP BY c.id ORDER BY c.activo DESC, c.nombres
            """,
            (hoy,),
        ).fetchall()

    def vehiculos(self, cliente_id: int):
        return self.db.execute(
            """
            SELECT v.*,
                   (SELECT MAX(m.fecha_fin) FROM mensualidad m WHERE m.vehiculo_id = v.id) AS mensualidad_hasta,
                   (SELECT c.codigo FROM registro_parqueo r JOIN celda c ON c.id = r.celda_id
                    WHERE r.vehiculo_id = v.id AND r.fecha_salida IS NULL) AS celda_actual
            FROM vehiculo v WHERE v.cliente_id = ? ORDER BY v.placa
            """,
            (cliente_id,),
        ).fetchall()

    def tiene_vehiculo_dentro(self, cliente_id: int) -> bool:
        fila = self.db.execute(
            """
            SELECT 1 FROM registro_parqueo r JOIN vehiculo v ON v.id = r.vehiculo_id
            WHERE v.cliente_id = ? AND r.fecha_salida IS NULL LIMIT 1
            """,
            (cliente_id,),
        ).fetchone()
        return fila is not None
