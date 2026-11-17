"""Consumo de la API de tipo de cambio (open.er-api.com, sin llave) y cálculo de pagos internacionales."""
import logging
import math
from dataclasses import dataclass

from excepciones.excepciones import ErrorServicioExterno, RespuestaInvalidaError, ValidacionError
from seguridad.validadores import validar_moneda

log = logging.getLogger("ecotech.servicios")
MONEDA_BASE = "CLP"        # los salarios del sistema se almacenan en pesos chilenos


@dataclass(frozen=True)
class TasaCambio:
    base: str
    destino: str
    tasa: float
    desde_cache: bool = False
    fecha_cache: str = ""


@dataclass(frozen=True)
class PagoInternacional:
    monto_base: float
    moneda_base: str
    monto_convertido: float
    moneda_destino: str
    tasa: TasaCambio


class ServicioTipoCambio:
    URL = "https://open.er-api.com/v6/latest/{base}"
    NOMBRE = "servicio de tipo de cambio"

    def __init__(self, cliente, sesion, repo=None):
        self._cliente, self._sesion, self._repo = cliente, sesion, repo

    def obtener_tasa(self, destino, base=MONEDA_BASE):
        self._sesion.exigir_autenticado()
        base, destino = validar_moneda(base), validar_moneda(destino)
        try:
            datos = self._cliente.get_json(self.URL.format(base=base), None, self.NOMBRE)
            tasa = self._extraer(datos, base, destino)
        except ErrorServicioExterno as e:
            respaldo = self._respaldo(base, destino) if e.recuperable else None
            if respaldo:
                return respaldo
            raise
        if self._repo:
            self._repo.guardar_tasa(base, destino, tasa.tasa)
        return tasa

    @staticmethod
    def _extraer(datos, base, destino):
        try:
            if datos["result"] != "success" or datos["base_code"] != base:
                raise ValueError
            valor = float(datos["rates"][destino])
        except (KeyError, TypeError, ValueError):
            log.error("Estructura inesperada en la respuesta de tipo de cambio")
            raise RespuestaInvalidaError("El servicio de tipo de cambio entregó datos incompletos.") from None
        if not math.isfinite(valor) or valor <= 0:
            raise RespuestaInvalidaError("El servicio de tipo de cambio entregó un valor inválido.")
        return TasaCambio(base, destino, valor)

    def _respaldo(self, base, destino):
        f = self._repo.ultima_tasa(base, destino) if self._repo else None
        return TasaCambio(base, destino, f["tasa"], True, f["consultado"]) if f else None

    def calcular_pago(self, monto_base, destino, base=MONEDA_BASE):
        """Convierte el salario (en moneda base) a la moneda del país donde se ejecuta el proyecto."""
        if isinstance(monto_base, bool) or not isinstance(monto_base, (int, float)) \
                or not math.isfinite(monto_base) or monto_base < 0:
            raise ValidacionError("El monto a convertir debe ser un número no negativo.")
        tasa = self.obtener_tasa(destino, base)
        return PagoInternacional(float(monto_base), tasa.base, round(monto_base * tasa.tasa, 2),
                                 tasa.destino, tasa)
