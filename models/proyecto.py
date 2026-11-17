import math
import re
from models.entidadbase import EntidadBase

class Proyecto(EntidadBase):
    def __init__(self, id_proyecto, nombre, fecha_inicio, empleados=None):
        self._id_proyecto = self._validar_id(id_proyecto, "id_proyecto")
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self._empleados = set()             # ids de empleados asignados (asociación 1..* - 0..*)
        for id_emp in empleados or ():
            self.asignar_empleado(id_emp)

    @property
    def id_proyecto(self):
        return self._id_proyecto

    @id_proyecto.setter
    def id_proyecto(self, valor):
        self._id_proyecto = self._validar_id(valor, "id_proyecto")

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = self._validar_texto(valor, "El nombre del proyecto")

    @property
    def fecha_inicio(self):
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor):
        self._fecha_inicio = self._validar_fecha(valor, "La fecha de inicio")

    @property
    def empleados_asignados(self):
        """Copia inmutable: la colección interna no se puede modificar desde afuera."""
        return tuple(sorted(self._empleados))

    def asignar_empleado(self, id_emp: int) -> bool:
        id_emp = self._validar_id(id_emp, "id_empleado", obligatorio=True)
        if id_emp in self._empleados:
            return False
        self._empleados.add(id_emp)
        return True

    def desasignar_empleado(self, id_emp: int) -> bool:
        id_emp = self._validar_id(id_emp, "id_empleado", obligatorio=True)
        if id_emp not in self._empleados:
            return False
        self._empleados.remove(id_emp)
        return True

    def __str__(self):
        emps = ", ".join(map(str, self.empleados_asignados)) or "ninguno"
        return (f"[Proyecto {self._id_proyecto}] {self._nombre} "
                f"(inicio: {self._fecha_inicio.isoformat()}; empleados: {emps})")