from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..db import get_db
from ..repositories import ClienteRepository, VehiculoRepository
from ..services import ReglaNegocioError, VehiculoService
from .auth_controller import admin_requerido, login_requerido

bp = Blueprint("vehiculos", __name__, url_prefix="/vehiculos")


@bp.route("/")
@login_requerido
def listar():
    return render_template(
        "vehiculos/lista.html",
        vehiculos=VehiculoRepository(get_db()).listar_con_cliente(),
        hoy=date.today().isoformat(),
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo():
    datos = request.form.to_dict() if request.method == "POST" else {
        "fecha_inicio": date.today().isoformat(),
        "fecha_fin": (date.today() + timedelta(days=30)).isoformat(),
        "valor": "180000",
        "documento": request.args.get("documento", ""),
    }
    if request.method == "POST":
        try:
            VehiculoService(get_db()).registrar(datos)
            flash("Vehículo registrado.", "ok")
            cliente = ClienteRepository(get_db()).buscar_por_documento(request.args.get("documento", ""))
            if cliente:
                return redirect(url_for("clientes.detalle", cliente_id=cliente.id))
            return redirect(url_for("vehiculos.listar"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    cliente = ClienteRepository(get_db()).buscar_por_documento(datos.get("documento") or "")
    return render_template("vehiculos/nuevo.html", d=datos, cliente=cliente)
