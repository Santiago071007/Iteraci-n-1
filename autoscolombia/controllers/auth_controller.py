from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from ..db import get_db
from ..repositories import UsuarioRepository
from ..services import AuthService

bp = Blueprint("auth", __name__)


@bp.before_app_request
def cargar_usuario():
    usuario_id = session.get("usuario_id")
    g.usuario = UsuarioRepository(get_db()).obtener(usuario_id) if usuario_id else None


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.login", next=request.path))
        return vista(*args, **kwargs)
    return envoltura


def admin_requerido(vista):
    @wraps(vista)
    @login_requerido
    def envoltura(*args, **kwargs):
        if not g.usuario.es_admin():
            flash("Esta opción solo está disponible para el administrador.", "error")
            return redirect(url_for("parqueo.tablero"))
        return vista(*args, **kwargs)
    return envoltura


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = AuthService(get_db()).autenticar(request.form.get("username"), request.form.get("password"))
        if usuario:
            session.clear()
            session["usuario_id"] = usuario.id
            destino = request.args.get("next") or ""
            return redirect(destino if destino.startswith("/") and not destino.startswith("//") else url_for("parqueo.tablero"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
