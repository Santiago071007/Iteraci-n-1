import re
from datetime import date

from ..models import Cliente
from ..repositories import ClienteRepository
from .errores import ReglaNegocioError

PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def normalizar_documento(documento) -> str:
    return re.sub(r"[\s.]", "", documento or "")


def limpiar_cliente(datos: dict) -> dict:
    """Normaliza y valida los datos de un cliente; devuelve los valores listos para guardar."""
    documento = normalizar_documento(datos.get("documento"))
    nombres = " ".join((datos.get("nombres") or "").split())
    telefono = re.sub(r"[\s-]", "", datos.get("telefono") or "")
    email = (datos.get("email") or "").strip().lower()
    if not documento.isdigit() or not 5 <= len(documento) <= 15:
        raise ReglaNegocioError("El documento debe tener entre 5 y 15 dígitos (sin puntos ni letras).")
    if not 3 <= len(nombres) <= 120:
        raise ReglaNegocioError("Ingrese el nombre completo del cliente.")
    if telefono and (not telefono.isdigit() or not 7 <= len(telefono) <= 10):
        raise ReglaNegocioError("El teléfono debe tener entre 7 y 10 dígitos.")
    if email and not PATRON_EMAIL.match(email):
        raise ReglaNegocioError("El correo electrónico no tiene un formato válido.")
    return {"documento": documento, "nombres": nombres, "telefono": telefono or None, "email": email or None}


class ClienteService:
    """Gestión de los clientes (usuarios del servicio de mensualidad)."""

    def __init__(self, db):
        self.db = db
        self.clientes = ClienteRepository(db)

    def obtener(self, cliente_id: int) -> Cliente:
        cliente = self.clientes.obtener(cliente_id)
        if not cliente:
            raise ReglaNegocioError("El cliente no existe.")
        return cliente

    def listar(self):
        return self.clientes.listar(date.today().isoformat())

    def crear(self, datos: dict) -> int:
        c = limpiar_cliente(datos)
        if self.clientes.buscar_por_documento(c["documento"]):
            raise ReglaNegocioError(f"Ya existe un cliente con documento {c['documento']}.")
        with self.db:
            return self.clientes.crear(c["documento"], c["nombres"], c["telefono"], c["email"])

    def actualizar(self, cliente_id: int, datos: dict):
        cliente = self.obtener(cliente_id)
        c = limpiar_cliente(datos)
        otro = self.clientes.buscar_por_documento(c["documento"])
        if otro and otro.id != cliente.id:
            raise ReglaNegocioError(f"El documento {c['documento']} ya pertenece a otro cliente.")
        with self.db:
            self.clientes.actualizar(cliente.id, c["documento"], c["nombres"], c["telefono"], c["email"])

    def cambiar_estado(self, cliente_id: int) -> bool:
        """Activa o desactiva el cliente. Devuelve el nuevo estado (True = activo)."""
        cliente = self.obtener(cliente_id)
        if cliente.activo and self.clientes.tiene_vehiculo_dentro(cliente.id):
            raise ReglaNegocioError(
                "El cliente tiene un vehículo dentro del parqueadero; registre la salida antes de desactivarlo."
            )
        with self.db:
            self.clientes.cambiar_estado(cliente.id, not cliente.activo)
        return not cliente.activo
