from config.base_datos import ConexionBD
from config.entorno import cargar_env
from excepciones.excepciones import ErrorBaseDatos
from seguridad.autenticacion import ServicioAutenticacion
from services.clima_service import ServicioClima
from services.cliente_http import ClienteHTTP
from services.consultas_repo import ConsultasExternasRepo
from services.tipo_cambio_service import ServicioTipoCambio
from views.loginview import iniciar_sesion
from views.mainview import AplicacionConsola


def main():
    cargar_env()                                   # llaves de API desde .env / variables de entorno
    conexion = ConexionBD("ecotech.db")
    try:
        conexion.crear_tablas()
    except ErrorBaseDatos as e:
        print(f"No fue posible iniciar la base de datos: {e}")
        return

    sesion = iniciar_sesion(ServicioAutenticacion(conexion))
    if sesion is None:                             # sin autenticación no se inicia el sistema
        return

    cliente, repo = ClienteHTTP(), ConsultasExternasRepo(conexion)
    AplicacionConsola(conexion, sesion,
                      ServicioClima(cliente, sesion, repo),
                      ServicioTipoCambio(cliente, sesion, repo)).ejecutar()


if __name__ == "__main__":
    main()
