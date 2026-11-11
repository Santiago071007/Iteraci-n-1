// Construye en StarUML los diagramas de la iteración 2 sobre el proyecto de la iteración 1.
// Se ejecuta con la consola de scripts de StarUML (script-console:run) desde staruml_exportar.py,
// que antepone la variable PARTE ("casos", "secuencia1", "secuencia2" o "componentes").
var F = app.factory;
var NUEVO = "#fff6d6";

function raiz() {
  var proyecto = app.project.getProject();
  for (var i = 0; i < proyecto.ownedElements.length; i++) {
    if (proyecto.ownedElements[i].name === "Autos Colombia - Iteración 2") return proyecto.ownedElements[i];
  }
  return F.createModel({ id: "UMLModel", parent: proyecto, modelInitializer: function (m) { m.name = "Autos Colombia - Iteración 2"; } });
}

function paquete(nombre) {
  var r = raiz();
  for (var i = 0; i < r.ownedElements.length; i++) if (r.ownedElements[i].name === nombre) return r.ownedElements[i];
  return F.createModel({ id: "UMLModel", parent: r, modelInitializer: function (m) { m.name = nombre; } });
}

function nombrar(nombre) { return function (m) { m.name = nombre; }; }

function nodo(tipo, padre, diagrama, nombre, x, y, w, h, extra) {
  var opciones = { id: tipo, parent: padre, diagram: diagrama, x1: x, y1: y, x2: x + w, y2: y + h, modelInitializer: nombrar(nombre) };
  if (extra) for (var k in extra) opciones[k] = extra[k];
  var v = F.createModelAndView(opciones);
  v.left = x; v.top = y; v.width = w; v.height = h;
  return v;
}

function arista(tipo, padre, diagrama, cola, cabeza, nombre) {
  var v = F.createModelAndView({
    id: tipo, parent: padre, diagram: diagrama, tailView: cola, headView: cabeza,
    tailModel: cola.model, headModel: cabeza.model,
    x1: cola.left + cola.width / 2, y1: cola.top + cola.height / 2,
    x2: cabeza.left + cabeza.width / 2, y2: cabeza.top + cabeza.height / 2,
    modelInitializer: nombrar(nombre || "")
  });
  v.showVisibility = false;
  return v;
}

function colorear(vista) {
  if (!vista) return;
  if (!vista.lineColor || String(vista.lineColor).charAt(0) === "$") vista.lineColor = "#000000";
  if (!vista.fillColor || String(vista.fillColor).charAt(0) === "$") vista.fillColor = "#ffffff";
  if (!vista.fontColor || String(vista.fontColor).charAt(0) === "$") vista.fontColor = "#000000";
  (vista.subViews || []).forEach(colorear);
}

function colorearTodo() {
  app.repository.select("@Diagram").forEach(function (d) { d.ownedViews.forEach(colorear); });
}

// ---------------------------------------------------------------- casos de uso
function casosDeUso(titulo, sujeto, actoresDef, casos, apoyos, relaciones) {
  var pkg = paquete("Casos de uso");
  var d = F.createDiagram({ id: "UMLUseCaseDiagram", parent: pkg, diagramInitializer: nombrar(titulo) });
  var alto = 0;
  casos.concat(apoyos).forEach(function (c) { alto = Math.max(alto, c[2] + 90); });
  nodo("UMLUseCaseSubject", pkg, d, sujeto, 190, 20, 860, alto);
  var v = {};
  actoresDef.forEach(function (a) { v[a[0]] = nodo("UMLActor", pkg, d, a[1], 60, a[2], 50, 85); });
  casos.forEach(function (c) { v[c[0]] = nodo("UMLUseCase", pkg, d, c[1], 230, c[2], 330, 52); });
  apoyos.forEach(function (c) { v[c[0]] = nodo("UMLUseCase", pkg, d, c[1], 680, c[2], 330, 52); });
  relaciones.forEach(function (r) {
    var tipo = { a: "UMLAssociation", i: "UMLInclude", e: "UMLExtend", g: "UMLGeneralization" }[r[0]];
    arista(tipo, pkg, d, v[r[1]], v[r[2]], r[0] === "e" ? "«extend»" : "");
  });
  return d;
}

function ajustarMensajes() {
  // StarUML a veces lleva los mensajes a sí mismo al final de la línea de vida: se devuelven a su
  // posición y se reordena la numeración de los mensajes según su posición vertical.
  var posicion = {};
  app.repository.select("@UMLSeqMessageView").forEach(function (v) {
    var doc = v.model.documentation || "";
    if (doc.indexOf("Y:") !== 0) return;
    var y = parseFloat(doc.slice(2));
    posicion[v.model._id] = y;
    if (v.tail === v.head) {
      var dy = y - v.points.points[0].y;
      v.points.points.forEach(function (p) { p.y += dy; });
    }
    v.model.documentation = "";
  });
  app.repository.select("@UMLInteraction").forEach(function (inter) {
    if (!inter.messages || !inter.messages.length || posicion[inter.messages[0]._id] === undefined) return;
    inter.messages.sort(function (a, b) { return posicion[a._id] - posicion[b._id]; });
  });
}

function ajustarFragmentos() {
  app.repository.select("@UMLCombinedFragmentView").forEach(function (cf) {
    var doc = cf.model.documentation || "";
    if (doc.indexOf("LIMITES:") !== 0) return;
    var limites = JSON.parse(doc.slice(8));
    var ops = cf.operandCompartment.subViews;
    ops.forEach(function (ov, i) {
      if (limites[i + 1] === undefined) return;
      ov.left = cf.left; ov.width = cf.width; ov.top = limites[i]; ov.height = limites[i + 1] - limites[i];
    });
    cf.operandCompartment.top = limites[0];
    cf.operandCompartment.height = limites[limites.length - 1] - limites[0];
    cf.model.documentation = "";
  });
}

function partesCasos() {
  casosDeUso("Casos de uso - Gestión de usuarios (Iteración 2)", "Sistema Autos Colombia: gestión de usuarios",
    [["op", "Operador", 120], ["ad", "Administrador", 470]],
    [["clave", "UC14 Cambiar mi contraseña", 60],
     ["consCli", "UC19 Consultar clientes y sus vehículos", 140],
     ["consUsu", "UC15 Consultar usuarios del sistema", 230],
     ["crearUsu", "UC10 Crear usuario del sistema", 305],
     ["editUsu", "UC11 Editar usuario y rol", 380],
     ["estUsu", "UC12 Activar o desactivar usuario", 455],
     ["resClave", "UC13 Restablecer contraseña", 530],
     ["regCli", "UC16 Registrar cliente", 615],
     ["editCli", "UC17 Editar datos del cliente", 690],
     ["estCli", "UC18 Activar o desactivar cliente", 765]],
    [["valUsu", "Validar datos del usuario", 300],
     ["cifrar", "Cifrar contraseña (hash)", 160],
     ["unAdmin", "Verificar que quede un administrador activo", 418],
     ["asociar", "UC20 Asociar vehículo al cliente", 540],
     ["valCli", "Validar datos del cliente", 652],
     ["dentro", "Verificar que no tenga vehículos dentro", 765]],
    [["g", "ad", "op"],
     ["a", "op", "clave"], ["a", "op", "consCli"],
     ["a", "ad", "consUsu"], ["a", "ad", "crearUsu"], ["a", "ad", "editUsu"], ["a", "ad", "estUsu"],
     ["a", "ad", "resClave"], ["a", "ad", "regCli"], ["a", "ad", "editCli"], ["a", "ad", "estCli"],
     ["i", "crearUsu", "valUsu"], ["i", "editUsu", "valUsu"],
     ["i", "crearUsu", "cifrar"], ["i", "resClave", "cifrar"], ["i", "clave", "cifrar"],
     ["i", "editUsu", "unAdmin"], ["i", "estUsu", "unAdmin"],
     ["e", "asociar", "regCli"],
     ["i", "regCli", "valCli"], ["i", "editCli", "valCli"],
     ["i", "estCli", "dentro"]]);

  casosDeUso("Casos de uso - Gestión de celdas (Iteración 2)", "Sistema Autos Colombia: gestión de celdas",
    [["op", "Operador", 110], ["ad", "Administrador", 430]],
    [["mapa", "UC21 Consultar mapa y listado de celdas", 60],
     ["detalle", "UC22 Consultar detalle e historial de una celda", 140],
     ["crear", "UC23 Crear celda", 240],
     ["editar", "UC25 Editar celda", 330],
     ["mant", "UC26 Poner celda en mantenimiento", 420],
     ["habil", "UC27 Habilitar celda", 510],
     ["elim", "UC28 Eliminar celda", 600]],
    [["lote", "UC24 Crear celdas por rango", 170],
     ["codigo", "Validar código único y formato", 285],
     ["ocupada", "Verificar que la celda no esté ocupada", 440],
     ["motivo", "Registrar motivo del mantenimiento", 525],
     ["historial", "Verificar que la celda no tenga historial", 615]],
    [["g", "ad", "op"],
     ["a", "op", "mapa"], ["a", "op", "detalle"],
     ["a", "ad", "crear"], ["a", "ad", "editar"], ["a", "ad", "mant"], ["a", "ad", "habil"], ["a", "ad", "elim"],
     ["e", "lote", "crear"],
     ["i", "crear", "codigo"], ["i", "editar", "codigo"],
     ["i", "editar", "ocupada"], ["i", "mant", "ocupada"], ["i", "elim", "ocupada"],
     ["i", "mant", "motivo"], ["i", "elim", "historial"]]);
}

// ---------------------------------------------------------------- secuencia
var PARTICIPANTES = {
  op: ["Operador", "actor"], ad: ["Administrador", "actor"],
  ac: [":AuthController"], pc: [":ParqueoController"], uc: [":UsuarioController"], cc: [":ClienteController"],
  vc: [":VehiculoController"], cec: [":CeldaController"],
  as: [":AuthService"], ps: [":ParqueoService"], us: [":UsuarioService"], cs: [":ClienteService"],
  vs: [":VehiculoService"], ces: [":CeldaService"],
  ur: [":UsuarioRepository"], vr: [":VehiculoRepository"], clr: [":ClienteRepository"],
  mr: [":MensualidadRepository"], rr: [":RegistroRepository"], cr: [":CeldaRepository"], nr: [":NovedadRepository"]
};

function secuencia(titulo, claves, pasos) {
  var pkg = paquete("Diagramas de secuencia");
  var col = F.createModel({ id: "UMLCollaboration", parent: pkg, modelInitializer: nombrar("Colaboración - " + titulo) });
  var inter = F.createModel({ id: "UMLInteraction", parent: col, modelInitializer: nombrar(titulo) });
  var d = F.createDiagram({ id: "UMLSequenceDiagram", parent: inter, diagramInitializer: nombrar(titulo) });
  var L = {}, centros = {}, anchos = {}, ANCHO_LETRA = 6.7;
  claves.forEach(function (k) { anchos[k] = 2 * Math.round(Math.max(110, PARTICIPANTES[k][0].length * 8 + 26) / 2); });
  // Separación mínima entre líneas de vida según el texto de los mensajes que las conectan.
  var mensajes = [];
  (function aplanar(lista) {
    lista.forEach(function (p) {
      if (p[0] === "m" || p[0] === "r") mensajes.push([claves.indexOf(p[1]), claves.indexOf(p[2]), p[3].length, false]);
      else if (p[0] === "s") mensajes.push([claves.indexOf(p[1]), claves.indexOf(p[1]), p[2].length, true]);
      else for (var i = 1; i < p.length; i++) aplanar(p[i].slice(1));
    });
  })(pasos);
  var c = [];
  claves.forEach(function (k, j) {
    if (j === 0) { c.push(Math.round(30 + anchos[k] / 2)); return; }
    var minimo = c[j - 1] + anchos[claves[j - 1]] / 2 + 40 + anchos[k] / 2;
    mensajes.forEach(function (m) {
      var i = Math.min(m[0], m[1]), f = Math.max(m[0], m[1]);
      if (m[3] && m[0] === j - 1) minimo = Math.max(minimo, c[j - 1] + m[2] * ANCHO_LETRA + 70);
      else if (!m[3] && f === j) minimo = Math.max(minimo, c[i] + m[2] * ANCHO_LETRA + 50);
    });
    c.push(Math.round(minimo));
  });
  var ultimo = claves[claves.length - 1];
  var maxX = Math.round(c[c.length - 1] + anchos[ultimo] / 2 + 30);
  mensajes.forEach(function (m) {
    if (m[3] && m[0] === claves.length - 1) maxX = Math.max(maxX, Math.round(c[m[0]] + m[2] * ANCHO_LETRA + 80));
  });
  claves.forEach(function (k, j) {
    var p = PARTICIPANTES[k], w = anchos[k], x = c[j] - w / 2;
    var v = F.createModelAndView({ id: "UMLLifeline", parent: inter, diagram: d, x1: x, y1: 40, x2: x + w, y2: 3000,
      modelInitializer: nombrar(p[1] === "actor" ? "" : p[0]) });
    if (p[1] === "actor") {
      var actor = F.createModel({ id: "UMLActor", parent: pkg, modelInitializer: nombrar(p[0]) });
      v.model.represent.type = actor;
      v.model.represent.name = "";
      v.stereotypeDisplay = "icon";
    }
    v.left = x; v.width = w;
    L[k] = v; centros[k] = c[j];
  });
  var y = 120, fragmentos = [];

  function mensaje(de, a, texto, tipo) {
    var mismo = de === a;
    F.createModelAndView({ id: "UMLMessage", parent: inter, diagram: d, tailView: L[de], headView: L[a],
      tailModel: L[de].model, headModel: L[a].model,
      x1: centros[de], y1: y, x2: mismo ? centros[a] + 40 : centros[a], y2: y,
      modelInitializer: function (m) { m.name = texto; m.messageSort = tipo; m.documentation = "Y:" + y; } });
  }

  function ejecutar(lista, nivel) {
    lista.forEach(function (p) {
      var t = p[0];
      if (t === "m") { mensaje(p[1], p[2], p[3], "synchCall"); y += 40; }
      else if (t === "r") { mensaje(p[1], p[2], p[3], "reply"); y += 36; }
      else if (t === "s") { mensaje(p[1], p[1], p[2], "synchCall"); y += 54; }
      else {
        var frag = { op: t, top: y - 8, nivel: nivel, cortes: [], guardas: [] };
        y += 52;
        for (var i = 1; i < p.length; i++) {
          if (i > 1) { frag.cortes.push(y - 6); y += 42; }
          frag.guardas.push(p[i][0]);
          ejecutar(p[i].slice(1), nivel + 1);
        }
        frag.bottom = y;
        y += 22;
        fragmentos.push(frag);
      }
    });
  }
  ejecutar(pasos, 0);

  fragmentos.forEach(function (f) {
    var margen = 12 + f.nivel * 12;
    var cf = F.createModelAndView({ id: "UMLCombinedFragment", parent: inter, diagram: d,
      x1: margen, y1: f.top, x2: maxX - 12 - f.nivel * 12, y2: f.bottom,
      modelInitializer: function (m) { m.interactionOperator = f.op; m.name = ""; } });
    for (var i = 1; i < f.guardas.length; i++) F.createModel({ id: "UMLInteractionOperand", parent: cf.model, field: "operands" });
    f.guardas.forEach(function (g, i) { cf.model.operands[i].guard = g; });
    // Las vistas de los operandos se crean al guardar; la parte "ajustar" usa estos límites.
    cf.model.documentation = "LIMITES:" + JSON.stringify([f.top + 24].concat(f.cortes).concat([f.bottom]));
  });

  claves.forEach(function (k) { L[k].height = y + 20 - 40; });
  d.ownedViews.forEach(function (v) {
    if (v.getClassName && v.getClassName() === "UMLFrameView") { v.left = 5; v.top = 5; v.width = maxX - 5; v.height = y + 30; }
  });
  return d;
}

function partesSecuencia1() {
  secuencia("SD01 Iniciar sesión (Iteración 1)", ["op", "ac", "as", "ur"], [
    ["m", "op", "ac", "POST /login(username, password)"],
    ["m", "ac", "as", "autenticar(username, password)"],
    ["m", "as", "ur", "buscar_por_username(username)"],
    ["r", "ur", "as", "usuario"],
    ["s", "as", "check_password_hash(hash, password)"],
    ["alt", ["usuario existe, está activo y la contraseña es correcta",
      ["r", "as", "ac", "usuario"],
      ["s", "ac", "session['usuario_id'] = usuario.id"],
      ["r", "ac", "op", "redirect al tablero"]],
     ["else",
      ["r", "as", "ac", "None"],
      ["r", "ac", "op", "'Usuario o contraseña incorrectos'"]]]
  ]);
  secuencia("SD02 Registrar entrada de vehículo (Iteración 1)", ["op", "pc", "ps", "vr", "clr", "mr", "rr", "cr"], [
    ["m", "op", "pc", "POST /entrada(placa, celda_id)"],
    ["m", "pc", "ps", "registrar_entrada(placa, usuario_id, celda_id)"],
    ["s", "ps", "normalizar_placa(), validar_placa()"],
    ["m", "ps", "vr", "buscar_por_placa(placa)"],
    ["r", "vr", "ps", "vehiculo"],
    ["m", "ps", "clr", "obtener(cliente_id)"],
    ["r", "clr", "ps", "cliente"],
    ["m", "ps", "mr", "vigente(vehiculo_id, hoy)"],
    ["r", "mr", "ps", "mensualidad"],
    ["m", "ps", "rr", "abierto_por_vehiculo(vehiculo_id)"],
    ["r", "rr", "ps", "None"],
    ["break", ["placa inválida, no registrado, cliente inactivo, sin mensualidad o ya dentro",
      ["r", "ps", "pc", "ReglaNegocioError(mensaje)"],
      ["r", "pc", "op", "mensaje de error"]]],
    ["alt", ["el operador eligió una celda",
      ["m", "ps", "cr", "obtener(celda_id)"],
      ["r", "cr", "ps", "celda libre y compatible"]],
     ["asignación automática",
      ["m", "ps", "cr", "libres(tipo)"],
      ["r", "cr", "ps", "primera celda libre"]]],
    ["m", "ps", "rr", "crear_entrada(vehiculo_id, celda_id, fecha, usuario_id)"],
    ["m", "ps", "cr", "cambiar_estado(celda_id, 'OCUPADA')"],
    ["r", "ps", "pc", "registro"],
    ["r", "pc", "op", "comprobante de entrada"]
  ]);
  secuencia("SD03 Registrar salida de vehículo (Iteración 1)", ["op", "pc", "ps", "vr", "rr", "cr"], [
    ["m", "op", "pc", "POST /salida(placa)"],
    ["m", "pc", "ps", "registrar_salida(placa, usuario_id)"],
    ["m", "ps", "vr", "buscar_por_placa(placa)"],
    ["r", "vr", "ps", "vehiculo"],
    ["m", "ps", "rr", "abierto_por_vehiculo(vehiculo_id)"],
    ["r", "rr", "ps", "registro"],
    ["break", ["el vehículo no está dentro",
      ["r", "ps", "pc", "ReglaNegocioError"],
      ["r", "pc", "op", "'no se encuentra dentro del parqueadero'"]]],
    ["m", "ps", "rr", "cerrar(registro_id, fecha_salida, usuario_id)"],
    ["m", "ps", "cr", "cambiar_estado(celda_id, 'LIBRE')"],
    ["r", "ps", "pc", "registro"],
    ["s", "pc", "tiempo_permanencia()"],
    ["r", "pc", "op", "comprobante de salida"]
  ]);
  secuencia("SD04 Registrar novedad (Iteración 1)", ["op", "pc", "ps", "vr", "rr", "nr"], [
    ["m", "op", "pc", "POST /novedades(placa, tipo, descripcion)"],
    ["m", "pc", "ps", "registrar_novedad(placa, usuario_id, tipo, descripcion)"],
    ["s", "ps", "validar tipo y descripción"],
    ["m", "ps", "vr", "buscar_por_placa(placa)"],
    ["r", "vr", "ps", "vehiculo"],
    ["m", "ps", "rr", "abierto_por_vehiculo(vehiculo_id)"],
    ["r", "rr", "ps", "registro | None"],
    ["alt", ["el vehículo está dentro",
      ["m", "ps", "nr", "crear(registro_id, usuario_id, fecha, tipo, descripcion)"],
      ["r", "nr", "ps", "novedad_id"],
      ["r", "ps", "pc", "novedad_id"],
      ["r", "pc", "op", "'Novedad registrada'"]],
     ["else",
      ["r", "ps", "pc", "ReglaNegocioError"],
      ["r", "pc", "op", "mensaje de error"]]]
  ]);
}

function partesSecuencia2() {
  secuencia("SD05 Crear usuario del sistema (Iteración 2)", ["ad", "uc", "us", "ur"], [
    ["m", "ad", "uc", "POST /usuarios/nuevo(nombre, username, rol, password, confirmacion)"],
    ["s", "uc", "admin_requerido()"],
    ["m", "uc", "us", "crear(datos)"],
    ["s", "us", "validar_nombre(), validar formato de username y rol"],
    ["m", "us", "ur", "buscar_por_username(username)"],
    ["r", "ur", "us", "None"],
    ["s", "us", "validar_clave(password, confirmacion)"],
    ["alt", ["datos válidos y username disponible",
      ["s", "us", "generate_password_hash(password)"],
      ["m", "us", "ur", "crear(nombre, username, hash, rol)"],
      ["r", "ur", "us", "usuario_id"],
      ["r", "us", "uc", "usuario_id"],
      ["r", "uc", "ad", "lista de usuarios + 'Usuario creado'"]],
     ["username en uso o datos inválidos",
      ["r", "us", "uc", "ReglaNegocioError(mensaje)"],
      ["r", "uc", "ad", "formulario con el mensaje de error"]]]
  ]);
  secuencia("SD06 Activar o desactivar usuario (Iteración 2)", ["ad", "uc", "us", "ur"], [
    ["m", "ad", "uc", "POST /usuarios/{id}/estado"],
    ["m", "uc", "us", "cambiar_estado(usuario_id, actor_id)"],
    ["m", "us", "ur", "obtener(usuario_id)"],
    ["r", "ur", "us", "usuario"],
    ["alt", ["usuario activo y es el mismo administrador",
      ["r", "us", "uc", "ReglaNegocioError('No puede desactivar su propio usuario')"]],
     ["es el último administrador activo",
      ["m", "us", "ur", "admins_activos()"],
      ["r", "ur", "us", "[usuario]"],
      ["r", "us", "uc", "ReglaNegocioError('Debe existir al menos un administrador activo')"]],
     ["en otro caso",
      ["m", "us", "ur", "cambiar_estado(usuario_id, not activo)"],
      ["r", "us", "uc", "nuevo estado"]]],
    ["r", "uc", "ad", "lista de usuarios + mensaje"]
  ]);
  secuencia("SD07 Registrar cliente y asociar vehículo (Iteración 2)", ["ad", "cc", "cs", "clr", "vc", "vs", "vr", "mr"], [
    ["m", "ad", "cc", "POST /clientes/nuevo(documento, nombres, telefono, email)"],
    ["m", "cc", "cs", "crear(datos)"],
    ["s", "cs", "limpiar_cliente(datos)"],
    ["m", "cs", "clr", "buscar_por_documento(documento)"],
    ["r", "clr", "cs", "None"],
    ["m", "cs", "clr", "crear(documento, nombres, telefono, email)"],
    ["r", "clr", "cs", "cliente_id"],
    ["r", "cs", "cc", "cliente_id"],
    ["r", "cc", "ad", "detalle del cliente"],
    ["opt", ["el administrador asocia un vehículo",
      ["m", "ad", "vc", "POST /vehiculos/nuevo?documento(placa, tipo, mensualidad)"],
      ["m", "vc", "vs", "registrar(datos)"],
      ["m", "vs", "vr", "buscar_por_placa(placa)"],
      ["r", "vr", "vs", "None"],
      ["m", "vs", "clr", "buscar_por_documento(documento)"],
      ["r", "clr", "vs", "cliente activo"],
      ["m", "vs", "vr", "crear(placa, tipo, marca, color, cliente_id)"],
      ["r", "vr", "vs", "vehiculo_id"],
      ["m", "vs", "mr", "crear(vehiculo_id, inicio, fin, valor)"],
      ["r", "vs", "vc", "vehiculo_id"],
      ["r", "vc", "ad", "detalle del cliente con el vehículo"]]]
  ]);
  secuencia("SD08 Crear celdas por rango (Iteración 2)", ["ad", "cec", "ces", "cr"], [
    ["m", "ad", "cec", "POST /celdas/nueva(modo='lote', prefijo, desde, hasta, tipo)"],
    ["m", "cec", "ces", "crear_lote(prefijo, desde, hasta, tipo)"],
    ["s", "ces", "validar rango (máx. 50) y formato de códigos"],
    ["loop", ["para cada código del rango",
      ["m", "ces", "cr", "buscar_por_codigo(codigo)"],
      ["r", "cr", "ces", "celda | None"]]],
    ["alt", ["ningún código existe",
      ["loop", ["para cada código del rango",
        ["m", "ces", "cr", "crear(codigo, tipo)"]]],
      ["r", "ces", "cec", "codigos"],
      ["r", "cec", "ad", "mapa de celdas + 'Se crearon N celdas'"]],
     ["algún código ya existe",
      ["r", "ces", "cec", "ReglaNegocioError(repetidas)"],
      ["r", "cec", "ad", "formulario con error, no se crea ninguna"]]]
  ]);
  secuencia("SD09 Mantenimiento y habilitación de celda (Iteración 2)", ["ad", "cec", "ces", "cr"], [
    ["m", "ad", "cec", "POST /celdas/{id}/mantenimiento(observacion)"],
    ["m", "cec", "ces", "poner_en_mantenimiento(celda_id, observacion)"],
    ["m", "ces", "cr", "obtener(celda_id)"],
    ["r", "cr", "ces", "celda"],
    ["alt", ["celda ocupada, ya en mantenimiento o motivo vacío",
      ["r", "ces", "cec", "ReglaNegocioError(mensaje)"]],
     ["celda libre",
      ["m", "ces", "cr", "cambiar_estado(celda_id, 'MANTENIMIENTO', observacion)"],
      ["r", "ces", "cec", "ok"]]],
    ["r", "cec", "ad", "detalle de la celda + mensaje"],
    ["opt", ["la celda fue reparada",
      ["m", "ad", "cec", "POST /celdas/{id}/habilitar"],
      ["m", "cec", "ces", "habilitar(celda_id)"],
      ["m", "ces", "cr", "cambiar_estado(celda_id, 'LIBRE')"],
      ["r", "cec", "ad", "'Celda habilitada y disponible'"]]]
  ]);
  secuencia("SD10 Eliminar celda (Iteración 2)", ["ad", "cec", "ces", "cr"], [
    ["m", "ad", "cec", "POST /celdas/{id}/eliminar"],
    ["m", "cec", "ces", "eliminar(celda_id)"],
    ["m", "ces", "cr", "obtener(celda_id)"],
    ["r", "cr", "ces", "celda"],
    ["m", "ces", "cr", "total_registros(celda_id)"],
    ["r", "cr", "ces", "n"],
    ["alt", ["celda ocupada",
      ["r", "ces", "cec", "ReglaNegocioError('está ocupada')"]],
     ["n > 0 (tiene historial)",
      ["r", "ces", "cec", "ReglaNegocioError('póngala en mantenimiento')"]],
     ["libre y sin historial",
      ["m", "ces", "cr", "eliminar(celda_id)"],
      ["r", "ces", "cec", "codigo"]]],
    ["r", "cec", "ad", "redirección + mensaje"]
  ]);
}

// ---------------------------------------------------------------- componentes
function partesComponentes() {
  var pkg = paquete("Componentes");
  var d = F.createDiagram({ id: "UMLComponentDiagram", parent: pkg, diagramInitializer: nombrar("Diagrama de componentes (Iteraciones 1 y 2)") });
  var V = {};

  function contenedor(clave, nombre, x, y, w, h) {
    V[clave] = nodo("UMLComponent", pkg, d, nombre, x, y, w, h);
    V[clave].fillColor = "#f4f7fb";
    return V[clave];
  }
  function componente(clave, nombre, padre, x, y, w, nuevo) {
    var extra = padre ? { containerView: V[padre] } : null;
    var v = nodo("UMLComponent", padre ? V[padre].model : pkg, d, nombre, x, y, w || 160, 56, extra);
    if (nuevo) v.fillColor = NUEVO;
    V[clave] = v;
    return v;
  }
  function interfaz(clave, nombre, x, y) {
    var v = nodo("UMLInterface", pkg, d, nombre, x, y, 28, 28);
    v.stereotypeDisplay = "icon";
    V[clave] = v;
    return v;
  }

  componente("nav", "Navegador web (equipo de portería)", null, 470, 20, 290);
  interfaz("http", "HTTP", 601, 112);

  contenedor("pres", "Presentación: controllers + templates (Flask Blueprints, Jinja2)", 20, 170, 1220, 150);
  var controladores = [
    ["ac", "AuthController", false], ["pc", "ParqueoController", false], ["vc", "VehiculoController", false],
    ["cc", "ClienteController", true], ["cec", "CeldaController", true], ["uc", "UsuarioController", true],
    ["vistas", "Vistas Jinja2 + CSS/JS", true]
  ];
  controladores.forEach(function (c, i) { componente(c[0], c[1], "pres", 40 + i * 172, 230, 160, c[2]); });

  var interfaces = [["iauth", "IAutenticacion"], ["iparq", "IParqueo"], ["iveh", "IVehiculos"],
    ["icli", "IClientes"], ["icel", "ICeldas"], ["iusu", "IUsuarios"]];
  interfaces.forEach(function (it, i) { interfaz(it[0], it[1], 106 + i * 172, 360); });

  contenedor("neg", "Lógica de negocio: services (reglas de negocio y transacciones)", 20, 430, 1220, 150);
  var servicios = [["as", "AuthService", false], ["ps", "ParqueoService", false], ["vs", "VehiculoService", false],
    ["cs", "ClienteService", true], ["ces", "CeldaService", true], ["us", "UsuarioService", true]];
  servicios.forEach(function (s, i) { componente(s[0], s[1], "neg", 40 + i * 172, 490, 160, s[2]); });

  interfaz("irepo", "IRepositorios", 616, 620);

  contenedor("datos", "Acceso a datos: repositories (un repositorio por tabla)", 20, 690, 1220, 150);
  var repos = [["rusu", "UsuarioRepository", false], ["rcli", "ClienteRepository", true], ["rveh", "VehiculoRepository", false],
    ["rmen", "MensualidadRepository", false], ["rreg", "RegistroRepository", false], ["rnov", "NovedadRepository", false],
    ["rcel", "CeldaRepository", true]];
  repos.forEach(function (r, i) { componente(r[0], r[1], "datos", 36 + i * 172, 750, 162, r[2]); });

  componente("models", "Modelo de dominio (models.py)", null, 170, 900, 260);
  componente("db", "Conexión y migración (db.py)", null, 500, 900, 260, true);
  componente("sqlite", "SQLite 3: autos_colombia.sqlite", null, 830, 900, 280);

  arista("UMLInterfaceRealization", pkg, d, V.pres, V.http);
  arista("UMLDependency", pkg, d, V.nav, V.http);
  var usa = { ac: "iauth", pc: "iparq", vc: "iveh", cc: "icli", cec: "icel", uc: "iusu" };
  var provee = { as: "iauth", ps: "iparq", vs: "iveh", cs: "icli", ces: "icel", us: "iusu" };
  for (var c in usa) arista("UMLDependency", pkg, d, V[c], V[usa[c]]);
  for (var s in provee) arista("UMLInterfaceRealization", pkg, d, V[s], V[provee[s]]);
  arista("UMLDependency", pkg, d, V.neg, V.irepo);
  arista("UMLInterfaceRealization", pkg, d, V.datos, V.irepo);
  arista("UMLDependency", pkg, d, V.datos, V.models, "");
  arista("UMLDependency", pkg, d, V.datos, V.db, "");
  arista("UMLDependency", pkg, d, V.db, V.sqlite, "");
}

try {
  if (PARTE === "casos") partesCasos();
  if (PARTE === "secuencia1") partesSecuencia1();
  if (PARTE === "secuencia2") partesSecuencia2();
  if (PARTE === "componentes") partesComponentes();
  if (PARTE === "ajustar") { ajustarFragmentos(); ajustarMensajes(); }
  colorearTodo();
  app.commands.execute("project:save");
  console.log("OK " + PARTE);
} catch (e) {
  console.log("ERROR " + PARTE + ": " + e + " " + (e && e.stack ? e.stack : ""));
}
