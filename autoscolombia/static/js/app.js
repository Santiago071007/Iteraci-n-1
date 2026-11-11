(function () {
  "use strict";

  const PLACA_CARRO = /^[A-Z]{3}\d{3}$/;
  const PLACA_MOTO = /^[A-Z]{3}\d{2}[A-Z]$/;

  function aFecha(texto) {
    return new Date(texto.replace(" ", "T"));
  }

  function duracion(ms) {
    let minutos = Math.max(0, Math.floor(ms / 60000));
    const dias = Math.floor(minutos / 1440);
    minutos -= dias * 1440;
    const horas = Math.floor(minutos / 60);
    minutos -= horas * 60;
    return (dias ? dias + " d " : "") + horas + " h " + minutos + " min";
  }

  function reloj() {
    const el = document.getElementById("reloj");
    if (!el) return;
    const pintar = () => {
      const ahora = new Date();
      const fecha = ahora.toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" });
      el.textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1) +
        " · " + ahora.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
    };
    pintar();
    setInterval(pintar, 15000);
  }

  function cronometros() {
    const items = document.querySelectorAll("[data-desde]");
    if (!items.length) return;
    const pintar = () => items.forEach((el) => {
      el.textContent = duracion(Date.now() - aFecha(el.dataset.desde));
    });
    pintar();
    setInterval(pintar, 30000);
  }

  function avisos() {
    document.querySelectorAll(".aviso").forEach((aviso) => {
      const cerrar = () => {
        aviso.classList.add("saliendo");
        setTimeout(() => aviso.remove(), 250);
      };
      aviso.querySelector(".aviso-cerrar")?.addEventListener("click", cerrar);
      setTimeout(cerrar, aviso.classList.contains("error") ? 9000 : 5000);
    });
  }

  function menu() {
    document.querySelectorAll("[data-menu]").forEach((b) =>
      b.addEventListener("click", () => document.body.classList.toggle("menu-abierto"))
    );
  }

  function placas() {
    document.querySelectorAll(".placa-input").forEach((input) => {
      const estado = document.getElementById(input.dataset.estado || "");
      const actualizar = () => {
        const limpia = input.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6);
        if (input.value !== limpia) input.value = limpia;
        let tipo = null;
        if (PLACA_CARRO.test(limpia)) tipo = "CARRO";
        else if (PLACA_MOTO.test(limpia)) tipo = "MOTO";

        if (estado) {
          estado.className = "placa-estado " + (tipo ? "ok" : limpia.length >= 6 ? "mal" : "");
          estado.textContent = tipo ? (tipo === "CARRO" ? "Carro · formato válido" : "Moto · formato válido")
            : limpia.length >= 6 ? "Formato no válido (carro ABC123 · moto ABC12D)" : "Carro ABC123 · Moto ABC12D";
        }
        document.querySelectorAll(".celda-opcion[data-tipo]").forEach((op) => {
          const oculta = tipo && op.dataset.tipo !== tipo;
          op.hidden = !!oculta;
          if (oculta && op.querySelector("input").checked) {
            document.getElementById("celda-auto").checked = true;
          }
        });
      };
      input.addEventListener("input", actualizar);
      actualizar();
    });
  }

  function filtros() {
    document.querySelectorAll("[data-filtrar]").forEach((input) => {
      const filas = document.querySelectorAll(input.dataset.filtrar + " tbody tr[data-texto]");
      const vacio = document.querySelector(input.dataset.filtrar + " .sin-resultados");
      input.addEventListener("input", () => {
        const q = input.value.trim().toUpperCase();
        let visibles = 0;
        filas.forEach((f) => {
          const ver = !q || f.dataset.texto.toUpperCase().includes(q);
          f.hidden = !ver;
          visibles += ver;
        });
        if (vacio) vacio.hidden = visibles !== 0;
      });
    });
  }

  function claves() {
    document.querySelectorAll("[data-ver-clave]").forEach((b) =>
      b.addEventListener("click", () => {
        const campo = document.getElementById(b.dataset.verClave);
        campo.type = campo.type === "password" ? "text" : "password";
      })
    );
  }

  function atajos() {
    const rutas = { e: "/entrada", s: "/salida", n: "/novedades" };
    document.addEventListener("keydown", (ev) => {
      const ruta = ev.altKey && rutas[ev.key.toLowerCase()];
      if (ruta && document.body.dataset.sesion) {
        ev.preventDefault();
        location.href = ruta;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    reloj();
    cronometros();
    avisos();
    menu();
    placas();
    filtros();
    claves();
    atajos();
  });
})();
