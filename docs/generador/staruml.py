import json
import uuid
from pathlib import Path

SALIDA = Path(__file__).resolve().parents[1] / "AutosColombia.mdj"
FUENTE = "Arial;13;0"
FUENTE_NEGRITA = "Arial;13;1"


def nuevo_id():
    return uuid.uuid4().hex[:24]


def ref(obj):
    return {"$ref": obj["_id"]}


def elemento(tipo, padre, coleccion="ownedElements", **campos):
    obj = {"_type": tipo, "_id": nuevo_id(), "_parent": ref(padre), **campos}
    if coleccion:
        padre.setdefault(coleccion, []).append(obj)
    return obj


def _base_vista(tipo, padre, modelo=None, **campos):
    v = {
        "_type": tipo, "_id": nuevo_id(), "_parent": ref(padre),
        "visible": True, "enabled": True, "lineColor": "#000000", "fillColor": "#ffffff",
        "fontColor": "#000000", "font": FUENTE, "showShadow": True, "parentStyle": False,
        "containerChangeable": False, "containerExtending": False, "subViews": [],
    }
    if modelo is not None:
        v["model"] = ref(modelo)
    v.update(campos)
    return v


def etiqueta(padre, texto="", visible=True, negrita=False, x=0, y=0, w=0, h=13):
    lab = _base_vista("LabelView", padre, text=texto, visible=visible,
                      font=FUENTE_NEGRITA if negrita else FUENTE, horizontalAlignment=2,
                      verticalAlignment=5, left=x, top=y, width=w, height=h)
    padre["subViews"].append(lab)
    return lab


def compartimento_nombre(vista, modelo, nombre, x, y, w):
    c = _base_vista("UMLNameCompartmentView", vista, modelo, left=x, top=y, width=w, height=25)
    vista["subViews"].append(c)
    c["stereotypeLabel"] = ref(etiqueta(c, visible=False, x=x, y=y, w=w))
    c["nameLabel"] = ref(etiqueta(c, nombre, negrita=True, x=x, y=y + 6, w=w))
    c["namespaceLabel"] = ref(etiqueta(c, visible=False, x=x, y=y, w=w))
    c["propertyLabel"] = ref(etiqueta(c, visible=False, x=x, y=y, w=w))
    return c


def compartimento(tipo, vista, modelo, x, y, w, h, visible=True):
    c = _base_vista(tipo, vista, modelo, left=x, top=y, width=w, height=h, visible=visible)
    vista["subViews"].append(c)
    return c


def vista_nodo(tipo, diagrama, modelo, x, y, w, h, nombre, atributos=(), operaciones=(),
               clasificador=True, extra_compartimentos=(), **campos):
    v = _base_vista(tipo, diagrama, modelo, left=x, top=y, width=w, height=h,
                    containerChangeable=True, autoResize=False, **campos)
    diagrama["ownedViews"].append(v)
    v["nameCompartment"] = ref(compartimento_nombre(v, modelo, nombre, x, y, w))
    if clasificador:
        yy = y + 25
        ca = compartimento("UMLAttributeCompartmentView", v, modelo, x, yy, w, 10 + 15 * len(atributos))
        for i, a in enumerate(atributos):
            ca["subViews"].append(_base_vista("UMLAttributeView", ca, a, left=x + 5, top=yy + 5 + 15 * i,
                                              width=w - 10, height=13, horizontalAlignment=0))
        yy += ca["height"]
        co = compartimento("UMLOperationCompartmentView", v, modelo, x, yy, w, 10 + 15 * len(operaciones))
        for i, o in enumerate(operaciones):
            co["subViews"].append(_base_vista("UMLOperationView", co, o, left=x + 5, top=yy + 5 + 15 * i,
                                              width=w - 10, height=13, horizontalAlignment=0))
        v["attributeCompartment"] = ref(ca)
        v["operationCompartment"] = ref(co)
        v["receptionCompartment"] = ref(compartimento("UMLReceptionCompartmentView", v, modelo, x, yy, w, 10, False))
        v["templateParameterCompartment"] = ref(
            compartimento("UMLTemplateParameterCompartmentView", v, modelo, x, y, w, 10, False))
        for nombre_campo, tipo_comp in extra_compartimentos:
            v[nombre_campo] = ref(compartimento(tipo_comp, v, modelo, x, yy, w, 10, False))
    return v


def _centro(v):
    return v["left"] + v["width"] / 2, v["top"] + v["height"] / 2


def etiqueta_arista(arista, modelo, posicion, distancia, alfa, texto="", visible=True):
    lab = _base_vista("EdgeLabelView", arista, modelo, text=texto, visible=visible, left=0, top=0,
                      width=0, height=13, alpha=alfa, distance=distancia, hostEdge=ref(arista),
                      edgePosition=posicion)
    arista["subViews"].append(lab)
    return lab


def vista_arista(tipo, diagrama, modelo, cola, cabeza, nombre="", puntos=None, estereotipo_visible=False):
    (x1, y1), (x2, y2) = _centro(cola), _centro(cabeza)
    puntos = puntos or [(x1, y1), (x2, y2)]
    a = _base_vista(tipo, diagrama, modelo, tail=ref(cola), head=ref(cabeza), lineStyle=1,
                    points=";".join(f"{px:.0f}:{py:.0f}" for px, py in puntos))
    diagrama["ownedViews"].append(a)
    a["nameLabel"] = ref(etiqueta_arista(a, modelo, 1, 15, 1.5708, nombre, bool(nombre)))
    a["stereotypeLabel"] = ref(etiqueta_arista(a, modelo, 1, 30, 1.5708, visible=estereotipo_visible))
    a["propertyLabel"] = ref(etiqueta_arista(a, modelo, 1, 15, -1.5708, visible=False))
    return a


def vista_asociacion(diagrama, asociacion, cola, cabeza, nombre=""):
    a = vista_arista("UMLAssociationView", diagrama, asociacion, cola, cabeza, nombre)
    e1, e2 = asociacion["end1"], asociacion["end2"]
    for prefijo, extremo, pos in (("tail", e1, 2), ("head", e2, 0)):
        a[f"{prefijo}RoleNameLabel"] = ref(etiqueta_arista(a, extremo, pos, 30, 0.5236, visible=False))
        a[f"{prefijo}PropertyLabel"] = ref(etiqueta_arista(a, extremo, pos, 40, 0.7854, visible=False))
        a[f"{prefijo}MultiplicityLabel"] = ref(
            etiqueta_arista(a, extremo, pos, 25, -0.5236, extremo.get("multiplicity", "")))
        q = _base_vista("UMLQualifierCompartmentView", a, extremo, left=0, top=0, width=10, height=10, visible=False)
        a["subViews"].append(q)
        a[f"{prefijo}QualifiersCompartment"] = ref(q)
    a["showVisibility"] = False
    return a


def diagrama(tipo, padre, nombre, por_defecto=False):
    return elemento(tipo, padre, name=nombre, visible=True, defaultDiagram=por_defecto, ownedViews=[])


def clase(padre, nombre, atributos=(), operaciones=(), estereotipo=None):
    c = elemento("UMLClass", padre, name=nombre)
    if estereotipo:
        c["stereotype"] = estereotipo
    attrs = []
    for texto in atributos:
        n, t = [s.strip() for s in texto.split(":")]
        attrs.append(elemento("UMLAttribute", c, "attributes", name=n, visibility="private", type=t))
    ops = []
    for texto in operaciones:
        firma, retorno = (texto, "") if texto.endswith(")") else texto.rsplit(":", 1)
        n, params = firma.split("(", 1)
        op = elemento("UMLOperation", c, "operations", name=n, visibility="public")
        for p in [p.strip() for p in params.rstrip(") ").split(",") if p.strip()]:
            elemento("UMLParameter", op, "parameters", name=p, direction="in")
        if retorno.strip():
            elemento("UMLParameter", op, "parameters", type=retorno.strip(), direction="return")
        ops.append(op)
    return c, attrs, ops


def asociacion(origen, destino, mult_origen, mult_destino, nombre="", composicion=False):
    a = elemento("UMLAssociation", origen, name=nombre)
    a["end1"] = {"_type": "UMLAssociationEnd", "_id": nuevo_id(), "_parent": ref(a), "reference": ref(origen),
                 "multiplicity": mult_origen, "aggregation": "composite" if composicion else "none",
                 "navigable": "unspecified"}
    a["end2"] = {"_type": "UMLAssociationEnd", "_id": nuevo_id(), "_parent": ref(a), "reference": ref(destino),
                 "multiplicity": mult_destino, "aggregation": "none", "navigable": "unspecified"}
    return a


def relacion(tipo, origen, destino, nombre="", estereotipo=None):
    r = elemento(tipo, origen, name=nombre, source=ref(origen), target=ref(destino))
    if estereotipo:
        r["stereotype"] = estereotipo
    return r


COMPARTIMENTOS_CU = (("extensionPointCompartment", "UMLExtensionPointCompartmentView"),)


def casos_de_uso(modelo):
    pkg = elemento("UMLModel", modelo, name="Casos de uso")
    d = diagrama("UMLUseCaseDiagram", pkg, "Casos de uso - Iteración 1", True)
    sujeto = elemento("UMLUseCaseSubject", pkg, name="Sistema Autos Colombia")
    vista_nodo("UMLUseCaseSubjectView", d, sujeto, 200, 20, 760, 760, "Sistema Autos Colombia", clasificador=False)

    operador = elemento("UMLActor", pkg, name="Operador")
    admin = elemento("UMLActor", pkg, name="Administrador")
    v_op = vista_nodo("UMLActorView", d, operador, 70, 230, 60, 90, "Operador", suppressAttributes=True, suppressOperations=True)
    v_ad = vista_nodo("UMLActorView", d, admin, 70, 570, 60, 90, "Administrador", suppressAttributes=True, suppressOperations=True)
    vista_arista("UMLGeneralizationView", d, relacion("UMLGeneralization", admin, operador), v_ad, v_op)

    vistas = {}
    casos = [
        ("login", "UC01 Iniciar sesión", 60), ("entrada", "UC02 Registrar entrada", 135),
        ("salida", "UC03 Registrar salida", 210), ("novedad", "UC04 Registrar novedad", 285),
        ("dentro", "UC05 Consultar vehículos dentro", 360), ("historial", "UC06 Consultar historial", 435),
        ("mapa", "UC07 Consultar mapa de celdas", 510),
        ("vehiculo", "UC08 Registrar vehículo de mensualidad", 610), ("celda", "UC09 Cambiar estado de celda", 690),
    ]
    modelos = {}
    for clave, nombre, y in casos:
        uc = elemento("UMLUseCase", pkg, name=nombre)
        modelos[clave] = uc
        vistas[clave] = vista_nodo("UMLUseCaseView", d, uc, 260, y, 250, 50, nombre, suppressAttributes=True,
                                   suppressOperations=True, extra_compartimentos=COMPARTIMENTOS_CU)
    for clave, nombre, y, base in [
        ("validar", "Validar placa y mensualidad", 80, "entrada"), ("asignar", "Asignar celda", 170, "entrada"),
        ("liberar", "Liberar celda", 270, "salida"), ("tiempo", "Calcular tiempo de permanencia", 360, "salida"),
    ]:
        uc = elemento("UMLUseCase", pkg, name=nombre)
        vistas[clave] = vista_nodo("UMLUseCaseView", d, uc, 650, y, 250, 50, nombre, suppressAttributes=True,
                                   suppressOperations=True, extra_compartimentos=COMPARTIMENTOS_CU)
        inc = relacion("UMLInclude", modelos[base], uc)
        vista_arista("UMLIncludeView", d, inc, vistas[base], vistas[clave], estereotipo_visible=True)

    for actor, v_actor, claves in ((operador, v_op, [c[0] for c in casos[:7]]), (admin, v_ad, ["vehiculo", "celda"])):
        for clave in claves:
            a = asociacion(actor, modelos[clave], "", "")
            vista_asociacion(d, a, v_actor, vistas[clave])


def clases(modelo):
    pkg = elemento("UMLModel", modelo, name="Diseño")
    d = diagrama("UMLClassDiagram", pkg, "Diagrama de clases")
    defs = {
        "Cliente": (["id: int", "documento: str", "nombres: str", "telefono: str", "email: str"], [], 30, 30, 200),
        "Vehiculo": (["id: int", "placa: str", "tipo: str", "marca: str", "color: str"], [], 330, 30, 200),
        "Mensualidad": (["id: int", "fecha_inicio: date", "fecha_fin: date", "valor: float"],
                        ["esta_vigente(hoy): bool"], 640, 30, 230),
        "Usuario": (["id: int", "nombre: str", "username: str", "password_hash: str", "rol: str", "activo: bool"],
                    ["es_admin(): bool"], 30, 300, 210),
        "RegistroParqueo": (["id: int", "fecha_entrada: datetime", "fecha_salida: datetime"],
                            ["esta_abierto(): bool", "tiempo_permanencia(): timedelta"], 330, 300, 250),
        "Celda": (["id: int", "codigo: str", "tipo_vehiculo: str", "estado: str"], ["esta_libre(): bool"], 680, 300, 200),
        "Novedad": (["id: int", "fecha: datetime", "tipo: str", "descripcion: str"], [], 330, 540, 250),
        "ParqueoService": (["vehiculos: VehiculoRepository", "celdas: CeldaRepository",
                            "registros: RegistroRepository", "novedades: NovedadRepository"],
                           ["registrar_entrada(placa, usuario_id, celda_id): RegistroParqueo",
                            "registrar_salida(placa, usuario_id): RegistroParqueo",
                            "registrar_novedad(placa, usuario_id, tipo, descripcion): int",
                            "alternar_mantenimiento(celda_id)", "tablero(): dict"], 650, 520, 420),
    }
    m, v = {}, {}
    for nombre, (attrs, ops, x, y, w) in defs.items():
        c, a, o = clase(pkg, nombre, attrs, ops, "service" if nombre.endswith("Service") else None)
        m[nombre] = c
        h = 25 + 10 + 15 * len(attrs) + 10 + 15 * len(ops)
        v[nombre] = vista_nodo("UMLClassView", d, c, x, y, w, h, nombre, a, o)
    for origen, destino, m1, m2, nombre, comp in [
        ("Cliente", "Vehiculo", "1", "1..*", "posee", False),
        ("Vehiculo", "Mensualidad", "1", "0..*", "tiene", False),
        ("Vehiculo", "RegistroParqueo", "1", "0..*", "ingresa", False),
        ("Celda", "RegistroParqueo", "1", "0..*", "asignada a", False),
        ("Usuario", "RegistroParqueo", "1", "0..*", "registra", False),
        ("RegistroParqueo", "Novedad", "1", "0..*", "contiene", True),
        ("Usuario", "Novedad", "1", "0..*", "reporta", False),
    ]:
        a = asociacion(m[origen], m[destino], m1, m2, nombre, comp)
        vista_asociacion(d, a, v[origen], v[destino], nombre)
    for destino in ("RegistroParqueo", "Celda", "Vehiculo"):
        dep = relacion("UMLDependency", m["ParqueoService"], m[destino], estereotipo="use")
        vista_arista("UMLDependencyView", d, dep, v["ParqueoService"], v[destino], estereotipo_visible=True)


def paquetes(modelo):
    raiz = elemento("UMLModel", modelo, name="Paquetes")
    d = diagrama("UMLPackageDiagram", raiz, "Diagrama de paquetes")
    app = elemento("UMLPackage", raiz, name="autoscolombia")
    vista_nodo("UMLPackageView", d, app, 20, 20, 720, 600, "autoscolombia", clasificador=False)
    p, v = {}, {}
    for nombre, x, y, padre, estereotipo in [
        ("controllers", 60, 90, app, "presentación"), ("templates", 300, 90, app, "vista"),
        ("static", 530, 90, app, None), ("services", 60, 280, app, "negocio"), ("db", 530, 280, app, None),
        ("repositories", 60, 470, app, "datos"), ("models", 300, 470, app, "dominio"),
        ("Flask", 820, 90, raiz, "framework"), ("sqlite3", 820, 280, raiz, "biblioteca"),
        ("tests", 820, 470, raiz, "pruebas"),
    ]:
        p[nombre] = elemento("UMLPackage", padre, name=nombre)
        if estereotipo:
            p[nombre]["stereotype"] = estereotipo
        v[nombre] = vista_nodo("UMLPackageView", d, p[nombre], x, y, 170, 90, nombre, clasificador=False)
    for origen, destino in [
        ("controllers", "templates"), ("templates", "static"), ("controllers", "services"),
        ("services", "repositories"), ("services", "models"), ("repositories", "models"),
        ("controllers", "db"), ("db", "Flask"), ("db", "sqlite3"),
    ]:
        dep = relacion("UMLDependency", p[origen], p[destino], estereotipo="import")
        vista_arista("UMLDependencyView", d, dep, v[origen], v[destino], estereotipo_visible=True)
    dep = relacion("UMLDependency", p["tests"], app, estereotipo="import")
    vista_arista("UMLDependencyView", d, dep, v["tests"], d["ownedViews"][0], estereotipo_visible=True)


def arquitectura(modelo):
    pkg = elemento("UMLModel", modelo, name="Arquitectura")
    d = diagrama("UMLDeploymentDiagram", pkg, "Arquitectura del sistema")
    nodos = {}
    for clave, nombre, x, y, w, h in [
        ("cliente", "Equipo portería", 10, 220, 250, 150),
        ("servidor", "Servidor de aplicación (Python 3 + Flask)", 290, 20, 560, 600),
        ("bd", "Servidor BD", 900, 380, 190, 160),
    ]:
        n = elemento("UMLNode", pkg, name=nombre)
        nodos[clave] = n
        vista_nodo("UMLNodeView", d, n, x, y, w, h, nombre, suppressAttributes=True, suppressOperations=True)
    m, v = {}, {}
    for clave, nombre, nodo, x, y, w in [
        ("navegador", "Navegador web", "cliente", 30, 280, 210),
        ("controladores", "Controladores (Blueprints)", "servidor", 320, 80, 230),
        ("vistas", "Vistas Jinja2 + CSS/JS", "servidor", 590, 80, 230),
        ("parqueo", "ParqueoService", "servidor", 320, 220, 160),
        ("vehiculo", "VehiculoService", "servidor", 490, 220, 160),
        ("auth", "AuthService", "servidor", 660, 220, 160),
        ("repos", "Repositorios (acceso a datos)", "servidor", 320, 360, 500),
        ("dominio", "Modelo de dominio (models.py)", "servidor", 320, 490, 500),
    ]:
        c = elemento("UMLComponent", nodos[nodo], name=nombre)
        m[clave] = c
        v[clave] = vista_nodo("UMLComponentView", d, c, x, y, w, 60, nombre, suppressAttributes=True, suppressOperations=True)
    artefacto = elemento("UMLArtifact", nodos["bd"], name="autos_colombia.sqlite")
    v["bd"] = vista_nodo("UMLArtifactView", d, artefacto, 915, 440, 160, 60, "autos_colombia.sqlite",
                         suppressAttributes=True, suppressOperations=True)
    m["bd"] = artefacto
    for origen, destino, nombre in [
        ("navegador", "controladores", "HTTP"), ("controladores", "vistas", ""),
        ("controladores", "parqueo", ""), ("controladores", "vehiculo", ""), ("controladores", "auth", ""),
        ("parqueo", "repos", ""), ("vehiculo", "repos", ""), ("auth", "repos", ""),
        ("repos", "dominio", ""), ("repos", "bd", "SQL"),
    ]:
        dep = relacion("UMLDependency", m[origen], m[destino], nombre)
        vista_arista("UMLDependencyView", d, dep, v[origen], v[destino], nombre)


def validar(proyecto):
    ids, refs, problemas = {}, [], []

    def recorrer(obj, padre_id):
        if isinstance(obj, dict):
            if "_id" in obj:
                if obj["_id"] in ids:
                    problemas.append(f"id duplicado {obj['_id']}")
                ids[obj["_id"]] = obj
                if padre_id and obj.get("_parent", {}).get("$ref") != padre_id:
                    problemas.append(f"_parent incorrecto en {obj['_type']} {obj.get('name', '')}")
                padre_id = obj["_id"]
            for k, val in obj.items():
                if k == "_parent":
                    continue
                if isinstance(val, dict) and set(val) == {"$ref"}:
                    refs.append((obj.get("_type"), k, val["$ref"]))
                else:
                    recorrer(val, padre_id)
        elif isinstance(obj, list):
            for x in obj:
                recorrer(x, padre_id)

    recorrer(proyecto, None)
    for tipo, campo, destino in refs:
        if destino not in ids:
            problemas.append(f"referencia rota {tipo}.{campo}")
    return len(ids), len(refs), problemas


def main():
    proyecto = {"_type": "Project", "_id": nuevo_id(), "name": "AutosColombia", "ownedElements": []}
    modelo = elemento("UMLModel", proyecto, name="Autos Colombia - Iteración 1")
    casos_de_uso(modelo)
    clases(modelo)
    paquetes(modelo)
    arquitectura(modelo)
    total, n_refs, problemas = validar(proyecto)
    SALIDA.write_text(json.dumps(proyecto, ensure_ascii=False, indent="\t"), encoding="utf-8")
    print(f"{SALIDA.name}: {total} objetos, {n_refs} referencias, problemas: {problemas or 'ninguno'}")


if __name__ == "__main__":
    main()
