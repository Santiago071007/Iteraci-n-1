from typing import Optional

from werkzeug.security import check_password_hash

from ..models import Usuario
from ..repositories import UsuarioRepository


class AuthService:
    def __init__(self, db):
        self.usuarios = UsuarioRepository(db)

    def autenticar(self, username: str, password: str) -> Optional[Usuario]:
        usuario = self.usuarios.buscar_por_username((username or "").strip().lower())
        if usuario and usuario.activo and check_password_hash(usuario.password_hash, password or ""):
            return usuario
        return None
