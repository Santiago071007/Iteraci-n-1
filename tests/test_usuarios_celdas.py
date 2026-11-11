"""Pruebas de la iteración 2: gestión de usuarios (empleados y clientes) y gestión de celdas.

Cada prueba indica entre corchetes el caso del plan de pruebas que automatiza (CP-xx).
"""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from autoscolombia import create_app
from autoscolombia.db import conectar, inicializar
from autoscolombia.services import (
    AuthService,
    CeldaService,
    ClienteService,
    ParqueoService,
    ReglaNegocioError,
    UsuarioService,
    VehiculoService,
)

ADMIN, OPERADOR = 1, 2


class BaseServicio(unittest.TestCase):
    def setUp(self):
        self.db = conectar(":memory:")
        inicializar(self.db)

    def tearDown(self):
        self.db.close()


class UsuarioServiceTest(BaseServicio):
    def setUp(self):
        super().setUp()
        self.servicio = UsuarioService(self.db)
        self.auth = AuthService(self.db)

    def nuevo(self, **cambios):
        datos = {"nombre": "Ana María Ruiz", "username": "aruiz", "rol": "OPERADOR",
                 "password": "Clave2026", "confirmacion": "Clave2026"}
        datos.update(cambios)
        return self.servicio.crear(datos)

    def test_crear_usuario_y_autenticar(self):  # [CP-01]
        usuario_id = self.nuevo(username="  ARuiz ")
        usuario = self.auth.autenticar("aruiz", "Clave2026")
        self.assertEqual(usuario.id, usuario_id)
        self.assertNotEqual(usuario.password_hash, "Clave2026")
        self.assertEqual(usuario.rol, "OPERADOR")

    def test_username_duplicado(self):  # [CP-02]
        with self.assertRaisesRegex(ReglaNegocioError, "ya está en uso"):
            self.nuevo(username="operador")

    def test_username_y_clave_invalidos(self):  # [CP-03]
        with self.assertRaisesRegex(ReglaNegocioError, "4 a 20 caracteres"):
            self.nuevo(username="a b")
        with self.assertRaisesRegex(ReglaNegocioError, "al menos 8"):
            self.nuevo(password="corta1", confirmacion="corta1")
        with self.assertRaisesRegex(ReglaNegocioError, "letras y números"):
            self.nuevo(password="solamenteletras", confirmacion="solamenteletras")
        with self.assertRaisesRegex(ReglaNegocioError, "no coinciden"):
            self.nuevo(confirmacion="Otra2026x")
        with self.assertRaisesRegex(ReglaNegocioError, "rol válido"):
            self.nuevo(rol="SUPERVISOR")

    def test_editar_nombre_y_rol(self):  # [CP-04]
        self.servicio.actualizar(OPERADOR, {"nombre": "Pedro Pablo Operador", "rol": "ADMIN"}, ADMIN)
        usuario = self.servicio.obtener(OPERADOR)
        self.assertEqual((usuario.nombre, usuario.rol), ("Pedro Pablo Operador", "ADMIN"))

    def test_usuario_inactivo_no_inicia_sesion(self):  # [CP-05]
        self.assertFalse(self.servicio.cambiar_estado(OPERADOR, ADMIN))
        self.assertIsNone(self.auth.autenticar("operador", "operador123"))
        self.assertTrue(self.servicio.cambiar_estado(OPERADOR, ADMIN))
        self.assertIsNotNone(self.auth.autenticar("operador", "operador123"))

    def test_no_se_desactiva_a_si_mismo_ni_al_ultimo_admin(self):  # [CP-06]
        with self.assertRaisesRegex(ReglaNegocioError, "propio usuario"):
            self.servicio.cambiar_estado(ADMIN, ADMIN)
        with self.assertRaisesRegex(ReglaNegocioError, "sí mismo"):
            self.servicio.actualizar(ADMIN, {"nombre": "Administrador", "rol": "OPERADOR"}, ADMIN)
        with self.assertRaisesRegex(ReglaNegocioError, "al menos un administrador"):
            self.servicio.actualizar(ADMIN, {"nombre": "Administrador", "rol": "OPERADOR"}, OPERADOR)
        segundo = self.nuevo(username="jefe", rol="ADMIN")
        self.servicio.cambiar_estado(ADMIN, segundo)
        with self.assertRaisesRegex(ReglaNegocioError, "al menos un administrador"):
            self.servicio.cambiar_estado(segundo, OPERADOR)

    def test_restablecer_y_cambiar_clave(self):  # [CP-07]
        self.servicio.restablecer_clave(OPERADOR, "NuevaClave1", "NuevaClave1")
        self.assertIsNotNone(self.auth.autenticar("operador", "NuevaClave1"))
        with self.assertRaisesRegex(ReglaNegocioError, "actual no es correcta"):
            self.servicio.cambiar_mi_clave(OPERADOR, "mala", "OtraClave2", "OtraClave2")
        with self.assertRaisesRegex(ReglaNegocioError, "diferente"):
            self.servicio.cambiar_mi_clave(OPERADOR, "NuevaClave1", "NuevaClave1", "NuevaClave1")
        self.servicio.cambiar_mi_clave(OPERADOR, "NuevaClave1", "OtraClave2", "OtraClave2")
        self.assertIsNone(self.auth.autenticar("operador", "NuevaClave1"))
        self.assertIsNotNone(self.auth.autenticar("operador", "OtraClave2"))


class ClienteServiceTest(BaseServicio):
    def setUp(self):
        super().setUp()
        self.servicio = ClienteService(self.db)
        self.parqueo = ParqueoService(self.db)

    def test_registrar_cliente_normaliza_datos(self):  # [CP-08]
        cliente_id = self.servicio.crear({"documento": "1.098.765.432", "nombres": "  Juan   Pérez ",
                                          "telefono": "300 123 4567", "email": "Juan@Correo.COM"})
        cliente = self.servicio.obtener(cliente_id)
        self.assertEqual((cliente.documento, cliente.nombres, cliente.telefono, cliente.email),
                         ("1098765432", "Juan Pérez", "3001234567", "juan@correo.com"))
        self.assertTrue(cliente.esta_activo())

    def test_validaciones_de_cliente(self):  # [CP-09]
        casos = [
            ({"documento": "1020304050", "nombres": "Repetido"}, "Ya existe"),
            ({"documento": "12AB", "nombres": "Juan Pérez"}, "documento"),
            ({"documento": "998877", "nombres": "J"}, "nombre completo"),
            ({"documento": "998877", "nombres": "Juan Pérez", "telefono": "12"}, "teléfono"),
            ({"documento": "998877", "nombres": "Juan Pérez", "email": "juan@"}, "correo"),
        ]
        for datos, mensaje in casos:
            with self.subTest(datos=datos), self.assertRaisesRegex(ReglaNegocioError, mensaje):
                self.servicio.crear(datos)

    def test_editar_cliente_sin_duplicar_documento(self):  # [CP-10]
        self.servicio.actualizar(1, {"documento": "1020304050", "nombres": "Laura Gómez R.", "telefono": "3110000000"})
        self.assertEqual(self.servicio.obtener(1).telefono, "3110000000")
        with self.assertRaisesRegex(ReglaNegocioError, "otro cliente"):
            self.servicio.actualizar(1, {"documento": "79876543", "nombres": "Laura Gómez"})

    def test_cliente_inactivo_no_ingresa_vehiculos(self):  # [CP-11]
        self.servicio.cambiar_estado(1)
        with self.assertRaisesRegex(ReglaNegocioError, "inactivo"):
            self.parqueo.registrar_entrada("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "inactivo"):
            hoy = date.today()
            VehiculoService(self.db).registrar({
                "placa": "NEW123", "tipo": "CARRO", "documento": "1020304050",
                "fecha_inicio": hoy.isoformat(), "fecha_fin": (hoy + timedelta(days=30)).isoformat(), "valor": "1",
            })
        self.servicio.cambiar_estado(1)
        self.assertTrue(self.parqueo.registrar_entrada("ABC123", OPERADOR).esta_abierto())

    def test_no_desactiva_cliente_con_vehiculo_dentro(self):  # [CP-12]
        self.parqueo.registrar_entrada("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "vehículo dentro"):
            self.servicio.cambiar_estado(1)

    def test_asociar_vehiculo_a_cliente_existente(self):  # [CP-13]
        hoy = date.today()
        cliente_id = self.servicio.crear({"documento": "55667788", "nombres": "Cliente Nuevo"})
        VehiculoService(self.db).registrar({
            "placa": "WER45T", "tipo": "MOTO", "documento": "55667788",
            "fecha_inicio": hoy.isoformat(), "fecha_fin": (hoy + timedelta(days=30)).isoformat(), "valor": "90000",
        })
        vehiculos = self.servicio.clientes.vehiculos(cliente_id)
        self.assertEqual([v["placa"] for v in vehiculos], ["WER45T"])


class CeldaServiceTest(BaseServicio):
    def setUp(self):
        super().setUp()
        self.servicio = CeldaService(self.db)
        self.parqueo = ParqueoService(self.db)

    def test_crear_celda(self):  # [CP-14]
        celda = self.servicio.obtener(self.servicio.crear(" a-09 ", "CARRO"))
        self.assertEqual((celda.codigo, celda.tipo_vehiculo, celda.estado), ("A-09", "CARRO", "LIBRE"))
        with self.assertRaisesRegex(ReglaNegocioError, "Ya existe"):
            self.servicio.crear("A-01", "CARRO")
        with self.assertRaisesRegex(ReglaNegocioError, "no es válido"):
            self.servicio.crear("CELDA9", "CARRO")
        with self.assertRaisesRegex(ReglaNegocioError, "tipo de vehículo"):
            self.servicio.crear("A-10", "BUS")

    def test_crear_celdas_por_rango(self):  # [CP-15]
        self.assertEqual(self.servicio.crear_lote("m", 5, 7, "MOTO"), ["M-05", "M-06", "M-07"])
        self.assertEqual(len(self.servicio.celdas.libres("MOTO")), 7)
        with self.assertRaisesRegex(ReglaNegocioError, "M-07"):
            self.servicio.crear_lote("M", 7, 9, "MOTO")
        self.assertIsNone(self.servicio.celdas.buscar_por_codigo("M-08"))
        with self.assertRaisesRegex(ReglaNegocioError, "máximo 50"):
            self.servicio.crear_lote("B", 1, 60, "CARRO")

    def test_editar_celda(self):  # [CP-16]
        self.servicio.actualizar(1, "A-11", "MOTO")
        self.assertEqual(self.servicio.obtener(1).codigo, "A-11")
        with self.assertRaisesRegex(ReglaNegocioError, "Ya existe"):
            self.servicio.actualizar(1, "A-02", "CARRO")
        registro = self.parqueo.registrar_entrada("JKL456", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "ocupada"):
            self.servicio.actualizar(registro.celda_id, "A-20", "CARRO")

    def test_mantenimiento_y_habilitar(self):  # [CP-17]
        self.servicio.poner_en_mantenimiento(1, "Demarcación borrada")
        celda = self.servicio.obtener(1)
        self.assertEqual((celda.estado, celda.observacion), ("MANTENIMIENTO", "Demarcación borrada"))
        self.assertNotIn(1, [c.id for c in self.servicio.celdas.libres("CARRO")])
        with self.assertRaisesRegex(ReglaNegocioError, "no está disponible"):
            self.parqueo.registrar_entrada("ABC123", OPERADOR, celda_id=1)
        self.servicio.habilitar(1)
        self.assertEqual(self.servicio.obtener(1).estado, "LIBRE")
        with self.assertRaisesRegex(ReglaNegocioError, "motivo"):
            self.servicio.poner_en_mantenimiento(1, "")

    def test_no_mantenimiento_de_celda_ocupada(self):  # [CP-18]
        registro = self.parqueo.registrar_entrada("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "ocupada"):
            self.servicio.poner_en_mantenimiento(registro.celda_id, "Revisión general")

    def test_eliminar_celda(self):  # [CP-19]
        nueva = self.servicio.crear("A-30", "CARRO")
        self.assertEqual(self.servicio.eliminar(nueva), "A-30")
        self.assertIsNone(self.servicio.celdas.obtener(nueva))
        registro = self.parqueo.registrar_entrada("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "ocupada"):
            self.servicio.eliminar(registro.celda_id)
        self.parqueo.registrar_salida("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "historial"):
            self.servicio.eliminar(registro.celda_id)


class RutasIteracion2Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.tmp.name) / "test.sqlite")})
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def entrar(self, usuario="admin", clave="admin123"):
        return self.cliente.post("/login", data={"username": usuario, "password": clave})

    def test_operador_no_accede_a_administracion(self):  # [CP-20]
        self.entrar("operador", "operador123")
        for ruta in ("/usuarios/", "/usuarios/nuevo", "/clientes/nuevo", "/celdas/nueva", "/clientes/1/editar"):
            self.assertEqual(self.cliente.get(ruta).status_code, 302, ruta)
        self.assertEqual(self.cliente.post("/celdas/1/eliminar").status_code, 302)
        for ruta in ("/clientes/", "/clientes/1", "/celdas/", "/celdas/1", "/usuarios/mi-clave"):
            self.assertEqual(self.cliente.get(ruta).status_code, 200, ruta)

    def test_admin_navega_y_gestiona(self):  # [CP-21]
        self.entrar()
        for ruta in ("/usuarios/", "/usuarios/nuevo", "/usuarios/2/editar", "/clientes/", "/clientes/nuevo",
                     "/clientes/1", "/clientes/1/editar", "/celdas/", "/celdas/nueva", "/celdas/8",
                     "/vehiculos/nuevo?documento=1020304050"):
            self.assertEqual(self.cliente.get(ruta).status_code, 200, ruta)
        r = self.cliente.post("/usuarios/nuevo", data={"nombre": "Nuevo Operador", "username": "nuevo.op",
                                                       "rol": "OPERADOR", "password": "Clave2026",
                                                       "confirmacion": "Clave2026"}, follow_redirects=True)
        self.assertIn("nuevo.op", r.get_data(as_text=True))
        r = self.cliente.post("/clientes/nuevo", data={"documento": "11223344", "nombres": "Cliente Web"},
                              follow_redirects=True)
        self.assertIn("Cliente Web", r.get_data(as_text=True))
        r = self.cliente.post("/celdas/nueva", data={"modo": "lote", "prefijo": "B", "desde": "1", "hasta": "3",
                                                     "tipo": "CARRO"}, follow_redirects=True)
        self.assertIn("B-01 a B-03", r.get_data(as_text=True))
        r = self.cliente.post("/celdas/1/mantenimiento", data={"observacion": "Pintura del piso"},
                              follow_redirects=True)
        self.assertIn("Pintura del piso", r.get_data(as_text=True))

    def test_usuario_desactivado_no_entra(self):  # [CP-05]
        self.entrar()
        self.cliente.post("/usuarios/2/estado")
        self.cliente.get("/logout")
        self.assertIn("incorrectos", self.entrar("operador", "operador123").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
