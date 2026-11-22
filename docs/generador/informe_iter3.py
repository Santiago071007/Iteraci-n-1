"""Genera docs/Informe_Iteracion3_AutosColombia.pdf a partir de informe_iter3.html.

Uso:  python docs/generador/informe_iter3.py [url-del-repositorio]
Requiere haber generado antes las capturas (capturas.py 28) y los diagramas (staruml_exportar.py).
"""
import platform
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from html import escape
from importlib.metadata import version
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DOCS = RAIZ / "docs"
REPO_POR_DEFECTO = "https://github.com/Santiago071007/Iteraci-n-1"
NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

MOCKUPS = [
    ("28_pago_nuevo", "Registrar pago: búsqueda por placa y lista de vehículos pendientes de pago", "HU24"),
    ("29_pago_cotizacion", "Valor a pagar de una mensualidad vencida: meses, período, medio, referencia y total", "HU24, HU25"),
    ("30_pago_error", "Pago rechazado: la referencia ya fue registrada en otro recibo", "HU25"),
    ("31_recibo", "Recibo de pago numerado, visto por el operador (sin opción de anular)", "HU26"),
    ("32_recibo_anular", "Recibo visto por el administrador, con el formulario de anulación", "HU32"),
    ("33_recibo_anulado", "Recibo anulado con fecha, responsable y motivo", "HU32"),
    ("34_pagos_historial", "Historial de pagos con filtros y total recaudado", "HU27"),
    ("35_cartera", "Mensualidades por cobrar: vencidas, por vencer y al día", "HU28"),
    ("36_caja_admin", "Cierre de caja del administrador: recaudo por medio de pago y por cajero", "HU31"),
    ("37_caja_operador", "Cierre de caja de una operadora: solo los pagos que ella recibió", "HU30"),
    ("38_tarifas", "Tarifas de mensualidad por tipo de vehículo", "HU33"),
    ("39_cliente_estado_cuenta", "Detalle del cliente con su estado de cuenta y acceso a pagar", "HU29"),
]

# ID, HU / requisito, caso, precondición, datos y pasos, resultado esperado
CASOS = [
    ("CP-01", "HU24 · RF36, RF38", "Consultar valor a pagar",
     "ABC123 (carro) con mensualidad vigente hasta hoy + 20 días.", "Consultar la placa «abc-123» para 1 mes.",
     "Tarifa y total $ 180.000; el período empieza en hoy + 21 días y termina un mes después. No se guarda nada."),
    ("CP-02", "HU25 · RF37, RN11", "Pago en efectivo de mensualidad vigente",
     "ABC123 vigente.", "Registrar 1 mes en efectivo como operador.",
     "Pago VIGENTE por $ 180.000 sin referencia, a nombre del operador; la mensualidad se amplía sin perder días."),
    ("CP-03", "HU25 · RF37, RN11", "Pago de mensualidad vencida habilita la entrada",
     "QRS234 vencida hace 30 días; su entrada se rechaza.", "Registrar 1 mes en efectivo y luego la entrada del vehículo.",
     "El período empieza hoy (no en la fecha vencida) y la entrada se registra."),
    ("CP-04", "HU25 · RF38, RN13", "Pago de varios meses",
     "Moto XYZ78D vigente; tarifa de moto $ 90.000.", "Registrar 3 meses con tarjeta, referencia «AP-774512».",
     "Valor $ 270.000; el período cubre exactamente 3 meses a partir del día siguiente al vencimiento."),
    ("CP-05", "HU25 · RN12", "Meses inválidos y anticipo máximo",
     "ABC123 vigente.", "Pagar 0, 13, vacío y «dos» meses; pagar 11 meses y luego 1 mes más.",
     "Los valores inválidos se rechazan; se aceptan 11 meses y el siguiente se rechaza por superar 12 meses por adelantado."),
    ("CP-06", "HU25 · RF39, RN14", "Medio de pago y referencia",
     "ABC123 vigente.", "Medio «CHEQUE»; transferencia sin referencia, con «ab» y con símbolos; luego « trf 99 12 ».",
     "Se rechazan el medio desconocido y las referencias inválidas; la válida se guarda como «TRF9912»."),
    ("CP-07", "HU25 · RF39, RN14", "Referencia duplicada",
     "Pago de ABC123 por billetera con «NEQ5550001».", "Registrar a JKL456 la misma referencia por billetera; luego por transferencia.",
     "El duplicado se rechaza indicando el recibo y JKL456 no cambia; con otro medio sí se acepta."),
    ("CP-08", "HU24 · RN15", "Vehículo o cliente no válidos",
     "Datos de ejemplo.", "Placa «12AB»; placa ZZZ999 no registrada; desactivar al cliente de ABC123 y cobrarle.",
     "Los tres casos se rechazan con su mensaje (formato, no registrado, cliente inactivo)."),
    ("CP-09", "RF38 · RNF21", "Períodos en fin de mes",
     "Fechas fijas.", "Sumar meses al 31 de enero (año normal y bisiesto), cruzar de año; pagar 1 mes el 31/01/2027.",
     "31 ene + 1 mes = 28 o 29 feb; nov + 3 = feb del año siguiente; el pago cubre del 31/01 al 27/02."),
    ("CP-10", "HU32 · RF46, RN16, RN18", "Anular pago",
     "Pago de 2 meses de ABC123.", "Anular con motivo «error»; con motivo válido; anular de nuevo; anular el recibo 9999.",
     "Motivo corto rechazado; queda ANULADO con responsable, fecha y motivo; la vigencia vuelve a la anterior y no suma en el recaudo."),
    ("CP-11", "HU32 · RN17", "Solo se anula el último pago",
     "Dos pagos seguidos de ABC123.", "Anular el primero; luego el segundo y después el primero.",
     "El primero se rechaza indicando el recibo posterior; en orden inverso ambos se anulan."),
    ("CP-12", "HU32 · RN17", "No anular con el vehículo dentro",
     "QRS234 pagó hoy y está dentro.", "Anular su pago; registrar la salida y anular; registrar la entrada.",
     "Dentro: se rechaza. Tras la salida se anula y la entrada vuelve a rechazarse por falta de mensualidad."),
    ("CP-13", "HU32 · RN14", "Reutilizar referencia de pago anulado",
     "Transferencia «TRF700100» registrada a la placa equivocada.", "Anular ese pago y registrar la misma referencia a JKL456.",
     "El nuevo pago se acepta."),
    ("CP-14", "HU33 · RF47, RN13", "Actualizar tarifas",
     "Un pago de carro ya registrado a $ 180.000.", "Cambiar carro a «195.000»; pagar 2 meses de otro carro; probar «abc», 500, 9.000.000 y tipo «BUS».",
     "Nuevo pago por $ 390.000; el recibo anterior sigue en $ 180.000 y la moto en $ 90.000; queda el autor del cambio; lo inválido se rechaza."),
    ("CP-15", "HU28 · RF42", "Mensualidades por cobrar",
     "Datos de ejemplo.", "Consultar hoy y con fecha hoy + 12 días; pagar QRS234; desactivar un cliente.",
     "Hoy: QRS234 vencida, 4 al día, $ 180.000 por cobrar. En 12 días MNO901 por vencer (3 días). Tras pagar no hay vencidas; el cliente inactivo no aparece."),
    ("CP-16", "HU30, HU31 · RF44, RF45", "Cierre de caja",
     "Pagos de hoy: 2 en efectivo (operador), 1 transferencia y 1 tarjeta anulada (operadora).", "Consultar el cierre general y el de la operadora; rango con fecha inicial posterior.",
     "General: $ 540.000 en 3 pagos, $ 360.000 en efectivo, 1 anulado, totales por cajero. Operadora: $ 180.000. Rango inválido rechazado."),
    ("CP-17", "RF48", "Recibo al registrar un vehículo",
     "Sesión de administrador.", "Registrar NVO123 con $ 180.000 por billetera «NEQ900800»; registrar otro con tarjeta sin referencia.",
     "El primero queda con un recibo a nombre del administrador; el segundo se rechaza y el vehículo no se crea."),
    ("CP-18", "RNF18", "Control de acceso por rol",
     "Sesión de operador.", "Abrir y enviar /pagos/tarifas; enviar /pagos/1/anular; abrir un recibo; consultar un pago; entrar sin sesión.",
     "Tarifas y anulación redirigen sin ejecutar; el recibo no ofrece anular; el operador sí consulta y cobra; sin sesión se pide iniciar sesión."),
    ("CP-19", "HU24–HU33", "Flujo web completo",
     "Sesión de operador y luego de administrador.", "Consultar QRS234, pagar 2 meses por transferencia, ingresar el vehículo, recorrer las pantallas, cambiar tarifa y anular.",
     "Recibo por $ 360.000 con su referencia; todas las pantallas responden; la tarifa cambia; la anulación exige motivo y la salida del vehículo."),
    ("CP-20", "RNF19", "La base de datos protege los pagos",
     "Acceso directo a SQLite.", "Insertar pagos con valor 0, 13 meses, medio «CHEQUE», tarjeta sin referencia y referencia repetida; anular sin motivo.",
     "Todas las operaciones son rechazadas por las restricciones de la base de datos."),
    ("CP-21", "RNF24", "Migración desde la iteración 2",
     "Base de datos sin las tablas pago y tarifa.", "Iniciar la aplicación, abrir el historial y registrar un pago.",
     "Se crean las tablas y las 2 tarifas, se conservan las 5 mensualidades y el pago genera su recibo."),
]


def resultados_pruebas():
    """Ejecuta todas las pruebas y devuelve {CP-xx: [(prueba, aprobada)]}, totales y regresión."""
    fuente = (RAIZ / "tests" / "test_pagos.py").read_text(encoding="utf-8")
    mapa = {}
    for nombre, cp in re.findall(r"def (test_\w+)\(self\):\s*#\s*\[(CP-\d+)\]", fuente):
        mapa.setdefault(nombre, []).append(cp)

    sys.path.insert(0, str(RAIZ))
    suite = unittest.defaultTestLoader.discover(str(RAIZ / "tests"), top_level_dir=str(RAIZ))

    class Resultado(unittest.TextTestResult):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.estados = []

        def addSuccess(self, test):
            super().addSuccess(test)
            self.estados.append((test, True))

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.estados.append((test, False))

        def addError(self, test, err):
            super().addError(test, err)
            self.estados.append((test, False))

    with open(Path(tempfile.gettempdir()) / "pruebas_autos.txt", "w", encoding="utf-8") as salida:
        resultado = unittest.TextTestRunner(stream=salida, verbosity=2, resultclass=Resultado).run(suite)

    por_caso, regresion = {}, []
    for test, ok in resultado.estados:
        nombre = test.id().split(".")[-1]
        if "test_pagos" in test.id():
            for cp in mapa.get(nombre, []):
                por_caso.setdefault(cp, []).append((nombre, ok))
        else:
            regresion.append(ok)
    return por_caso, resultado.testsRun, len(resultado.failures) + len(resultado.errors), regresion


def tabla_casos(por_caso):
    filas = []
    for cp, hu, caso, pre, pasos, esperado in CASOS:
        pruebas = por_caso.get(cp, [])
        ok = bool(pruebas) and all(p[1] for p in pruebas)
        obtenido = ("Igual al esperado" if ok else "Difiere del esperado") + "<br><span class='meta'>" + \
            ", ".join(f"<code>{p[0]}</code>" for p in pruebas) + "</span>"
        estado = "<b class='ok'>Aprobado</b>" if ok else "<b class='mal'>Fallido</b>"
        filas.append(
            f"<tr><td><b>{cp}</b></td><td>{hu}</td><td><b>{caso}</b><br><span class='meta'>{pre}</span></td>"
            f"<td>{pasos}</td><td>{esperado}</td><td>{obtenido}</td><td>{estado}</td></tr>"
        )
    return "\n".join(filas)


def bloque_mockups():
    partes = []
    for archivo, titulo, hu in MOCKUPS:
        partes.append(f'<figure data-fig="{archivo}"><img src="../img/mockups/{archivo}.png" style="width:100%;max-height:19cm;object-fit:contain">'
                      f"<figcaption>{titulo} ({hu}).</figcaption></figure>")
    return "\n".join(partes)


def metodo(ruta, nombre):
    fuente = (RAIZ / ruta).read_text(encoding="utf-8")
    inicio = fuente.index(f"    def {nombre}(")
    siguiente = fuente.find("\n    def ", inicio + 10)
    cuerpo = fuente[inicio: siguiente if siguiente != -1 else len(fuente)]
    return escape(cuerpo.split("\n    # ----")[0].rstrip())


def numerar_figuras(html):
    numeros = {}
    for i, clave in enumerate(re.findall(r'<figure data-fig="([^"]+)"', html), start=1):
        numeros[clave] = i
    html = re.sub(r'(<figure data-fig="([^"]+)"[^>]*>.*?<figcaption>)',
                  lambda m: f"{m.group(1)}Figura {numeros[m.group(2)]}. ", html, flags=re.S)
    return re.sub(r"\{\{fig:([^}]+)\}\}", lambda m: str(numeros[m.group(1)]), html), len(numeros)


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else REPO_POR_DEFECTO
    hoy = date.today()
    por_caso, total, fallas, regresion = resultados_pruebas()
    aprobados = sum(1 for c in CASOS if por_caso.get(c[0]) and all(p[1] for p in por_caso[c[0]]))
    estilos = re.search(r"<style>(.*?)</style>", (AQUI / "informe_iter2.html").read_text(encoding="utf-8"), re.S).group(1)
    html = (AQUI / "informe_iter3.html").read_text(encoding="utf-8")
    reemplazos = {
        "{{ESTILOS}}": estilos.strip("\n"),
        "{{FECHA}}": f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}",
        "{{MOCKUPS}}": bloque_mockups(),
        "{{CASOS_PRUEBA}}": tabla_casos(por_caso),
        "{{N_CASOS}}": str(len(CASOS)),
        "{{N_APROBADOS}}": str(aprobados),
        "{{N_PRUEBAS}}": str(total),
        "{{N_FALLAS}}": str(fallas),
        "{{N_REGRESION_OK}}": str(sum(regresion)),
        "{{N_REGRESION}}": str(len(regresion)),
        "{{N_ITER3}}": str(total - len(regresion)),
        "{{RESULTADO}}": "todas aprobadas" if fallas == 0 else f"{fallas} con fallas",
        "{{PYTHON}}": platform.python_version(),
        "{{FLASK}}": version("flask"),
        "{{SQLITE}}": sqlite3.sqlite_version,
        "{{CODIGO_REGISTRAR}}": metodo("autoscolombia/services/pago_service.py", "registrar_pago"),
        "{{CODIGO_ANULAR}}": metodo("autoscolombia/services/pago_service.py", "anular_pago"),
        "{{REPO}}": escape(repo),
    }
    for clave, valor in reemplazos.items():
        html = html.replace(clave, valor)
    html, n_figuras = numerar_figuras(html)

    salida_html = DOCS / "informe" / "informe_iter3.html"
    salida_html.parent.mkdir(exist_ok=True)
    salida_html.write_text(html, encoding="utf-8")
    pdf = DOCS / "Informe_Iteracion3_AutosColombia.pdf"
    navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
    if not navegador:
        sys.exit(f"HTML generado en {salida_html}; instale Edge o Chrome para exportar el PDF.")
    pdf.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        try:
            subprocess.run(
                [navegador, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}",
                 "--no-pdf-header-footer", f"--print-to-pdf={pdf}", salida_html.as_uri()],
                capture_output=True, timeout=180,
            )
        except subprocess.TimeoutExpired:
            pass
    print("PDF:", pdf if pdf.exists() else "NO GENERADO", f"| {n_figuras} figuras | {total} pruebas, {fallas} fallas |",
          f"{aprobados}/{len(CASOS)} casos aprobados")


if __name__ == "__main__":
    main()
