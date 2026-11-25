1. 

Herramienta: Claude (Anthropic). Rol de la IA: apoyo en el diseño y la codificación

    1. Prompt: "Ayúdame a añadir a mi sistema de empleados de EcoTech el consumo de APIs de clima y tipo de cambio, autenticación, validación y manejo de errores, según la guía y la rúbrica de evaluacion." 

        Resultado: Estructura de módulos `seguridad/`, `services/`, ampliación de `excepciones/` y del menú.

    2. "Analiza el código generado: ¿qué vulnerabilidades tiene?"

        Resultado: 

            ```python
            API\_KEY = "a1b2c3..."                                   # (A) llave en el código
            def clima(ciudad):
                r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}\&appid={API\_KEY}")
                return r.json()\["main"]\["temp"]                     # (B) Sin `timeout`
            def login(u, p):
                return u == "admin" and p == "1234"                 # (C) credencial fija y en texto plano
            try: ...
            except Exception as e: print(f"Error: {e}")             # (D) expone la URL con la llave

        Vulnerabilidades principales:

            A) Llave de API en el código fuente (queda en Git/ZIP).

            B) Sin `timeout`: el programa puede quedar colgado indefinidamente.

            C) Autenticación con contraseña en texto plano, sin sal, sin límite de intentos; no vinculada al consumo de la API.

            D) `except Exception` genérico: oculta la causa y `requests` incluye la URL (con `appid`) en el mensaje.

3. Decisiones: modificación y descarte

    A) Fragmento: Acceso a la API (Modificado)
    
       Justificación tecnica: cada servicio llama a `sesion.exigir\_autenticado()` antes de validar o consultar: la ejecución queda ligada al estado de autenticación (probado: sin sesión, la API ni se invoca).

    B) Fragmento: Login con `==` (Descartado)

       Justificacion tecnica: mensaje genérico, 3 intentos, bloqueo y sesión con expiración por inactividad. Se eligió `hashlib` (librería estándar) para no depender de paquetes externos. 

4. Consulta a otra IA para que analizaran mi codigo.

Herramienta: Chat GPT (OpenAI). Rol de la IA: analisis del codigo

Prompt: "Puedes analizar el siguiente codigo."

Resultado:

   Mi valoración es que EcoTech Solutions es un proyecto bastante sólido y ambicioso para un trabajo académico de Python y POO.

   Sus mayores fortalezas son:
   1. Una arquitectura modular que separa correctamente las responsabilidades.
   2. Una aplicación consistente de los pilares de programación orientada a objetos.
   3. El uso de clases abstractas y herencia para reutilizar código.
   4. La implementación del patrón DAO para gestionar la persistencia.
   5. La integración de dos servicios externos mediante API.
   6. Un sistema de autenticación que incorpora hashing de contraseñas, validaciones y control de sesiones.
   Lo más interesante es que el proyecto combina varios conocimientos diferentes en una misma aplicación: POO, bases de datos, seguridad informática, manejo de   excepciones, solicitudes HTTP y servicios externos.

   Mi recomendación: no reestructuraría el proyecto desde cero. La arquitectura actual es buena. Me concentraría en corregir el control de sesiones, mejorar la administración de usuarios y añadir pruebas automatizadas.