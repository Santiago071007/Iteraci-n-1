import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from autoscolombia import create_app
from autoscolombia.db import get_db
from autoscolombia.services import ParqueoService

SALIDA = RAIZ / "docs" / "img" / "mockups"
NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
PANTALLAS = [
    ("01_login", "/logout", None),
    ("02_tablero", "/", None),
    ("03_entrada", "/entrada", None),
    ("04_entrada_error", "/entrada", {"placa": "QRS234"}),
    ("05_comprobante_entrada", "/registros/4", None),
    ("06_salida", "/salida", None),
    ("07_comprobante_salida", "/registros/1", None),
    ("08_activos", "/activos", None),
    ("09_novedades", "/novedades", None),
    ("10_historial", "/historial", None),
    ("11_vehiculos", "/vehiculos/", None),
    ("12_vehiculo_nuevo", "/vehiculos/nuevo", None),
    ("13_celdas", "/celdas/", None),
    # Iteración 2: gestión de usuarios y de celdas
    ("14_usuarios", "/usuarios/", None),
    ("15_usuario_nuevo", "/usuarios/nuevo", None),
    ("16_usuario_error", "/usuarios/nuevo", {"nombre": "Lucía Torres", "username": "ltorres", "rol": "OPERADOR",
                                             "password": "Turno2026", "confirmacion": "Turno2026"}),
    ("17_usuario_editar", "/usuarios/2/editar", None),
    ("18_mi_clave", "/usuarios/mi-clave", None),
    ("19_clientes", "/clientes/", None),
    ("20_cliente_nuevo", "/clientes/nuevo", None),
    ("21_cliente_detalle", "/clientes/2", None),
    ("22_cliente_vehiculo", "/vehiculos/nuevo?documento=43987654", None),
    ("23_celdas", "/celdas/", None),
    ("24_celda_nueva", "/celdas/nueva", {"modo": "lote", "prefijo": "A", "desde": "7", "hasta": "10", "tipo": "CARRO"}),
    ("25_celda_detalle", "/celdas/1", None),
    ("26_celda_mantenimiento", "/celdas/8", None),
    ("27_celda_error", "/celdas/1/eliminar", {}),
]


def preparar_datos(app):
    with app.app_context():
        servicio = ParqueoService(get_db())
        ahora = datetime.now().replace(second=0, microsecond=0)
        servicio.registrar_entrada("ABC123", 2, ahora=ahora - timedelta(hours=5, minutes=20))
        servicio.registrar_entrada("JKL456", 2, ahora=ahora - timedelta(hours=3, minutes=5))
        servicio.registrar_entrada("XYZ78D", 2, ahora=ahora - timedelta(hours=1, minutes=40))
        servicio.registrar_entrada("MNO901", 2, ahora=ahora - timedelta(minutes=35))
        servicio.registrar_salida("ABC123", 2, ahora=ahora - timedelta(minutes=10))
        servicio.registrar_novedad("JKL456", 2, "DANO", "Rayón en la puerta trasera derecha al ingresar.",
                                   ahora=ahora - timedelta(hours=3))


def main():
    navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
    if not navegador:
        sys.exit("No se encontró Edge ni Chrome.")
    SALIDA.mkdir(parents=True, exist_ok=True)
    css = (RAIZ / "autoscolombia" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (RAIZ / "autoscolombia" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        app = create_app({"TESTING": True, "DATABASE": str(tmp / "demo.sqlite")})
        preparar_datos(app)
        cliente = app.test_client()
        for nombre, ruta, formulario in PANTALLAS:
            if nombre != "01_login":
                cliente.post("/login", data={"username": "admin", "password": "admin123"})
            if formulario is not None:
                html = cliente.post(ruta, data=formulario, follow_redirects=True).get_data(as_text=True)
            else:
                html = cliente.get(ruta, follow_redirects=True).get_data(as_text=True)
            html = html.replace('<link rel="stylesheet" href="/static/css/app.css">', f"<style>{css}</style>")
            html = html.replace('<script src="/static/js/app.js" defer></script>', f"<script>{js}</script>")
            pagina = tmp / f"{nombre}.html"
            pagina.write_text(html, encoding="utf-8")
            png = SALIDA / f"{nombre}.png"
            png.unlink(missing_ok=True)
            try:
                subprocess.run(
                    [navegador, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=1500",
                     f"--user-data-dir={tmp / 'perfil'}", "--window-size=1280,760",
                     f"--screenshot={png}", pagina.as_uri()],
                    capture_output=True, timeout=30,
                )
            except subprocess.TimeoutExpired:
                pass
            print("ok" if png.exists() else "SIN PNG", png.name)
        shutil.rmtree(tmp / "perfil", ignore_errors=True)


if __name__ == "__main__":
    main()
