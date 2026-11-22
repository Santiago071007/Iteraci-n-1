"""Pruebas de la iteración 3: gestión de pagos de mensualidades.

Cada prueba indica entre corchetes el caso del plan de pruebas que automatiza (CP-xx).
"""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

from autoscolombia import create_app
from autoscolombia.db import conectar, inicializar
from autoscolombia.services import ClienteService, PagoService, ParqueoService, ReglaNegocioError, VehiculoService
from autoscolombia.services.pago_service import sumar_meses

ADMIN, OPERADOR, OPERADORA = 1, 2, 3
HOY = date.today()


def dia(desplazamiento: int) -> str:
    return (HOY + timedelta(days=desplazamiento)).isoformat()


class PagoServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = conectar(":memory:")
        inicializar(self.db)
        self.servicio = PagoService(self.db)

    def tearDown(self):
        self.db.close()

    def vence(self, placa: str) -> str:
        return self.servicio.mensualidades.ultima(self.servicio.vehiculos.buscar_por_placa(placa).id).fecha_fin

    def test_cotizar_mensualidad_vigente(self):  # [CP-01]
        c = self.servicio.cotizar("abc-123")
        self.assertTrue(c["vigente"])
        self.assertEqual((c["tarifa"], c["valor"], c["meses"]), (180000, 180000, 1))
        self.assertEqual(c["inicio"], dia(21))  # el día siguiente al vencimiento actual (hoy + 20)
        self.assertEqual(c["fin"], (sumar_meses(HOY + timedelta(days=21), 1) - timedelta(days=1)).isoformat())
        self.assertEqual(self.vence("ABC123"), dia(20))  # cotizar no guarda nada

    def test_pago_en_efectivo_amplia_la_vigencia(self):  # [CP-02]
        pago = self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", "", OPERADOR)
        self.assertEqual((pago.estado, pago.medio, pago.referencia, pago.valor), ("VIGENTE", "EFECTIVO", None, 180000))
        self.assertEqual((pago.periodo_inicio, pago.usuario_id), (dia(21), OPERADOR))
        self.assertEqual(self.vence("ABC123"), pago.periodo_fin)
        self.assertGreater(pago.periodo_fin, dia(45))
        self.assertEqual(self.servicio.pagos.detalle(pago.id)["cajero"], "Pedro Operador")

    def test_pago_de_mensualidad_vencida_habilita_la_entrada(self):  # [CP-03]
        parqueo = ParqueoService(self.db)
        with self.assertRaisesRegex(ReglaNegocioError, "mensualidad vigente"):
            parqueo.registrar_entrada("QRS234", OPERADOR)
        self.assertFalse(self.servicio.cotizar("QRS234")["vigente"])
        pago = self.servicio.registrar_pago("QRS234", 1, "EFECTIVO", None, OPERADOR)
        self.assertEqual(pago.periodo_inicio, HOY.isoformat())  # empieza hoy, no en la fecha vencida
        self.assertTrue(parqueo.registrar_entrada("QRS234", OPERADOR).esta_abierto())

    def test_pago_de_varios_meses(self):  # [CP-04]
        pago = self.servicio.registrar_pago("XYZ78D", "3", "TARJETA", "AP-774512", OPERADOR)
        inicio = HOY + timedelta(days=29)
        self.assertEqual((pago.meses, pago.valor), (3, 270000))  # 3 × tarifa de moto
        self.assertEqual(pago.periodo_inicio, inicio.isoformat())
        self.assertEqual(pago.periodo_fin, (sumar_meses(inicio, 3) - timedelta(days=1)).isoformat())

    def test_meses_invalidos_y_anticipo_maximo(self):  # [CP-05]
        for meses in (0, 13, "", "dos"):
            with self.assertRaisesRegex(ReglaNegocioError, "meses"):
                self.servicio.registrar_pago("ABC123", meses, "EFECTIVO", None, OPERADOR)
        self.servicio.registrar_pago("ABC123", 11, "EFECTIVO", None, OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "12 meses por adelantado"):
            self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", None, OPERADOR)
        self.assertEqual(len(self.servicio.pagos.listar(texto="ABC123")), 2)  # el de ejemplo y el de 11 meses

    def test_medio_de_pago_y_referencia(self):  # [CP-06]
        with self.assertRaisesRegex(ReglaNegocioError, "medio de pago"):
            self.servicio.registrar_pago("ABC123", 1, "CHEQUE", "123456", OPERADOR)
        for referencia in ("", "ab", "ref con símbolos $$"):
            with self.assertRaisesRegex(ReglaNegocioError, "referencia"):
                self.servicio.registrar_pago("ABC123", 1, "TRANSFERENCIA", referencia, OPERADOR)
        pago = self.servicio.registrar_pago("ABC123", 1, "TRANSFERENCIA", " trf 99 12 ", OPERADOR)
        self.assertEqual(pago.referencia, "TRF9912")

    def test_referencia_duplicada_no_registra_dos_veces(self):  # [CP-07]
        primero = self.servicio.registrar_pago("ABC123", 1, "BILLETERA", "NEQ5550001", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, f"recibo N.º {primero.id}"):
            self.servicio.registrar_pago("JKL456", 1, "BILLETERA", "neq5550001", OPERADORA)
        self.assertEqual(self.vence("JKL456"), dia(25))  # la mensualidad de JKL456 no cambió
        otro = self.servicio.registrar_pago("JKL456", 1, "TRANSFERENCIA", "NEQ5550001", OPERADORA)
        self.assertTrue(otro.esta_vigente())  # la misma referencia en otro medio es otro comprobante

    def test_rechaza_placa_invalida_no_registrada_o_cliente_inactivo(self):  # [CP-08]
        with self.assertRaisesRegex(ReglaNegocioError, "formato"):
            self.servicio.cotizar("12AB")
        with self.assertRaisesRegex(ReglaNegocioError, "no está registrado"):
            self.servicio.registrar_pago("ZZZ999", 1, "EFECTIVO", None, OPERADOR)
        ClienteService(self.db).cambiar_estado(1)
        with self.assertRaisesRegex(ReglaNegocioError, "inactivo"):
            self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", None, OPERADOR)

    def test_calculo_de_periodos_en_fin_de_mes(self):  # [CP-09]
        self.assertEqual(sumar_meses(date(2027, 1, 31), 1), date(2027, 2, 28))
        self.assertEqual(sumar_meses(date(2028, 1, 31), 1), date(2028, 2, 29))  # bisiesto
        self.assertEqual(sumar_meses(date(2026, 11, 15), 3), date(2027, 2, 15))  # cambio de año
        self.assertEqual(sumar_meses(date(2026, 3, 31), 12), date(2027, 3, 31))
        ahora = datetime(2027, 1, 31, 10, 0)
        VehiculoService(self.db).registrar({
            "placa": "FEB001", "tipo": "CARRO", "documento": "1020304050",
            "fecha_inicio": "2026-12-01", "fecha_fin": "2026-12-31", "valor": "0",
        })
        pago = self.servicio.registrar_pago("FEB001", 1, "EFECTIVO", None, OPERADOR, ahora=ahora)
        self.assertEqual((pago.periodo_inicio, pago.periodo_fin), ("2027-01-31", "2027-02-27"))

    def test_anular_pago_retira_el_periodo(self):  # [CP-10]
        pago = self.servicio.registrar_pago("ABC123", 2, "EFECTIVO", None, OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "motivo"):
            self.servicio.anular_pago(pago.id, "error", ADMIN)
        anulado = self.servicio.anular_pago(pago.id, "Se registró a la placa equivocada", ADMIN)
        self.assertEqual((anulado.estado, anulado.anulado_por), ("ANULADO", ADMIN))
        self.assertEqual(anulado.motivo_anulacion, "Se registró a la placa equivocada")
        self.assertIsNotNone(anulado.anulado_en)
        self.assertEqual(self.vence("ABC123"), dia(20))  # volvió a la vigencia anterior
        self.assertEqual(self.servicio.recaudo(HOY.isoformat(), HOY.isoformat())["total"], 0)
        with self.assertRaisesRegex(ReglaNegocioError, "ya está anulado"):
            self.servicio.anular_pago(pago.id, "Se registró a la placa equivocada", ADMIN)
        with self.assertRaisesRegex(ReglaNegocioError, "no existe"):
            self.servicio.anular_pago(9999, "Se registró a la placa equivocada", ADMIN)

    def test_solo_se_anula_el_ultimo_pago_del_vehiculo(self):  # [CP-11]
        primero = self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", None, OPERADOR)
        segundo = self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", None, OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, f"recibo N.º {segundo.id}"):
            self.servicio.anular_pago(primero.id, "Pago duplicado por error del cajero", ADMIN)
        self.servicio.anular_pago(segundo.id, "Pago duplicado por error del cajero", ADMIN)
        self.servicio.anular_pago(primero.id, "Pago duplicado por error del cajero", ADMIN)
        self.assertEqual(self.vence("ABC123"), dia(20))

    def test_no_anula_pago_vigente_con_vehiculo_dentro(self):  # [CP-12]
        pago = self.servicio.registrar_pago("QRS234", 1, "EFECTIVO", None, OPERADOR)
        parqueo = ParqueoService(self.db)
        parqueo.registrar_entrada("QRS234", OPERADOR)
        with self.assertRaisesRegex(ReglaNegocioError, "registre la salida"):
            self.servicio.anular_pago(pago.id, "El cliente pidió la devolución", ADMIN)
        parqueo.registrar_salida("QRS234", OPERADOR)
        self.servicio.anular_pago(pago.id, "El cliente pidió la devolución", ADMIN)
        with self.assertRaisesRegex(ReglaNegocioError, "mensualidad vigente"):
            parqueo.registrar_entrada("QRS234", OPERADOR)

    def test_referencia_de_pago_anulado_se_puede_reutilizar(self):  # [CP-13]
        pago = self.servicio.registrar_pago("ABC123", 1, "TRANSFERENCIA", "TRF700100", OPERADOR)
        self.servicio.anular_pago(pago.id, "Se registró a la placa equivocada", ADMIN)
        corregido = self.servicio.registrar_pago("JKL456", 1, "TRANSFERENCIA", "TRF700100", OPERADOR)
        self.assertTrue(corregido.esta_vigente())

    def test_tarifas(self):  # [CP-14]
        anterior = self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", None, OPERADOR)
        self.assertEqual(self.servicio.actualizar_tarifa("CARRO", "195.000", ADMIN), 195000)
        nuevo = self.servicio.registrar_pago("JKL456", 2, "EFECTIVO", None, OPERADOR)
        self.assertEqual(nuevo.valor, 390000)
        self.assertEqual(self.servicio.pagos.obtener(anterior.id).valor, 180000)  # el recibo anterior no cambia
        self.assertEqual(self.servicio.cotizar("XYZ78D")["tarifa"], 90000)  # la tarifa de moto no cambió
        fila = [t for t in self.servicio.tarifas.listar() if t["tipo_vehiculo"] == "CARRO"][0]
        self.assertEqual((fila["usuario"], fila["valor_mensual"]), ("Administrador", 195000))
        for tipo, valor, mensaje in (("CARRO", "abc", "número entero"), ("CARRO", 500, "debe estar entre"),
                                     ("CARRO", 9_000_000, "debe estar entre"), ("BUS", 100000, "tipo de vehículo")):
            with self.assertRaisesRegex(ReglaNegocioError, mensaje):
                self.servicio.actualizar_tarifa(tipo, valor, ADMIN)

    def test_cartera_clasifica_las_mensualidades(self):  # [CP-15]
        cartera = self.servicio.cartera()
        self.assertEqual([v["placa"] for v in cartera["vencidas"]], ["QRS234"])
        self.assertEqual((len(cartera["por_vencer"]), len(cartera["al_dia"])), (0, 4))
        self.assertEqual(cartera["por_cobrar"], 180000)
        en_12_dias = self.servicio.cartera(HOY + timedelta(days=12))
        self.assertEqual([(v["placa"], v["dias"]) for v in en_12_dias["por_vencer"]], [("MNO901", 3)])
        self.servicio.registrar_pago("QRS234", 1, "EFECTIVO", None, OPERADOR)
        self.assertEqual(self.servicio.cartera()["vencidas"], [])
        ClienteService(self.db).cambiar_estado(1)  # los vehículos de clientes inactivos no se cobran
        self.assertNotIn("ABC123", [v["placa"] for v in self.servicio.cartera()["al_dia"]])

    def test_cierre_de_caja(self):  # [CP-16]
        hoy = HOY.isoformat()
        self.servicio.registrar_pago("ABC123", 1, "EFECTIVO", None, OPERADOR)
        self.servicio.registrar_pago("XYZ78D", 2, "EFECTIVO", None, OPERADOR)
        self.servicio.registrar_pago("JKL456", 1, "TRANSFERENCIA", "TRF810022", OPERADORA)
        anulado = self.servicio.registrar_pago("MNO901", 1, "TARJETA", "AP-100200", OPERADORA)
        self.servicio.anular_pago(anulado.id, "El datáfono rechazó la transacción", ADMIN)
        cierre = self.servicio.recaudo(hoy, hoy)
        self.assertEqual((cierre["total"], cierre["cantidad"], cierre["efectivo"]), (540000, 3, 360000))
        self.assertEqual({m["medio"]: m["total"] for m in cierre["medios_totales"]},
                         {"EFECTIVO": 360000, "TRANSFERENCIA": 180000, "TARJETA": 0, "BILLETERA": 0})
        self.assertEqual([p["id"] for p in cierre["anulados"]], [anulado.id])
        self.assertEqual({c["cajero"]: c["total"] for c in cierre["cajeros"]},
                         {"Pedro Operador": 360000, "Lucía Torres Vega": 180000})
        propio = self.servicio.recaudo(hoy, hoy, OPERADORA)  # el operador solo ve lo que recibió
        self.assertEqual((propio["total"], propio["cantidad"], propio["cajeros"]), (180000, 1, []))
        with self.assertRaisesRegex(ReglaNegocioError, "fecha inicial"):
            self.servicio.recaudo(dia(1), hoy)

    def test_registro_de_vehiculo_genera_recibo_de_la_primera_mensualidad(self):  # [CP-17]
        datos = {"placa": "NVO123", "tipo": "CARRO", "documento": "1020304050",
                 "fecha_inicio": dia(0), "fecha_fin": dia(30), "valor": "180000",
                 "medio": "BILLETERA", "referencia": "NEQ900800"}
        VehiculoService(self.db).registrar(datos, ADMIN)
        pagos = self.servicio.pagos.listar(texto="NVO123")
        self.assertEqual(len(pagos), 1)
        self.assertEqual((pagos[0]["valor"], pagos[0]["medio"], pagos[0]["referencia"], pagos[0]["cajero"]),
                         (180000, "BILLETERA", "NEQ900800", "Administrador"))
        with self.assertRaisesRegex(ReglaNegocioError, "referencia"):
            VehiculoService(self.db).registrar({**datos, "placa": "NVO124", "medio": "TARJETA", "referencia": ""}, ADMIN)
        self.assertIsNone(self.servicio.vehiculos.buscar_por_placa("NVO124"))

    def test_la_base_de_datos_protege_los_pagos(self):  # [CP-20]
        insertar = ("INSERT INTO pago (vehiculo_id, fecha, meses, periodo_inicio, periodo_fin, valor, medio, "
                    "referencia, usuario_id) VALUES (1, '2026-11-01 10:00:00', ?, '2026-11-01', '2026-11-30', ?, ?, ?, 2)")
        for parametros in ((1, 0, "EFECTIVO", None), (13, 180000, "EFECTIVO", None),
                           (1, 180000, "CHEQUE", "123456"), (1, 180000, "TARJETA", None)):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(insertar, parametros)
        self.db.execute(insertar, (1, 180000, "TARJETA", "AP-1"))
        with self.assertRaises(sqlite3.IntegrityError):  # índice único de referencia por medio
            self.db.execute(insertar, (1, 180000, "TARJETA", "AP-1"))
        with self.assertRaises(sqlite3.IntegrityError):  # un pago no se anula sin motivo ni responsable
            self.db.execute("UPDATE pago SET estado = 'ANULADO' WHERE id = 1")


class RutasPagosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ruta_bd = str(Path(self.tmp.name) / "test.sqlite")
        self.app = create_app({"TESTING": True, "DATABASE": self.ruta_bd})
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def entrar(self, usuario="operador", clave="operador123"):
        self.cliente.get("/logout")
        return self.cliente.post("/login", data={"username": usuario, "password": clave})

    def texto(self, ruta, **kwargs):
        return self.cliente.get(ruta, follow_redirects=True, **kwargs).get_data(as_text=True)

    def test_operador_no_anula_ni_cambia_tarifas(self):  # [CP-18]
        self.entrar()
        self.assertEqual(self.cliente.get("/pagos/tarifas").status_code, 302)
        r = self.cliente.post("/pagos/tarifas", data={"tipo": "CARRO", "valor": "1000000"}, follow_redirects=True)
        self.assertIn("solo está disponible para el administrador", r.get_data(as_text=True))
        r = self.cliente.post("/pagos/1/anular", data={"motivo": "Intento sin permiso de anulación"}, follow_redirects=True)
        self.assertIn("solo está disponible para el administrador", r.get_data(as_text=True))
        recibo = self.texto("/pagos/1")
        self.assertIn("Pagado", recibo)
        self.assertNotIn("Anular recibo", recibo)
        self.assertNotIn("Tarifas</a>", recibo)
        self.assertIn("$ 180.000", self.texto("/pagos/nuevo?placa=ABC123"))  # el operador sí consulta y cobra
        self.cliente.get("/logout")
        self.assertIn("/login", self.cliente.get("/pagos/").headers["Location"])

    def test_flujo_web_de_pagos(self):  # [CP-19]
        self.entrar()
        consulta = self.texto("/pagos/nuevo?placa=qrs234")
        self.assertIn("Vencida desde", consulta)
        self.assertIn("Carlos Pérez Duarte", consulta)
        r = self.cliente.post("/pagos/nuevo", data={"placa": "QRS234", "meses": "2", "medio": "TRANSFERENCIA",
                                                    "referencia": ""}, follow_redirects=True)
        self.assertIn("Escriba la referencia", r.get_data(as_text=True))
        r = self.cliente.post("/pagos/nuevo", data={"placa": "QRS234", "meses": "2", "medio": "TRANSFERENCIA",
                                                    "referencia": "trf556677"}, follow_redirects=True)
        recibo = r.get_data(as_text=True)
        for esperado in ("Pago registrado", "Recibo de pago", "$ 360.000", "Ref. TRF556677", "Pedro Operador"):
            self.assertIn(esperado, recibo)
        self.assertIn("Entrada registrada", self.cliente.post(
            "/entrada", data={"placa": "QRS234"}, follow_redirects=True).get_data(as_text=True))
        for ruta in ("/pagos/", "/pagos/nuevo", "/pagos/cartera", "/pagos/caja", "/pagos/6", "/clientes/2",
                     "/vehiculos/", "/pagos/?medio=TRANSFERENCIA&estado=VIGENTE&texto=QRS"):
            self.assertEqual(self.cliente.get(ruta).status_code, 200, ruta)
        self.assertEqual(self.cliente.get("/pagos/999").status_code, 404)
        self.assertIn("$ 360.000", self.texto("/pagos/caja"))
        self.assertIn("N.º 00006", self.texto("/clientes/2"))  # estado de cuenta del cliente
        self.assertIn("1 recibo(s)", self.texto("/pagos/?texto=TRF556677"))

        self.entrar("admin", "admin123")
        r = self.cliente.post("/pagos/tarifas", data={"tipo": "MOTO", "valor": "95000"}, follow_redirects=True)
        self.assertIn("actualizada a $ 95.000", r.get_data(as_text=True))
        r = self.cliente.post("/pagos/6/anular", data={"motivo": "corto"}, follow_redirects=True)
        self.assertIn("motivo de la anulación", r.get_data(as_text=True))
        r = self.cliente.post("/pagos/6/anular", data={"motivo": "Prueba de anulación con vehículo dentro"},
                              follow_redirects=True)
        self.assertIn("registre la salida antes de anular", r.get_data(as_text=True))
        self.cliente.post("/salida", data={"placa": "QRS234"})
        r = self.cliente.post("/pagos/6/anular", data={"motivo": "Transferencia devuelta por el banco"},
                              follow_redirects=True)
        anulado = r.get_data(as_text=True)
        for esperado in ("Recibo anulado", "Transferencia devuelta por el banco", "por Administrador"):
            self.assertIn(esperado, anulado)
        self.assertIn("Recaudo de todos los cajeros", self.texto("/pagos/caja"))

    def test_migracion_de_base_de_datos_de_la_iteracion_2(self):  # [CP-21]
        with closing(sqlite3.connect(self.ruta_bd)) as bd:
            bd.executescript("DROP TABLE pago; DROP TABLE tarifa;")  # así quedó la base en la iteración 2
        self.cliente = create_app({"TESTING": True, "DATABASE": self.ruta_bd}).test_client()
        with closing(sqlite3.connect(self.ruta_bd)) as bd:
            self.assertEqual(bd.execute("SELECT COUNT(*) FROM tarifa").fetchone()[0], 2)
            self.assertEqual(bd.execute("SELECT COUNT(*) FROM pago").fetchone()[0], 0)
            self.assertEqual(bd.execute("SELECT COUNT(*) FROM mensualidad").fetchone()[0], 5)
        self.entrar()
        self.assertIn("No hay pagos", self.texto("/pagos/"))
        r = self.cliente.post("/pagos/nuevo", data={"placa": "ABC123", "meses": "1", "medio": "EFECTIVO"},
                              follow_redirects=True)
        self.assertIn("Recibo N.º", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
