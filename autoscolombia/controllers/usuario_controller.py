from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..services import ReglaNegocioError, UsuarioService
from ..services.usuario_service import ROLES
from .auth_controller import admin_requerido, login_requerido

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.route("/")
@admin_requerido
def listar():
    return render_template("usuarios/lista.html", usuarios=UsuarioService(get_db()).usuarios.listar(), roles=ROLES)


@bp.route("/nuevo", methods=["GET", "POST"])
@admin_requerido
def nuevo():
    datos = request.form.to_dict() if request.method == "POST" else {"rol": "OPERADOR"}
    if request.method == "POST":
        try:
            UsuarioService(get_db()).crear(datos)
            flash(f"Usuario {datos['username'].strip().lower()} creado.", "ok")
            return redirect(url_for("usuarios.listar"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("usuarios/form.html", d=datos, usuario=None, roles=ROLES)


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@admin_requerido
def editar(usuario_id):
    servicio = UsuarioService(get_db())
    usuario = servicio.usuarios.obtener(usuario_id) or abort(404)
    datos = request.form.to_dict() if request.method == "POST" else {"nombre": usuario.nombre, "rol": usuario.rol}
    if request.method == "POST":
        try:
            servicio.actualizar(usuario_id, datos, g.usuario.id)
            flash("Datos del usuario actualizados.", "ok")
            return redirect(url_for("usuarios.listar"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("usuarios/form.html", d=datos, usuario=usuario, roles=ROLES)


@bp.route("/<int:usuario_id>/estado", methods=["POST"])
@admin_requerido
def estado(usuario_id):
    try:
        activo = UsuarioService(get_db()).cambiar_estado(usuario_id, g.usuario.id)
        flash("Usuario activado." if activo else "Usuario desactivado; ya no podrá iniciar sesión.", "ok")
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("usuarios.listar"))


@bp.route("/<int:usuario_id>/clave", methods=["POST"])
@admin_requerido
def restablecer_clave(usuario_id):
    try:
        UsuarioService(get_db()).restablecer_clave(
            usuario_id, request.form.get("password"), request.form.get("confirmacion")
        )
        flash("Contraseña restablecida.", "ok")
        return redirect(url_for("usuarios.listar"))
    except ReglaNegocioError as error:
        flash(str(error), "error")
    return redirect(url_for("usuarios.editar", usuario_id=usuario_id))


@bp.route("/mi-clave", methods=["GET", "POST"])
@login_requerido
def mi_clave():
    if request.method == "POST":
        try:
            UsuarioService(get_db()).cambiar_mi_clave(
                g.usuario.id, request.form.get("actual"), request.form.get("password"), request.form.get("confirmacion")
            )
            flash("Su contraseña fue cambiada.", "ok")
            return redirect(url_for("parqueo.tablero"))
        except ReglaNegocioError as error:
            flash(str(error), "error")
    return render_template("usuarios/mi_clave.html")
