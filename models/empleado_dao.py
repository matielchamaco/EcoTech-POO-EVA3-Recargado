from abc import ABC, abstractmethod

from config.base_datos import ConexionBD
from excepciones.excepciones import RegistroNoEncontradoError, ValidacionError
from models.empleado import Empleado
from models.entidadbase_dao import RepositorioBase

class EmpleadoDAO(RepositorioBase):
    _NOMBRE_ENTIDAD = "Empleado"

    @staticmethod
    def _a_objeto(fila):
        return Empleado(fila["id_empleado"], fila["nombre"], fila["correo"],
                        fila["salario"], fila["id_depto"])

    def crear(self, e: Empleado):
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO empleados (id_empleado, nombre, correo, salario, id_depto) "
            "VALUES (?, ?, ?, ?, ?)",
            (e.id_empleado, e.nombre, e.correo, e.salario, e.id_depto))
        e.id_empleado = nuevo_id
        return e

    def obtener(self, id_empleado):
        filas = self._consultar("SELECT * FROM empleados WHERE id_empleado = ?", (id_empleado,))
        if not filas:
            raise self._no_encontrado(id_empleado)
        return self._a_objeto(filas[0])

    def listar(self):
        return [self._a_objeto(f) for f in self._consultar("SELECT * FROM empleados ORDER BY id_empleado")]

    def actualizar(self, e: Empleado):
        _, afectadas = self._ejecutar(
            "UPDATE empleados SET nombre = ?, correo = ?, salario = ?, id_depto = ? "
            "WHERE id_empleado = ?",
            (e.nombre, e.correo, e.salario, e.id_depto, e.id_empleado))
        if afectadas == 0:
            raise self._no_encontrado(e.id_empleado)
        return e

    def eliminar(self, id_empleado):
        _, afectadas = self._ejecutar("DELETE FROM empleados WHERE id_empleado = ?", (id_empleado,))
        if afectadas == 0:
            raise self._no_encontrado(id_empleado)