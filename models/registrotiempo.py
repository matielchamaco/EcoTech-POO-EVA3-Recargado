from models.entidadbase import EntidadBase
from abc import ABC, abstractmethod
from datetime import date, datetime

from excepciones.excepciones import ValidacionError

class RegistroTiempo(EntidadBase):
    MAX_HORAS = 24

    def __init__(self, id_emp, id_proy, horas, fecha, id_registro=None):
        self._id_registro = self._validar_id(id_registro, "id_registro")
        self._id_empleado = self._validar_id(id_emp, "id_empleado", obligatorio=True)
        self._id_proyecto = self._validar_id(id_proy, "id_proyecto", obligatorio=True)
        self.horas = horas
        self.fecha = fecha

    @property
    def id_registro(self):
        return self._id_registro

    @id_registro.setter
    def id_registro(self, valor):
        self._id_registro = self._validar_id(valor, "id_registro")

    @property
    def id_empleado(self):
        return self._id_empleado

    @property
    def id_proyecto(self):
        return self._id_proyecto

    @property
    def horas(self):
        return self._horas

    @horas.setter
    def horas(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValidacionError("Las horas deben ser un número.")
        if not self._horas_validas(valor):
            raise ValidacionError(f"Las horas deben estar entre 0 (exclusivo) y {self.MAX_HORAS}.")
        self._horas = float(valor)

    @property
    def fecha(self):
        return self._fecha

    @fecha.setter
    def fecha(self, valor):
        valor = self._validar_fecha(valor, "La fecha del registro")
        if valor > date.today():
            raise ValidacionError("La fecha del registro no puede ser futura.")
        self._fecha = valor

    @classmethod
    def _horas_validas(cls, valor) -> bool:
        return 0 < valor <= cls.MAX_HORAS

    def validar_rango_horas(self) -> bool:
        return self._horas_validas(self._horas)

    def __str__(self):
        return (f"[Registro {self._id_registro}] empleado {self._id_empleado} | "
                f"proyecto {self._id_proyecto} | {self._horas} h | {self._fecha.isoformat()}")