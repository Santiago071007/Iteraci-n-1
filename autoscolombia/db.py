import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

CARPETA_BD = Path(__file__).resolve().parent.parent / "database"


def conectar(ruta: str) -> sqlite3.Connection:
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def close_db(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def inicializar(conexion: sqlite3.Connection, con_datos: bool = True):
    conexion.executescript((CARPETA_BD / "schema.sql").read_text(encoding="utf-8"))
    if con_datos:
        conexion.executescript((CARPETA_BD / "seed.sql").read_text(encoding="utf-8"))
        conexion.executemany(
            "INSERT INTO usuario (nombre, username, password_hash, rol) VALUES (?, ?, ?, ?)",
            [
                ("Administrador", "admin", generate_password_hash("admin123"), "ADMIN"),
                ("Pedro Operador", "operador", generate_password_hash("operador123"), "OPERADOR"),
            ],
        )
    conexion.commit()


@click.command("init-db")
@click.option("--sin-datos", is_flag=True, help="Crea las tablas sin datos de ejemplo.")
def init_db_command(sin_datos):
    inicializar(get_db(), con_datos=not sin_datos)
    click.echo("Base de datos inicializada.")


def registrar(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    if not Path(app.config["DATABASE"]).exists():
        Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
        conexion = conectar(app.config["DATABASE"])
        inicializar(conexion)
        conexion.close()
