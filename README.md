Como ejecutar el programa

1. Abrir un entorno virtual (>python create enviroment)
2. Crear un archivo .env ("copy .env.example .env" en la consola)
3. Instalar las librerias correspondientes ("pip install requests" en la consola) / PD: En la evaluacion formativa por error habia puesto "requirements", la cual no se utiliza ya que no existe un archivo requirements.txt.

Funciones principales

1. Seguridad:

   1. Inicio de sesión con contraseñas cifradas (PBKDF2 con sal por usuario), mensaje de error genérico y bloqueo tras 3 intentos.
   2. En el primer uso el programa te pide crear el usuario administrador.
   3. Los servicios exigen sesión autenticada antes de hacer cualquier cosa, y la sesión expira a los 15 minutos de inactividad.
   4. La ciudad, la moneda, el usuario y la contraseña se validan con listas blancas.
   5. La llave de la API va en .env, que no se sube al repositorio; se incluye .env.example como plantilla.

2. Pagos Internacionales: esta opcion funciona mediante ServicioTipoCambio en services/tipo_cambio_service.py, utilizando ExchangeRate-API para convertir salarios almacenados en pesos chilenos a otras monedas.

   Consulta: ClienteHTTP.get_json hace un GET a https://open.er-api.com/v6/latest/CLP. Aplica timeout, reintentos, revisión del código HTTP y conversión de errores a excepciones propias.

   Aclaraciones: 
    1. La tasa es referencial y no sirve como instrumento de pago.
    2. Todo el salario se convierte a una sola moneda. No hay proporcionalidad por días ni por horas trabajadas.
    3. Se guarda la tasa consultada, pero no el pago calculado.

3. Clima: esta opcion funciona mediante ServicioClima en services/clima_service.py, y se usa para apoyar la toma de decisiones en la ejecución de proyectos mediante la medicion del clima en distintas ubicaciones. Utiliza OpenWeatherMap para consultar las condiciones meteorológicas actuales de una ciudad.

   Clasifica las condiciones en tres niveles:
      - ALTO: condiciones climáticas severas o temperaturas extremas.
      - MEDIO: lluvia, nieve o humedad elevada.
      - BAJO: condiciones consideradas favorables.

   Consulta: arma los parámetros q, appid, units=metric y lang=es, y llama a ClienteHTTP.get_json. Este aplica timeout, reintentos, solo HTTPS y traduce los códigos HTTP a excepciones propias.

   Aclaraciones:
   1. No considera el viento (aunque la API lo entrega).
   2. Es el clima actual, no un pronóstico.

Resumiendo: Tanto la funcion Clima como Pagos Internacinales usan requests y reciben el JSON. De la respuesta se toman solo los campos necesarios, comprobando tipo y rango.

4. Uso de .gitignore: archivo de texto que le indica a Git qué archivos o carpetas ignorar y no incluir en el control de versiones, la cual se utiliza en este caso para evitar subir archivos .env, ya que contiene datos sensibles del programa que no pueden ser subidos a internet, razon por la cual existe el archivo .env.example, ademas de otros archivos que de igual forma no se recomiendan ser subidos al repositorio como .db, .log y el cache del programa.

5. Manejo de errores:

   1. Hay un timeout, reintentos acotados y solo se permite HTTPS.
   2. Tiene excepciones propias para cada tipo de fallo y trata los códigos 200, 400, 401/403, 404, 429 y 5xx de forma distinta.
   3. Los mensajes al usuario no incluyen la URL ni la llave, y el detalle técnico queda en ecotech.log.
   4. Cada consulta se guarda en SQLite. Si la API cae, el sistema usa el último dato guardado y avisa al usuario.

6. Limitaciones Tecnicas: 

   1. El bloqueo por intentos es por ejecución del programa, por lo que al reinciar los intentos tambien se reinician.
   2. Autenticación local de un solo rol; no hay autorización por perfiles.

---------------------------------------------------------------------------------------------------------------------------------------------------------------
