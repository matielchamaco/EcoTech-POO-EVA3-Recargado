"""Excepciones propias del sistema EcoTech Solutions.

Tener una jerarquía propia permite capturar con precisión cada tipo de falla
(criterio 2.1.4) en lugar de usar un 'except Exception' genérico.
"""


class ErrorEcoTech(Exception):
    """Clase base de todas las excepciones del sistema."""


class ValidacionError(ErrorEcoTech):
    """Un dato ingresado no cumple las reglas del dominio."""


class RegistroNoEncontradoError(ErrorEcoTech):
    """No existe un registro con el identificador solicitado."""


class ErrorBaseDatos(ErrorEcoTech):
    """Falla de conexión, consulta o restricción en la base de datos."""


# ---------- Unidad 3: seguridad y servicios externos ----------
class ErrorAutenticacion(ErrorEcoTech):
    """Credenciales inválidas, cuenta bloqueada o sesión inexistente/expirada."""


class ErrorConfiguracion(ErrorEcoTech):
    """Falta o es inválida una variable de entorno (p. ej. la llave de una API)."""


class ErrorServicioExterno(ErrorEcoTech):
    """Falla al consumir una API externa. El mensaje es SIEMPRE apto para el usuario final
    (nunca incluye URLs, llaves ni trazas); el detalle técnico va al log.

    recuperable=True indica que tiene sentido reintentar más tarde o usar datos en caché.
    """

    def __init__(self, mensaje, recuperable=True):
        super().__init__(mensaje)
        self.recuperable = recuperable


class ErrorConexionExterna(ErrorServicioExterno):
    """No hay conectividad con el servicio (DNS, red caída, conexión rechazada)."""


class TimeoutExterno(ErrorServicioExterno):
    """El servicio no respondió dentro del tiempo máximo configurado."""


class RecursoExternoNoEncontrado(ErrorServicioExterno):
    """HTTP 404: el recurso consultado (ciudad, moneda) no existe en el servicio."""

    def __init__(self, mensaje):
        super().__init__(mensaje, recuperable=False)


class RespuestaInvalidaError(ErrorServicioExterno):
    """La respuesta no es JSON o no tiene la estructura/valores esperados."""

    def __init__(self, mensaje):
        super().__init__(mensaje, recuperable=False)
