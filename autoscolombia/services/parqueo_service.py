import re
from datetime import datetime
from typing import Optional

from ..models import FORMATO_FECHA_HORA, RegistroParqueo
from ..repositories import (
    CeldaRepository,
    MensualidadRepository,
    NovedadRepository,
    RegistroRepository,
    VehiculoRepository,
)
from .errores import ReglaNegocioError

PATRONES_PLACA = {
    "CARRO": re.compile(r"^[A-Z]{3}\d{3}$"),
    "MOTO": re.compile(r"^[A-Z]{3}\d{2}[A-Z]$"),
}
TIPOS_NOVEDAD = {"DANO": "Daño", "OBJETO": "Objeto olvidado", "INCIDENTE": "Incidente", "OTRO": "Otro"}


def normalizar_placa(placa: Optional[str]) -> str:
    return re.sub(r"[\s-]", "", placa or "").upper()


def validar_placa(placa: str, tipo: Optional[str] = None):
    patrones = [PATRONES_PLACA[tipo]] if tipo else PATRONES_PLACA.values()
    if not any(p.match(placa) for p in patrones):
        raise ReglaNegocioError(
            f"La placa '{placa}' no tiene un formato válido (carro: ABC123, moto: ABC12D)."
        )


def formatear_duracion(segundos: float) -> str:
    minutos = int(segundos // 60)
    dias, minutos = divmod(minutos, 24 * 60)
    horas, minutos = divmod(minutos, 60)
    partes = ([f"{dias} d"] if dias else []) + [f"{horas} h", f"{minutos} min"]
    return " ".join(partes)


class ParqueoService:
    def __init__(self, db):
        self.db = db
        self.vehiculos = VehiculoRepository(db)
        self.mensualidades = MensualidadRepository(db)
        self.celdas = CeldaRepository(db)
        self.registros = RegistroRepository(db)
        self.novedades = NovedadRepository(db)

    def _vehiculo_dentro(self, placa: str):
        placa = normalizar_placa(placa)
        validar_placa(placa)
        vehiculo = self.vehiculos.buscar_por_placa(placa)
        registro = self.registros.abierto_por_vehiculo(vehiculo.id) if vehiculo else None
        if not registro:
            raise ReglaNegocioError(f"El vehículo {placa} no se encuentra dentro del parqueadero.")
        return vehiculo, registro

    def registrar_entrada(
        self, placa: str, usuario_id: int, celda_id: Optional[int] = None, ahora: Optional[datetime] = None
    ) -> RegistroParqueo:
        ahora = ahora or datetime.now()
        placa = normalizar_placa(placa)
        validar_placa(placa)

        vehiculo = self.vehiculos.buscar_por_placa(placa)
        if not vehiculo:
            raise ReglaNegocioError(f"El vehículo {placa} no está registrado como mensualidad.")
        if not self.mensualidades.vigente(vehiculo.id, ahora.date()):
            raise ReglaNegocioError(f"El vehículo {placa} no tiene una mensualidad vigente.")
        if self.registros.abierto_por_vehiculo(vehiculo.id):
            raise ReglaNegocioError(f"El vehículo {placa} ya se encuentra dentro del parqueadero.")

        if celda_id:
            celda = self.celdas.obtener(celda_id)
            if not celda or not celda.esta_libre():
                raise ReglaNegocioError("La celda seleccionada no está disponible.")
            if celda.tipo_vehiculo != vehiculo.tipo:
                raise ReglaNegocioError(f"La celda {celda.codigo} no corresponde a un vehículo tipo {vehiculo.tipo}.")
        else:
            libres = self.celdas.libres(vehiculo.tipo)
            if not libres:
                raise ReglaNegocioError(f"No hay celdas libres para vehículos tipo {vehiculo.tipo}.")
            celda = libres[0]

        with self.db:
            registro_id = self.registros.crear_entrada(
                vehiculo.id, celda.id, ahora.strftime(FORMATO_FECHA_HORA), usuario_id
            )
            self.celdas.cambiar_estado(celda.id, "OCUPADA")
        return self.registros.obtener(registro_id)

    def registrar_salida(self, placa: str, usuario_id: int, ahora: Optional[datetime] = None) -> RegistroParqueo:
        ahora = ahora or datetime.now()
        _, registro = self._vehiculo_dentro(placa)
        with self.db:
            self.registros.cerrar(registro.id, ahora.strftime(FORMATO_FECHA_HORA), usuario_id)
            self.celdas.cambiar_estado(registro.celda_id, "LIBRE")
        return self.registros.obtener(registro.id)

    def registrar_novedad(
        self, placa: str, usuario_id: int, tipo: str, descripcion: str, ahora: Optional[datetime] = None
    ) -> int:
        ahora = ahora or datetime.now()
        descripcion = (descripcion or "").strip()
        if tipo not in TIPOS_NOVEDAD:
            raise ReglaNegocioError("Seleccione un tipo de novedad válido.")
        if len(descripcion) < 5:
            raise ReglaNegocioError("Describa la novedad (mínimo 5 caracteres).")
        _, registro = self._vehiculo_dentro(placa)
        with self.db:
            return self.novedades.crear(
                registro.id, usuario_id, ahora.strftime(FORMATO_FECHA_HORA), tipo, descripcion[:500]
            )

    def alternar_mantenimiento(self, celda_id: int):
        celda = self.celdas.obtener(celda_id)
        if not celda:
            raise ReglaNegocioError("La celda no existe.")
        if celda.estado == "OCUPADA":
            raise ReglaNegocioError(f"La celda {celda.codigo} está ocupada; registre primero la salida.")
        with self.db:
            self.celdas.cambiar_estado(celda.id, "LIBRE" if celda.estado == "MANTENIMIENTO" else "MANTENIMIENTO")

    def tablero(self, hoy: Optional[datetime] = None) -> dict:
        hoy = (hoy or datetime.now()).date().isoformat()
        movimientos = self.registros.movimientos_del_dia(hoy)
        return {
            "resumen": self.celdas.resumen(),
            "mapa": self.celdas.mapa(),
            "entradas_hoy": movimientos["entradas"] or 0,
            "salidas_hoy": movimientos["salidas"] or 0,
            "dentro": len(self.registros.activos()),
            "recientes": self.registros.ultimos_movimientos(),
        }
