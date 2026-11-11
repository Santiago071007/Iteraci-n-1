from datetime import datetime

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..services import ParqueoService, ReglaNegocioError
from ..services.parqueo_service import TIPOS_NOVEDAD, formatear_duracion
from .auth_controller import login_requerido

bp = Blueprint("parqueo", __name__)


@bp.app_template_filter("duracion")
def filtro_duracion(fecha_entrada, fecha_salida=None):
    fin = datetime.fromisoformat(fecha_salida) if fecha_salida else datetime.now()
    return formatear_duracion((fin - datetime.fromisoformat(fecha_entrada)).total_seconds())


@bp.route("/")
@login_requerido
def tablero():
    return render_template("parqueo/tablero.html", **ParqueoService(get_db()).tablero())


@bp.route("/entrada", methods=["GET", "POST"])
@login_requerido
def entrada():
    servicio = ParqueoService(get_db())
    if request.method == "POST":
        try:
            registro = servicio.registrar_entrada(
                request.form.get("placa"), g.usuario.id, request.form.get("celda_id", type=int)
            )
            flash("Entrada registrada correctamente.", "ok")
            return redirect(url_for("parqueo.comprobante", registro_id=registro.id))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("parqueo/entrada.html", celdas=servicio.celdas.libres())


@bp.route("/salida", methods=["GET", "POST"])
@login_requerido
def salida():
    servicio = ParqueoService(get_db())
    if request.method == "POST":
        try:
            registro = servicio.registrar_salida(request.form.get("placa"), g.usuario.id)
            flash("Salida registrada correctamente.", "ok")
            return redirect(url_for("parqueo.comprobante", registro_id=registro.id))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("parqueo/salida.html", activos=servicio.registros.activos())


@bp.route("/registros/<int:registro_id>")
@login_requerido
def comprobante(registro_id):
    servicio = ParqueoService(get_db())
    registro = servicio.registros.detalle(registro_id)
    if registro is None:
        abort(404)
    return render_template(
        "parqueo/comprobante.html",
        r=registro,
        novedades=servicio.novedades.por_registro(registro_id),
        tipos=TIPOS_NOVEDAD,
    )


@bp.route("/activos")
@login_requerido
def activos():
    return render_template("parqueo/activos.html", activos=ParqueoService(get_db()).registros.activos())


@bp.route("/historial")
@login_requerido
def historial():
    placa = request.args.get("placa", "").strip().upper()
    fecha = request.args.get("fecha", "")
    registros = ParqueoService(get_db()).registros.historial(placa, fecha)
    return render_template("parqueo/historial.html", registros=registros, placa=placa, fecha=fecha)


@bp.route("/novedades", methods=["GET", "POST"])
@login_requerido
def novedades():
    servicio = ParqueoService(get_db())
    if request.method == "POST":
        try:
            servicio.registrar_novedad(
                request.form.get("placa"), g.usuario.id, request.form.get("tipo"), request.form.get("descripcion")
            )
            flash("Novedad registrada.", "ok")
            return redirect(url_for("parqueo.novedades"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template(
        "parqueo/novedades.html",
        activos=servicio.registros.activos(),
        novedades=servicio.novedades.recientes(),
        tipos=TIPOS_NOVEDAD,
        placa=request.values.get("placa", ""),
    )
