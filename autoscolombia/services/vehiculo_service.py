from datetime import date

from ..repositories import ClienteRepository, MensualidadRepository, VehiculoRepository
from .cliente_service import limpiar_cliente, normalizar_documento
from .errores import ReglaNegocioError
from .parqueo_service import normalizar_placa, validar_placa


class VehiculoService:
    def __init__(self, db):
        self.db = db
        self.clientes = ClienteRepository(db)
        self.vehiculos = VehiculoRepository(db)
        self.mensualidades = MensualidadRepository(db)

    def registrar(self, datos: dict) -> int:
        placa = normalizar_placa(datos.get("placa"))
        tipo = datos.get("tipo")
        if tipo not in ("CARRO", "MOTO"):
            raise ReglaNegocioError("Seleccione el tipo de vehículo.")
        validar_placa(placa, tipo)
        if self.vehiculos.buscar_por_placa(placa):
            raise ReglaNegocioError(f"Ya existe un vehículo con placa {placa}.")

        cliente = self.clientes.buscar_por_documento(normalizar_documento(datos.get("documento")))
        if cliente and not cliente.esta_activo():
            raise ReglaNegocioError(
                f"El cliente {cliente.nombres} está inactivo; actívelo antes de registrarle vehículos."
            )
        nuevo_cliente = None if cliente else limpiar_cliente(datos)

        try:
            inicio = date.fromisoformat(datos.get("fecha_inicio") or "")
            fin = date.fromisoformat(datos.get("fecha_fin") or "")
            valor = float(datos.get("valor") or 0)
        except ValueError as error:
            raise ReglaNegocioError("Revise las fechas y el valor de la mensualidad.") from error
        if fin < inicio or valor < 0:
            raise ReglaNegocioError("La fecha final debe ser posterior a la inicial y el valor no negativo.")

        with self.db:
            cliente_id = cliente.id if cliente else self.clientes.crear(
                nuevo_cliente["documento"], nuevo_cliente["nombres"], nuevo_cliente["telefono"], nuevo_cliente["email"]
            )
            vehiculo_id = self.vehiculos.crear(
                placa, tipo, datos.get("marca") or None, datos.get("color") or None, cliente_id
            )
            self.mensualidades.crear(vehiculo_id, inicio.isoformat(), fin.isoformat(), valor)
        return vehiculo_id
