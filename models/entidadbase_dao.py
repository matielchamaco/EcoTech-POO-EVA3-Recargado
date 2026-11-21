from abc import ABC, abstractmethod

from config.base_datos import ConexionBD
from excepciones.excepciones import RegistroNoEncontradoError, ValidacionError
from models.empleado import Empleado
from models.departamento import Departamento
from models.proyecto import Proyecto
from models.registrotiempo import RegistroTiempo

class EntidadBaseDAO(ABC):
    _NOMBRE_ENTIDAD = "Registro"

    def __init__(self, conexion: ConexionBD):
        self._conexion = conexion

    # --- código común reutilizado por todas las subclases ---
    def _ejecutar(self, sql, params=()):
        """Ejecuta INSERT/UPDATE/DELETE. Retorna (lastrowid, filas_afectadas)."""
        with self._conexion.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid, cur.rowcount

    def _consultar(self, sql, params=()):
        with self._conexion.cursor() as cur:
            return cur.execute(sql, params).fetchall()

    def _no_encontrado(self, id_):
        return RegistroNoEncontradoError(f"{self._NOMBRE_ENTIDAD} con id {id_} no existe.")

    @abstractmethod
    def crear(self, entidad): ...

    @abstractmethod
    def obtener(self, id_): ...

    @abstractmethod
    def listar(self): ...

    @abstractmethod
    def actualizar(self, entidad): ...

    @abstractmethod
    def eliminar(self, id_): ...