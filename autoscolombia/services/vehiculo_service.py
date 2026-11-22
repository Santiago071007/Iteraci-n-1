from datetime import date, datetime
from typing import Optional

from ..models import FORMATO_FECHA_HORA
from ..repositories import ClienteRepository, MensualidadRepository, PagoRepository, VehiculoRepository
from .cliente_service import limpiar_cliente, normalizar_documento
from .errores import ReglaNegocioError
from .pago_service import validar_medio
from .parqueo_service import normalizar_placa, validar_placa


class VehiculoService:
    def __init__(self, db):
        self.db = db
        self.clientes = ClienteRepository(db)
        self.vehiculos = VehiculoRepository(db)
        self.mensualidades = MensualidadRepository(db)
        self.pagos = PagoRepository(db)

    def registrar(self, datos: dict, usuario_id: Optional[int] = None) -> int:
        """Registra el vehículo con su primera mensualidad. Si se indica quién recibe el dinero
        (usuario_id) y el valor es mayor que cero, esa mensualidad queda con su recibo de pago."""
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
        cobra = bool(usuario_id) and valor > 0
        if cobra:
            medio, referencia = validar_medio(datos.get("medio") or "EFECTIVO", datos.get("referencia"))
            if referencia and self.pagos.referencia_en_uso(medio, referencia):
                raise ReglaNegocioError(f"La referencia {referencia} ya fue registrada en otro recibo.")

        with self.db:
            cliente_id = cliente.id if cliente else self.clientes.crear(
                nuevo_cliente["documento"], nuevo_cliente["nombres"], nuevo_cliente["telefono"], nuevo_cliente["email"]
            )
            vehiculo_id = self.vehiculos.crear(
                placa, tipo, datos.get("marca") or None, datos.get("color") or None, cliente_id
            )
            mensualidad_id = self.mensualidades.crear(vehiculo_id, inicio.isoformat(), fin.isoformat(), valor)
            if cobra:
                self.pagos.crear(
                    mensualidad_id, vehiculo_id, datetime.now().strftime(FORMATO_FECHA_HORA), 1,
                    inicio.isoformat(), fin.isoformat(), valor, medio, referencia, usuario_id,
                )
        return vehiculo_id
