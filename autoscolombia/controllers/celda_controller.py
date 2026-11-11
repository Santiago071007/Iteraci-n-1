from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..db import get_db
from ..services import CeldaService, ReglaNegocioError
from ..services.celda_service import TIPOS_CELDA
from .auth_controller import admin_requerido, login_requerido

bp = Blueprint("celdas", __name__, url_prefix="/celdas")


def _volver(celda_id: int) -> str:
    destino = request.form.get("volver") or ""
    if destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("celdas.detalle", celda_id=celda_id)


@bp.route("/")
@login_requerido
def listar():
    celdas = CeldaService(get_db()).celdas
    return render_template("celdas/lista.html", mapa=celdas.mapa(), resumen=celdas.resumen())


@bp.route("/nueva", methods=["GET", "POST"])
@admin_requerido
def nueva():
    datos = request.form.to_dict() if request.method == "POST" else {"modo": "una", "tipo": "CARRO"}
    if request.method == "POST":
        servicio = CeldaService(get_db())
        try:
            if datos.get("modo") == "lote":
                codigos = servicio.crear_lote(datos.get("prefijo"), datos.get("desde"), datos.get("hasta"), datos.get("tipo"))
                flash(f"Se crearon {len(codigos)} celdas: {codigos[0]} a {codigos[-1]}.", "ok")
            else:
                servicio.crear(datos.get("codigo"), datos.get("tipo"))
                flash("Celda creada y disponible.", "ok")
            return redirect(url_for("celdas.listar"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("celdas/nueva.html", d=datos, tipos=TIPOS_CELDA)


@bp.route("/<int:celda_id>")
@login_requerido
def detalle(celda_id):
    servicio = CeldaService(get_db())
    celda = servicio.celdas.obtener(celda_id) or abort(404)
    datos = {"codigo": celda.codigo, "tipo": celda.tipo_vehiculo}
    return render_template(
        "celdas/detalle.html",
        celda=celda,
        d=datos,
        tipos=TIPOS_CELDA,
        historial=servicio.celdas.historial(celda_id),
        usos=servicio.celdas.total_registros(celda_id),
    )


@bp.route("/<int:celda_id>/editar", methods=["POST"])
@admin_requerido
def editar(celda_id):
    try:
        CeldaService(get_db()).actualizar(celda_id, request.form.get("codigo"), request.form.get("tipo"))
        flash("Celda actualizada.", "ok")
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("celdas.detalle", celda_id=celda_id))


@bp.route("/<int:celda_id>/mantenimiento", methods=["POST"])
@admin_requerido
def mantenimiento(celda_id):
    try:
        CeldaService(get_db()).poner_en_mantenimiento(celda_id, request.form.get("observacion"))
        flash("Celda en mantenimiento; no se asignará a nuevos ingresos.", "ok")
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(_volver(celda_id))


@bp.route("/<int:celda_id>/habilitar", methods=["POST"])
@admin_requerido
def habilitar(celda_id):
    try:
        CeldaService(get_db()).habilitar(celda_id)
        flash("Celda habilitada y disponible.", "ok")
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(_volver(celda_id))


@bp.route("/<int:celda_id>/eliminar", methods=["POST"])
@admin_requerido
def eliminar(celda_id):
    try:
        codigo = CeldaService(get_db()).eliminar(celda_id)
        flash(f"Celda {codigo} eliminada.", "ok")
        return redirect(url_for("celdas.listar"))
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("celdas.detalle", celda_id=celda_id))
