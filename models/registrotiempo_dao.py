from config.base_datos import ConexionBD
from excepciones.excepciones import RegistroNoEncontradoError, ValidacionError
from models.registrotiempo import RegistroTiempo
from models.entidadbase_dao import EntidadBaseDAO

class RegistroTiempoDAO(EntidadBaseDAO):
    _NOMBRE_ENTIDAD = "Registro de tiempo"

    @staticmethod
    def _a_objeto(fila):
        return RegistroTiempo(fila["id_empleado"], fila["id_proyecto"], fila["horas"],
                              fila["fecha"], fila["id_registro"])

    def crear(self, r: RegistroTiempo):
        if not r.validar_rango_horas():
            raise ValidacionError("Las horas del registro están fuera del rango permitido.")
        nuevo_id, _ = self._ejecutar(
            "INSERT INTO registros_tiempo (id_registro, id_empleado, id_proyecto, horas, fecha) "
            "VALUES (?, ?, ?, ?, ?)",
            (r.id_registro, r.id_empleado, r.id_proyecto, r.horas, r.fecha.isoformat()))
        r.id_registro = nuevo_id
        return r

    def obtener(self, id_registro):
        filas = self._consultar("SELECT * FROM registros_tiempo WHERE id_registro = ?", (id_registro,))
        if not filas:
            raise self._no_encontrado(id_registro)
        return self._a_objeto(filas[0])

    def listar(self):
        return [self._a_objeto(f) for f in self._consultar("SELECT * FROM registros_tiempo ORDER BY id_registro")]

    def listar_por_empleado(self, id_empleado):
        filas = self._consultar(
            "SELECT * FROM registros_tiempo WHERE id_empleado = ? ORDER BY fecha", (id_empleado,))
        return [self._a_objeto(f) for f in filas]

    def actualizar(self, r: RegistroTiempo):
        if not r.validar_rango_horas():
            raise ValidacionError("Las horas del registro están fuera del rango permitido.")
        _, afectadas = self._ejecutar(
            "UPDATE registros_tiempo SET horas = ?, fecha = ? WHERE id_registro = ?",
            (r.horas, r.fecha.isoformat(), r.id_registro))
        if afectadas == 0:
            raise self._no_encontrado(r.id_registro)
        return r

    def eliminar(self, id_registro):
        _, afectadas = self._ejecutar("DELETE FROM registros_tiempo WHERE id_registro = ?", (id_registro,))
        if afectadas == 0:
            raise self._no_encontrado(id_registro)