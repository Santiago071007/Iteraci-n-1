from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

FORMATO_FECHA_HORA = "%Y-%m-%d %H:%M:%S"


def a_fecha_hora(valor: Optional[str]) -> Optional[datetime]:
    return datetime.strptime(valor, FORMATO_FECHA_HORA) if valor else None


@dataclass
class Usuario:
    id: int
    nombre: str
    username: str
    password_hash: str
    rol: str
    activo: int = 1

    def es_admin(self) -> bool:
        return self.rol == "ADMIN"


@dataclass
class Cliente:
    id: int
    documento: str
    nombres: str
    telefono: Optional[str]
    email: Optional[str]


@dataclass
class Vehiculo:
    id: int
    placa: str
    tipo: str
    marca: Optional[str]
    color: Optional[str]
    cliente_id: int


@dataclass
class Mensualidad:
    id: int
    vehiculo_id: int
    fecha_inicio: str
    fecha_fin: str
    valor: float

    def esta_vigente(self, hoy: date) -> bool:
        return self.fecha_inicio <= hoy.isoformat() <= self.fecha_fin


@dataclass
class Celda:
    id: int
    codigo: str
    tipo_vehiculo: str
    estado: str

    def esta_libre(self) -> bool:
        return self.estado == "LIBRE"


@dataclass
class RegistroParqueo:
    id: int
    vehiculo_id: int
    celda_id: int
    fecha_entrada: str
    fecha_salida: Optional[str]
    usuario_entrada_id: int
    usuario_salida_id: Optional[int]

    def esta_abierto(self) -> bool:
        return self.fecha_salida is None

    def tiempo_permanencia(self, hasta: Optional[datetime] = None) -> timedelta:
        fin = a_fecha_hora(self.fecha_salida) or hasta or datetime.now()
        return fin - a_fecha_hora(self.fecha_entrada)


@dataclass
class Novedad:
    id: int
    registro_id: int
    usuario_id: int
    fecha: str
    tipo: str
    descripcion: str
