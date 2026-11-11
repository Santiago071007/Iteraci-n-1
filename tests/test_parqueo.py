import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from autoscolombia import create_app
from autoscolombia.db import conectar, inicializar
from autoscolombia.services import ParqueoService, ReglaNegocioError, VehiculoService

OPERADOR = 2


class ParqueoServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = conectar(":memory:")
        inicializar(self.db)
        self.servicio = ParqueoService(self.db)

    def tearDown(self):
        self.db.close()

    def test_entrada_asigna_celda_libre_y_la_ocupa(self):
        registro = self.servicio.registrar_entrada("abc-123", OPERADOR)
        celda = self.servicio.celdas.obtener(registro.celda_id)
        self.assertEqual(celda.estado, "OCUPADA")
        self.assertEqual(celda.tipo_vehiculo, "CARRO")
        self.assertTrue(registro.esta_abierto())

    def test_moto_va_a_celda_de_moto(self):
        registro = self.servicio.registrar_entrada("XYZ78D", OPERADOR)
        self.assertEqual(self.servicio.celdas.obtener(registro.celda_id).tipo_vehiculo, "MOTO")

    def test_no_permite_doble_entrada(self):
        self.servicio.registrar_entrada("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "ya se encuentra dentro"):
            self.servicio.registrar_entrada("ABC123", OPERADOR)

    def test_rechaza_placa_invalida_no_registrada_y_mensualidad_vencida(self):
        with self.assertRaisesRegex(ReglaNegocioError, "formato"):
            self.servicio.registrar_entrada("12AB", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "no está registrado"):
            self.servicio.registrar_entrada("ZZZ999", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "mensualidad vigente"):
            self.servicio.registrar_entrada("QRS234", OPERADOR)

    def test_rechaza_celda_ocupada_o_de_otro_tipo(self):
        primero = self.servicio.registrar_entrada("ABC123", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "no está disponible"):
            self.servicio.registrar_entrada("JKL456", OPERADOR, celda_id=primero.celda_id)
        celda_moto = self.servicio.celdas.libres("MOTO")[0]
        with self.assertRaisesRegex(ReglaNegocioError, "no corresponde"):
            self.servicio.registrar_entrada("JKL456", OPERADOR, celda_id=celda_moto.id)

    def test_sin_celdas_libres(self):
        for celda in self.servicio.celdas.libres("MOTO"):
            self.servicio.celdas.cambiar_estado(celda.id, "MANTENIMIENTO")
        with self.assertRaisesRegex(ReglaNegocioError, "No hay celdas libres"):
            self.servicio.registrar_entrada("XYZ78D", OPERADOR)

    def test_salida_libera_celda_y_calcula_permanencia(self):
        entrada = datetime(2026, 10, 20, 8, 0, 0)
        registro = self.servicio.registrar_entrada("ABC123", OPERADOR, ahora=entrada)
        salida = self.servicio.registrar_salida("ABC123", OPERADOR, ahora=entrada + timedelta(hours=2, minutes=15))
        self.assertFalse(salida.esta_abierto())
        self.assertEqual(salida.tiempo_permanencia(), timedelta(hours=2, minutes=15))
        self.assertEqual(self.servicio.celdas.obtener(registro.celda_id).estado, "LIBRE")

    def test_salida_de_vehiculo_que_no_esta_dentro(self):
        with self.assertRaisesRegex(ReglaNegocioError, "no se encuentra dentro"):
            self.servicio.registrar_salida("ABC123", OPERADOR)

    def test_novedad_solo_para_vehiculos_dentro(self):
        with self.assertRaises(ReglaNegocioError):
            self.servicio.registrar_novedad("ABC123", OPERADOR, "DANO", "Rayón en la puerta")
        registro = self.servicio.registrar_entrada("ABC123", OPERADOR)
        self.servicio.registrar_novedad("ABC123", OPERADOR, "DANO", "Rayón en la puerta")
        self.assertEqual(len(self.servicio.novedades.por_registro(registro.id)), 1)

    def test_registrar_vehiculo_nuevo_y_darle_entrada(self):
        hoy = datetime.now().date()
        VehiculoService(self.db).registrar({
            "placa": "TTT111", "tipo": "CARRO", "documento": "123456", "nombres": "Cliente Prueba",
            "fecha_inicio": hoy.isoformat(), "fecha_fin": (hoy + timedelta(days=30)).isoformat(), "valor": "150000",
        })
        self.assertTrue(self.servicio.registrar_entrada("TTT111", OPERADOR).esta_abierto())

    def test_placa_de_moto_no_valida_para_carro(self):
        with self.assertRaisesRegex(ReglaNegocioError, "formato"):
            VehiculoService(self.db).registrar({"placa": "AAA11B", "tipo": "CARRO"})


class RutasTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DATABASE": str(Path(self.tmp.name) / "test.sqlite")})
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def entrar(self, usuario="operador", clave="operador123"):
        return self.cliente.post("/login", data={"username": usuario, "password": clave})

    def test_requiere_sesion(self):
        self.assertIn("/login", self.cliente.get("/").headers["Location"])

    def test_flujo_entrada_y_salida(self):
        self.entrar()
        respuesta = self.cliente.post("/entrada", data={"placa": "ABC123"}, follow_redirects=True)
        self.assertIn("Entrada registrada", respuesta.get_data(as_text=True))
        respuesta = self.cliente.post("/salida", data={"placa": "ABC123"}, follow_redirects=True)
        self.assertIn("Comprobante de salida", respuesta.get_data(as_text=True))
        for ruta in ("/", "/activos", "/historial", "/novedades", "/vehiculos/", "/celdas/"):
            self.assertEqual(self.cliente.get(ruta).status_code, 200, ruta)

    def test_operador_no_registra_vehiculos(self):
        self.entrar()
        self.assertEqual(self.cliente.get("/vehiculos/nuevo").status_code, 302)

    def test_login_incorrecto(self):
        self.assertIn("incorrectos", self.entrar(clave="mala").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
