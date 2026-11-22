// Diagramas de la iteración 3 (gestión de pagos). staruml_exportar.py lo ejecuta en la consola de
// scripts de StarUML a continuación de las funciones de staruml_iter2.js, con la variable PARTE
// ("casos3", "secuencia3" o "componentes3").
var ITER2 = "#fff6d6";
var ITER3 = "#dff3e4";

// Los elementos nuevos se crean en su propio modelo; esta definición reemplaza la de staruml_iter2.js.
function raiz() {
  var proyecto = app.project.getProject();
  for (var i = 0; i < proyecto.ownedElements.length; i++) {
    if (proyecto.ownedElements[i].name === "Autos Colombia - Iteración 3") return proyecto.ownedElements[i];
  }
  return F.createModel({ id: "UMLModel", parent: proyecto, modelInitializer: function (m) { m.name = "Autos Colombia - Iteración 3"; } });
}

PARTICIPANTES.pgc = [":PagoController"];
PARTICIPANTES.pgs = [":PagoService"];
PARTICIPANTES.pr = [":PagoRepository"];
PARTICIPANTES.tr = [":TarifaRepository"];

// ---------------------------------------------------------------- casos de uso
function partesCasos3() {
  casosDeUso("Casos de uso - Gestión de pagos (Iteración 3)", "Sistema Autos Colombia: gestión de pagos",
    [["op", "Operador", 190], ["ad", "Administrador", 590]],
    [["reg", "UC29 Registrar pago de mensualidad", 70],
     ["recibo", "UC30 Consultar e imprimir recibo de pago", 150],
     ["hist", "UC31 Consultar historial de pagos", 225],
     ["cartera", "UC32 Consultar mensualidades por cobrar", 300],
     ["cuenta", "UC33 Consultar estado de cuenta del cliente", 375],
     ["caja", "UC34 Realizar cierre de caja", 450],
     ["cajeros", "UC35 Consultar recaudo por cajero y fechas", 545],
     ["anular", "UC36 Anular pago", 630],
     ["tarifa", "UC37 Actualizar tarifas de mensualidad", 715]],
    [["cotizar", "Calcular período y valor a pagar", 40],
     ["medio", "Validar medio de pago y referencia", 108],
     ["vigencia", "Ampliar la vigencia de la mensualidad", 176],
     ["generar", "Generar recibo numerado", 244],
     ["ultimo", "Verificar último pago y vehículo fuera", 575],
     ["motivo", "Registrar motivo y retirar el período", 645],
     ["valtar", "Validar valor de la tarifa", 715]],
    [["g", "ad", "op"],
     ["a", "op", "reg"], ["a", "op", "recibo"], ["a", "op", "hist"], ["a", "op", "cartera"],
     ["a", "op", "cuenta"], ["a", "op", "caja"],
     ["a", "ad", "cajeros"], ["a", "ad", "anular"], ["a", "ad", "tarifa"],
     ["i", "reg", "cotizar"], ["i", "reg", "medio"], ["i", "reg", "vigencia"], ["i", "reg", "generar"],
     ["e", "cajeros", "caja"],
     ["i", "anular", "ultimo"], ["i", "anular", "motivo"],
     ["i", "tarifa", "valtar"]]);
}

// ---------------------------------------------------------------- secuencia
function partesSecuencia3() {
  secuencia("SD11 Registrar pago de mensualidad (Iteración 3)", ["op", "pgc", "pgs", "vr", "clr", "mr", "tr", "pr"], [
    ["m", "op", "pgc", "GET /pagos/nuevo?placa"],
    ["m", "pgc", "pgs", "cotizar(placa, meses)"],
    ["m", "pgs", "vr", "buscar_por_placa(placa)"],
    ["r", "vr", "pgs", "vehiculo"],
    ["m", "pgs", "clr", "obtener(cliente_id)"],
    ["r", "clr", "pgs", "cliente activo"],
    ["m", "pgs", "mr", "ultima(vehiculo_id)"],
    ["r", "mr", "pgs", "mensualidad"],
    ["m", "pgs", "tr", "obtener(tipo)"],
    ["r", "tr", "pgs", "tarifa"],
    ["s", "pgs", "calcular inicio, fin y valor"],
    ["r", "pgs", "pgc", "cotización"],
    ["r", "pgc", "op", "formulario con período y total"],
    ["m", "op", "pgc", "POST /pagos/nuevo(placa, meses, medio, referencia)"],
    ["m", "pgc", "pgs", "registrar_pago(placa, meses, medio, referencia, usuario_id)"],
    ["s", "pgs", "cotizar() y validar_medio()"],
    ["opt", ["el medio no es efectivo",
      ["m", "pgs", "pr", "referencia_en_uso(medio, referencia)"],
      ["r", "pr", "pgs", "pago | None"]]],
    ["alt", ["datos válidos y referencia sin usar",
      ["m", "pgs", "mr", "crear(vehiculo_id, inicio, fin, valor)"],
      ["r", "mr", "pgs", "mensualidad_id"],
      ["m", "pgs", "pr", "crear(mensualidad_id, vehiculo_id, fecha, meses, valor, medio, usuario_id)"],
      ["r", "pr", "pgs", "pago_id"],
      ["r", "pgs", "pgc", "pago"],
      ["r", "pgc", "op", "recibo numerado + 'Pago registrado'"]],
     ["placa, cliente, meses, medio o referencia no válidos",
      ["r", "pgs", "pgc", "ReglaNegocioError(mensaje)"],
      ["r", "pgc", "op", "formulario con el mensaje de error"]]]
  ]);
  secuencia("SD12 Anular pago (Iteración 3)", ["ad", "pgc", "pgs", "pr", "rr", "mr"], [
    ["m", "ad", "pgc", "POST /pagos/{id}/anular(motivo)"],
    ["s", "pgc", "admin_requerido()"],
    ["m", "pgc", "pgs", "anular_pago(pago_id, motivo, usuario_id)"],
    ["m", "pgs", "pr", "obtener(pago_id)"],
    ["r", "pr", "pgs", "pago"],
    ["m", "pgs", "pr", "posterior_vigente(vehiculo_id, periodo_fin)"],
    ["r", "pr", "pgs", "pago posterior | None"],
    ["m", "pgs", "rr", "abierto_por_vehiculo(vehiculo_id)"],
    ["r", "rr", "pgs", "registro | None"],
    ["alt", ["ya anulado, motivo corto, hay un pago posterior o el vehículo está dentro con ese período",
      ["r", "pgs", "pgc", "ReglaNegocioError(mensaje)"]],
     ["pago vigente y anulable",
      ["m", "pgs", "mr", "eliminar(mensualidad_id)"],
      ["m", "pgs", "pr", "anular(pago_id, fecha, usuario_id, motivo)"],
      ["r", "pgs", "pgc", "pago ANULADO"]]],
    ["r", "pgc", "ad", "recibo + mensaje"]
  ]);
  secuencia("SD13 Consultar mensualidades por cobrar (Iteración 3)", ["op", "pgc", "pgs", "pr"], [
    ["m", "op", "pgc", "GET /pagos/cartera"],
    ["m", "pgc", "pgs", "cartera(hoy)"],
    ["m", "pgs", "pr", "estado_de_vehiculos()"],
    ["r", "pr", "pgs", "vehículos con vencimiento y tarifa"],
    ["loop", ["para cada vehículo de cliente activo",
      ["s", "pgs", "clasificar: vencida, por vencer (5 días o menos) o al día"]]],
    ["s", "pgs", "sumar el valor por cobrar"],
    ["r", "pgs", "pgc", "vencidas, por_vencer, al_dia, por_cobrar"],
    ["r", "pgc", "op", "listado con indicadores y botón Cobrar"]
  ]);
  secuencia("SD14 Realizar cierre de caja (Iteración 3)", ["op", "pgc", "pgs", "pr"], [
    ["m", "op", "pgc", "GET /pagos/caja?desde&hasta"],
    ["alt", ["el usuario es operador",
      ["s", "pgc", "usuario_id = su propio id; un solo día"]],
     ["el usuario es administrador",
      ["s", "pgc", "usuario_id = None (todos los cajeros)"]]],
    ["m", "pgc", "pgs", "recaudo(desde, hasta, usuario_id)"],
    ["m", "pgs", "pr", "totales_por_medio(desde, hasta, usuario_id)"],
    ["r", "pr", "pgs", "total y cantidad por medio"],
    ["m", "pgs", "pr", "listar(desde, hasta, usuario_id)"],
    ["r", "pr", "pgs", "recibos del período"],
    ["opt", ["consulta del administrador",
      ["m", "pgs", "pr", "totales_por_usuario(desde, hasta)"],
      ["r", "pr", "pgs", "recaudo por cajero"]]],
    ["r", "pgs", "pgc", "total, efectivo, anulados, detalle"],
    ["r", "pgc", "op", "cierre de caja imprimible"]
  ]);
  secuencia("SD15 Actualizar tarifa (Iteración 3)", ["ad", "pgc", "pgs", "tr"], [
    ["m", "ad", "pgc", "POST /pagos/tarifas(tipo, valor)"],
    ["s", "pgc", "admin_requerido()"],
    ["m", "pgc", "pgs", "actualizar_tarifa(tipo, valor, usuario_id)"],
    ["s", "pgs", "validar tipo de vehículo y rango del valor"],
    ["alt", ["tipo y valor válidos",
      ["m", "pgs", "tr", "actualizar(tipo, valor, fecha, usuario_id)"],
      ["r", "pgs", "pgc", "valor"],
      ["r", "pgc", "ad", "tarifas + 'Tarifa actualizada'"]],
     ["valor fuera de rango o tipo no válido",
      ["r", "pgs", "pgc", "ReglaNegocioError(mensaje)"],
      ["r", "pgc", "ad", "formulario con el mensaje de error"]]]
  ]);
}

// ---------------------------------------------------------------- componentes
function partesComponentes3() {
  var pkg = paquete("Componentes");
  var d = F.createDiagram({ id: "UMLComponentDiagram", parent: pkg,
    diagramInitializer: nombrar("Diagrama de componentes actualizado (Iteraciones 1, 2 y 3)") });
  var V = {};

  function contenedor(clave, nombre, x, y, w, h) {
    V[clave] = nodo("UMLComponent", pkg, d, nombre, x, y, w, h);
    V[clave].fillColor = "#f4f7fb";
    return V[clave];
  }
  function componente(clave, nombre, padre, x, y, w, color) {
    var extra = padre ? { containerView: V[padre] } : null;
    var v = nodo("UMLComponent", padre ? V[padre].model : pkg, d, nombre, x, y, w || 160, 56, extra);
    if (color) v.fillColor = color;
    V[clave] = v;
    return v;
  }
  function interfaz(clave, nombre, x, y) {
    var v = nodo("UMLInterface", pkg, d, nombre, x, y, 28, 28);
    v.stereotypeDisplay = "icon";
    V[clave] = v;
    return v;
  }

  var ANCHO = 1590, PASO = 193;
  componente("nav", "Navegador web (equipo de portería)", null, 665, 20, 290);
  interfaz("http", "HTTP", 796, 112);

  contenedor("pres", "Presentación: controllers + templates (Flask Blueprints, Jinja2)", 20, 170, ANCHO, 150);
  var controladores = [
    ["ac", "AuthController", null], ["pc", "ParqueoController", null], ["vc", "VehiculoController", null],
    ["cc", "ClienteController", ITER2], ["cec", "CeldaController", ITER2], ["uc", "UsuarioController", ITER2],
    ["pgc", "PagoController", ITER3], ["vistas", "Vistas Jinja2 + CSS/JS", ITER3]
  ];
  controladores.forEach(function (c, i) { componente(c[0], c[1], "pres", 40 + i * PASO, 230, 180, c[2]); });

  var interfaces = [["iauth", "IAutenticacion"], ["iparq", "IParqueo"], ["iveh", "IVehiculos"],
    ["icli", "IClientes"], ["icel", "ICeldas"], ["iusu", "IUsuarios"], ["ipag", "IPagos"]];
  interfaces.forEach(function (it, i) { interfaz(it[0], it[1], 116 + i * PASO, 360); });

  contenedor("neg", "Lógica de negocio: services (reglas de negocio y transacciones)", 20, 430, ANCHO, 150);
  var servicios = [["as", "AuthService", null], ["ps", "ParqueoService", null], ["vs", "VehiculoService", ITER3],
    ["cs", "ClienteService", ITER2], ["ces", "CeldaService", ITER2], ["us", "UsuarioService", ITER2],
    ["pgs", "PagoService", ITER3]];
  servicios.forEach(function (s, i) { componente(s[0], s[1], "neg", 40 + i * PASO, 490, 180, s[2]); });

  interfaz("irepo", "IRepositorios", 801, 620);

  contenedor("datos", "Acceso a datos: repositories (un repositorio por tabla)", 20, 690, ANCHO, 150);
  var repos = [["rusu", "UsuarioRepository", null], ["rcli", "ClienteRepository", ITER2], ["rveh", "VehiculoRepository", null],
    ["rmen", "MensualidadRepository", ITER3], ["rreg", "RegistroRepository", null], ["rnov", "NovedadRepository", null],
    ["rcel", "CeldaRepository", ITER2], ["rpag", "PagoRepository", ITER3], ["rtar", "TarifaRepository", ITER3]];
  repos.forEach(function (r, i) { componente(r[0], r[1], "datos", 34 + i * 173, 750, 164, r[2]); });

  componente("models", "Modelo de dominio (models.py)", null, 330, 900, 260, ITER3);
  componente("db", "Conexión y migración (db.py)", null, 685, 900, 260, ITER3);
  componente("sqlite", "SQLite 3: autos_colombia.sqlite", null, 1040, 900, 280);

  arista("UMLInterfaceRealization", pkg, d, V.pres, V.http);
  arista("UMLDependency", pkg, d, V.nav, V.http);
  var usa = { ac: "iauth", pc: "iparq", vc: "iveh", cc: "icli", cec: "icel", uc: "iusu", pgc: "ipag" };
  var provee = { as: "iauth", ps: "iparq", vs: "iveh", cs: "icli", ces: "icel", us: "iusu", pgs: "ipag" };
  for (var c in usa) arista("UMLDependency", pkg, d, V[c], V[usa[c]]);
  for (var s in provee) arista("UMLInterfaceRealization", pkg, d, V[s], V[provee[s]]);
  arista("UMLDependency", pkg, d, V.neg, V.irepo);
  arista("UMLInterfaceRealization", pkg, d, V.datos, V.irepo);
  arista("UMLDependency", pkg, d, V.datos, V.models, "");
  arista("UMLDependency", pkg, d, V.datos, V.db, "");
  arista("UMLDependency", pkg, d, V.db, V.sqlite, "");
}

try {
  if (PARTE === "casos3") partesCasos3();
  if (PARTE === "secuencia3") partesSecuencia3();
  if (PARTE === "componentes3") partesComponentes3();
  colorearTodo();
  app.commands.execute("project:save");
  console.log("OK " + PARTE);
} catch (e) {
  console.log("ERROR " + PARTE + ": " + e + " " + (e && e.stack ? e.stack : ""));
}
