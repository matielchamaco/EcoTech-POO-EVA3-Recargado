"""Pruebas de la Unidad 3 (sin red: la API se simula con unittest.mock). Ejecutar: python -m unittest -v"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock

import requests

from config.base_datos import ConexionBD
from config.entorno import obtener_api_key
from excepciones.excepciones import (ErrorAutenticacion, ErrorConexionExterna, ErrorConfiguracion,
                                     ErrorServicioExterno, RecursoExternoNoEncontrado,
                                     RespuestaInvalidaError, TimeoutExterno, ValidacionError)
from seguridad.autenticacion import ServicioAutenticacion, Sesion, hashear_password
from seguridad.validadores import validar_ciudad, validar_moneda, validar_password_nueva
from services.clima_service import ServicioClima
from services.cliente_http import ClienteHTTP
from services.consultas_repo import ConsultasExternasRepo
from services.tipo_cambio_service import ServicioTipoCambio


def respuesta(codigo=200, json_=None, json_error=False):
    r = MagicMock()
    r.status_code = codigo
    if json_error:
        r.json.side_effect = ValueError("no json")
    else:
        r.json.return_value = json_
    return r


CLIMA_OK = {"name": "Chillán", "sys": {"country": "CL"}, "main": {"temp": 18.5, "humidity": 60},
            "weather": [{"id": 800, "description": "cielo claro"}]}
CAMBIO_OK = {"result": "success", "base_code": "CLP", "rates": {"USD": 0.00105, "EUR": 0.00097}}


class PruebasValidacion(unittest.TestCase):
    def test_ciudad(self):
        self.assertEqual(validar_ciudad("  Chillán "), "Chillán")
        for malo in ("", "   ", "Lima; DROP TABLE", "a", "Santiago&appid=x", "../etc", "Ci\x00udad", "x" * 61, 123):
            with self.assertRaises(ValidacionError, msg=repr(malo)):
                validar_ciudad(malo)

    def test_moneda(self):
        self.assertEqual(validar_moneda(" usd "), "USD")
        for malo in ("", "XXX", "US", "USD/../", "DOLAR"):
            with self.assertRaises(ValidacionError):
                validar_moneda(malo)

    def test_password_nueva(self):
        validar_password_nueva("Clave1234")
        for malo in ("corta1", "sololetrasaaa", "12345678", ""):
            with self.assertRaises(ValidacionError):
                validar_password_nueva(malo)


class PruebasAutenticacion(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.bd = ConexionBD(os.path.join(self._dir.name, "t.db"))
        self.bd.crear_tablas()
        self.auth = ServicioAutenticacion(self.bd)

    def tearDown(self):
        self._dir.cleanup()

    def test_password_no_se_guarda_en_texto_plano(self):
        self.auth.registrar("admin", "Clave1234")
        with self.bd.cursor() as cur:
            fila = cur.execute("SELECT * FROM usuarios").fetchone()
        self.assertNotIn("Clave1234", tuple(fila))
        self.assertEqual(len(fila["hash"]), 64)

    def test_sal_distinta_por_usuario(self):
        self.assertNotEqual(hashear_password("Clave1234")[0], hashear_password("Clave1234")[0])

    def test_login_correcto_e_incorrecto(self):
        self.auth.registrar("admin", "Clave1234")
        self.assertTrue(self.auth.autenticar("ADMIN", "Clave1234").autenticado)
        for u, p in (("admin", "mala"), ("nadie", "Clave1234"), ("", ""), ("admin", "")):
            with self.assertRaises(ErrorAutenticacion) as ctx:
                self.auth.autenticar(u, p)
            self.assertEqual(str(ctx.exception), "Usuario o contraseña incorrectos.")

    def test_usuario_duplicado(self):
        self.auth.registrar("admin", "Clave1234")
        with self.assertRaises(ValidacionError):
            self.auth.registrar("admin", "Otra12345")

    def test_inyeccion_sql_en_login(self):
        self.auth.registrar("admin", "Clave1234")
        with self.assertRaises(ErrorAutenticacion):
            self.auth.autenticar("admin' OR '1'='1", "x")

    def test_sesion_expirada_y_cerrada(self):
        s = Sesion("admin", inactividad_max=-1)
        with self.assertRaises(ErrorAutenticacion):
            s.exigir_autenticado()
        with self.assertRaises(ErrorAutenticacion):
            Sesion().exigir_autenticado()


class PruebasClienteHTTP(unittest.TestCase):
    def cliente(self, resp=None, error=None):
        http = MagicMock()
        if error:
            http.get.side_effect = error
        else:
            http.get.return_value = resp
        return ClienteHTTP(sesion_http=http)

    def test_ok(self):
        self.assertEqual(self.cliente(respuesta(200, {"a": 1})).get_json("https://x.cl/api"), {"a": 1})

    def test_codigos_http(self):
        casos = {404: RecursoExternoNoEncontrado, 401: ErrorServicioExterno, 403: ErrorServicioExterno,
                 429: ErrorServicioExterno, 500: ErrorServicioExterno, 503: ErrorServicioExterno,
                 418: ErrorServicioExterno}
        for codigo, exc in casos.items():
            with self.assertRaises(exc, msg=codigo):
                self.cliente(respuesta(codigo, {})).get_json("https://x.cl/api")

    def test_errores_de_red(self):
        with self.assertRaises(TimeoutExterno):
            self.cliente(error=requests.exceptions.Timeout()).get_json("https://x.cl")
        with self.assertRaises(ErrorConexionExterna):
            self.cliente(error=requests.exceptions.ConnectionError()).get_json("https://x.cl")
        with self.assertRaises(ErrorServicioExterno):
            self.cliente(error=requests.exceptions.RequestException()).get_json("https://x.cl")

    def test_json_invalido_y_no_objeto(self):
        with self.assertRaises(RespuestaInvalidaError):
            self.cliente(respuesta(json_error=True)).get_json("https://x.cl")
        with self.assertRaises(RespuestaInvalidaError):
            self.cliente(respuesta(200, [1, 2])).get_json("https://x.cl")

    def test_rechaza_http_sin_cifrar(self):
        with self.assertRaises(ErrorServicioExterno):
            self.cliente(respuesta(200, {})).get_json("http://inseguro.cl")

    def test_mensaje_no_expone_la_llave(self):
        err = requests.exceptions.ConnectionError("HTTPSConnectionPool url=...?appid=SECRETO123456789012")
        with self.assertRaises(ErrorConexionExterna) as ctx:
            self.cliente(error=err).get_json("https://x.cl?appid=SECRETO123456789012")
        self.assertNotIn("SECRETO", str(ctx.exception))


class PruebasServicios(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.bd = ConexionBD(os.path.join(self._dir.name, "t.db"))
        self.bd.crear_tablas()
        self.repo = ConsultasExternasRepo(self.bd)
        self.cliente = MagicMock()
        self.sesion = Sesion("admin")
        self.clima = ServicioClima(self.cliente, self.sesion, self.repo)
        self.cambio = ServicioTipoCambio(self.cliente, self.sesion, self.repo)
        os.environ["OPENWEATHER_API_KEY"] = "abcdef0123456789abcdef0123456789"

    def tearDown(self):
        os.environ.pop("OPENWEATHER_API_KEY", None)
        self._dir.cleanup()

    def test_clima_ok_y_persistido(self):
        self.cliente.get_json.return_value = CLIMA_OK
        c = self.clima.obtener_clima("Chillán")
        self.assertEqual((c.temperatura, c.humedad, c.pais), (18.5, 60.0, "CL"))
        self.assertIsNotNone(self.repo.ultimo_clima("chillán"))
        self.assertEqual(self.clima.evaluar_riesgo(c)[0], "BAJO")

    def test_requiere_autenticacion(self):
        sin = ServicioClima(self.cliente, Sesion(), self.repo)
        with self.assertRaises(ErrorAutenticacion):
            sin.obtener_clima("Chillán")
        self.cliente.get_json.assert_not_called()          # ni siquiera se llama a la API

    def test_entrada_invalida_no_llega_a_la_api(self):
        with self.assertRaises(ValidacionError):
            self.clima.obtener_clima("Lima&appid=x")
        self.cliente.get_json.assert_not_called()

    def test_clima_respuesta_incompleta_o_fuera_de_rango(self):
        self.cliente.get_json.return_value = {"name": "X"}
        with self.assertRaises(RespuestaInvalidaError):
            self.clima.obtener_clima("Chillán")
        malo = dict(CLIMA_OK, main={"temp": 999, "humidity": 60})
        self.cliente.get_json.return_value = malo
        with self.assertRaises(RespuestaInvalidaError):
            self.clima.obtener_clima("Chillán")

    def test_falta_llave(self):
        os.environ.pop("OPENWEATHER_API_KEY")
        with self.assertRaises(ErrorConfiguracion):
            self.clima.obtener_clima("Chillán")

    def test_llave_con_formato_invalido_no_se_revela(self):
        os.environ["OPENWEATHER_API_KEY"] = "corta!"
        with self.assertRaises(ErrorConfiguracion) as ctx:
            obtener_api_key("OPENWEATHER_API_KEY")
        self.assertNotIn("corta", str(ctx.exception))

    def test_clima_usa_respaldo_si_falla_la_red(self):
        self.cliente.get_json.return_value = CLIMA_OK
        self.clima.obtener_clima("Chillán")
        self.cliente.get_json.side_effect = TimeoutExterno("lento")
        c = self.clima.obtener_clima("Chillán")
        self.assertTrue(c.desde_cache)

    def test_clima_sin_respaldo_propaga_error_controlado(self):
        self.cliente.get_json.side_effect = ErrorConexionExterna("sin red")
        with self.assertRaises(ErrorConexionExterna):
            self.clima.obtener_clima("Temuco")

    def test_ciudad_inexistente_no_usa_respaldo(self):
        self.cliente.get_json.return_value = CLIMA_OK
        self.clima.obtener_clima("Chillán")
        self.cliente.get_json.side_effect = RecursoExternoNoEncontrado("no existe")
        with self.assertRaises(RecursoExternoNoEncontrado):
            self.clima.obtener_clima("Chillán")

    def test_riesgo_tormenta_y_temperatura(self):
        self.cliente.get_json.return_value = dict(CLIMA_OK, weather=[{"id": 211, "description": "tormenta"}])
        self.assertEqual(self.clima.evaluar_riesgo(self.clima.obtener_clima("Chillán"))[0], "ALTO")

    def test_pago_internacional(self):
        self.cliente.get_json.return_value = CAMBIO_OK
        pago = self.cambio.calcular_pago(1_500_000, "usd")
        self.assertAlmostEqual(pago.monto_convertido, 1575.0, places=2)
        self.assertIsNotNone(self.repo.ultima_tasa("CLP", "USD"))

    def test_pago_rechaza_montos_y_monedas_invalidos(self):
        for monto in (-1, "mucho", float("nan"), True):
            with self.assertRaises(ValidacionError):
                self.cambio.calcular_pago(monto, "USD")
        with self.assertRaises(ValidacionError):
            self.cambio.calcular_pago(1000, "XXX")

    def test_cambio_respuesta_invalida(self):
        for malo in ({"result": "error"}, {"result": "success", "base_code": "CLP", "rates": {"USD": -3}},
                     {"result": "success", "base_code": "CLP", "rates": {}}):
            self.cliente.get_json.return_value = malo
            with self.assertRaises(RespuestaInvalidaError):
                self.cambio.obtener_tasa("USD")

    def test_cambio_usa_respaldo(self):
        self.cliente.get_json.return_value = CAMBIO_OK
        self.cambio.obtener_tasa("EUR")
        self.cliente.get_json.side_effect = ErrorConexionExterna("sin red")
        t = self.cambio.obtener_tasa("EUR")
        self.assertTrue(t.desde_cache)
        self.assertAlmostEqual(t.tasa, 0.00097)


if __name__ == "__main__":
    unittest.main()
