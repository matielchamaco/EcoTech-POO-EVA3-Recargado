Como ejecutar el programa

1. Abrir un entorno virtual (>python create enviroment)
2. Crear un archivo .env (copy .env.example .env)
3. Instalar las librerias correspondientes (pip install requirements)

Funciones principales

1. Administrador: para utilizar el programa necesitamos crear un usuario administrador, esto con el objetivo de asegurar el programa de gestion ante modificaciones externas, evitando que cualquier empleado trate de alterar la base de datos de la empresa gracias a la funcion de iniciar sesion.

2. Pagos Internacionales: esta opcion funciona mediante ServicioTipoCambio en services/tipo_cambio_service.py, se usan para convertir la moneda local (en este caso CLP) a otras monedas extranjeras.

   Consulta: ClienteHTTP.get_json hace un GET a https://open.er-api.com/v6/latest/CLP. Aplica timeout, reintentos, revisión del código HTTP y conversión de errores a excepciones propias.

   Aclaraciones: 
    1. La tasa es referencial y no sirve como instrumento de pago.
    2. Todo el salario se convierte a una sola moneda. No hay proporcionalidad por días ni por horas trabajadas.
    3. Se guarda la tasa consultada, pero no el pago calculado.

3. Clima: esta opcion funciona mediante ServicioClima en services/clima_service.py, y se usa para apoyar la toma de decisiones en la ejecución de proyectos mediante la medicion del clima en distintas ubicaciones.

   Consulta: arma los parámetros q, appid, units=metric y lang=es, y llama a ClienteHTTP.get_json. Este aplica timeout, reintentos, solo HTTPS y traduce los códigos HTTP a excepciones propias.

   Aclaraciones:
   1. No considera el viento (aunque la API lo entrega).
   2. Es el clima actual, no un pronóstico.

4. IA: por ahora estoy usando como apoyo a Claude de Anthropic, pero más adelante utilizaré otras como Gemini o Chat GPT, para comprobar si mi código esta bien estrucutrado o para probar otras soluciones.

