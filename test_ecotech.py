"""Pruebas automáticas (unittest). Ejecutar con:  python -m unittest -v"""
import os
import tempfile
import unittest
from datetime import date, timedelta

from config.base_datos import ConexionBD
from excepciones.excepciones import ErrorBaseDatos, RegistroNoEncontradoError, ValidacionError
from models.departamento import Departamento
from models.departamento_dao import DepartamentoDAO as DepartamentoRepositorio
from models.empleado import Empleado
from models.empleado_dao import EmpleadoDAO as EmpleadoRepositorio
from models.entidadbase import EntidadBase
from models.proyecto import Proyecto
from models.proyecto_dao import ProyectoDAO as ProyectoRepositorio
from models.registrotiempo import RegistroTiempo
from models.registrotiempo_dao import RegistroTiempoDAO as RegistroTiempoRepositorio


class PruebasModelo(unittest.TestCase):
    def test_entidad_base_es_abstracta(self):
        with self.assertRaises(TypeError):
            EntidadBase()

    def test_salario_encapsulado(self):
        e = Empleado(None, "Ana", "ana@ecotech.cl", 1000)
        self.assertFalse(hasattr(e, "__salario"))       # el nombre real está "mangled"
        with self.assertRaises(ValidacionError):
            e.salario = -1
        self.assertNotIn("1000", str(e))                # el salario no se filtra en __str__

    def test_validaciones_empleado(self):
        with self.assertRaises(ValidacionError):
            Empleado(None, "Ana", "correo-malo", 1000)
        with self.assertRaises(ValidacionError):
            Empleado(None, "   ", "ana@ecotech.cl", 1000)
        with self.assertRaises(ValidacionError):
            Empleado(None, "Ana", "ana@ecotech.cl", "mucho")

    def test_asignar_a_depto(self):
        e = Empleado(1, "Ana", "ana@ecotech.cl", 1000)
        self.assertTrue(e.asignar_a_depto(3))
        self.assertFalse(e.asignar_a_depto(3))
        with self.assertRaises(ValidacionError):
            e.asignar_a_depto(0)

    def test_proyecto_asignaciones(self):
        p = Proyecto(None, "Hidrógeno Verde", "2026-01-15")
        self.assertTrue(p.asignar_empleado(5))
        self.assertFalse(p.asignar_empleado(5))
        self.assertTrue(p.desasignar_empleado(5))
        self.assertFalse(p.desasignar_empleado(5))

    def test_registro_horas_y_fecha(self):
        hoy = date.today()
        self.assertTrue(RegistroTiempo(1, 1, 6.5, hoy).validar_rango_horas())
        for horas in (0, -2, 25, float("nan")):
            with self.assertRaises(ValidacionError):
                RegistroTiempo(1, 1, horas, hoy)
        with self.assertRaises(ValidacionError):
            RegistroTiempo(1, 1, 5, hoy + timedelta(days=1))


class PruebasBaseDatos(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.conexion = ConexionBD(os.path.join(self._dir.name, "test.db"))
        self.conexion.crear_tablas()
        self.deptos = DepartamentoRepositorio(self.conexion)
        self.emps = EmpleadoRepositorio(self.conexion)
        self.proys = ProyectoRepositorio(self.conexion)
        self.regs = RegistroTiempoRepositorio(self.conexion)

    def tearDown(self):
        self._dir.cleanup()

    def test_crud_empleado(self):
        e = self.emps.crear(Empleado(None, "Ana", "ana@ecotech.cl", 1500000))
        self.assertIsNotNone(e.id_empleado)
        e.salario = 1600000
        self.emps.actualizar(e)
        self.assertEqual(self.emps.obtener(e.id_empleado).salario, 1600000)
        self.assertEqual(len(self.emps.listar()), 1)
        self.emps.eliminar(e.id_empleado)
        with self.assertRaises(RegistroNoEncontradoError):
            self.emps.obtener(e.id_empleado)

    def test_correo_duplicado(self):
        self.emps.crear(Empleado(None, "Ana", "ana@ecotech.cl", 1))
        with self.assertRaises(ErrorBaseDatos):
            self.emps.crear(Empleado(None, "Otra", "ana@ecotech.cl", 1))

    def test_inyeccion_sql_no_funciona(self):
        d = self.deptos.crear(Departamento(None, "x'); DROP TABLE departamentos;--"))
        self.assertEqual(self.deptos.obtener(d.id_depto).nombre, "x'); DROP TABLE departamentos;--")

    def test_eliminar_depto_conserva_empleado(self):
        d = self.deptos.crear(Departamento(None, "Ventas"))
        e = self.emps.crear(Empleado(None, "Ana", "ana@ecotech.cl", 1, d.id_depto))
        self.deptos.eliminar(d.id_depto)
        self.assertIsNone(self.emps.obtener(e.id_empleado).id_depto)

    def test_proyecto_con_empleados(self):
        e = self.emps.crear(Empleado(None, "Ana", "ana@ecotech.cl", 1))
        p = Proyecto(None, "H2", "2026-02-01")
        p.asignar_empleado(e.id_empleado)
        self.proys.crear(p)
        self.assertEqual(self.proys.obtener(p.id_proyecto).empleados_asignados, (e.id_empleado,))
        p.desasignar_empleado(e.id_empleado)
        self.proys.actualizar(p)
        self.assertEqual(self.proys.obtener(p.id_proyecto).empleados_asignados, ())

    def test_asignar_empleado_inexistente(self):
        p = self.proys.crear(Proyecto(None, "H2", "2026-02-01"))
        p.asignar_empleado(999)
        with self.assertRaises(ErrorBaseDatos):
            self.proys.actualizar(p)

    def test_registro_tiempo_y_restriccion(self):
        e = self.emps.crear(Empleado(None, "Ana", "ana@ecotech.cl", 1))
        p = self.proys.crear(Proyecto(None, "H2", "2026-02-01"))
        r = self.regs.crear(RegistroTiempo(e.id_empleado, p.id_proyecto, 6.5, date.today()))
        self.assertEqual(len(self.regs.listar_por_empleado(e.id_empleado)), 1)
        with self.assertRaises(ErrorBaseDatos):         # historial protegido (RESTRICT)
            self.emps.eliminar(e.id_empleado)
        self.regs.eliminar(r.id_registro)
        self.emps.eliminar(e.id_empleado)

    def test_conexion_invalida(self):
        mala = ConexionBD(os.path.join(self._dir.name, "no_existe", "x.db"))
        with self.assertRaises(ErrorBaseDatos):
            mala.crear_tablas()


if __name__ == "__main__":
    unittest.main()
