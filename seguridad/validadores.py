"""Validación y saneamiento de entradas del usuario (lista blanca, no lista negra).

Todo dato que termina en una URL, una consulta o la base de datos pasa primero por aquí.
"""
import re
import unicodedata

from excepciones.excepciones import ValidacionError

# Monedas permitidas para pagos internacionales (código ISO 4217 -> país/zona).
MONEDAS_SOPORTADAS = {
    "CLP": "Chile", "USD": "Estados Unidos", "EUR": "Eurozona", "ARS": "Argentina",
    "PEN": "Perú", "COP": "Colombia", "MXN": "México", "BRL": "Brasil", "UYU": "Uruguay",
}

_LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
_PATRON_CIUDAD = re.compile(rf"[{_LETRAS}][{_LETRAS} .'\-]{{1,59}}")
_PATRON_USUARIO = re.compile(r"[A-Za-z0-9_.\-]{3,30}")


def _limpiar(valor, campo, maximo):
    """Exige texto, normaliza Unicode, quita espacios y rechaza caracteres de control."""
    if not isinstance(valor, str):
        raise ValidacionError(f"{campo} debe ser texto.")
    valor = unicodedata.normalize("NFC", valor).strip()
    if not valor:
        raise ValidacionError(f"{campo} no puede estar vacío.")
    if len(valor) > maximo:
        raise ValidacionError(f"{campo} no puede superar {maximo} caracteres.")
    if any(unicodedata.category(c).startswith("C") for c in valor):
        raise ValidacionError(f"{campo} contiene caracteres no permitidos.")
    return valor


def validar_ciudad(valor):
    valor = _limpiar(valor, "La ciudad", 60)
    if not _PATRON_CIUDAD.fullmatch(valor):
        raise ValidacionError("La ciudad solo puede contener letras, espacios, punto, apóstrofo y guion.")
    return valor


def validar_moneda(valor):
    valor = _limpiar(valor, "La moneda", 3).upper()
    if valor not in MONEDAS_SOPORTADAS:
        raise ValidacionError("Moneda no soportada. Opciones: " + ", ".join(MONEDAS_SOPORTADAS) + ".")
    return valor


def validar_usuario(valor):
    valor = _limpiar(valor, "El usuario", 30)
    if not _PATRON_USUARIO.fullmatch(valor):
        raise ValidacionError("El usuario debe tener 3-30 caracteres: letras, números, '_', '.' o '-'.")
    return valor


def validar_password_nueva(valor):
    """Política mínima para contraseñas NUEVAS (no se recorta ni se normaliza la contraseña)."""
    if not isinstance(valor, str) or not (8 <= len(valor) <= 128):
        raise ValidacionError("La contraseña debe tener entre 8 y 128 caracteres.")
    if not (re.search(r"[A-Za-z]", valor) and re.search(r"\d", valor)):
        raise ValidacionError("La contraseña debe incluir al menos una letra y un número.")
    return valor


def validar_password_ingresada(valor):
    """Para el login: solo evita valores vacíos o absurdamente largos (DoS por hashing)."""
    if not isinstance(valor, str) or not valor or len(valor) > 128:
        raise ValidacionError("Credenciales incorrectas.")
    return valor
