from typing import Optional

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
