from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..db import get_db
from ..services import ClienteService, ReglaNegocioError
from .auth_controller import admin_requerido, login_requerido

bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@bp.route("/")
@login_requerido
def listar():
    return render_template("clientes/lista.html", clientes=ClienteService(get_db()).listar())


@bp.route("/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo():
    datos = request.form.to_dict() if request.method == "POST" else {}
    if request.method == "POST":
        try:
            cliente_id = ClienteService(get_db()).crear(datos)
            flash("Cliente registrado. Ahora puede asociarle vehículos.", "ok")
            return redirect(url_for("clientes.detalle", cliente_id=cliente_id))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("clientes/form.html", d=datos, cliente=None)


@bp.route("/<int:cliente_id>")
@login_requerido
def detalle(cliente_id):
    servicio = ClienteService(get_db())
    cliente = servicio.clientes.obtener(cliente_id) or abort(404)
    return render_template(
        "clientes/detalle.html",
        c=cliente,
        vehiculos=servicio.clientes.vehiculos(cliente_id),
        hoy=date.today().isoformat(),
    )


@bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@admin_requerido
def editar(cliente_id):
    servicio = ClienteService(get_db())
    cliente = servicio.clientes.obtener(cliente_id) or abort(404)
    datos = request.form.to_dict() if request.method == "POST" else {
        "documento": cliente.documento, "nombres": cliente.nombres,
        "telefono": cliente.telefono or "", "email": cliente.email or "",
    }
    if request.method == "POST":
        try:
            servicio.actualizar(cliente_id, datos)
            flash("Datos del cliente actualizados.", "ok")
            return redirect(url_for("clientes.detalle", cliente_id=cliente_id))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("clientes/form.html", d=datos, cliente=cliente)


@bp.route("/<int:cliente_id>/estado", methods=["POST"])
@admin_requerido
def estado(cliente_id):
    try:
        activo = ClienteService(get_db()).cambiar_estado(cliente_id)
        flash("Cliente activado." if activo else "Cliente desactivado; sus vehículos no podrán ingresar.", "ok")
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("clientes.detalle", cliente_id=cliente_id))
