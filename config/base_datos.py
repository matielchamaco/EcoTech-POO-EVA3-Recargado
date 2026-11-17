"""Conexión a la base de datos con la librería oficial sqlite3 (biblioteca estándar de Python).

Parámetros relevantes:
- ruta: archivo .db (se crea si no existe).
- PRAGMA foreign_keys = ON: SQLite no valida claves foráneas por defecto; se activa en cada conexión.
- row_factory = sqlite3.Row: permite acceder a las columnas por nombre.
"""
import logging
import sqlite3
from contextlib import contextmanager

from excepciones.excepciones import ErrorBaseDatos

ESQUEMA = """
CREATE TABLE IF NOT EXISTS departamentos (
    id_depto    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    id_gerente  INTEGER,
    FOREIGN KEY (id_gerente) REFERENCES empleados(id_empleado) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS empleados (
    id_empleado INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    correo      TEXT NOT NULL UNIQUE,
    salario     REAL NOT NULL CHECK (salario >= 0),
    id_depto    INTEGER,
    FOREIGN KEY (id_depto) REFERENCES departamentos(id_depto) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE,
    fecha_inicio TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proyecto_empleado (
    id_proyecto INTEGER NOT NULL,
    id_empleado INTEGER NOT NULL,
    PRIMARY KEY (id_proyecto, id_empleado),
    FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto) ON DELETE CASCADE,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS registros_tiempo (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    id_proyecto INTEGER NOT NULL,
    horas       REAL NOT NULL CHECK (horas > 0 AND horas <= 24),
    fecha       TEXT NOT NULL,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado) ON DELETE RESTRICT,
    FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT NOT NULL UNIQUE,
    sal         TEXT NOT NULL,
    hash        TEXT NOT NULL,
    iteraciones INTEGER NOT NULL,
    creado      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS consultas_clima (
    id_consulta INTEGER PRIMARY KEY AUTOINCREMENT,
    ciudad      TEXT NOT NULL,
    pais        TEXT,
    temperatura REAL NOT NULL,
    humedad     REAL NOT NULL,
    descripcion TEXT NOT NULL,
    codigo      INTEGER NOT NULL,
    consultado  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tipos_cambio (
    id_tasa    INTEGER PRIMARY KEY AUTOINCREMENT,
    base       TEXT NOT NULL,
    destino    TEXT NOT NULL,
    tasa       REAL NOT NULL CHECK (tasa > 0),
    consultado TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
# Decisiones de diseño (coherentes con el informe):
# - Empleado->Departamento: SET NULL (agregación: el empleado existe aunque se elimine el depto).
# - RegistroTiempo: RESTRICT (no se pierde el historial de horas necesario para auditoría).


class ConexionBD:
    def __init__(self, ruta="ecotech.db"):
        self._ruta = ruta

    @contextmanager
    def cursor(self):
        """Entrega un cursor dentro de una transacción: commit si todo sale bien, rollback si falla."""
        conexion = None
        try:
            conexion = sqlite3.connect(self._ruta)
            conexion.row_factory = sqlite3.Row
            conexion.execute("PRAGMA foreign_keys = ON")
            yield conexion.cursor()
            conexion.commit()
        except sqlite3.IntegrityError as e:
            if conexion:
                conexion.rollback()
            raise ErrorBaseDatos(
                "La operación viola una restricción (dato duplicado, referencia "
                "inexistente o registro en uso)."
            ) from e
        except sqlite3.Error as e:
            if conexion:
                conexion.rollback()
            logging.getLogger("ecotech.bd").error("Error sqlite3: %s", e)   # detalle solo en el log
            raise ErrorBaseDatos("No fue posible completar la operación en la base de datos.") from e
        finally:
            if conexion:
                conexion.close()

    def crear_tablas(self):
        with self.cursor() as cur:
            cur.executescript(ESQUEMA)
