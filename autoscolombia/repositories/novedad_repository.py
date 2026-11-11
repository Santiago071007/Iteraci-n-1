class NovedadRepository:
    def __init__(self, db):
        self.db = db

    def crear(self, registro_id, usuario_id, fecha, tipo, descripcion) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO novedad (registro_id, usuario_id, fecha, tipo, descripcion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (registro_id, usuario_id, fecha, tipo, descripcion),
        )
        return cursor.lastrowid

    def por_registro(self, registro_id: int):
        return self.db.execute(
            """
            SELECT n.*, u.nombre AS usuario FROM novedad n JOIN usuario u ON u.id = n.usuario_id
            WHERE n.registro_id = ? ORDER BY n.fecha
            """,
            (registro_id,),
        ).fetchall()

    def recientes(self, limite: int = 50):
        return self.db.execute(
            """
            SELECT n.*, u.nombre AS usuario, v.placa, c.codigo AS celda
            FROM novedad n
            JOIN usuario u ON u.id = n.usuario_id
            JOIN registro_parqueo r ON r.id = n.registro_id
            JOIN vehiculo v ON v.id = r.vehiculo_id
            JOIN celda c ON c.id = r.celda_id
            ORDER BY n.fecha DESC LIMIT ?
            """,
            (limite,),
        ).fetchall()
