"""Autenticación con contraseñas cifradas (hash) y control de sesión.

- Contraseñas: PBKDF2-HMAC-SHA256 (hashlib, biblioteca estándar) con sal aleatoria única por
  usuario e iteraciones configurables. Jamás se guarda la contraseña en texto plano.
- Comparación en tiempo constante (hmac.compare_digest) para evitar ataques de temporización.
- Mensaje de error genérico: no revela si falló el usuario o la contraseña.
- Sesión con vencimiento por inactividad; los servicios externos la exigen en cada llamada.
"""
import hashlib
import hmac
import logging
import os
import secrets
import time

from excepciones.excepciones import ErrorAutenticacion, ErrorBaseDatos, ValidacionError
from seguridad.validadores import (validar_password_ingresada, validar_password_nueva,
                                   validar_usuario)

log = logging.getLogger("ecotech.seguridad")

ITERACIONES = 600_000          # recomendación OWASP para PBKDF2-HMAC-SHA256
_MENSAJE_LOGIN = "Usuario o contraseña incorrectos."


def hashear_password(password, sal=None, iteraciones=ITERACIONES):
    sal = sal if sal is not None else os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, iteraciones)
    return sal.hex(), h.hex(), iteraciones


def verificar_password(password, sal_hex, hash_hex, iteraciones):
    _, calculado, _ = hashear_password(password, bytes.fromhex(sal_hex), iteraciones)
    return hmac.compare_digest(calculado, hash_hex)


class Sesion:
    """Estado de autenticación. Sin usuario => no autenticada."""
    INACTIVIDAD_MAX = 15 * 60  # segundos

    def __init__(self, usuario=None, inactividad_max=None):
        self._usuario = usuario
        self._token = secrets.token_hex(16) if usuario else None
        self._max = inactividad_max or self.INACTIVIDAD_MAX
        self._ultimo = time.monotonic()

    @property
    def autenticado(self):
        return self._usuario is not None and (time.monotonic() - self._ultimo) <= self._max

    @property
    def usuario(self):
        return self._usuario

    def exigir_autenticado(self):
        """Punto único de control de acceso: se invoca antes de cada operación sensible."""
        if self._usuario is not None and not self.autenticado:
            log.warning("Sesión de '%s' expirada por inactividad", self._usuario)
            self.cerrar()
            raise ErrorAutenticacion("Su sesión expiró por inactividad. Inicie sesión nuevamente.")
        if not self.autenticado:
            raise ErrorAutenticacion("Debe iniciar sesión para usar esta función.")
        self._ultimo = time.monotonic()

    def cerrar(self):
        self._usuario = None
        self._token = None


class ServicioAutenticacion:
    MAX_INTENTOS = 3

    def __init__(self, conexion):
        self._conexion = conexion

    def hay_usuarios(self):
        with self._conexion.cursor() as cur:
            return cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] > 0

    def registrar(self, usuario, password):
        usuario = validar_usuario(usuario)
        validar_password_nueva(password)
        sal, h, it = hashear_password(password)
        try:
            with self._conexion.cursor() as cur:
                cur.execute("INSERT INTO usuarios (usuario, sal, hash, iteraciones) VALUES (?, ?, ?, ?)",
                            (usuario.lower(), sal, h, it))
        except ErrorBaseDatos:
            raise ValidacionError("No se pudo crear el usuario (¿ya existe?).") from None
        log.warning("Usuario '%s' creado", usuario.lower())

    def autenticar(self, usuario, password):
        """Devuelve una Sesion o lanza ErrorAutenticacion (mensaje siempre genérico)."""
        try:
            usuario = validar_usuario(usuario).lower()
            validar_password_ingresada(password)
        except ValidacionError:
            raise ErrorAutenticacion(_MENSAJE_LOGIN) from None
        with self._conexion.cursor() as cur:
            fila = cur.execute("SELECT sal, hash, iteraciones FROM usuarios WHERE usuario = ?",
                               (usuario,)).fetchone()
        if fila is None:
            hashear_password(password)       # costo equivalente: no delata usuarios inexistentes
            ok = False
        else:
            ok = verificar_password(password, fila["sal"], fila["hash"], fila["iteraciones"])
        if not ok:
            log.warning("Intento de login fallido para '%s'", usuario)
            raise ErrorAutenticacion(_MENSAJE_LOGIN)
        log.warning("Login correcto de '%s'", usuario)
        return Sesion(usuario)
