from typing import Optional

from ..models import Cliente, Vehiculo


class ClienteRepository:
    def __init__(self, db):
        self.db = db

    def buscar_por_documento(self, documento: str) -> Optional[Cliente]:
        fila = self.db.execute("SELECT * FROM cliente WHERE documento = ?", (documento,)).fetchone()
        return Cliente(**fila) if fila else None

    def crear(self, documento, nombres, telefono, email) -> int:
        cursor = self.db.execute(
            "INSERT INTO cliente (documento, nombres, telefono, email) VALUES (?, ?, ?, ?)",
            (documento, nombres, telefono, email),
        )
        return cursor.lastrowid


class VehiculoRepository:
    def __init__(self, db):
        self.db = db

    def buscar_por_placa(self, placa: str) -> Optional[Vehiculo]:
        fila = self.db.execute("SELECT * FROM vehiculo WHERE placa = ?", (placa,)).fetchone()
        return Vehiculo(**fila) if fila else None

    def crear(self, placa, tipo, marca, color, cliente_id) -> int:
        cursor = self.db.execute(
            "INSERT INTO vehiculo (placa, tipo, marca, color, cliente_id) VALUES (?, ?, ?, ?, ?)",
            (placa, tipo, marca, color, cliente_id),
        )
        return cursor.lastrowid

    def listar_con_cliente(self):
        return self.db.execute(
            """
            SELECT v.*, c.nombres AS cliente, c.documento,
                   (SELECT MAX(m.fecha_fin) FROM mensualidad m WHERE m.vehiculo_id = v.id) AS mensualidad_hasta,
                   EXISTS (SELECT 1 FROM registro_parqueo r
                           WHERE r.vehiculo_id = v.id AND r.fecha_salida IS NULL) AS dentro
            FROM vehiculo v JOIN cliente c ON c.id = v.cliente_id
            ORDER BY v.placa
            """
        ).fetchall()
