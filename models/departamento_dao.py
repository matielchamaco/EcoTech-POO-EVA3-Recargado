from config.base_datos import ConexionBD
from excepciones.excepciones import RegistroNoEncontradoError, ValidacionError
from models.departamento import Departamento
from models.entidadbase_dao import EntidadBaseDAO

class DepartamentoDAO(EntidadBaseDAO):
    _NOMBRE_ENTIDAD = "Departamento"

    @staticmethod
    def _a_objeto(fila):
        return Departamento(fila["id_depto"], fila["nombre"], fila["id_gerente"])

    def crear(self, d: Departamento):
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO departamentos (id_depto, nombre, id_gerente) VALUES (?, ?, ?)",
            (d.id_depto, d.nombre, d.id_gerente))
        d.id_depto = nuevo_id
        return d

    def obtener(self, id_depto):
        filas = self._consultar("SELECT * FROM departamentos WHERE id_depto = ?", (id_depto,))
        if not filas:
            raise self._no_encontrado(id_depto)
        return self._a_objeto(filas[0])

    def listar(self):
        return [self._a_objeto(f) for f in self._consultar("SELECT * FROM departamentos ORDER BY id_depto")]

    def actualizar(self, d: Departamento):
        _, afectadas = self._ejecutar(
            "UPDATE departamentos SET nombre = ?, id_gerente = ? WHERE id_depto = ?",
            (d.nombre, d.id_gerente, d.id_depto))
        if afectadas == 0:
            raise self._no_encontrado(d.id_depto)
        return d

    def eliminar(self, id_depto):
        _, afectadas = self._ejecutar("DELETE FROM departamentos WHERE id_depto = ?", (id_depto,))
        if afectadas == 0:
            raise self._no_encontrado(id_depto)