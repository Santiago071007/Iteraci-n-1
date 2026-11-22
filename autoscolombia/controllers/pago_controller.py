from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..services import PagoService, ReglaNegocioError
from ..services.pago_service import MAX_MESES, MEDIOS_PAGO, TIPOS_VEHICULO
from .auth_controller import admin_requerido, login_requerido

bp = Blueprint("pagos", __name__, url_prefix="/pagos")


@bp.app_template_filter("pesos")
def filtro_pesos(valor) -> str:
    return "$ " + f"{float(valor or 0):,.0f}".replace(",", ".")


@bp.route("/")
@login_requerido
def listar():
    filtros = {clave: request.args.get(clave, "").strip() for clave in ("desde", "hasta", "medio", "estado", "texto")}
    pagos = PagoService(get_db()).pagos.listar(**filtros)
    vigentes = [p for p in pagos if p["estado"] == "VIGENTE"]
    return render_template(
        "pagos/lista.html", pagos=pagos, f=filtros, medios=MEDIOS_PAGO,
        total=sum(p["valor"] for p in vigentes), vigentes=len(vigentes),
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo():
    servicio = PagoService(get_db())
    placa = request.values.get("placa", "")
    meses = request.values.get("meses", "1")
    cotizacion = None
    if request.method == "POST":
        try:
            pago = servicio.registrar_pago(
                placa, meses, request.form.get("medio"), request.form.get("referencia"), g.usuario.id
            )
            flash(f"Pago registrado. Recibo N.º {pago.id:05d}.", "ok")
            return redirect(url_for("pagos.recibo", pago_id=pago.id))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    if placa:
        # Se muestra el vehículo con lo que se digitó; si eso no es válido, con un mes.
        for intento in (meses, 1):
            try:
                cotizacion = servicio.cotizar(placa, intento)
                break
            except ReglaNegocioError as error:
                if request.method == "GET" and intento == meses:
                    flash(str(error), "error")
    return render_template(
        "pagos/nuevo.html", c=cotizacion, placa=placa, medios=MEDIOS_PAGO, max_meses=MAX_MESES,
        d=request.values, pendientes=servicio.cartera(),
    )


@bp.route("/<int:pago_id>")
@login_requerido
def recibo(pago_id):
    pago = PagoService(get_db()).pagos.detalle(pago_id) or abort(404)
    return render_template("pagos/recibo.html", p=pago, medios=MEDIOS_PAGO)


@bp.route("/<int:pago_id>/anular", methods=["POST"])
@admin_requerido
def anular(pago_id):
    try:
        PagoService(get_db()).anular_pago(pago_id, request.form.get("motivo"), g.usuario.id)
        flash(f"Recibo N.º {pago_id} anulado; el período pagado se retiró de la mensualidad.", "ok")
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("pagos.recibo", pago_id=pago_id))


@bp.route("/cartera")
@login_requerido
def cartera():
    return render_template("pagos/cartera.html", hoy=date.today().isoformat(), **PagoService(get_db()).cartera())


@bp.route("/caja")
@login_requerido
def caja():
    """Cierre de caja. El operador ve solo lo que él recibió; el administrador ve a todos los cajeros."""
    hoy = date.today().isoformat()
    desde = request.args.get("desde") or hoy
    hasta = request.args.get("hasta") or desde
    if not g.usuario.es_admin():
        desde = hasta = request.args.get("desde") or hoy
    try:
        reporte = PagoService(get_db()).recaudo(desde, hasta, None if g.usuario.es_admin() else g.usuario.id)
    except ReglaNegocioError as error:
        flash(str(error), "error")
        desde = hasta = hoy
        reporte = PagoService(get_db()).recaudo(hoy, hoy, None if g.usuario.es_admin() else g.usuario.id)
    return render_template("pagos/caja.html", desde=desde, hasta=hasta, hoy=hoy, medios=MEDIOS_PAGO, **reporte)


@bp.route("/tarifas", methods=["GET", "POST"])
@admin_requerido
def tarifas():
    servicio = PagoService(get_db())
    if request.method == "POST":
        try:
            tipo = request.form.get("tipo")
            valor = servicio.actualizar_tarifa(tipo, request.form.get("valor"), g.usuario.id)
            flash(f"Tarifa de {TIPOS_VEHICULO[tipo].lower()} actualizada a {filtro_pesos(valor)}. "
                  "Aplica para los pagos que se registren desde ahora.", "ok")
            return redirect(url_for("pagos.tarifas"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("pagos/tarifas.html", tarifas=servicio.tarifas.listar(), tipos=TIPOS_VEHICULO, d=request.form)
