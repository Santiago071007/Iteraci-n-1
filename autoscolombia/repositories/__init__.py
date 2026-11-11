from .celda_repository import CeldaRepository
from .mensualidad_repository import MensualidadRepository
from .novedad_repository import NovedadRepository
from .registro_repository import RegistroRepository
from .usuario_repository import UsuarioRepository
from .vehiculo_repository import ClienteRepository, VehiculoRepository

__all__ = [
    "CeldaRepository",
    "ClienteRepository",
    "MensualidadRepository",
    "NovedadRepository",
    "RegistroRepository",
    "UsuarioRepository",
    "VehiculoRepository",
]
