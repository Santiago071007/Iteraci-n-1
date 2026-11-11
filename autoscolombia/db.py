import sqlite3
from functools import lru_cache
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


@lru_cache(maxsize=None)
def _hash_semilla(clave: str) -> str:
    return generate_password_hash(clave)


def inicializar(conexion: sqlite3.Connection, con_datos: bool = True):
    conexion.executescript((CARPETA_BD / "schema.sql").read_text(encoding="utf-8"))
    if con_datos:
        conexion.executescript((CARPETA_BD / "seed.sql").read_text(encoding="utf-8"))
        conexion.executemany(
            "INSERT INTO usuario (nombre, username, password_hash, rol, activo) VALUES (?, ?, ?, ?, ?)",
            [
                ("Administrador", "admin", _hash_semilla("admin123"), "ADMIN", 1),
                ("Pedro Operador", "operador", _hash_semilla("operador123"), "OPERADOR", 1),
                ("Lucía Torres Vega", "ltorres", _hash_semilla("Turno2026"), "OPERADOR", 1),
                ("Mario Díaz Salcedo", "mdiaz", _hash_semilla("Turno2026"), "OPERADOR", 0),
            ],
        )
    conexion.commit()


# Columnas agregadas en la iteración 2: (tabla, columna, definición).
COLUMNAS_ITERACION_2 = [
    ("usuario", "creado_en", "DATETIME"),
    ("cliente", "activo", "INTEGER NOT NULL DEFAULT 1"),
    ("celda", "observacion", "VARCHAR(200)"),
]


def migrar(conexion: sqlite3.Connection):
    """Actualiza una base de datos creada en la iteración 1 sin perder sus datos."""
    for tabla, columna, definicion in COLUMNAS_ITERACION_2:
        columnas = {fila["name"] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}
        if columna not in columnas:
            conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")
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
    else:
        conexion = conectar(app.config["DATABASE"])
        migrar(conexion)
        conexion.close()
