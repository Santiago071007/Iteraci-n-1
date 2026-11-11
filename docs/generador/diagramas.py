import subprocess
import tempfile
from pathlib import Path

from svg import BORDE, CABECERA, CREMA, FONDO_CAPA, SUAVE, Caja, Svg

SALIDA = Path(__file__).resolve().parents[1] / "img" / "diagramas"
NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def arquitectura():
    s = Svg(1060, 660)
    cliente = s.nodo(20, 80, 200, 140, "«device» Equipo portería")
    navegador = s.componente(40, 130, 160, 60, "Navegador web\n(HTML5 / CSS3)")

    servidor = s.nodo(280, 30, 560, 610, "«execution environment» Servidor de aplicación · Python 3 + Flask")
    capas = [
        (70, "Capa de presentación (controllers + templates)", [
            ("Controladores\n(Blueprints Flask)", 200), ("Vistas Jinja2\n+ hoja de estilos", 200)]),
        (215, "Capa de lógica de negocio (services)", [
            ("ParqueoService", 150), ("VehiculoService", 150), ("AuthService", 130)]),
        (360, "Capa de acceso a datos (repositories)", [
            ("RegistroRepository\nCeldaRepository", 150), ("VehiculoRepository\nMensualidadRepository", 185),
            ("NovedadRepository\nUsuarioRepository", 150)]),
    ]
    cajas_capa = []
    for y, titulo, comps in capas:
        capa = s.rect(300, y, 520, 120, relleno=FONDO_CAPA, rx=6)
        s.texto(312, y + 16, titulo, ancla="start", peso="700", tam=12.5, color="#12305a")
        total = sum(w for _, w in comps) + 16 * (len(comps) - 1)
        x = 300 + (520 - total) / 2
        for nombre, w in comps:
            s.componente(x, y + 38, w, 64, nombre, tam=11.5)
            x += w + 16
        cajas_capa.append(capa)
    modelos = s.rect(300, 505, 520, 52, relleno=CREMA, rx=6)
    s.texto(560, 531, "Modelo de dominio (models.py): Usuario, Cliente, Vehiculo, Mensualidad,\nCelda, RegistroParqueo, Novedad",
            tam=12)
    s.rect(300, 572, 520, 50, relleno="#fff", rx=6, punteado=True)
    s.texto(560, 597, "db.py · conexión sqlite3, creación del esquema y datos iniciales", tam=12)

    bd_nodo = s.nodo(880, 380, 160, 170, "«device» Servidor BD")
    bd = s.cilindro(905, 420, 110, 100, "SQLite\nautos_colombia\n.sqlite")

    s.linea([navegador.der(), (300, 160)], inicio="llena", fin="llena")
    s.texto(250, 148, "HTTP", tam=11.5, color=SUAVE, cursiva=True)
    s.linea([cajas_capa[0].abajo(), cajas_capa[1].arriba()], fin="llena")
    s.linea([cajas_capa[1].abajo(), cajas_capa[2].arriba()], fin="llena")
    s.linea([cajas_capa[2].der(0.75), (905, 450)], fin="llena")
    s.texto(862, 430, "SQL", tam=11.5, color=SUAVE, cursiva=True)
    return s


def casos_de_uso():
    s = Svg(1000, 780)
    s.rect(230, 20, 740, 740, relleno="#fbfcfe", rx=8)
    s.texto(600, 42, "Sistema Autos Colombia · Iteración 1: entrada y salida de vehículos", peso="700", tam=13.5)

    operador = s.actor(110, 220, "Operador")
    admin = s.actor(110, 560, "Administrador")
    s.linea([(110, 560), (110, 336)], fin="triangulo")

    x1, x2, rx, ry = 410, 770, 120, 28
    uc = {}
    nombres_op = [
        ("login", "UC01 Iniciar sesión"), ("entrada", "UC02 Registrar entrada"),
        ("salida", "UC03 Registrar salida"), ("novedad", "UC04 Registrar novedad"),
        ("dentro", "UC05 Consultar vehículos\ndentro"), ("historial", "UC06 Consultar historial"),
        ("mapa", "UC07 Consultar mapa\nde celdas"),
    ]
    for i, (k, nombre) in enumerate(nombres_op):
        uc[k] = s.elipse(x1, 95 + i * 76, rx, ry, nombre)
    uc["vehiculo"] = s.elipse(x1, 640, rx, ry, "UC08 Registrar vehículo\nde mensualidad")
    uc["celda"] = s.elipse(x1, 715, rx, ry, "UC09 Cambiar estado\nde celda")

    incluidos = [
        ("validar", 100, "Validar placa y\nmensualidad", "entrada"),
        ("asignar", 190, "Asignar celda", "entrada"),
        ("liberar", 290, "Liberar celda", "salida"),
        ("tiempo", 380,"Calcular tiempo\nde permanencia", "salida"),
    ]
    for k, y, nombre, base in incluidos:
        uc[k] = s.elipse(x2, y, 105, ry, nombre, relleno="#f6f8fb")
        s.conectar(uc[base], uc[k], etiqueta="«include»", punteado=True, fin="flecha", tam=10.5)

    origen = (132, 262)
    for k, _ in nombres_op:
        s.linea([origen, uc[k].izq()])
    origen = (132, 602)
    for k in ("vehiculo", "celda"):
        s.linea([origen, uc[k].izq()])
    return s


def clases():
    s = Svg(1180, 790)
    cliente = s.clase(30, 30, 210, "Cliente", ["- id: int", "- documento: str", "- nombres: str", "- telefono: str", "- email: str"])
    vehiculo = s.clase(380, 30, 220, "Vehiculo", ["- id: int", "- placa: str", "- tipo: str", "- marca: str", "- color: str"])
    mensualidad = s.clase(760, 30, 250, "Mensualidad",
                          ["- id: int", "- fecha_inicio: date", "- fecha_fin: date", "- valor: float"],
                          ["+ esta_vigente(hoy: date): bool"])
    usuario = s.clase(30, 330, 220, "Usuario",
                      ["- id: int", "- nombre: str", "- username: str", "- password_hash: str", "- rol: str", "- activo: bool"],
                      ["+ es_admin(): bool"])
    registro = s.clase(380, 330, 280, "RegistroParqueo",
                       ["- id: int", "- fecha_entrada: datetime", "- fecha_salida: datetime"],
                       ["+ esta_abierto(): bool", "+ tiempo_permanencia(): timedelta"])
    celda = s.clase(800, 330, 210, "Celda",
                    ["- id: int", "- codigo: str", "- tipo_vehiculo: str", "- estado: str"],
                    ["+ esta_libre(): bool"])
    novedad = s.clase(380, 600, 280, "Novedad",
                      ["- id: int", "- fecha: datetime", "- tipo: str", "- descripcion: str"])
    servicio = s.clase(760, 560, 400, "ParqueoService",
                       ["- vehiculos: VehiculoRepository", "- celdas: CeldaRepository",
                        "- registros: RegistroRepository", "- novedades: NovedadRepository"],
                       ["+ registrar_entrada(placa, usuario_id, celda_id): RegistroParqueo",
                        "+ registrar_salida(placa, usuario_id): RegistroParqueo",
                        "+ registrar_novedad(placa, usuario_id, tipo, desc): int",
                        "+ alternar_mantenimiento(celda_id)", "+ tablero(): dict"],
                       estereotipo="service")

    s.conectar(cliente, vehiculo, "posee", "1", "1..*")
    s.conectar(vehiculo, mensualidad, "tiene", "1", "0..*")
    p = [vehiculo.abajo(0.4), (vehiculo.x + vehiculo.w * 0.4, registro.y)]
    s.linea(p); s.etiquetas(p, "ingresa", "1", "0..*")
    p = [celda.izq(0.4), (registro.x + registro.w, celda.y + celda.h * 0.4)]
    s.linea(p); s.etiquetas(p, "asignada a", "1", "0..*")
    p = [usuario.der(0.3), (registro.x, usuario.y + usuario.h * 0.3)]
    s.linea(p); s.etiquetas(p, "registra", "1", "0..*")
    p = [(registro.x + registro.w * 0.5, registro.y + registro.h), novedad.arriba()]
    s.linea(p, inicio="rombo"); s.etiquetas(p, None, None, "0..*")
    s.texto(registro.x + registro.w * 0.5 + 40, (registro.y + registro.h + novedad.y) / 2, "contiene", tam=11.5, color=SUAVE, cursiva=True)
    p = [usuario.abajo(), (usuario.x + usuario.w / 2, novedad.y + 60), (novedad.x, novedad.y + 60)]
    s.linea(p); s.etiquetas(p, None, "1", "0..*")
    s.texto(250, novedad.y + 48, "reporta", tam=11.5, color=SUAVE, cursiva=True)
    s.linea([servicio.izq(0.12), (registro.x + registro.w, servicio.y + servicio.h * 0.12)], punteado=True, fin="flecha")
    s.texto(710, servicio.y + servicio.h * 0.12 - 10, "«use»", tam=11, color=SUAVE)
    s.linea([servicio.arriba(0.55), (servicio.x + servicio.w * 0.55, celda.y + celda.h)], punteado=True, fin="flecha")
    s.texto(servicio.x + servicio.w * 0.55 + 28, servicio.y - 22, "«use»", tam=11, color=SUAVE)
    return s


def paquetes():
    s = Svg(1040, 660)
    s.paquete(20, 50, 720, 590, "autoscolombia", relleno="#fbfcfe", titulo_dentro=True)
    w, h = 190, 78
    p = {
        "controllers": s.paquete(60, 110, w, h, "controllers", estereotipo="presentación"),
        "templates": s.paquete(300, 110, w, h, "templates", estereotipo="vista"),
        "static": s.paquete(530, 110, w - 20, h, "static/css"),
        "services": s.paquete(60, 300, w, h, "services", estereotipo="negocio"),
        "db": s.paquete(530, 300, w - 20, h, "db"),
        "repositories": s.paquete(60, 500, w, h, "repositories", estereotipo="datos"),
        "models": s.paquete(300, 500, w, h, "models", estereotipo="dominio"),
    }
    ext = {
        "flask": s.paquete(820, 110, 190, h, "Flask", estereotipo="framework"),
        "sqlite": s.paquete(820, 300, 190, h, "sqlite3", estereotipo="biblioteca"),
        "tests": s.paquete(820, 500, 190, h, "tests", estereotipo="pruebas"),
    }
    marco = Caja(20, 30, 720, 610)
    dependencias = [
        ("controllers", "templates"), ("templates", "static"), ("controllers", "services"),
        ("services", "repositories"), ("services", "models"), ("repositories", "models"),
        ("controllers", "db"),
    ]
    todos = {**p, **ext}
    for a, b in dependencias:
        s.conectar(todos[a], todos[b], punteado=True, fin="flecha")
    s.linea([p["db"].der(0.3), ext["flask"].izq(0.8)], punteado=True, fin="flecha")
    s.linea([p["db"].der(0.6), ext["sqlite"].izq(0.6)], punteado=True, fin="flecha")
    s.linea([ext["tests"].izq(0.6), (marco.x + marco.w, ext["tests"].y + ext["tests"].h * 0.6)], punteado=True, fin="flecha")
    s.texto(770, 225, "«import»", tam=11, color=SUAVE)
    s.texto(780, 372, "«import»", tam=11, color=SUAVE)
    s.texto(780, 572, "«import»", tam=11, color=SUAVE)
    return s


def mer():
    s = Svg(1200, 900)
    ent = {}
    pos = {
        "CLIENTE": (150, 210), "VEHICULO": (560, 210), "MENSUALIDAD": (1000, 210),
        "USUARIO": (130, 520), "REGISTRO_PARQUEO": (560, 520), "CELDA": (1000, 520),
        "NOVEDAD": (560, 790),
    }
    for nombre, (cx, cy) in pos.items():
        w = max(130, len(nombre) * 11 + 30)
        ent[nombre] = s.rect(cx - w / 2, cy - 24, w, 48, relleno=CABECERA, grosor=1.6)
        s.texto(cx, cy, nombre, peso="700")

    atributos = {
        "CLIENTE": [("id_cliente", -60, -105, True), ("documento", 30, -135, False), ("nombres", 110, -100, False),
                    ("telefono", -100, -45, False), ("email", 125, -50, False)],
        "VEHICULO": [("id_vehiculo", -120, -90, True), ("placa", -40, -125, False), ("tipo", 40, -125, False),
                     ("marca", 120, -95, False), ("color", 140, -50, False)],
        "MENSUALIDAD": [("id_mensualidad", -95, -110, True), ("fecha_inicio", 20, -130, False),
                        ("fecha_fin", 110, -85, False), ("valor", 110, 50, False)],
        "USUARIO": [("id_usuario", -40, -100, True), ("nombre", 55, -95, False), ("activo", -75, -50, False),
                    ("rol", 25, 90, False), ("password_hash", 120, 140, False), ("username", 150, 80, False)],
        "REGISTRO_PARQUEO": [("id_registro", 165, -80, True), ("fecha_entrada", 185, 80, False),
                             ("fecha_salida", 140, 135, False)],
        "CELDA": [("id_celda", -40, -100, True), ("codigo", 75, -85, False), ("tipo_vehiculo", 70, 80, False),
                  ("estado", -40, 95, False)],
        "NOVEDAD": [("id_novedad", -230, 40, True), ("fecha", 210, -25, False), ("tipo", 230, 30, False),
                    ("descripcion", 150, 75, False)],
    }
    for nombre, attrs in atributos.items():
        cx, cy = pos[nombre]
        for texto, dx, dy, pk in attrs:
            rx = max(42, len(texto) * 4.1 + 14)
            e = s.elipse(cx + dx, cy + dy, rx, 16, texto, tam=11.5, subrayado=pk)
            s.linea([ent[nombre].borde(e.centro), e.borde(ent[nombre].centro)], grosor=1)

    relaciones = [
        ("CLIENTE", "VEHICULO", "posee", "1", "N", (345, 210)),
        ("VEHICULO", "MENSUALIDAD", "tiene", "1", "N", (790, 210)),
        ("VEHICULO", "REGISTRO_PARQUEO", "ingresa", "1", "N", (560, 365)),
        ("USUARIO", "REGISTRO_PARQUEO", "registra", "1", "N", (330, 520)),
        ("CELDA", "REGISTRO_PARQUEO", "asigna", "1", "N", (800, 520)),
        ("REGISTRO_PARQUEO", "NOVEDAD", "contiene", "1", "N", (560, 660)),
    ]
    for a, b, verbo, ca, cb, (rx_, ry_) in relaciones:
        r = s.rombo(rx_, ry_, 110, 56, verbo)
        p1, p2 = ent[a].borde(r.centro), r.borde(ent[a].centro)
        s.linea([p1, p2]); s.etiquetas([p1, p2], None, ca, None)
        p1, p2 = r.borde(ent[b].centro), ent[b].borde(r.centro)
        s.linea([p1, p2]); s.etiquetas([p1, p2], None, None, cb)
    r = s.rombo(250, 790, 110, 56, "reporta")
    p = [ent["USUARIO"].abajo(0.15), (ent["USUARIO"].x + ent["USUARIO"].w * 0.15, 790), r.izq()]
    s.linea(p)
    s.etiquetas(p, None, "1", None)
    p = [(r.x + r.w, 790), ent["NOVEDAD"].izq()]
    s.linea(p); s.etiquetas(p, None, None, "N")
    s.texto(20, 880, "Notación de Chen · atributo subrayado = identificador", ancla="start", tam=11.5, color=SUAVE)
    return s


TABLAS = {
    "cliente": [("id", "INTEGER", "PK NN"), ("documento", "VARCHAR(20)", "NN UQ"), ("nombres", "VARCHAR(120)", "NN"),
                ("telefono", "VARCHAR(20)", ""), ("email", "VARCHAR(120)", "")],
    "vehiculo": [("id", "INTEGER", "PK NN"), ("placa", "VARCHAR(6)", "NN UQ"), ("tipo", "VARCHAR(10)", "NN"),
                 ("marca", "VARCHAR(40)", ""), ("color", "VARCHAR(30)", ""), ("cliente_id", "INTEGER", "FK NN")],
    "mensualidad": [("id", "INTEGER", "PK NN"), ("vehiculo_id", "INTEGER", "FK NN"), ("fecha_inicio", "DATE", "NN"),
                    ("fecha_fin", "DATE", "NN"), ("valor", "DECIMAL(12,2)", "NN")],
    "usuario": [("id", "INTEGER", "PK NN"), ("nombre", "VARCHAR(100)", "NN"), ("username", "VARCHAR(40)", "NN UQ"),
                ("password_hash", "VARCHAR(255)", "NN"), ("rol", "VARCHAR(15)", "NN"), ("activo", "INTEGER", "NN")],
    "registro_parqueo": [("id", "INTEGER", "PK NN"), ("vehiculo_id", "INTEGER", "FK NN"), ("celda_id", "INTEGER", "FK NN"),
                         ("fecha_entrada", "DATETIME", "NN"), ("fecha_salida", "DATETIME", ""),
                         ("usuario_entrada_id", "INTEGER", "FK NN"), ("usuario_salida_id", "INTEGER", "FK")],
    "celda": [("id", "INTEGER", "PK NN"), ("codigo", "VARCHAR(10)", "NN UQ"), ("tipo_vehiculo", "VARCHAR(10)", "NN"),
              ("estado", "VARCHAR(15)", "NN")],
    "novedad": [("id", "INTEGER", "PK NN"), ("registro_id", "INTEGER", "FK NN"), ("usuario_id", "INTEGER", "FK NN"),
                ("fecha", "DATETIME", "NN"), ("tipo", "VARCHAR(20)", "NN"), ("descripcion", "VARCHAR(500)", "NN")],
}


def modelo_tablas(con_tipos):
    w = 320 if con_tipos else 230
    sep = 110 if con_tipos else 120
    x = [30, 30 + w + sep, 30 + 2 * (w + sep)]
    s = Svg(x[2] + w + 30, 800)
    cols = {k: [(c, t, set(m.split())) for c, t, m in v] for k, v in TABLAS.items()}
    t = {
        "cliente": s.tabla(x[0], 40, w, "cliente", cols["cliente"], con_tipos),
        "vehiculo": s.tabla(x[1], 40, w, "vehiculo", cols["vehiculo"], con_tipos),
        "mensualidad": s.tabla(x[2], 40, w, "mensualidad", cols["mensualidad"], con_tipos),
        "usuario": s.tabla(x[0], 330, w, "usuario", cols["usuario"], con_tipos),
        "registro_parqueo": s.tabla(x[1], 300, w, "registro_parqueo", cols["registro_parqueo"], con_tipos),
        "celda": s.tabla(x[2], 330, w, "celda", cols["celda"], con_tipos),
        "novedad": s.tabla(x[1], 580, w, "novedad", cols["novedad"], con_tipos),
    }

    def fila(tabla, i):
        return t[tabla].y + 28 + 13 + i * 20

    s.linea([(x[0] + w, fila("cliente", 0)), (x[1], fila("vehiculo", 5))], inicio="uno", fin="muchos")
    s.linea([(x[1] + w, fila("vehiculo", 0)), (x[2], fila("mensualidad", 1))], inicio="uno", fin="muchos")
    s.linea([(x[1] + w / 2, t["vehiculo"].y + t["vehiculo"].h), (x[1] + w / 2, t["registro_parqueo"].y)], inicio="uno", fin="muchos")
    s.linea([(x[2], fila("celda", 0)), (x[1] + w, fila("registro_parqueo", 2))], inicio="uno", fin="muchos")
    s.linea([(x[0] + w, fila("usuario", 0)), (x[1], fila("registro_parqueo", 5))], inicio="uno", fin="muchos")
    s.linea([(x[0] + w, fila("usuario", 2)), (x[1], fila("registro_parqueo", 6))], inicio="uno", fin="muchos", punteado=True)
    s.linea([(x[1] + w / 2, t["registro_parqueo"].y + t["registro_parqueo"].h), (x[1] + w / 2, t["novedad"].y)], inicio="uno", fin="muchos")
    ux = x[0] + w / 2
    s.linea([(ux, t["usuario"].y + t["usuario"].h), (ux, fila("novedad", 2)), (x[1], fila("novedad", 2))], inicio="uno", fin="muchos")
    leyenda = "PK = llave primaria · FK = llave foránea · ‖ uno  ⋲ muchos"
    if con_tipos:
        leyenda += " · NN = NOT NULL · UQ = UNIQUE · SGBD: SQLite 3"
    s.texto(30, 775, leyenda, ancla="start", tam=11.5, color=SUAVE)
    return s


def a_png(svgs):
    navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
    if not navegador:
        print("Sin navegador: solo se generan SVG.")
        return
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for ruta, svg in svgs:
            png = ruta.with_suffix(".png")
            png.unlink(missing_ok=True)
            try:
                subprocess.run(
                    [navegador, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                     f"--user-data-dir={Path(tmp) / 'perfil'}", f"--window-size={svg.ancho},{svg.alto}",
                     f"--screenshot={png}", ruta.as_uri()],
                    capture_output=True, timeout=30,
                )
            except subprocess.TimeoutExpired:
                pass
            print("png" if png.exists() else "SIN PNG", png.name)


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    generados = []
    for nombre, svg in [
        ("arquitectura", arquitectura()),
        ("casos_de_uso", casos_de_uso()),
        ("clases", clases()),
        ("paquetes", paquetes()),
        ("mer", mer()),
        ("modelo_relacional", modelo_tablas(False)),
        ("modelo_fisico", modelo_tablas(True)),
    ]:
        ruta = SALIDA / f"{nombre}.svg"
        svg.guardar(ruta)
        generados.append((ruta, svg))
        print("ok", ruta.name)
    a_png(generados)


if __name__ == "__main__":
    main()
