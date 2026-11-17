"""Cliente HTTP común para consumir APIs externas con la librería oficial `requests`.

Responsabilidades (criterios 3.1.1 y 3.1.3):
- Solo HTTPS, timeout explícito (conexión, lectura) y reintentos acotados ante 429/5xx.
- Traducir cada fallo (red, timeout, código HTTP, JSON inválido) a una excepción propia.
- Los mensajes al usuario NO contienen URL, parámetros ni llaves: requests incluye la URL
  completa (con `appid=...`) en sus excepciones, por eso se registra solo la URL sin query.
"""
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from excepciones.excepciones import (ErrorConexionExterna, ErrorServicioExterno,
                                     RecursoExternoNoEncontrado, RespuestaInvalidaError,
                                     TimeoutExterno)

log = logging.getLogger("ecotech.servicios")


class ClienteHTTP:
    def __init__(self, timeout=(3.05, 8), reintentos=2, sesion_http=None):
        self._timeout = timeout                       # (conexión, lectura) en segundos
        if sesion_http is None:
            sesion_http = requests.Session()
            retry = Retry(total=reintentos, backoff_factor=0.5, status_forcelist=(429, 502, 503, 504),
                          allowed_methods=("GET",), raise_on_status=False)
            sesion_http.mount("https://", HTTPAdapter(max_retries=retry))
        self._http = sesion_http

    def get_json(self, url, params=None, servicio="servicio externo"):
        if not url.lower().startswith("https://"):
            raise ErrorServicioExterno("Solo se permiten conexiones seguras (HTTPS).", recuperable=False)
        url_log = url.split("?")[0]                   # sin parámetros: pueden contener la llave
        try:
            resp = self._http.get(url, params=params, timeout=self._timeout)
        except requests.exceptions.Timeout:
            log.error("Timeout consultando %s (%s)", servicio, url_log)
            raise TimeoutExterno(f"El {servicio} tardó demasiado en responder. Intente más tarde.") from None
        except requests.exceptions.ConnectionError:
            log.error("Sin conexión con %s (%s)", servicio, url_log)
            raise ErrorConexionExterna(f"No hay conexión con el {servicio}. Revise su red.") from None
        except requests.exceptions.RequestException as e:
            log.error("Fallo de solicitud a %s (%s): %s", servicio, url_log, type(e).__name__)
            raise ErrorServicioExterno(f"No se pudo consultar el {servicio}.") from None

        self._validar_estado(resp, servicio, url_log)

        try:
            datos = resp.json()
        except ValueError:
            log.error("Respuesta no JSON de %s (%s)", servicio, url_log)
            raise RespuestaInvalidaError(f"El {servicio} entregó una respuesta no válida.") from None
        if not isinstance(datos, dict):
            raise RespuestaInvalidaError(f"El {servicio} entregó una respuesta inesperada.")
        return datos

    @staticmethod
    def _validar_estado(resp, servicio, url_log):
        codigo = resp.status_code
        if codigo == 200:
            return
        log.error("HTTP %s desde %s (%s)", codigo, servicio, url_log)
        if codigo == 404:
            raise RecursoExternoNoEncontrado("No se encontró el recurso solicitado (revise ciudad o moneda).")
        if codigo in (401, 403):
            raise ErrorServicioExterno(f"El {servicio} rechazó la autorización. Contacte al administrador.",
                                       recuperable=False)
        if codigo == 400:
            raise ErrorServicioExterno(f"El {servicio} no aceptó la consulta enviada.", recuperable=False)
        if codigo == 429:
            raise ErrorServicioExterno(f"Se superó el límite de consultas del {servicio}. Espere un momento.")
        if 500 <= codigo <= 599:
            raise ErrorServicioExterno(f"El {servicio} no está disponible en este momento.")
        raise ErrorServicioExterno(f"El {servicio} respondió con un estado inesperado ({codigo}).")
