from abc import ABC, abstractmethod
from datetime import date, datetime

from excepciones.excepciones import ValidacionError


class EntidadBase(ABC):
    """Clase abstracta con las validaciones reutilizables por todas las entidades.

    Evita duplicar código de validación en cada clase (criterio 2.1.2).
    """

    @staticmethod
    def _validar_id(valor, campo, obligatorio=False):
        if valor is None:
            if obligatorio:
                raise ValidacionError(f"{campo} es obligatorio.")
            return None
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ValidacionError(f"{campo} debe ser un entero positivo.")
        return valor

    @staticmethod
    def _validar_texto(valor, campo, maximo=100):
        if not isinstance(valor, str):
            raise ValidacionError(f"{campo} debe ser texto.")
        valor = valor.strip()
        if not valor:
            raise ValidacionError(f"{campo} no puede estar vacío.")
        if len(valor) > maximo:
            raise ValidacionError(f"{campo} no puede superar {maximo} caracteres.")
        return valor

    @staticmethod
    def _validar_fecha(valor, campo):
        if isinstance(valor, datetime):      # datetime es subclase de date: va primero
            return valor.date()
        if isinstance(valor, date):
            return valor
        if isinstance(valor, str):
            try:
                return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise ValidacionError(
                    f"{campo} debe ser una fecha válida con formato AAAA-MM-DD."
                ) from None
        raise ValidacionError(f"{campo} debe ser una fecha.")

    @abstractmethod
    def __str__(self) -> str:
        """Cada entidad define su representación legible."""