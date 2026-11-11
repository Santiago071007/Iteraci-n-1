import re
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from ..models import Usuario
from ..repositories import UsuarioRepository
from .errores import ReglaNegocioError

ROLES = {"ADMIN": "Administrador", "OPERADOR": "Operador"}
PATRON_USERNAME = re.compile(r"^[a-z][a-z0-9._]{3,19}$")
LONGITUD_MINIMA_CLAVE = 8


def validar_clave(clave: Optional[str], confirmacion: Optional[str] = None):
    clave = clave or ""
    if len(clave) < LONGITUD_MINIMA_CLAVE or not re.search(r"[A-Za-z]", clave) or not re.search(r"\d", clave):
        raise ReglaNegocioError(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres e incluir letras y números."
        )
    if confirmacion is not None and clave != confirmacion:
        raise ReglaNegocioError("La contraseña y su confirmación no coinciden.")


def validar_nombre(nombre: Optional[str]) -> str:
    nombre = " ".join((nombre or "").split())
    if not 3 <= len(nombre) <= 100:
        raise ReglaNegocioError("Ingrese el nombre completo (entre 3 y 100 caracteres).")
    return nombre


class UsuarioService:
    """Gestión de los usuarios del sistema (empleados que operan el parqueadero)."""

    def __init__(self, db):
        self.db = db
        self.usuarios = UsuarioRepository(db)

    def obtener(self, usuario_id: int) -> Usuario:
        usuario = self.usuarios.obtener(usuario_id)
        if not usuario:
            raise ReglaNegocioError("El usuario no existe.")
        return usuario

    @staticmethod
    def _validar_rol(rol: Optional[str]):
        if rol not in ROLES:
            raise ReglaNegocioError("Seleccione un rol válido (Administrador u Operador).")

    def _queda_otro_admin(self, usuario_id: int) -> bool:
        return any(u.id != usuario_id for u in self.usuarios.admins_activos())

    def crear(self, datos: dict) -> int:
        nombre = validar_nombre(datos.get("nombre"))
        username = (datos.get("username") or "").strip().lower()
        if not PATRON_USERNAME.match(username):
            raise ReglaNegocioError(
                "El usuario debe tener de 4 a 20 caracteres (letras minúsculas, números, punto o guion bajo) "
                "y empezar por una letra."
            )
        if self.usuarios.buscar_por_username(username):
            raise ReglaNegocioError(f"El nombre de usuario '{username}' ya está en uso.")
        rol = datos.get("rol")
        self._validar_rol(rol)
        validar_clave(datos.get("password"), datos.get("confirmacion"))
        with self.db:
            return self.usuarios.crear(nombre, username, generate_password_hash(datos["password"]), rol)

    def actualizar(self, usuario_id: int, datos: dict, actor_id: int):
        usuario = self.obtener(usuario_id)
        nombre = validar_nombre(datos.get("nombre"))
        rol = datos.get("rol")
        self._validar_rol(rol)
        if usuario.es_admin() and rol != "ADMIN":
            if usuario.id == actor_id:
                raise ReglaNegocioError("No puede quitarse a sí mismo el rol de administrador.")
            if usuario.activo and not self._queda_otro_admin(usuario.id):
                raise ReglaNegocioError("Debe existir al menos un administrador activo.")
        with self.db:
            self.usuarios.actualizar(usuario.id, nombre, rol)

    def cambiar_estado(self, usuario_id: int, actor_id: int) -> bool:
        """Activa o desactiva el usuario. Devuelve el nuevo estado (True = activo)."""
        usuario = self.obtener(usuario_id)
        if usuario.activo:
            if usuario.id == actor_id:
                raise ReglaNegocioError("No puede desactivar su propio usuario.")
            if usuario.es_admin() and not self._queda_otro_admin(usuario.id):
                raise ReglaNegocioError("Debe existir al menos un administrador activo.")
        with self.db:
            self.usuarios.cambiar_estado(usuario.id, not usuario.activo)
        return not usuario.activo

    def restablecer_clave(self, usuario_id: int, nueva: str, confirmacion: str):
        usuario = self.obtener(usuario_id)
        validar_clave(nueva, confirmacion)
        with self.db:
            self.usuarios.cambiar_clave(usuario.id, generate_password_hash(nueva))

    def cambiar_mi_clave(self, usuario_id: int, actual: str, nueva: str, confirmacion: str):
        usuario = self.obtener(usuario_id)
        if not check_password_hash(usuario.password_hash, actual or ""):
            raise ReglaNegocioError("La contraseña actual no es correcta.")
        if actual == nueva:
            raise ReglaNegocioError("La nueva contraseña debe ser diferente a la actual.")
        validar_clave(nueva, confirmacion)
        with self.db:
            self.usuarios.cambiar_clave(usuario.id, generate_password_hash(nueva))
