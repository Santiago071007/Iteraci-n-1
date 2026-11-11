from flask import Blueprint, flash, redirect, render_template, url_for

from ..db import get_db
from ..services import ParqueoService, ReglaNegocioError
from .auth_controller import admin_requerido, login_requerido

bp = Blueprint("celdas", __name__, url_prefix="/celdas")


@bp.route("/")
@login_requerido
def listar():
    servicio = ParqueoService(get_db())
    return render_template("celdas/lista.html", mapa=servicio.celdas.mapa(), resumen=servicio.celdas.resumen())


@bp.route("/<int:celda_id>/mantenimiento", methods=["POST"])
@admin_requerido
def mantenimiento(celda_id):
    try:
        ParqueoService(get_db()).alternar_mantenimiento(celda_id)
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("celdas.listar"))
