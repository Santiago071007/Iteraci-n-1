from .auth_controller import bp as auth_bp
from .celda_controller import bp as celdas_bp
from .cliente_controller import bp as clientes_bp
from .parqueo_controller import bp as parqueo_bp
from .usuario_controller import bp as usuarios_bp
from .vehiculo_controller import bp as vehiculos_bp

BLUEPRINTS = [auth_bp, parqueo_bp, vehiculos_bp, clientes_bp, celdas_bp, usuarios_bp]
