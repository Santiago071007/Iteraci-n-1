"""Genera el proyecto StarUML completo (iteraciones 1 y 2) y exporta las imágenes de los diagramas.

1. staruml.py crea docs/AutosColombia.mdj con los diagramas de la iteración 1.
2. StarUML ejecuta staruml_iter2.js (consola de scripts) para agregar casos de uso, secuencia y componentes.
3. StarUML exporta cada diagrama nuevo a PNG; aquí se pone fondo blanco y se guarda en docs/img/staruml/.

Uso:  python docs/generador/staruml_exportar.py [ruta\\a\\StarUML.exe]
También se puede indicar la ruta con la variable de entorno STARUML.
"""
import os
import re
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
PARTES = ["casos", "secuencia1", "secuencia2", "componentes", "ajustar"]
CANDIDATOS = [
    os.environ.get("STARUML", ""),
    r"C:\Program Files\StarUML\StarUML.exe",
    str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "StarUML" / "StarUML.exe"),
]


def slug(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    texto = re.sub(r"\(iteraci[oó]n(es)? [^)]*\)", "", texto)
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def ejecutar_parte(staruml: str, parte: str, script: str):
    codigo = f'var PARTE = "{parte}";\n{script}'
    r = subprocess.run([staruml, "exec", str(MDJ), "-c", "script-console:run", "-a", codigo],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
                       env={**os.environ, "RUST_LOG": "StarUML::scripting=info"})
    salida = r.stdout + r.stderr
    if f"OK {parte}" not in salida:
        sys.exit(f"Falló la parte {parte}:\n{salida[-3000:]}")
    print("  parte", parte, "ok")


def main():
    staruml = sys.argv[1] if len(sys.argv) > 1 else next((c for c in CANDIDATOS if c and Path(c).exists()), None)
    if not staruml:
        sys.exit("No se encontró StarUML. Indique la ruta: python staruml_exportar.py C:\\ruta\\StarUML.exe")

    subprocess.run([sys.executable, str(AQUI / "staruml.py")], check=True)
    script = (AQUI / "staruml_iter2.js").read_text(encoding="utf-8")
    for parte in PARTES:
        ejecutar_parte(staruml, parte, script)

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
