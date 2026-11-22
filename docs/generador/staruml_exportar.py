"""Genera el proyecto StarUML completo (iteraciones 1, 2 y 3) y exporta las imágenes de los diagramas.

1. staruml.py crea docs/AutosColombia.mdj con los diagramas de la iteración 1.
2. StarUML ejecuta staruml_iter2.js (consola de scripts) para agregar casos de uso, secuencia y componentes.
3. StarUML ejecuta staruml_iter3.js para agregar los diagramas de gestión de pagos y el de componentes actualizado.
4. StarUML exporta cada diagrama nuevo a PNG; aquí se pone fondo blanco y se guarda en docs/img/staruml/.

Los scripts se ejecutan dentro de StarUML con una extensión temporal (comando autoscolombia:run) que se
instala en la carpeta de extensiones del usuario mientras corre este programa y se elimina al terminar.
Funciona con StarUML 7 y 8.

Uso:  python docs/generador/staruml_exportar.py [ruta\\a\\StarUML.exe]
También se puede indicar la ruta con la variable de entorno STARUML.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
DOCS = AQUI.parent
MDJ = DOCS / "AutosColombia.mdj"
SALIDA = DOCS / "img" / "staruml"
PARTES = ["casos", "secuencia1", "secuencia2", "componentes", "casos3", "secuencia3", "componentes3", "ajustar"]
CANDIDATOS = [
    os.environ.get("STARUML", ""),
    r"C:\Program Files\StarUML\StarUML.exe",
    str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "StarUML" / "StarUML.exe"),
]


def slug(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    texto = re.sub(r"\(iteraci[oó]n(es)? [^)]*\)", "", texto)
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


EXTENSION = Path(os.environ.get("APPDATA", "")) / "StarUML" / "extensions" / "user" / "autoscolombia-generador"
EXTENSION_PACKAGE = '{"name": "autoscolombia-generador", "title": "Autos Colombia - generador de diagramas", ' \
                    '"version": "1.0.0", "engines": {"staruml": ">=3.0.0"}}'
EXTENSION_MAIN = """
const fs = require("fs");

// Ejecuta el script indicado en AUTOSCOLOMBIA_SCRIPT con acceso a `app` y deja su salida en AUTOSCOLOMBIA_LOG.
function init() {
  app.commands.register("autoscolombia:run", function () {
    const lineas = [];
    const consola = { log: function () { lineas.push(Array.prototype.join.call(arguments, " ")); } };
    try {
      const codigo = fs.readFileSync(process.env.AUTOSCOLOMBIA_SCRIPT, "utf8");
      new Function("app", "console", codigo)(app, consola);
    } catch (e) {
      lineas.push("ERROR " + e + " " + (e && e.stack ? e.stack : ""));
    }
    fs.writeFileSync(process.env.AUTOSCOLOMBIA_LOG, lineas.join("\\n"), "utf8");
  });
}

exports.init = init;
"""


def instalar_extension():
    EXTENSION.mkdir(parents=True, exist_ok=True)
    (EXTENSION / "package.json").write_text(EXTENSION_PACKAGE, encoding="utf-8")
    (EXTENSION / "main.js").write_text(EXTENSION_MAIN, encoding="utf-8")


def ejecutar_parte(staruml: str, parte: str, script: str):
    with tempfile.TemporaryDirectory() as tmp:
        archivo, registro = Path(tmp) / "script.js", Path(tmp) / "salida.txt"
        archivo.write_text(f'var PARTE = "{parte}";\n{script}', encoding="utf-8")
        r = subprocess.run([staruml, "exec", str(MDJ), "-c", "autoscolombia:run"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
                           env={**os.environ, "AUTOSCOLOMBIA_SCRIPT": str(archivo), "AUTOSCOLOMBIA_LOG": str(registro)})
        salida = registro.read_text(encoding="utf-8") if registro.exists() else r.stdout[-1500:]
    if f"OK {parte}" not in salida:
        sys.exit(f"Falló la parte {parte}:\n{salida[-3000:]}")
    print("  parte", parte, "ok")


def main():
    staruml = sys.argv[1] if len(sys.argv) > 1 else next((c for c in CANDIDATOS if c and Path(c).exists()), None)
    if not staruml:
        sys.exit("No se encontró StarUML. Indique la ruta: python staruml_exportar.py C:\\ruta\\StarUML.exe")

    subprocess.run([sys.executable, str(AQUI / "staruml.py")], check=True)
    script = (AQUI / "staruml_iter2.js").read_text(encoding="utf-8")
    # La iteración 3 reutiliza las funciones de la 2 (todo lo anterior a su bloque de ejecución).
    script3 = script.split("\ntry {")[0] + "\n" + (AQUI / "staruml_iter3.js").read_text(encoding="utf-8")
    instalar_extension()
    try:
        for parte in PARTES:
            ejecutar_parte(staruml, parte, script3 if parte.endswith("3") else script)
    finally:
        shutil.rmtree(EXTENSION, ignore_errors=True)

    SALIDA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([staruml, "image", str(MDJ), "-f", "png", "-o", str(Path(tmp) / "<%=filenamify(element.name)%>.png")],
                       capture_output=True, timeout=300)
        for png in sorted(Path(tmp).glob("*.png")):
            nombre = png.stem
            if "Iteración 1" in nombre and not nombre.startswith("SD"):
                continue  # las imágenes de la iteración 1 se conservan como se entregaron
            if nombre in ("Diagrama de clases", "Diagrama de paquetes", "Arquitectura del sistema"):
                continue
            imagen = Image.open(png).convert("RGBA")
            fondo = Image.new("RGBA", imagen.size, "white")
            fondo.alpha_composite(imagen)
            destino = SALIDA / f"{slug(nombre)}.png"
            fondo.convert("RGB").save(destino, optimize=True)
            print("  imagen", destino.name, imagen.size)


if __name__ == "__main__":
    main()
