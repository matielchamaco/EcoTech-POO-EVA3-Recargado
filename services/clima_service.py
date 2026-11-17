"""Consumo de la API de clima OpenWeatherMap (requiere llave: OPENWEATHER_API_KEY en .env)."""
import logging
import math
from dataclasses import dataclass

from config.entorno import obtener_api_key
from excepciones.excepciones import ErrorServicioExterno, RespuestaInvalidaError
from seguridad.validadores import validar_ciudad

log = logging.getLogger("ecotech.servicios")


@dataclass(frozen=True)
class Clima:
    ciudad: str
    pais: str
    temperatura: float          # °C
    humedad: float              # %
    descripcion: str
    codigo_condicion: int       # id OpenWeather: 2xx tormenta, 5xx lluvia, 6xx nieve, 800 despejado...
    desde_cache: bool = False
    fecha_cache: str = ""


class ServicioClima:
    URL = "https://api.openweathermap.org/data/2.5/weather"
    NOMBRE = "servicio de clima"

    def __init__(self, cliente, sesion, repo=None):
        self._cliente, self._sesion, self._repo = cliente, sesion, repo

    def obtener_clima(self, ciudad):
        self._sesion.exigir_autenticado()                    # 1) solo usuarios autenticados
        ciudad = validar_ciudad(ciudad)                      # 2) entrada validada (lista blanca)
        llave = obtener_api_key("OPENWEATHER_API_KEY")       # 3) llave desde entorno, nunca en el código
        params = {"q": ciudad, "appid": llave, "units": "metric", "lang": "es"}
        try:
            datos = self._cliente.get_json(self.URL, params, self.NOMBRE)
            clima = self._extraer(datos)
        except ErrorServicioExterno as e:
            respaldo = self._respaldo(ciudad) if e.recuperable else None
            if respaldo:
                return respaldo                              # continuidad operativa con el último dato
            raise
        if self._repo:
            self._repo.guardar_clima(clima)
        return clima

    @staticmethod
    def _extraer(datos):
        """Selecciona solo lo necesario y verifica tipos y rangos antes de usar el dato."""
        try:
            temp = float(datos["main"]["temp"])
            hum = float(datos["main"]["humidity"])
            cond = datos["weather"][0]
            clima = Clima(ciudad=str(datos["name"])[:60], pais=str(datos.get("sys", {}).get("country", ""))[:2],
                          temperatura=temp, humedad=hum, descripcion=str(cond["description"])[:80],
                          codigo_condicion=int(cond["id"]))
        except (KeyError, IndexError, TypeError, ValueError):
            log.error("Estructura inesperada en la respuesta del clima")
            raise RespuestaInvalidaError("El servicio de clima entregó datos incompletos.") from None
        if not (math.isfinite(temp) and -90 <= temp <= 60 and math.isfinite(hum) and 0 <= hum <= 100):
            raise RespuestaInvalidaError("El servicio de clima entregó valores fuera de rango.")
        return clima

    def _respaldo(self, ciudad):
        if not self._repo:
            return None
        f = self._repo.ultimo_clima(ciudad)
        if not f:
            return None
        return Clima(f["ciudad"].title(), f["pais"] or "", f["temperatura"], f["humedad"], f["descripcion"],
                     f["codigo"], desde_cache=True, fecha_cache=f["consultado"])

    @staticmethod
    def evaluar_riesgo(c: Clima):
        """Apoyo a la decisión: devuelve (nivel, recomendación) para planificar actividades."""
        if 200 <= c.codigo_condicion < 300 or c.codigo_condicion in (781, 771):
            return "ALTO", "Tormenta o fenómeno severo: posponer trabajos en terreno."
        if c.temperatura >= 35 or c.temperatura <= 0:
            return "ALTO", "Temperatura extrema: reprogramar o reforzar medidas de seguridad."
        if 500 <= c.codigo_condicion < 700 or c.humedad >= 90:
            return "MEDIO", "Lluvia, nieve o humedad muy alta: considerar ajustar actividades al aire libre."
        return "BAJO", "Condiciones favorables para ejecutar actividades en terreno."
