"""Flujo de acceso por consola: primer uso (crear administrador) e inicio de sesión."""
from getpass import getpass
import sys

from excepciones.excepciones import ErrorAutenticacion, ErrorBaseDatos, ValidacionError
from seguridad.autenticacion import ServicioAutenticacion


def _leer(texto, secreto=False):
    if not secreto:
        return input(texto)
    if sys.stdin.isatty():
        return getpass(texto)          # terminal real: la clave no se muestra
    print("  (Aviso: este entorno no puede ocultar la contraseña; se verá al escribir)")
    return input(texto)


def _crear_primer_usuario(auth: ServicioAutenticacion):
    print("\nPrimer uso: cree el usuario administrador del sistema.")
    print("(La contraseña: 8-128 caracteres, con al menos una letra y un número.)")
    while True:
        try:
            usuario = _leer("Nuevo usuario: ")
            clave = _leer("Nueva contraseña: ", True)
            if clave != _leer("Repita la contraseña: ", True):
                print("  [Error] Las contraseñas no coinciden.")
                continue
            auth.registrar(usuario, clave)
            print("  Usuario creado correctamente.")
            return
        except ValidacionError as e:
            print(f"  [Error] {e}")


def iniciar_sesion(auth: ServicioAutenticacion):
    """Retorna una Sesion autenticada, o None si se agotan los intentos o se cancela."""
    try:
        if not auth.hay_usuarios():
            _crear_primer_usuario(auth)
        print("\n===== EcoTech Solutions - Inicio de sesión =====")
        for intento in range(1, auth.MAX_INTENTOS + 1):
            try:
                return auth.autenticar(_leer("Usuario: "), _leer("Contraseña: ", True))
            except ErrorAutenticacion as e:
                restantes = auth.MAX_INTENTOS - intento
                print(f"  [Error] {e}" + (f" Intentos restantes: {restantes}." if restantes else ""))
        print("  Acceso bloqueado: demasiados intentos fallidos.")
    except (KeyboardInterrupt, EOFError):
        print("\n  Inicio de sesión cancelado.")
    except ErrorBaseDatos as e:
        print(f"  [Error] {e}")
    return None
