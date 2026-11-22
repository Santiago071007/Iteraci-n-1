"""Genera los mockups (capturas de la aplicación con datos de ejemplo) en docs/img/mockups.

Uso:  python docs/generador/capturas.py [desde]
`desde` es el número de la primera pantalla a generar (por ejemplo 28 para solo la iteración 3).
"""
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
from autoscolombia.services import PagoService, ParqueoService

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
    # Iteración 3: gestión de pagos. Cuarto elemento opcional: {"usuario": ..., "alto": ...}
    ("28_pago_nuevo", "/pagos/nuevo", None),
    ("29_pago_cotizacion", "/pagos/nuevo?placa=QRS234&meses=2&medio=TRANSFERENCIA&referencia=TRF556677", None, {"alto": 800}),
    ("30_pago_error", "/pagos/nuevo", {"placa": "QRS234", "meses": "1", "medio": "TRANSFERENCIA", "referencia": "TRF915530"},
     {"usuario": "operador", "alto": 800}),
    ("31_recibo", "/pagos/{recibo}", None, {"usuario": "operador", "alto": 930}),
    ("32_recibo_anular", "/pagos/{recibo}", None, {"alto": 930}),
    ("33_recibo_anulado", "/pagos/{anulado}", None, {"alto": 1010}),
    ("34_pagos_historial", "/pagos/", None, {"alto": 900}),
    ("35_cartera", "/pagos/cartera", None, {"alto": 880}),
    ("36_caja_admin", "/pagos/caja", None, {"alto": 980}),
    ("37_caja_operador", "/pagos/caja", None, {"usuario": "ltorres", "alto": 800}),
    ("38_tarifas", "/pagos/tarifas", None),
    ("39_cliente_estado_cuenta", "/clientes/2", None, {"alto": 800}),
]
CLAVES = {"admin": "admin123", "operador": "operador123", "ltorres": "Turno2026"}


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
        return preparar_pagos(ahora)


def preparar_pagos(ahora):
    """Pagos del día de dos cajeros (uno anulado) y dos vehículos con la mensualidad por vencer."""
    bd = get_db()
    hoy = ahora.date()
    por_vencer = [("HJK45E", "MOTO", "Honda", "Rojo", 5, 3, 90000), ("TUV567", "CARRO", "Toyota", "Plata", 3, 0, 180000)]
    for placa, tipo, marca, color, cliente_id, dias, valor in por_vencer:
        inicio, fin = (hoy - timedelta(days=30 - dias)).isoformat(), (hoy + timedelta(days=dias)).isoformat()
        vehiculo_id = bd.execute("INSERT INTO vehiculo (placa, tipo, marca, color, cliente_id) VALUES (?, ?, ?, ?, ?)",
                                 (placa, tipo, marca, color, cliente_id)).lastrowid
        mensualidad_id = bd.execute("INSERT INTO mensualidad (vehiculo_id, fecha_inicio, fecha_fin, valor) VALUES (?, ?, ?, ?)",
                                    (vehiculo_id, inicio, fin, valor)).lastrowid
        bd.execute("INSERT INTO pago (mensualidad_id, vehiculo_id, fecha, meses, periodo_inicio, periodo_fin, valor, medio, usuario_id) "
                   "VALUES (?, ?, ?, 1, ?, ?, ?, 'EFECTIVO', 3)", (mensualidad_id, vehiculo_id, inicio + " 10:25:00", inicio, fin, valor))
    bd.commit()
    pagos = PagoService(bd)
    pagos.registrar_pago("ABC123", 1, "EFECTIVO", None, 2, ahora=ahora - timedelta(hours=4, minutes=12))
    recibo = pagos.registrar_pago("XYZ78D", 2, "BILLETERA", "NEQ884213", 2, ahora=ahora - timedelta(hours=3, minutes=31))
    pagos.registrar_pago("JKL456", 1, "TRANSFERENCIA", "TRF915530", 3, ahora=ahora - timedelta(hours=2, minutes=48))
    anulado = pagos.registrar_pago("MNO901", 1, "TARJETA", "AP-203948", 3, ahora=ahora - timedelta(hours=1, minutes=55))
    pagos.anular_pago(anulado.id, "El datáfono rechazó la transacción; el cliente pagó en efectivo.", 1,
                      ahora=ahora - timedelta(hours=1, minutes=47))
    pagos.registrar_pago("MNO901", 1, "EFECTIVO", None, 3, ahora=ahora - timedelta(hours=1, minutes=44))
    return {"recibo": recibo.id, "anulado": anulado.id}


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
        ids = preparar_datos(app)
        cliente = app.test_client()
        desde = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        for nombre, ruta, formulario, *resto in PANTALLAS:
            if int(nombre[:2]) < desde:
                continue
            opciones = resto[0] if resto else {}
            usuario = opciones.get("usuario", "admin")
            ruta = ruta.format(**ids)
            if nombre != "01_login":
                cliente.get("/logout")
                cliente.post("/login", data={"username": usuario, "password": CLAVES[usuario]})
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
                     f"--user-data-dir={tmp / 'perfil'}", f"--window-size=1280,{opciones.get('alto', 760)}",
                     f"--screenshot={png}", pagina.as_uri()],
                    capture_output=True, timeout=30,
                )
            except subprocess.TimeoutExpired:
                pass
            print("ok" if png.exists() else "SIN PNG", png.name)
        shutil.rmtree(tmp / "perfil", ignore_errors=True)


if __name__ == "__main__":
    main()
