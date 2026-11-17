import logging
from datetime import date
from models.empleado import Empleado
from models.departamento import Departamento
from models.proyecto import Proyecto
from models.registrotiempo import RegistroTiempo
from config.base_datos import ConexionBD
from excepciones.excepciones import ErrorEcoTech
from seguridad.autenticacion import Sesion
from seguridad.validadores import MONEDAS_SOPORTADAS, validar_ciudad, validar_moneda
from services.clima_service import ServicioClima
from services.consultas_repo import ConsultasExternasRepo
from services.tipo_cambio_service import MONEDA_BASE, ServicioTipoCambio

from models.empleado_dao import EmpleadoDAO
from models.departamento_dao import DepartamentoDAO
from models.proyecto_dao import ProyectoDAO
from models.registrotiempo_dao import RegistroTiempoDAO

logging.basicConfig(filename="ecotech.log", level=logging.WARNING,
                    format="%(asctime)s %(levelname)s %(message)s")


# ---------- Entrada de datos con validación de tipo (el dominio valida las reglas) ----------
def pedir_texto(mensaje, opcional=False):
    texto = input(mensaje).strip()
    return None if (opcional and not texto) else texto


def pedir_entero(mensaje, opcional=False):
    while True:
        texto = input(mensaje).strip()
        if opcional and not texto:
            return None
        try:
            return int(texto)
        except ValueError:
            print("  Debe ingresar un número entero.")


def pedir_decimal(mensaje, opcional=False):
    while True:
        texto = input(mensaje).strip().replace(",", ".")
        if opcional and not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            print("  Debe ingresar un número (ej. 6.5).")


def confirmar(mensaje):
    return input(f"{mensaje} (s/n): ").strip().lower() == "s"


class AplicacionConsola:
    def __init__(self, conexion: ConexionBD, sesion: Sesion = None,
                 clima: ServicioClima = None, cambio: ServicioTipoCambio = None):
        self._sesion = sesion
        self._clima = clima
        self._cambio = cambio
        self._consultas = ConsultasExternasRepo(conexion)
        self._deptos = DepartamentoDAO(conexion)
        self._emps = EmpleadoDAO(conexion)
        self._proys = ProyectoDAO(conexion)
        self._regs = RegistroTiempoDAO(conexion)

    # ---------- Ejecución protegida: ningún error debe cerrar el programa ----------
    @staticmethod
    def _proteger(accion):
        try:
            accion()
        except ErrorEcoTech as e:               # excepciones propias: mensajes ya aptos para el usuario
            print(f"  [Error] {e}")
        except (KeyboardInterrupt, EOFError):
            print("\n  Operación cancelada.")
        except Exception:                       # error no previsto: se registra y se informa genéricamente
            logging.exception("Error inesperado")
            print("  [Error inesperado] No se pudo completar la operación (detalle en ecotech.log).")

    def _submenu(self, titulo, opciones):
        while True:
            print(f"\n=== {titulo} ===")
            for clave, (texto, _) in opciones.items():
                print(f"  {clave}. {texto}")
            print("  0. Volver")
            eleccion = input("Opción: ").strip()
            if eleccion == "0":
                return
            if eleccion in opciones:
                self._proteger(opciones[eleccion][1])
            else:
                print("  Opción no válida.")

    def ejecutar(self):
        principal = {
            "1": ("Departamentos", self.menu_departamentos),
            "2": ("Empleados", self.menu_empleados),
            "3": ("Proyectos", self.menu_proyectos),
            "4": ("Registros de tiempo", self.menu_registros),
            "5": ("Servicios externos (clima y pagos internacionales)", self.menu_servicios),
        }
        while True:
            print("\n===== EcoTech Solutions - Gestión de Empleados =====")
            for clave, (texto, _) in principal.items():
                print(f"  {clave}. {texto}")
            print("  0. Cerrar sesión y salir")
            try:
                if self._sesion is not None:
                    self._sesion.exigir_autenticado()     # control de acceso en cada vuelta del menú
                eleccion = input("Opción: ").strip()
            except ErrorEcoTech as e:
                print(f"  [Error] {e}")
                return
            except (KeyboardInterrupt, EOFError):
                eleccion = "0"
            if eleccion == "0":
                if self._sesion is not None:
                    self._sesion.cerrar()
                print("Sesión cerrada. Hasta pronto.")
                return
            if eleccion in principal:
                try:
                    principal[eleccion][1]()
                except (KeyboardInterrupt, EOFError):
                    print("\n  Volviendo al menú principal.")
            else:
                print("  Opción no válida.")

    # ---------- Departamentos ----------
    def menu_departamentos(self):
        self._submenu("Departamentos", {
            "1": ("Registrar", self._depto_registrar),
            "2": ("Listar", lambda: self._listar(self._deptos.listar())),
            "3": ("Buscar por ID", lambda: print(self._deptos.obtener(pedir_entero("ID: ")))),
            "4": ("Actualizar", self._depto_actualizar),
            "5": ("Eliminar", lambda: self._eliminar(self._deptos, "departamento")),
        })

    def _depto_registrar(self):
        d = Departamento(None, pedir_texto("Nombre: "), pedir_entero("ID del gerente (Enter = ninguno): ", True))
        print("  Creado:", self._deptos.crear(d))

    def _depto_actualizar(self):
        d = self._deptos.obtener(pedir_entero("ID del departamento: "))
        nombre = pedir_texto(f"Nuevo nombre [{d.nombre}] (Enter = mantener): ", True)
        if nombre:
            d.editar_departamento(nombre)
        gerente = pedir_entero(f"Nuevo ID de gerente [{d.id_gerente}] (Enter = mantener): ", True)
        if gerente is not None:
            d.id_gerente = gerente
        print("  Actualizado:", self._deptos.actualizar(d))

    # ---------- Empleados ----------
    def menu_empleados(self):
        self._submenu("Empleados", {
            "1": ("Registrar", self._emp_registrar),
            "2": ("Listar", lambda: self._listar(self._emps.listar())),
            "3": ("Buscar por ID (incluye salario)", self._emp_buscar),
            "4": ("Actualizar", self._emp_actualizar),
            "5": ("Eliminar", lambda: self._eliminar(self._emps, "empleado")),
            "6": ("Asignar a departamento", self._emp_asignar_depto),
        })

    def _emp_registrar(self):
        e = Empleado(None, pedir_texto("Nombre: "), pedir_texto("Correo: "),
                     pedir_decimal("Salario: "), pedir_entero("ID de departamento (Enter = ninguno): ", True))
        print("  Creado:", self._emps.crear(e))

    def _emp_buscar(self):
        e = self._emps.obtener(pedir_entero("ID: "))
        print(e)
        print(f"  Salario: {e.salario:,.0f}")

    def _emp_actualizar(self):
        e = self._emps.obtener(pedir_entero("ID del empleado: "))
        nombre = pedir_texto(f"Nombre [{e.nombre}] (Enter = mantener): ", True)
        correo = pedir_texto(f"Correo [{e.correo}] (Enter = mantener): ", True)
        salario = pedir_decimal("Nuevo salario (Enter = mantener): ", True)
        if nombre:
            e.nombre = nombre
        if correo:
            e.correo = correo
        if salario is not None:
            e.salario = salario
        print("  Actualizado:", self._emps.actualizar(e))

    def _emp_asignar_depto(self):
        e = self._emps.obtener(pedir_entero("ID del empleado: "))
        if e.asignar_a_depto(pedir_entero("ID del departamento: ")):
            self._emps.actualizar(e)
            print("  Empleado asignado:", e)
        else:
            print("  El empleado ya pertenecía a ese departamento.")

    # ---------- Proyectos ----------
    def menu_proyectos(self):
        self._submenu("Proyectos", {
            "1": ("Registrar", self._proy_registrar),
            "2": ("Listar", lambda: self._listar(self._proys.listar())),
            "3": ("Buscar por ID", lambda: print(self._proys.obtener(pedir_entero("ID: ")))),
            "4": ("Actualizar", self._proy_actualizar),
            "5": ("Eliminar", lambda: self._eliminar(self._proys, "proyecto")),
            "6": ("Asignar empleado", lambda: self._proy_asignacion(True)),
            "7": ("Desasignar empleado", lambda: self._proy_asignacion(False)),
        })

    def _proy_registrar(self):
        p = Proyecto(None, pedir_texto("Nombre: "), pedir_texto("Fecha de inicio (AAAA-MM-DD): "))
        print("  Creado:", self._proys.crear(p))

    def _proy_actualizar(self):
        p = self._proys.obtener(pedir_entero("ID del proyecto: "))
        nombre = pedir_texto(f"Nombre [{p.nombre}] (Enter = mantener): ", True)
        fecha = pedir_texto(f"Fecha inicio [{p.fecha_inicio}] (Enter = mantener): ", True)
        if nombre:
            p.nombre = nombre
        if fecha:
            p.fecha_inicio = fecha
        print("  Actualizado:", self._proys.actualizar(p))

    def _proy_asignacion(self, asignar):
        p = self._proys.obtener(pedir_entero("ID del proyecto: "))
        id_emp = pedir_entero("ID del empleado: ")
        cambio = p.asignar_empleado(id_emp) if asignar else p.desasignar_empleado(id_emp)
        if cambio:
            self._proys.actualizar(p)
            print("  Listo:", p)
        else:
            print("  Sin cambios (el empleado ya estaba asignado)." if asignar
                  else "  Sin cambios (el empleado no estaba asignado).")

    # ---------- Registros de tiempo ----------
    def menu_registros(self):
        self._submenu("Registros de tiempo", {
            "1": ("Registrar", self._reg_registrar),
            "2": ("Listar todos", lambda: self._listar(self._regs.listar())),
            "3": ("Listar por empleado",
                  lambda: self._listar(self._regs.listar_por_empleado(pedir_entero("ID empleado: ")))),
            "4": ("Buscar por ID", lambda: print(self._regs.obtener(pedir_entero("ID: ")))),
            "5": ("Actualizar", self._reg_actualizar),
            "6": ("Eliminar", lambda: self._eliminar(self._regs, "registro")),
        })

    def _reg_registrar(self):
        id_emp = pedir_entero("ID del empleado: ")
        id_proy = pedir_entero("ID del proyecto: ")
        horas = pedir_decimal("Horas trabajadas: ")
        fecha = pedir_texto("Fecha AAAA-MM-DD (Enter = hoy): ", True) or date.today()
        print("  Creado:", self._regs.crear(RegistroTiempo(id_emp, id_proy, horas, fecha)))

    def _reg_actualizar(self):
        r = self._regs.obtener(pedir_entero("ID del registro: "))
        horas = pedir_decimal(f"Horas [{r.horas}] (Enter = mantener): ", True)
        fecha = pedir_texto(f"Fecha [{r.fecha}] (Enter = mantener): ", True)
        if horas is not None:
            r.horas = horas
        if fecha:
            r.fecha = fecha
        print("  Actualizado:", self._regs.actualizar(r))

    # ---------- Servicios externos (Unidad 3) ----------
    def menu_servicios(self):
        self._submenu("Servicios externos", {
            "1": ("Consultar clima para planificar un proyecto", self._srv_clima),
            "2": ("Consultar tipo de cambio", self._srv_tipo_cambio),
            "3": ("Calcular pago internacional de un empleado", self._srv_pago),
            "4": ("Ver historial local de consultas", self._srv_historial),
        })

    def _srv_clima(self):
        p = self._proys.obtener(pedir_entero("ID del proyecto: "))
        c = self._clima.obtener_clima(pedir_texto("Ciudad donde se ejecuta: "))
        nivel, texto = self._clima.evaluar_riesgo(c)
        print(f"  Proyecto: {p.nombre}")
        print(f"  Clima en {c.ciudad} ({c.pais}): {c.temperatura:.1f} °C, {c.descripcion}, humedad {c.humedad:.0f}%")
        if c.desde_cache:
            print(f"  [Aviso] Servicio no disponible: dato guardado el {c.fecha_cache}.")
        print(f"  Riesgo operativo {nivel}: {texto}")

    @staticmethod
    def _pedir_moneda():
        print("  Monedas: " + ", ".join(f"{k} ({v})" for k, v in MONEDAS_SOPORTADAS.items()))
        return validar_moneda(pedir_texto("Moneda destino: "))

    def _srv_tipo_cambio(self):
        t = self._cambio.obtener_tasa(self._pedir_moneda())
        print(f"  1 {t.base} = {t.tasa:.6f} {t.destino}")
        if t.desde_cache:
            print(f"  [Aviso] Servicio no disponible: tasa guardada el {t.fecha_cache}.")

    def _srv_pago(self):
        e = self._emps.obtener(pedir_entero("ID del empleado: "))
        pago = self._cambio.calcular_pago(e.salario, self._pedir_moneda())
        print(f"  {e.nombre}: {pago.monto_base:,.0f} {MONEDA_BASE} -> {pago.monto_convertido:,.2f} {pago.moneda_destino}"
              f" (tasa {pago.tasa.tasa:.6f})")
        if pago.tasa.desde_cache:
            print(f"  [Aviso] Tasa guardada el {pago.tasa.fecha_cache}; confirme el valor antes de pagar.")

    def _srv_historial(self):
        self._sesion.exigir_autenticado()
        print("  Últimos climas consultados:")
        for f in self._consultas.historial_clima() or []:
            print(f"   {f['consultado']} | {f['ciudad'].title()} | {f['temperatura']:.1f} °C | {f['descripcion']}")
        print("  Últimos tipos de cambio:")
        for f in self._consultas.historial_tasas() or []:
            print(f"   {f['consultado']} | 1 {f['base']} = {f['tasa']:.6f} {f['destino']}")

    # ---------- Utilidades comunes ----------
    @staticmethod
    def _listar(elementos):
        if not elementos:
            print("  (sin registros)")
        for elemento in elementos:
            print(" ", elemento)

    @staticmethod
    def _eliminar(repo, nombre):
        id_ = pedir_entero(f"ID del {nombre} a eliminar: ")
        if confirmar(f"¿Eliminar {nombre} {id_}?"):
            repo.eliminar(id_)
            print("  Eliminado.")
        else:
            print("  Operación cancelada.")