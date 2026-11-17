import math
import re
from models.entidadbase import EntidadBase

from excepciones.excepciones import ValidacionError

class Empleado(EntidadBase):
    _PATRON_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")

    def __init__(self, id_empleado, nombre, correo, salario, id_depto=None):
        self._id_empleado = self._validar_id(id_empleado, "id_empleado")
        self.nombre = nombre
        self.correo = correo
        self.salario = salario              # pasa por el setter -> se valida
        self._id_depto = self._validar_id(id_depto, "id_depto")

    @property
    def id_empleado(self):
        return self._id_empleado

    @id_empleado.setter
    def id_empleado(self, valor):
        self._id_empleado = self._validar_id(valor, "id_empleado")

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = self._validar_texto(valor, "El nombre del empleado")

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        valor = self._validar_texto(valor, "El correo", maximo=120).lower()
        if not self._PATRON_CORREO.match(valor):
            raise ValidacionError("El correo no tiene un formato válido.")
        self._correo = valor

    # __salario: atributo privado (name mangling -> _Empleado__salario), dato sensible (PII)
    @property
    def salario(self):
        return self.__salario

    @salario.setter
    def salario(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValidacionError("El salario debe ser un número.")
        if not math.isfinite(valor) or valor < 0:
            raise ValidacionError("El salario no puede ser negativo.")
        self.__salario = float(valor)

    @property
    def id_depto(self):
        return self._id_depto

    def asignar_a_depto(self, id_depto: int) -> bool:
        """Asigna el empleado a un departamento. Retorna False si ya pertenecía a él."""
        nuevo = self._validar_id(id_depto, "id_depto", obligatorio=True)
        if nuevo == self._id_depto:
            return False
        self._id_depto = nuevo
        return True

    def __str__(self):
        # Por seguridad (PII) la representación general NO incluye el salario.
        depto = self._id_depto if self._id_depto else "sin departamento"
        return f"[Empleado {self._id_empleado}] {self._nombre} <{self._correo}> (depto: {depto})"