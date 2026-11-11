from .auth_controller import bp as auth_bp
from .celda_controller import bp as celdas_bp
from .parqueo_controller import bp as parqueo_bp
from .vehiculo_controller import bp as vehiculos_bp

BLUEPRINTS = [auth_bp, parqueo_bp, vehiculos_bp, celdas_bp]
