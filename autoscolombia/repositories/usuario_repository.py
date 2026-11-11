from typing import List, Optional

from ..models import Usuario


class UsuarioRepository:
    def __init__(self, db):
        self.db = db

    def buscar_por_username(self, username: str) -> Optional[Usuario]:
        fila = self.db.execute("SELECT * FROM usuario WHERE username = ?", (username,)).fetchone()
        return Usuario(**fila) if fila else None

    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        fila = self.db.execute("SELECT * FROM usuario WHERE id = ?", (usuario_id,)).fetchone()
        return Usuario(**fila) if fila else None

    def listar(self):
        return self.db.execute(
            """
            SELECT u.*,
                   (SELECT COUNT(*) FROM registro_parqueo r
                    WHERE r.usuario_entrada_id = u.id OR r.usuario_salida_id = u.id) AS movimientos
            FROM usuario u ORDER BY u.activo DESC, u.rol, u.nombre
            """
        ).fetchall()

    def crear(self, nombre, username, password_hash, rol) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO usuario (nombre, username, password_hash, rol, activo, creado_en)
            VALUES (?, ?, ?, ?, 1, datetime('now', 'localtime'))
            """,
            (nombre, username, password_hash, rol),
        )
        return cursor.lastrowid

    def actualizar(self, usuario_id: int, nombre: str, rol: str):
        self.db.execute("UPDATE usuario SET nombre = ?, rol = ? WHERE id = ?", (nombre, rol, usuario_id))

    def cambiar_estado(self, usuario_id: int, activo: bool):
        self.db.execute("UPDATE usuario SET activo = ? WHERE id = ?", (int(activo), usuario_id))

    def cambiar_clave(self, usuario_id: int, password_hash: str):
        self.db.execute("UPDATE usuario SET password_hash = ? WHERE id = ?", (password_hash, usuario_id))

    def admins_activos(self) -> List[Usuario]:
        filas = self.db.execute("SELECT * FROM usuario WHERE rol = 'ADMIN' AND activo = 1").fetchall()
        return [Usuario(**f) for f in filas]
