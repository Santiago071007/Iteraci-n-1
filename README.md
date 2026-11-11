# Autos Colombia · Parqueadero por mensualidad

Sistema web para gestionar la operación diaria del parqueadero **Autos Colombia**.

**Iteración 1 – Gestión de la entrada y salida de vehículos:** registro de entradas y salidas con validación de placa y mensualidad vigente, asignación y liberación automática de celdas, novedades por vehículo, mapa de ocupación, vehículos dentro e historial.

## Tecnologías

Python 3.10+ · Flask 3.1 · Jinja2 · SQLite 3 · HTML5/CSS3 · unittest

## Ejecutar

En Windows basta con hacer doble clic en `iniciar.bat` (la primera vez crea el entorno e instala Flask; requiere Python e internet).

Manualmente:

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
flask --app app run
```

Abrir http://127.0.0.1:5000. La base de datos se crea sola con datos de ejemplo la primera vez.

| Usuario  | Contraseña  | Rol           |
|----------|-------------|---------------|
| admin    | admin123    | Administrador |
| operador | operador123 | Operador      |

Placas de ejemplo: `ABC123`, `JKL456`, `MNO901` (carros), `XYZ78D` (moto), `QRS234` (mensualidad vencida, para ver el rechazo).

Reiniciar la base de datos: `flask --app app init-db`

## Pruebas

```bash
python -m unittest discover -s tests -t . -v
```

## Estructura

```
autoscolombia/
  controllers/    capa de presentación (Blueprints de Flask)
  services/       lógica de negocio (ParqueoService, VehiculoService, AuthService)
  repositories/   acceso a datos (un repositorio por tabla)
  models.py       entidades del dominio
  db.py           conexión SQLite y creación del esquema
  templates/      vistas Jinja2
database/
  schema.sql      modelo físico (DDL)
  seed.sql        datos de ejemplo
tests/            pruebas automatizadas
docs/             informe PDF, diagramas (SVG/PNG) y mockups
```

## Documentación

- Informe: [`docs/Informe_Iteracion1_AutosColombia.pdf`](docs/Informe_Iteracion1_AutosColombia.pdf)
- Diagramas: [`docs/img/diagramas`](docs/img/diagramas) – arquitectura, casos de uso, clases, paquetes, MER, MR y modelo físico
- Proyecto StarUML: [`docs/AutosColombia.mdj`](docs/AutosColombia.mdj), imágenes exportadas en [`docs/img/staruml`](docs/img/staruml) – casos de uso, clases, paquetes y arquitectura (`python docs/generador/staruml.py` lo regenera)
- Mockups: [`docs/img/mockups`](docs/img/mockups)
- Regenerar diagramas, capturas e informe: `python docs/generador/diagramas.py`, `python docs/generador/capturas.py`, `python docs/generador/informe.py <url-repo>`
