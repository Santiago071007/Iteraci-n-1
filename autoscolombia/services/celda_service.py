import re
from typing import List, Optional

from ..models import Celda
from ..repositories import CeldaRepository
from .errores import ReglaNegocioError

TIPOS_CELDA = {"CARRO": "Carro", "MOTO": "Moto"}
PATRON_CODIGO = re.compile(r"^[A-Z]{1,2}-\d{2,3}$")
MAXIMO_LOTE = 50


def normalizar_codigo(codigo: Optional[str]) -> str:
    return re.sub(r"\s", "", codigo or "").upper()


class CeldaService:
    """Gestión de las celdas del parqueadero: creación, edición, estado y eliminación."""

    def __init__(self, db):
        self.db = db
        self.celdas = CeldaRepository(db)

    def obtener(self, celda_id: int) -> Celda:
        celda = self.celdas.obtener(celda_id)
        if not celda:
            raise ReglaNegocioError("La celda no existe.")
        return celda

    @staticmethod
    def _validar(codigo: str, tipo: Optional[str]):
        if not PATRON_CODIGO.match(codigo):
            raise ReglaNegocioError(
                f"El código '{codigo}' no es válido. Use letra(s), guion y número, p. ej. A-09 o M-05."
            )
        if tipo not in TIPOS_CELDA:
            raise ReglaNegocioError("Seleccione el tipo de vehículo de la celda.")

    def crear(self, codigo: str, tipo: str) -> int:
        codigo = normalizar_codigo(codigo)
        self._validar(codigo, tipo)
        if self.celdas.buscar_por_codigo(codigo):
            raise ReglaNegocioError(f"Ya existe una celda con el código {codigo}.")
        with self.db:
            return self.celdas.crear(codigo, tipo)

    def crear_lote(self, prefijo: str, desde, hasta, tipo: str) -> List[str]:
        prefijo = normalizar_codigo(prefijo).rstrip("-")
        try:
            desde, hasta = int(desde), int(hasta)
        except (TypeError, ValueError) as error:
            raise ReglaNegocioError("Indique el número inicial y el final del rango.") from error
        if desde < 1 or hasta < desde:
            raise ReglaNegocioError("El número final debe ser mayor o igual al inicial y ambos positivos.")
        if hasta - desde + 1 > MAXIMO_LOTE:
            raise ReglaNegocioError(f"Se pueden crear máximo {MAXIMO_LOTE} celdas a la vez.")
        codigos = [f"{prefijo}-{n:02d}" for n in range(desde, hasta + 1)]
        for codigo in codigos:
            self._validar(codigo, tipo)
        repetidas = [c for c in codigos if self.celdas.buscar_por_codigo(c)]
        if repetidas:
            raise ReglaNegocioError(f"Ya existen las celdas {', '.join(repetidas)}; no se creó ninguna.")
        with self.db:
            for codigo in codigos:
                self.celdas.crear(codigo, tipo)
        return codigos

    def actualizar(self, celda_id: int, codigo: str, tipo: str):
        celda = self.obtener(celda_id)
        codigo = normalizar_codigo(codigo)
        self._validar(codigo, tipo)
        if celda.esta_ocupada():
            raise ReglaNegocioError(f"La celda {celda.codigo} está ocupada; no se puede modificar.")
        otra = self.celdas.buscar_por_codigo(codigo)
        if otra and otra.id != celda.id:
            raise ReglaNegocioError(f"Ya existe una celda con el código {codigo}.")
        with self.db:
            self.celdas.actualizar(celda.id, codigo, tipo)

    def poner_en_mantenimiento(self, celda_id: int, observacion: str):
        celda = self.obtener(celda_id)
        observacion = " ".join((observacion or "").split())
        if celda.esta_ocupada():
            raise ReglaNegocioError(f"La celda {celda.codigo} está ocupada; registre primero la salida.")
        if celda.estado == "MANTENIMIENTO":
            raise ReglaNegocioError(f"La celda {celda.codigo} ya está en mantenimiento.")
        if len(observacion) < 5:
            raise ReglaNegocioError("Indique el motivo del mantenimiento (mínimo 5 caracteres).")
        with self.db:
            self.celdas.cambiar_estado(celda.id, "MANTENIMIENTO", observacion[:200])

    def habilitar(self, celda_id: int):
        celda = self.obtener(celda_id)
        if celda.estado != "MANTENIMIENTO":
            raise ReglaNegocioError(f"La celda {celda.codigo} no está en mantenimiento.")
        with self.db:
            self.celdas.cambiar_estado(celda.id, "LIBRE")

    def eliminar(self, celda_id: int) -> str:
        celda = self.obtener(celda_id)
        if celda.esta_ocupada():
            raise ReglaNegocioError(f"La celda {celda.codigo} está ocupada; no se puede eliminar.")
        if self.celdas.total_registros(celda.id):
            raise ReglaNegocioError(
                f"La celda {celda.codigo} tiene movimientos en el historial; póngala en mantenimiento en lugar de eliminarla."
            )
        with self.db:
            self.celdas.eliminar(celda.id)
        return celda.codigo
