import math
from html import escape

FUENTE = "Segoe UI, Arial, Helvetica, sans-serif"
BORDE = "#1d2b44"
TEXTO = "#1d2433"
SUAVE = "#5b6575"
CABECERA = "#dbe6f5"
CREMA = "#fff8e1"
FONDO_CAPA = "#f3f6fb"

DEFS = f"""<defs>
<marker id="flecha" viewBox="0 0 12 12" refX="12" refY="6" markerWidth="12" markerHeight="12" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,1 L12,6 L0,11" fill="none" stroke="{BORDE}" stroke-width="1.4"/></marker>
<marker id="llena" viewBox="0 0 12 12" refX="12" refY="6" markerWidth="12" markerHeight="12" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,1 L12,6 L0,11 z" fill="{BORDE}"/></marker>
<marker id="triangulo" viewBox="0 0 16 16" refX="16" refY="8" markerWidth="16" markerHeight="16" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M1,1 L16,8 L1,15 z" fill="#fff" stroke="{BORDE}" stroke-width="1.3"/></marker>
<marker id="rombo" viewBox="0 0 20 12" refX="20" refY="6" markerWidth="20" markerHeight="12" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,6 L10,1 L20,6 L10,11 z" fill="{BORDE}"/></marker>
<marker id="muchos" viewBox="0 0 16 16" refX="16" refY="8" markerWidth="16" markerHeight="16" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,8 L16,1 M0,8 L16,8 M0,8 L16,15 M3,2 L3,14" fill="none" stroke="{BORDE}" stroke-width="1.3"/></marker>
<marker id="uno" viewBox="0 0 16 16" refX="16" refY="8" markerWidth="16" markerHeight="16" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M6,1 L6,15 M10,1 L10,15" fill="none" stroke="{BORDE}" stroke-width="1.3"/></marker>
</defs>"""


class Caja:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def centro(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def borde(self, hacia):
        cx, cy = self.centro
        dx, dy = hacia[0] - cx, hacia[1] - cy
        if dx == 0 and dy == 0:
            return cx, cy
        escala = min(
            (self.w / 2) / abs(dx) if dx else math.inf,
            (self.h / 2) / abs(dy) if dy else math.inf,
        )
        return cx + dx * escala, cy + dy * escala

    def arriba(self, f=0.5):
        return self.x + self.w * f, self.y

    def abajo(self, f=0.5):
        return self.x + self.w * f, self.y + self.h

    def izq(self, f=0.5):
        return self.x, self.y + self.h * f

    def der(self, f=0.5):
        return self.x + self.w, self.y + self.h * f


class Elipse(Caja):
    def __init__(self, cx, cy, rx, ry):
        super().__init__(cx - rx, cy - ry, 2 * rx, 2 * ry)
        self.rx, self.ry = rx, ry

    def borde(self, hacia):
        cx, cy = self.centro
        dx, dy = hacia[0] - cx, hacia[1] - cy
        t = 1 / math.sqrt((dx / self.rx) ** 2 + (dy / self.ry) ** 2)
        return cx + dx * t, cy + dy * t


class Rombo(Caja):
    def borde(self, hacia):
        cx, cy = self.centro
        dx, dy = hacia[0] - cx, hacia[1] - cy
        t = 1 / (abs(dx) / (self.w / 2) + abs(dy) / (self.h / 2))
        return cx + dx * t, cy + dy * t


class Svg:
    def __init__(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.elementos = []

    def add(self, s):
        self.elementos.append(s)

    def guardar(self, ruta):
        contenido = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.ancho} {self.alto}" '
            f'width="{self.ancho}" height="{self.alto}" font-family="{FUENTE}">'
            f'<rect width="100%" height="100%" fill="#fff"/>{DEFS}' + "\n".join(self.elementos) + "</svg>"
        )
        ruta.write_text(contenido, encoding="utf-8")

    def texto(self, x, y, s, tam=13, ancla="middle", peso="normal", color=TEXTO, cursiva=False, subrayado=False):
        lineas = str(s).split("\n")
        y0 = y - (len(lineas) - 1) * tam * 0.62
        estilo = ' font-style="italic"' if cursiva else ""
        deco = ' text-decoration="underline"' if subrayado else ""
        for i, linea in enumerate(lineas):
            self.add(
                f'<text x="{x:.1f}" y="{y0 + i * tam * 1.25:.1f}" font-size="{tam}" text-anchor="{ancla}" '
                f'dominant-baseline="central" font-weight="{peso}" fill="{color}"{estilo}{deco}>{escape(linea)}</text>'
            )

    def rect(self, x, y, w, h, relleno="#fff", borde=BORDE, rx=0, punteado=False, grosor=1.3):
        dash = ' stroke-dasharray="6 4"' if punteado else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"{dash}/>')
        return Caja(x, y, w, h)

    def elipse(self, cx, cy, rx, ry, texto=None, relleno="#fff", tam=12.5, punteado=False, subrayado=False):
        dash = ' stroke-dasharray="5 3"' if punteado else ""
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{relleno}" stroke="{BORDE}" stroke-width="1.3"{dash}/>')
        if texto:
            self.texto(cx, cy, texto, tam=tam, subrayado=subrayado)
        return Elipse(cx, cy, rx, ry)

    def rombo(self, cx, cy, w, h, texto, relleno=CREMA):
        puntos = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"
        self.add(f'<polygon points="{puntos}" fill="{relleno}" stroke="{BORDE}" stroke-width="1.3"/>')
        self.texto(cx, cy, texto, tam=12)
        return Rombo(cx - w / 2, cy - h / 2, w, h)

    def linea(self, puntos, punteado=False, inicio=None, fin=None, grosor=1.3, color=BORDE):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
        extra = ' stroke-dasharray="6 4"' if punteado else ""
        if inicio:
            extra += f' marker-start="url(#{inicio})"'
        if fin:
            extra += f' marker-end="url(#{fin})"'
        self.add(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{grosor}"{extra}/>')

    def conectar(self, a, b, etiqueta=None, m1=None, m2=None, tam=11.5, **kw):
        p1 = a.borde(b.centro)
        p2 = b.borde(a.centro)
        self.linea([p1, p2], **kw)
        self.etiquetas([p1, p2], etiqueta, m1, m2, tam)
        return p1, p2

    def etiquetas(self, puntos, etiqueta=None, m1=None, m2=None, tam=11.5, desplazamiento=11):
        p1, p2 = puntos[0], puntos[-1]
        if etiqueta:
            i = len(puntos) // 2
            a, b = (puntos[i - 1], puntos[i]) if len(puntos) > 2 else (p1, p2)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            self.add(f'<rect x="{mx - len(etiqueta) * 3.4 - 3}" y="{my - 9}" width="{len(etiqueta) * 6.8 + 6}" height="18" fill="#fff"/>')
            self.texto(mx, my, etiqueta, tam=tam, color=SUAVE, cursiva=True)
        for (pa, pb), m in (((puntos[0], puntos[1]), m1), ((puntos[-1], puntos[-2]), m2)):
            if not m:
                continue
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            largo = math.hypot(dx, dy) or 1
            ux, uy = dx / largo, dy / largo
            x = pa[0] + ux * 20 - uy * desplazamiento
            y = pa[1] + uy * 20 + ux * desplazamiento
            self.texto(x, y, m, tam=12, peso="600")

    def actor(self, cx, arriba, nombre):
        c = BORDE
        self.add(f'<circle cx="{cx}" cy="{arriba + 11}" r="11" fill="#fff" stroke="{c}" stroke-width="1.5"/>')
        self.add(f'<line x1="{cx}" y1="{arriba + 22}" x2="{cx}" y2="{arriba + 55}" stroke="{c}" stroke-width="1.5"/>')
        self.add(f'<line x1="{cx - 20}" y1="{arriba + 33}" x2="{cx + 20}" y2="{arriba + 33}" stroke="{c}" stroke-width="1.5"/>')
        self.add(f'<polyline points="{cx - 16},{arriba + 80} {cx},{arriba + 55} {cx + 16},{arriba + 80}" fill="none" stroke="{c}" stroke-width="1.5"/>')
        self.texto(cx, arriba + 96, nombre, peso="600")
        return Caja(cx - 22, arriba, 44, 82)

    def clase(self, x, y, w, nombre, atributos=(), metodos=(), estereotipo=None, relleno="#fff"):
        fila = 18
        cab = 32 if estereotipo else 26
        h_attr = max(len(atributos), 0) * fila + 10
        h_met = len(metodos) * fila + 10 if metodos else 10
        h = cab + h_attr + h_met
        self.rect(x, y, w, h, relleno=relleno)
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{cab}" fill="{CABECERA}" stroke="{BORDE}" stroke-width="1.3"/>')
        if estereotipo:
            self.texto(x + w / 2, y + 10, f"«{estereotipo}»", tam=10.5, color=SUAVE)
            self.texto(x + w / 2, y + 23, nombre, peso="700")
        else:
            self.texto(x + w / 2, y + cab / 2, nombre, peso="700")
        yy = y + cab
        for i, a in enumerate(atributos):
            self.texto(x + 8, yy + 14 + i * fila, a, tam=12, ancla="start")
        yy += h_attr
        self.add(f'<line x1="{x}" y1="{yy}" x2="{x + w}" y2="{yy}" stroke="{BORDE}" stroke-width="1.3"/>')
        for i, m in enumerate(metodos):
            self.texto(x + 8, yy + 14 + i * fila, m, tam=12, ancla="start")
        return Caja(x, y, w, h)

    def paquete(self, x, y, w, h, nombre, relleno="#fff", titulo_dentro=False, estereotipo=None):
        tab_w = max(70, len(nombre) * 8 + 20)
        self.add(f'<rect x="{x}" y="{y - 20}" width="{tab_w}" height="20" fill="{CABECERA}" stroke="{BORDE}" stroke-width="1.3"/>')
        self.rect(x, y, w, h, relleno=relleno)
        if titulo_dentro:
            self.texto(x + 10, y - 10, nombre, peso="700", ancla="start", tam=12.5)
        else:
            if estereotipo:
                self.texto(x + w / 2, y + h / 2 - 9, f"«{estereotipo}»", tam=10.5, color=SUAVE)
            self.texto(x + w / 2, y + h / 2 + (6 if estereotipo else 0), nombre, peso="700")
        return Caja(x, y - 20, w, h + 20)

    def componente(self, x, y, w, h, nombre, relleno="#fff", tam=12.5):
        self.rect(x, y, w, h, relleno=relleno, rx=4)
        ix, iy = x + w - 24, y + 8
        self.add(f'<rect x="{ix}" y="{iy}" width="14" height="18" fill="#fff" stroke="{BORDE}"/>')
        self.add(f'<rect x="{ix - 4}" y="{iy + 3}" width="8" height="4" fill="#fff" stroke="{BORDE}"/>')
        self.add(f'<rect x="{ix - 4}" y="{iy + 11}" width="8" height="4" fill="#fff" stroke="{BORDE}"/>')
        self.texto(x + (w - 24) / 2, y + h / 2, nombre, tam=tam)
        return Caja(x, y, w, h)

    def nodo(self, x, y, w, h, nombre, d=12):
        self.add(f'<polygon points="{x},{y} {x + d},{y - d} {x + w + d},{y - d} {x + w},{y}" fill="#e9eef6" stroke="{BORDE}" stroke-width="1.3"/>')
        self.add(f'<polygon points="{x + w},{y} {x + w + d},{y - d} {x + w + d},{y + h - d} {x + w},{y + h}" fill="#d5deeb" stroke="{BORDE}" stroke-width="1.3"/>')
        self.rect(x, y, w, h, relleno="#fbfcfe")
        self.texto(x + 10, y + 16, nombre, peso="700", ancla="start", tam=12.5)
        return Caja(x, y, w, h)

    def cilindro(self, x, y, w, h, nombre):
        ry = 10
        self.add(
            f'<path d="M{x},{y + ry} a{w / 2},{ry} 0 0,0 {w},0 v{h - 2 * ry} a{w / 2},{ry} 0 0,1 {-w},0 z" '
            f'fill="{CREMA}" stroke="{BORDE}" stroke-width="1.3"/>'
        )
        self.add(f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{CREMA}" stroke="{BORDE}" stroke-width="1.3"/>')
        self.texto(x + w / 2, y + h / 2 + 6, nombre, tam=12)
        return Caja(x, y, w, h)

    def tabla(self, x, y, w, nombre, columnas, con_tipos=False):
        fila = 20
        h = 28 + len(columnas) * fila + 6
        self.rect(x, y, w, h)
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="28" fill="{CABECERA}" stroke="{BORDE}" stroke-width="1.3"/>')
        self.texto(x + w / 2, y + 14, nombre, peso="700")
        for i, (col, tipo, marcas) in enumerate(columnas):
            yy = y + 28 + 13 + i * fila
            clave = " ".join(m for m in ("PK", "FK") if m in marcas)
            self.texto(x + 8, yy, clave, tam=10.5, ancla="start", peso="700", color="#a15c00")
            self.texto(x + 44, yy, col, tam=12, ancla="start", subrayado="PK" in marcas,
                       peso="600" if "PK" in marcas else "normal")
            if con_tipos:
                restr = " ".join(m for m in ("NN", "UQ") if m in marcas)
                self.texto(x + w - 8, yy, f"{tipo}  {restr}".strip(), tam=11, ancla="end", color=SUAVE)
        return Caja(x, y, w, h)
