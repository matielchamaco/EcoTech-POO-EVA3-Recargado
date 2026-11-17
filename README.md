# EcoTech Solutions – Sistema de Gestión de Empleados (ES2 + ES3 – TI3021)

CRUD orientado a objetos en Python 3.10+ con SQLite (`sqlite3`, librería oficial).

## Ejecutar
    pip install requests          # librería oficial para consumir APIs
    copy .env.example .env        # (Linux/Mac: cp) y pegar la llave de OpenWeatherMap
    python main.py                # primer uso: crea el usuario administrador; luego inicia sesión
    python -m unittest -v         # pruebas automáticas (no requieren internet)

## Unidad 3 – Servicios externos y seguridad
| Criterio | Dónde |
|---|---|
| 3.1.1 Consumo de APIs (`requests`, JSON) | `services/cliente_http.py`, `clima_service.py` (OpenWeatherMap), `tipo_cambio_service.py` (open.er-api.com) |
| 3.1.2 Autenticación, validación, datos sensibles, control de acceso | `seguridad/autenticacion.py` (PBKDF2 + sal + sesión), `seguridad/validadores.py`, `config/entorno.py` (.env), `sesion.exigir_autenticado()` |
| 3.1.3 Errores: timeouts, HTTP, continuidad, mensajes seguros | `ClienteHTTP`, jerarquía en `excepciones/excepciones.py`, respaldo local en `services/consultas_repo.py` |
| 3.1.4 IA: evidencia, análisis, refactorización | `docs/REGISTRO_IA.md` |


## Correspondencia UML → código
| UML | Código |
|---|---|
| Departamento, Empleado, Proyecto, RegistroTiempo | `modelos.py` (una clase cada una) |
| Departamento 1 — 0..* Empleado (agregación) | `Empleado._id_depto`, FK `ON DELETE SET NULL` |
| Empleado 1..* — 0..* Proyecto (asociación) | `Proyecto._empleados` (set de ids), tabla `proyecto_empleado` |
| Empleado / Proyecto 1 — 0..* RegistroTiempo | `RegistroTiempo._id_empleado` / `_id_proyecto`, FK `ON DELETE RESTRICT` |
| `- __salario: float` | `Empleado.__salario` + `@property salario` con validación |

Elementos agregados que NO están en el diagrama (agregar al UML o justificarlos en la defensa):
`EntidadBase` (clase abstracta de validaciones), `RepositorioBase` + repositorios (persistencia),
`ConexionBD`, excepciones propias, `Empleado.nombre`, `Empleado.id_depto`.

## Registro de uso de IA
Ver `docs/REGISTRO_IA.md`.
