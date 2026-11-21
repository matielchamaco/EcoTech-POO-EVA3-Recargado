from config.base_datos import ConexionBD
from excepciones.excepciones import RegistroNoEncontradoError, ValidacionError
from models.proyecto import Proyecto
from models.entidadbase_dao import EntidadBaseDAO

class ProyectoDAO(EntidadBaseDAO):
    _NOMBRE_ENTIDAD = "Proyecto"

    def _a_objeto(self, fila):
        asignados = self._consultar(
            "SELECT id_empleado FROM proyecto_empleado WHERE id_proyecto = ?", (fila["id_proyecto"],))
        return Proyecto(fila["id_proyecto"], fila["nombre"], fila["fecha_inicio"],
                        [a["id_empleado"] for a in asignados])

    def crear(self, p: Proyecto):
        with self._conexion.cursor() as cur:        # una sola transacción: proyecto + asignaciones
            cur.execute("INSERT INTO proyectos (id_proyecto, nombre, fecha_inicio) VALUES (?, ?, ?)",
                        (p.id_proyecto, p.nombre, p.fecha_inicio.isoformat()))
            nuevo_id = cur.lastrowid
            cur.executemany("INSERT INTO proyecto_empleado (id_proyecto, id_empleado) VALUES (?, ?)",
                            [(nuevo_id, e) for e in p.empleados_asignados])
        p.id_proyecto = nuevo_id
        return p

    def obtener(self, id_proyecto):
        filas = self._consultar("SELECT * FROM proyectos WHERE id_proyecto = ?", (id_proyecto,))
        if not filas:
            raise self._no_encontrado(id_proyecto)
        return self._a_objeto(filas[0])

    def listar(self):
        return [self._a_objeto(f) for f in self._consultar("SELECT * FROM proyectos ORDER BY id_proyecto")]

    def actualizar(self, p: Proyecto):
        with self._conexion.cursor() as cur:
            cur.execute("UPDATE proyectos SET nombre = ?, fecha_inicio = ? WHERE id_proyecto = ?",
                        (p.nombre, p.fecha_inicio.isoformat(), p.id_proyecto))
            if cur.rowcount == 0:
                raise self._no_encontrado(p.id_proyecto)
            # Se sincronizan las asignaciones con el estado actual del objeto.
            cur.execute("DELETE FROM proyecto_empleado WHERE id_proyecto = ?", (p.id_proyecto,))
            cur.executemany("INSERT INTO proyecto_empleado (id_proyecto, id_empleado) VALUES (?, ?)",
                            [(p.id_proyecto, e) for e in p.empleados_asignados])
        return p

    def eliminar(self, id_proyecto):
        _, afectadas = self._ejecutar("DELETE FROM proyectos WHERE id_proyecto = ?", (id_proyecto,))
        if afectadas == 0:
            raise self._no_encontrado(id_proyecto)