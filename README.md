# Autos Colombia · Parqueadero por mensualidad

Sistema web para gestionar la operación diaria del parqueadero **Autos Colombia**.

**Iteración 1 – Gestión de la entrada y salida de vehículos:** registro de entradas y salidas con validación de placa y mensualidad vigente, asignación y liberación automática de celdas, novedades por vehículo, mapa de ocupación, vehículos dentro e historial.

**Iteración 2 – Gestión de usuarios y gestión de celdas:** usuarios del sistema (crear, editar rol, activar/desactivar, restablecer y cambiar contraseña, siempre con al menos un administrador activo), clientes (registrar, editar, activar/desactivar, asociar vehículos; un cliente inactivo no ingresa) y celdas (crear una o por rango, editar, mantenimiento con motivo, habilitar, eliminar si no tiene historial, detalle con historial de uso).

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
| ltorres  | Turno2026   | Operador      |
| mdiaz    | Turno2026   | Operador (inactivo, para probar el rechazo) |

Placas de ejemplo: `ABC123`, `JKL456`, `MNO901` (carros), `XYZ78D` (moto), `QRS234` (mensualidad vencida, para ver el rechazo).

Reiniciar la base de datos: `flask --app app init-db`. Una base de datos creada en la iteración 1 se actualiza sola al iniciar (columnas nuevas, sin perder datos).

## Pruebas

```bash
python -m unittest discover -s tests -t . -v
```

## Estructura

```
autoscolombia/
  controllers/    capa de presentación (Blueprints de Flask)
  services/       lógica de negocio (ParqueoService, VehiculoService, AuthService,
                  UsuarioService, ClienteService, CeldaService)
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

- Informe iteración 2: [`docs/Informe_Iteracion2_AutosColombia.pdf`](docs/Informe_Iteracion2_AutosColombia.pdf) – requerimientos, casos de uso, historias de usuario, mockups, diagramas de secuencia (iteraciones 1 y 2), diagrama de componentes y plan de pruebas
- Informe iteración 1: [`docs/Informe_Iteracion1_AutosColombia.pdf`](docs/Informe_Iteracion1_AutosColombia.pdf)
- Proyecto StarUML: [`docs/AutosColombia.mdj`](docs/AutosColombia.mdj) con los modelos de ambas iteraciones; imágenes exportadas en [`docs/img/staruml`](docs/img/staruml)
- Diagramas de la iteración 1 (SVG/PNG): [`docs/img/diagramas`](docs/img/diagramas) – arquitectura, casos de uso, clases, paquetes, MER, MR y modelo físico
- Mockups: [`docs/img/mockups`](docs/img/mockups) (01–13 iteración 1, 14–27 iteración 2)

### Regenerar la documentación

```bash
python docs/generador/capturas.py                      # mockups (capturas de la aplicación)
python docs/generador/staruml_exportar.py RUTA\StarUML.exe   # proyecto StarUML e imágenes de los diagramas
python docs/generador/informe_iter2.py <url-repo>      # informe PDF de la iteración 2 (ejecuta las pruebas)
```

`staruml_exportar.py` crea los diagramas de la iteración 1 con `staruml.py` y agrega los de la iteración 2 ejecutando `staruml_iter2.js` en la consola de scripts de StarUML 8.
