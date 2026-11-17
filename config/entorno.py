"""Gestión de información sensible (llaves de API) fuera del código fuente.

- Las llaves se leen de variables de entorno; si existe un archivo .env local (excluido de Git)
  se cargan desde ahí. Una variable ya definida en el sistema operativo tiene prioridad.
- Nunca se imprime ni se registra el VALOR de una llave, solo el NOMBRE de la variable.
"""
import os
import re
from pathlib import Path

from excepciones.excepciones import ErrorConfiguracion

_RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"


def cargar_env(ruta=_RUTA_ENV):
    """Carga pares CLAVE=valor de un .env simple (sin dependencias externas)."""
    try:
        if not Path(ruta).is_file():
            return
        lineas = Path(ruta).read_text(encoding="utf-8").splitlines()
    except OSError:
        return                                   # sin .env legible: se usarán solo variables del SO
    for linea in lineas:
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def obtener_api_key(nombre, patron=r"[A-Za-z0-9]{16,64}"):
    """Entrega la llave validada o lanza ErrorConfiguracion sin revelar su valor."""
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        raise ErrorConfiguracion(f"Falta configurar la variable {nombre} (ver .env.example).")
    if not re.fullmatch(patron, valor):
        raise ErrorConfiguracion(f"La variable {nombre} tiene un formato inválido.")
    return valor
