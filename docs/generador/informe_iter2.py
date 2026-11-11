"""Genera docs/Informe_Iteracion2_AutosColombia.pdf a partir de informe_iter2.html.

Uso:  python docs/generador/informe_iter2.py [url-del-repositorio]
Requiere haber generado antes las capturas (capturas.py) y los diagramas (staruml_exportar.py).
"""
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from html import escape
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
    ("14_usuarios", "Usuarios del sistema: indicadores, búsqueda, edición y activación/desactivación", "HU10, HU12"),
    ("15_usuario_nuevo", "Crear usuario del sistema con rol y contraseña", "HU10"),
    ("16_usuario_error", "Creación rechazada: el nombre de usuario ya está en uso", "HU10"),
    ("17_usuario_editar", "Editar usuario, cambiar rol y restablecer contraseña", "HU11, HU13"),
    ("18_mi_clave", "Cambiar mi contraseña", "HU14"),
    ("19_clientes", "Listado de clientes con estado de mensualidades y vehículos dentro", "HU16"),
    ("20_cliente_nuevo", "Registrar cliente", "HU15"),
    ("21_cliente_detalle", "Detalle del cliente con sus vehículos; editar y desactivar", "HU16, HU17, HU18"),
    ("22_cliente_vehiculo", "Asociar un vehículo de mensualidad a un cliente existente", "HU18"),
    ("23_celdas", "Gestión de celdas: resumen por tipo, mapa y listado", "HU19, HU23"),
    ("24_celda_nueva", "Crear celdas por rango (rechazo por códigos repetidos)", "HU19"),
    ("25_celda_detalle", "Detalle de celda: poner en mantenimiento, editar e historial de uso", "HU20, HU21, HU23"),
    ("26_celda_mantenimiento", "Celda en mantenimiento con su motivo y opción de habilitar", "HU21"),
    ("27_celda_error", "Eliminación rechazada: la celda tiene historial", "HU22"),
]

# ID, HU / requisito, caso, precondición, datos y pasos, resultado esperado
CASOS = [
    ("CP-01", "HU10 · RF16", "Crear usuario del sistema",
     "Sesión de administrador.", "Nombre «Ana María Ruiz», usuario «ARuiz», rol Operador, clave «Clave2026» (dos veces).",
     "Se crea el usuario «aruiz» (en minúsculas), activo; la clave se guarda cifrada y permite iniciar sesión."),
    ("CP-02", "HU10 · RF17", "Usuario duplicado",
     "Existe el usuario «operador».", "Crear otro usuario con nombre de usuario «operador».",
     "Se rechaza: «El nombre de usuario 'operador' ya está en uso». No se crea nada."),
    ("CP-03", "HU10 · RF17", "Validar formato de usuario, contraseña y rol",
     "Sesión de administrador.", "Usuario «a b»; clave «corta1»; clave sin números; confirmación distinta; rol «SUPERVISOR».",
     "Cada caso se rechaza con un mensaje que explica la regla incumplida."),
    ("CP-04", "HU11 · RF18", "Editar nombre y rol",
     "Existe el operador «operador».", "Cambiar nombre a «Pedro Pablo Operador» y rol a Administrador.",
     "Se guardan el nuevo nombre y el rol; el nombre de usuario no cambia."),
    ("CP-05", "HU12 · RF19", "Usuario inactivo no inicia sesión",
     "Usuario «operador» activo.", "Desactivarlo e intentar iniciar sesión; luego activarlo e intentar de nuevo.",
     "Inactivo: «Usuario o contraseña incorrectos». Activo de nuevo: ingresa normalmente."),
    ("CP-06", "HU11, HU12 · RF20", "Proteger a los administradores",
     "Un solo administrador activo.", "Desactivarse a sí mismo; quitarse el rol; quitar el rol o desactivar al último administrador.",
     "Todas las acciones se rechazan; siempre queda al menos un administrador activo."),
    ("CP-07", "HU13, HU14 · RF21, RF22", "Restablecer y cambiar contraseña",
     "Usuario «operador».", "Admin restablece a «NuevaClave1»; el usuario la cambia con clave actual errada, igual y luego válida.",
     "Funciona la clave restablecida; se rechaza clave actual errada o repetida; tras el cambio solo sirve la nueva."),
    ("CP-08", "HU15 · RF24, RF25", "Registrar cliente",
     "Sesión de administrador.", "Documento «1.098.765.432», nombre «  Juan   Pérez », tel. «300 123 4567», correo «Juan@Correo.COM».",
     "Se guarda normalizado: 1098765432, «Juan Pérez», 3001234567, juan@correo.com; estado activo."),
    ("CP-09", "HU15 · RF25", "Validar datos del cliente",
     "Existe el documento 1020304050.", "Documento repetido; documento «12AB»; nombre de 1 letra; teléfono «12»; correo «juan@».",
     "Cada registro se rechaza con el mensaje correspondiente."),
    ("CP-10", "HU16 · RF26", "Editar cliente sin duplicar documento",
     "Clientes 1 y 2 registrados.", "Cambiar el teléfono del cliente 1; luego asignarle el documento del cliente 2.",
     "El teléfono se actualiza; el documento duplicado se rechaza."),
    ("CP-11", "HU17 · RF28", "Cliente inactivo no ingresa vehículos",
     "Cliente con vehículo ABC123 y mensualidad vigente.", "Desactivar el cliente; registrar entrada de ABC123 y asociarle un vehículo; reactivarlo.",
     "Inactivo: entrada y nuevo vehículo rechazados. Reactivado: la entrada se registra."),
    ("CP-12", "HU17 · RF28", "No desactivar cliente con vehículo dentro",
     "ABC123 está dentro del parqueadero.", "Desactivar al propietario de ABC123.",
     "Se rechaza: debe registrarse primero la salida."),
    ("CP-13", "HU18 · RF29", "Asociar vehículo a cliente",
     "Cliente 55667788 sin vehículos.", "Registrar la moto WER45T con mensualidad desde el detalle del cliente.",
     "El vehículo queda asociado al cliente y aparece en su detalle."),
    ("CP-14", "HU19 · RF30", "Crear una celda",
     "Sesión de administrador.", "Código « a-09 » tipo Carro; luego «A-01» (existente), «CELDA9» y tipo «BUS».",
     "Se crea A-09 libre; los demás casos se rechazan (código repetido, formato, tipo)."),
    ("CP-15", "HU19 · RF31", "Crear celdas por rango",
     "Existen M-01 a M-04.", "Crear M-05 a M-07; luego M-07 a M-09; luego B-01 a B-60.",
     "Se crean 3 celdas; el segundo rango no crea ninguna (M-07 repetida); el tercero supera el máximo de 50."),
    ("CP-16", "HU20 · RF32", "Editar celda",
     "A-01 libre; JKL456 ocupa otra celda.", "Cambiar A-01 a «A-11»/Moto; usar el código «A-02»; editar la celda ocupada.",
     "Primer cambio guardado; código repetido y celda ocupada se rechazan."),
    ("CP-17", "HU21 · RF33", "Mantenimiento y habilitación",
     "A-01 libre.", "Ponerla en mantenimiento con motivo «Demarcación borrada»; intentar asignarla; habilitarla; motivo vacío.",
     "Queda en mantenimiento con su motivo y no se asigna; al habilitar vuelve a LIBRE; sin motivo se rechaza."),
    ("CP-18", "HU21 · RN03", "No mantenimiento de celda ocupada",
     "ABC123 ocupa una celda.", "Poner esa celda en mantenimiento.",
     "Se rechaza: la celda está ocupada."),
    ("CP-19", "HU22 · RF34", "Eliminar celda",
     "Celda A-30 nueva; celda usada por ABC123.", "Eliminar A-30; eliminar la celda ocupada; registrar salida y eliminarla.",
     "A-30 se elimina; la ocupada y la que tiene historial se rechazan (se sugiere mantenimiento)."),
    ("CP-20", "RNF10", "Control de acceso por rol",
     "Sesión de operador.", "Abrir /usuarios, /usuarios/nuevo, /clientes/nuevo, /celdas/nueva, editar cliente, eliminar celda.",
     "Se redirige al tablero sin ejecutar; consultas de clientes y celdas y «mi contraseña» sí están permitidas."),
    ("CP-21", "HU10, HU15, HU19, HU21", "Flujo web del administrador",
     "Sesión de administrador.", "Recorrer todas las pantallas; crear usuario, cliente, celdas B-01 a B-03 y poner A-01 en mantenimiento.",
     "Todas las pantallas responden 200 y cada operación muestra su confirmación."),
]


def resultados_pruebas():
    """Ejecuta las pruebas y devuelve {CP-xx: [(prueba, aprobada)]}, totales y resumen."""
    fuente = (RAIZ / "tests" / "test_usuarios_celdas.py").read_text(encoding="utf-8")
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

    por_caso, iter1 = {}, []
    for test, ok in resultado.estados:
        nombre = test.id().split(".")[-1]
        if "test_usuarios_celdas" in test.id():
            for cp in mapa.get(nombre, []):
                por_caso.setdefault(cp, []).append((nombre, ok))
        else:
            iter1.append(ok)
    return por_caso, resultado.testsRun, len(resultado.failures) + len(resultado.errors), iter1


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
        partes.append(f'<figure data-fig="{archivo}"><img src="../img/mockups/{archivo}.png" style="width:100%">'
                      f"<figcaption>{titulo} ({hu}).</figcaption></figure>")
    return "\n".join(partes)


def metodo(ruta, clase_metodo):
    fuente = (RAIZ / ruta).read_text(encoding="utf-8")
    inicio = fuente.index(f"    def {clase_metodo}(")
    siguiente = fuente.find("\n    def ", inicio + 10)
    return escape(fuente[inicio: siguiente if siguiente != -1 else len(fuente)].rstrip())


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
    por_caso, total, fallas, iter1 = resultados_pruebas()
    aprobados = sum(1 for c in CASOS if por_caso.get(c[0]) and all(p[1] for p in por_caso[c[0]]))
    html = (AQUI / "informe_iter2.html").read_text(encoding="utf-8")
    reemplazos = {
        "{{FECHA}}": f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}",
        "{{MOCKUPS}}": bloque_mockups(),
        "{{CASOS_PRUEBA}}": tabla_casos(por_caso),
        "{{N_CASOS}}": str(len(CASOS)),
        "{{N_APROBADOS}}": str(aprobados),
        "{{N_PRUEBAS}}": str(total),
        "{{N_FALLAS}}": str(fallas),
        "{{N_ITER1}}": str(len(iter1)),
        "{{N_ITER1_OK}}": str(sum(iter1)),
        "{{N_ITER2}}": str(total - len(iter1)),
        "{{RESULTADO}}": "todas aprobadas" if fallas == 0 else f"{fallas} con fallas",
        "{{CODIGO_USUARIO}}": metodo("autoscolombia/services/usuario_service.py", "cambiar_estado"),
        "{{CODIGO_CELDA}}": metodo("autoscolombia/services/celda_service.py", "eliminar"),
        "{{REPO}}": escape(repo),
    }
    for clave, valor in reemplazos.items():
        html = html.replace(clave, valor)
    html, n_figuras = numerar_figuras(html)

    salida_html = DOCS / "informe" / "informe_iter2.html"
    salida_html.parent.mkdir(exist_ok=True)
    salida_html.write_text(html, encoding="utf-8")
    pdf = DOCS / "Informe_Iteracion2_AutosColombia.pdf"
    navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
    if not navegador:
        sys.exit(f"HTML generado en {salida_html}; instale Edge o Chrome para exportar el PDF.")
    pdf.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        try:
            subprocess.run(
                [navegador, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}",
                 "--no-pdf-header-footer", f"--print-to-pdf={pdf}", salida_html.as_uri()],
                capture_output=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            pass
    print("PDF:", pdf if pdf.exists() else "NO GENERADO", f"| {n_figuras} figuras | {total} pruebas, {fallas} fallas |",
          f"{aprobados}/{len(CASOS)} casos aprobados")


if __name__ == "__main__":
    main()
