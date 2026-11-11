import os
from pathlib import Path

from flask import Flask

from . import db
from .controllers import BLUEPRINTS
from .iconos import icono


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-autos-colombia"),
        DATABASE=str(Path(app.instance_path) / "autos_colombia.sqlite"),
    )
    if config:
        app.config.update(config)

    app.jinja_env.globals["icono"] = icono
    db.registrar(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    return app
