import re
import subprocess
import sys
import tempfile
from datetime import date
from html import escape
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DOCS = RAIZ / "docs"
NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

MOCKUPS = [
    ("01_login", 2, "Inicio de sesión", "HU01"),
    ("02_tablero", 3, "Tablero con indicadores y mapa de celdas", "HU06"),
    ("03_entrada", 4, "Registrar entrada", "HU02"),
    ("04_entrada_error", 5, "Entrada rechazada por mensualidad vencida", "HU03"),
    ("05_comprobante_entrada", 6, "Comprobante de entrada", "HU02"),
    ("06_salida", 7, "Registrar salida", "HU04"),
    ("07_comprobante_salida", 8, "Comprobante de salida con tiempo de permanencia", "HU04"),
    ("08_activos", 9, "Vehículos dentro del parqueadero", "HU06"),
    ("09_novedades", 10, "Registro y consulta de novedades", "HU05"),
    ("10_historial", 11, "Historial de movimientos con filtros", "HU07"),
    ("11_vehiculos", 12, "Vehículos de mensualidad", "HU08"),
    ("12_vehiculo_nuevo", 13, "Registrar vehículo de mensualidad", "HU08"),
    ("13_celdas", 14, "Gestión del estado de las celdas", "HU09"),
]


def ejecutar_pruebas():
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                       cwd=RAIZ, capture_output=True, text=True)
    total = re.search(r"Ran (\d+) test", r.stderr)
    estado = "OK" if r.returncode == 0 else "con fallas"
    return (total.group(1) if total else "?"), f"{total.group(1) if total else '?'} pruebas, resultado {estado}"


def bloque_mockups():
    partes = []
    for archivo, fig, titulo, hu in MOCKUPS:
        partes.append(
            f'<figure><img src="../img/mockups/{archivo}.png" style="width:100%">'
            f"<figcaption>Figura {fig}. {titulo} ({hu}).</figcaption></figure>"
        )
    return "\n".join(partes)


def codigo_entrada():
    fuente = (RAIZ / "autoscolombia" / "services" / "parqueo_service.py").read_text(encoding="utf-8")
    inicio = fuente.index("    def registrar_entrada")
    fin = fuente.index("    def registrar_salida")
    return escape(fuente[inicio:fin].rstrip())


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "[pegar aquí la URL del repositorio en GitHub]"
    hoy = date.today()
    n_pruebas, resultado = ejecutar_pruebas()
    html = (AQUI / "informe.html").read_text(encoding="utf-8")
    reemplazos = {
        "{{FECHA_MAYUS}}": f"{MESES[hoy.month - 1].capitalize()} de {hoy.year}",
        "{{MOCKUPS}}": bloque_mockups(),
        "{{DDL}}": escape((RAIZ / "database" / "schema.sql").read_text(encoding="utf-8")),
        "{{CODIGO_ENTRADA}}": codigo_entrada(),
        "{{REPO}}": escape(repo),
        "{{N_PRUEBAS}}": n_pruebas,
        "{{RESULTADO_PRUEBAS}}": resultado,
    }
    for clave, valor in reemplazos.items():
        html = html.replace(clave, valor)

    salida_html = DOCS / "informe" / "informe.html"
    salida_html.parent.mkdir(exist_ok=True)
    salida_html.write_text(html, encoding="utf-8")
    pdf = DOCS / "Informe_Iteracion1_AutosColombia.pdf"

    navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
    if not navegador:
        sys.exit(f"HTML generado en {salida_html}; instale Edge o Chrome para exportar el PDF.")
    pdf.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        try:
            subprocess.run(
                [navegador, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}",
                 "--no-pdf-header-footer", f"--print-to-pdf={pdf}", salida_html.as_uri()],
                capture_output=True, timeout=90,
            )
        except subprocess.TimeoutExpired:
            pass
    print("PDF:", pdf if pdf.exists() else "NO GENERADO", "|", resultado)


if __name__ == "__main__":
    main()
