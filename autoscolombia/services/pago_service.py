import calendar
import re
from datetime import date, datetime, timedelta
from typing import Optional

from ..models import FORMATO_FECHA_HORA, Pago
from ..repositories import (
    ClienteRepository,
    MensualidadRepository,
    PagoRepository,
    RegistroRepository,
    TarifaRepository,
    VehiculoRepository,
)
from .errores import ReglaNegocioError
from .parqueo_service import normalizar_placa, validar_placa

MEDIOS_PAGO = {
    "EFECTIVO": "Efectivo",
    "TRANSFERENCIA": "Transferencia bancaria",
    "TARJETA": "Tarjeta débito o crédito",
    "BILLETERA": "Billetera digital (Nequi, Daviplata)",
}
TIPOS_VEHICULO = {"CARRO": "Carro", "MOTO": "Moto"}
MAX_MESES = 12
DIAS_AVISO = 5
TARIFA_MINIMA, TARIFA_MAXIMA = 10_000, 2_000_000
PATRON_REFERENCIA = re.compile(r"^[A-Z0-9-]{4,30}$")


def sumar_meses(fecha: date, meses: int) -> date:
    """Misma fecha `meses` después; si el día no existe en el mes destino usa el último día."""
    indice = fecha.month - 1 + meses
    anio, mes = fecha.year + indice // 12, indice % 12 + 1
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def validar_medio(medio: Optional[str], referencia: Optional[str]) -> tuple[str, Optional[str]]:
    """Valida el medio de pago y normaliza la referencia (obligatoria salvo en efectivo)."""
    if medio not in MEDIOS_PAGO:
        raise ReglaNegocioError("Seleccione un medio de pago válido.")
    referencia = re.sub(r"\s", "", referencia or "").upper()
    if medio == "EFECTIVO":
        return medio, None
    if not PATRON_REFERENCIA.match(referencia):
        raise ReglaNegocioError(
            "Escriba la referencia o número de aprobación del pago (4 a 30 letras, números o guiones)."
        )
    return medio, referencia


class PagoService:
    """Gestión de pagos de mensualidades: tarifas, recaudo, recibos, anulaciones, cartera y cierre de caja."""

    def __init__(self, db):
        self.db = db
        self.pagos = PagoRepository(db)
        self.tarifas = TarifaRepository(db)
        self.vehiculos = VehiculoRepository(db)
        self.clientes = ClienteRepository(db)
        self.mensualidades = MensualidadRepository(db)
        self.registros = RegistroRepository(db)

    # ------------------------------------------------------------------ tarifas
    def actualizar_tarifa(self, tipo_vehiculo: str, valor, usuario_id: int, ahora: Optional[datetime] = None):
        if tipo_vehiculo not in TIPOS_VEHICULO:
            raise ReglaNegocioError("Seleccione un tipo de vehículo válido.")
        try:
            valor = int(str(valor).replace(".", "").replace(",", "").replace("$", "").strip())
        except ValueError as error:
            raise ReglaNegocioError("El valor de la tarifa debe ser un número entero en pesos.") from error
        if not TARIFA_MINIMA <= valor <= TARIFA_MAXIMA:
            raise ReglaNegocioError(
                f"La tarifa mensual debe estar entre $ {TARIFA_MINIMA:,} y $ {TARIFA_MAXIMA:,}.".replace(",", ".")
            )
        ahora = ahora or datetime.now()
        with self.db:
            self.tarifas.actualizar(tipo_vehiculo, valor, ahora.strftime(FORMATO_FECHA_HORA), usuario_id)
        return valor

    # ------------------------------------------------------------------ pagos
    def cotizar(self, placa: str, meses=1, hoy: Optional[date] = None) -> dict:
        """Calcula, sin guardar nada, el período y el valor que cubriría un pago."""
        hoy = hoy or date.today()
        placa = normalizar_placa(placa)
        validar_placa(placa)
        vehiculo = self.vehiculos.buscar_por_placa(placa)
        if not vehiculo:
            raise ReglaNegocioError(f"El vehículo {placa} no está registrado; regístrelo antes de recibir el pago.")
        cliente = self.clientes.obtener(vehiculo.cliente_id)
        if not cliente.esta_activo():
            raise ReglaNegocioError(f"El cliente {cliente.nombres} está inactivo; actívelo antes de recibir pagos.")
        try:
            meses = int(meses)
        except (TypeError, ValueError) as error:
            raise ReglaNegocioError("Indique cuántos meses se pagan.") from error
        if not 1 <= meses <= MAX_MESES:
            raise ReglaNegocioError(f"Se pueden pagar entre 1 y {MAX_MESES} meses por recibo.")

        ultima = self.mensualidades.ultima(vehiculo.id)
        vigente = bool(ultima and ultima.fecha_fin >= hoy.isoformat())
        inicio = date.fromisoformat(ultima.fecha_fin) + timedelta(days=1) if vigente else hoy
        fin = sumar_meses(inicio, meses) - timedelta(days=1)
        if fin >= sumar_meses(hoy, MAX_MESES):
            raise ReglaNegocioError(
                f"El vehículo {placa} quedaría pagado hasta {fin.isoformat()}; "
                f"no se reciben más de {MAX_MESES} meses por adelantado."
            )
        tarifa = self.tarifas.obtener(vehiculo.tipo)
        return {
            "vehiculo": vehiculo,
            "cliente": cliente,
            "meses": meses,
            "tarifa": tarifa.valor_mensual,
            "valor": tarifa.valor_mensual * meses,
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat(),
            "vence": ultima.fecha_fin if ultima else None,
            "vigente": vigente,
            "dias": (date.fromisoformat(ultima.fecha_fin) - hoy).days if ultima else None,
        }

    def registrar_pago(self, placa: str, meses, medio: str, referencia: Optional[str], usuario_id: int,
                       ahora: Optional[datetime] = None) -> Pago:
        ahora = ahora or datetime.now()
        c = self.cotizar(placa, meses, ahora.date())
        medio, referencia = validar_medio(medio, referencia)
        repetido = referencia and self.pagos.referencia_en_uso(medio, referencia)
        if repetido:
            raise ReglaNegocioError(
                f"La referencia {referencia} ya fue registrada en el recibo N.º {repetido.id}; el pago no se duplicó."
            )
        with self.db:
            mensualidad_id = self.mensualidades.crear(c["vehiculo"].id, c["inicio"], c["fin"], c["valor"])
            pago_id = self.pagos.crear(
                mensualidad_id, c["vehiculo"].id, ahora.strftime(FORMATO_FECHA_HORA), c["meses"],
                c["inicio"], c["fin"], c["valor"], medio, referencia, usuario_id,
            )
        return self.pagos.obtener(pago_id)

    def anular_pago(self, pago_id: int, motivo: str, usuario_id: int, ahora: Optional[datetime] = None) -> Pago:
        """Anula un recibo y retira el período que había pagado. El recibo se conserva como ANULADO."""
        ahora = ahora or datetime.now()
        pago = self.pagos.obtener(pago_id)
        if not pago:
            raise ReglaNegocioError("El recibo no existe.")
        if not pago.esta_vigente():
            raise ReglaNegocioError(f"El recibo N.º {pago.id} ya está anulado.")
        motivo = " ".join((motivo or "").split())
        if len(motivo) < 10:
            raise ReglaNegocioError("Explique el motivo de la anulación (mínimo 10 caracteres).")
        posterior = self.pagos.posterior_vigente(pago.vehiculo_id, pago.periodo_fin)
        if posterior:
            raise ReglaNegocioError(
                f"El vehículo tiene un pago posterior (recibo N.º {posterior.id}); anule primero ese recibo."
            )
        hoy = ahora.date().isoformat()
        cubre_hoy = pago.periodo_inicio <= hoy <= pago.periodo_fin
        if cubre_hoy and self.registros.abierto_por_vehiculo(pago.vehiculo_id):
            raise ReglaNegocioError(
                "El vehículo está dentro del parqueadero con este período; registre la salida antes de anular."
            )
        with self.db:
            if pago.mensualidad_id:
                self.mensualidades.eliminar(pago.mensualidad_id)
            self.pagos.anular(pago.id, ahora.strftime(FORMATO_FECHA_HORA), usuario_id, motivo[:200])
        return self.pagos.obtener(pago.id)

    # ------------------------------------------------------------------ consultas
    def cartera(self, hoy: Optional[date] = None) -> dict:
        """Clasifica los vehículos de clientes activos según el estado de su mensualidad."""
        hoy = hoy or date.today()
        grupos = {"vencidas": [], "por_vencer": [], "al_dia": []}
        for fila in self.pagos.estado_de_vehiculos():
            v = dict(fila)
            v["dias"] = (date.fromisoformat(v["vence"]) - hoy).days if v["vence"] else None
            if v["dias"] is None or v["dias"] < 0:
                grupos["vencidas"].append(v)
            elif v["dias"] <= DIAS_AVISO:
                grupos["por_vencer"].append(v)
            else:
                grupos["al_dia"].append(v)
        grupos["por_cobrar"] = sum(v["tarifa"] for v in grupos["vencidas"] + grupos["por_vencer"])
        grupos["dias_aviso"] = DIAS_AVISO
        return grupos

    def recaudo(self, desde: str, hasta: str, usuario_id: Optional[int] = None) -> dict:
        """Cierre de caja: totales por medio de pago (y por cajero) de los pagos vigentes del rango."""
        try:
            if date.fromisoformat(desde) > date.fromisoformat(hasta):
                raise ReglaNegocioError("La fecha inicial no puede ser posterior a la final.")
        except ValueError as error:
            raise ReglaNegocioError("Revise las fechas del reporte.") from error
        por_medio = {fila["medio"]: fila for fila in self.pagos.totales_por_medio(desde, hasta, usuario_id)}
        medios = [
            {"medio": clave, "nombre": nombre,
             "cantidad": por_medio[clave]["cantidad"] if clave in por_medio else 0,
             "total": por_medio[clave]["total"] if clave in por_medio else 0}
            for clave, nombre in MEDIOS_PAGO.items()
        ]
        pagos = self.pagos.listar(desde=desde, hasta=hasta, usuario_id=usuario_id)
        return {
            "medios_totales": medios,
            "total": sum(m["total"] for m in medios),
            "cantidad": sum(m["cantidad"] for m in medios),
            "efectivo": medios[0]["total"],
            "anulados": [p for p in pagos if p["estado"] == "ANULADO"],
            "pagos": pagos,
            "cajeros": [] if usuario_id else self.pagos.totales_por_usuario(desde, hasta),
        }
