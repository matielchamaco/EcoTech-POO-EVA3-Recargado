# Registro de uso de IA y decisiones técnicas (ES3 – criterio 3.1.4)

**Herramienta:** Claude (Anthropic). **Rol de la IA:** apoyo en el diseño y la codificación; cada fragmento fue
revisado, probado (`python -m unittest -v`) y ajustado. Completa/ajusta este documento con tus propios prompts
y capturas: debes poder explicar cada línea en la defensa.

## 1. Prompts utilizados (resumen)
| N° | Prompt (resumen) | Resultado |
|---|---|---|
| 1 | "Ayúdame a añadir a mi sistema de empleados de EcoTech el consumo de APIs de clima y tipo de cambio, autenticación, validación y manejo de errores, según la guía y la rúbrica de la ES3." | Estructura de módulos `seguridad/`, `services/`, ampliación de `excepciones/` y del menú. |
| 2 | "Analiza el código generado: ¿qué vulnerabilidades tiene?" (versión ingenua, ver §2) | Lista de riesgos y correcciones del §3. |

## 2. Primera propuesta típica de la IA (versión ingenua) y sus problemas
```python
API_KEY = "a1b2c3..."                                   # (A) llave en el código
def clima(ciudad):
    r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={API_KEY}")
    return r.json()["main"]["temp"]                     # (B)(C)(D)
def login(u, p):
    return u == "admin" and p == "1234"                 # (E) credencial fija y en texto plano
try: ...
except Exception as e: print(f"Error: {e}")             # (F) expone la URL con la llave
```
| Id | Vulnerabilidad / defecto | Criterio afectado |
|---|---|---|
| A | Llave de API en el código fuente (queda en Git/ZIP). | 3.1.2 (info sensible) |
| B | Sin `timeout`: el programa puede quedar colgado indefinidamente. | 3.1.3 |
| C | No se revisa `status_code`; un 404/500 se procesa como éxito y falla con `KeyError`. | 3.1.3 |
| D | Entrada del usuario interpolada en la URL (inyección de parámetros, p. ej. `Lima&appid=...`); sin validar tipo/rango del dato recibido. | 3.1.2 / 3.1.1 |
| E | Autenticación con contraseña en texto plano, sin sal, sin límite de intentos; no vinculada al consumo de la API. | 3.1.2 |
| F | `except Exception` genérico: oculta la causa y `requests` incluye la URL (con `appid`) en el mensaje → fuga de la llave. | 3.1.3 |
| G | Sin HTTPS forzado ni reintentos acotados; sin respaldo si el servicio cae. | 3.1.3 |

## 3. Decisiones: uso, modificación o descarte
| Fragmento | Decisión | Justificación técnica |
|---|---|---|
| `requests.get` simple | **Modificado** → `services/cliente_http.py` | `Session` + `Retry` (solo GET, 429/5xx), `timeout=(3.05, 8)`, solo HTTPS. Centraliza el consumo y evita repetir código (DRY). |
| `params` por f-string | **Descartado** | Se usa `params=` de `requests` (codifica la URL) **y** validación por lista blanca (`seguridad/validadores.py`). |
| `API_KEY` literal | **Descartado** | `config/entorno.py` lee `OPENWEATHER_API_KEY` de variable de entorno/.env (fuera de Git, `.env.example` sin valor). Nunca se imprime ni registra el valor. |
| Login con `==` | **Descartado** | PBKDF2-HMAC-SHA256 (600 000 iteraciones, sal de 16 bytes por usuario), `hmac.compare_digest`, mensaje genérico, 3 intentos, bloqueo y sesión con expiración por inactividad. Se eligió `hashlib` (librería estándar) para no depender de paquetes externos. |
| Acceso a la API | **Modificado** | Cada servicio llama a `sesion.exigir_autenticado()` **antes** de validar o consultar: la ejecución queda ligada al estado de autenticación (probado: sin sesión, la API ni se invoca). |
| `except Exception` | **Modificado** | Jerarquía propia (`ErrorServicioExterno` → `TimeoutExterno`, `ErrorConexionExterna`, `RecursoExternoNoEncontrado`, `RespuestaInvalidaError`). Cada excepción trae un mensaje apto para el usuario; el detalle va a `ecotech.log` **sin** query string. |
| `r.json()["main"]["temp"]` | **Modificado** | Se extraen solo los campos necesarios, con `try/except` de `KeyError/IndexError/TypeError/ValueError` y verificación de tipos y rangos (temperatura −90..60 °C, humedad 0..100 %, tasa > 0 y finita). |
| Caída del servicio | **Agregado** | Tablas `consultas_clima` y `tipos_cambio` (SQLite, consultas parametrizadas): ante fallo recuperable se usa el último dato guardado y se avisa al usuario (continuidad operativa). No se usa respaldo ante 404/respuesta inválida/credenciales rechazadas. |
| `ErrorBaseDatos(f"...{e}")` (código previo) | **Modificado** | Mostraba el texto interno de SQLite; ahora mensaje genérico y detalle solo en el log. |
| `test_ecotech.py` previo | **Corregido** | Importaba módulos inexistentes (`modelos`, `repositorios`); se actualizaron los imports y se agregó `test_seguridad_servicios.py` (API simulada con `unittest.mock`, sin red). |

## 4. Limitaciones conocidas (honestidad técnica)
- Los salarios se asumen en CLP (`MONEDA_BASE`); la tasa es referencial, no instrumento de pago.
- La API gratuita de tipo de cambio no garantiza SLA; por eso existe el respaldo local.
- El bloqueo por intentos es por ejecución del programa (no persistente entre reinicios).
- Autenticación local de un solo rol; no hay autorización por perfiles.
