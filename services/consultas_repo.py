"""Persistencia local (SQLite) de lo consultado a las APIs: historial y respaldo (caché).

Si una API falla, el sistema puede seguir operando con el último dato guardado.
Todas las consultas SQL son parametrizadas (sin concatenar texto del usuario).
"""
from config.base_datos import ConexionBD


class ConsultasExternasRepo:
    def __init__(self, conexion: ConexionBD):
        self._conexion = conexion

    # ----- clima -----
    def guardar_clima(self, c):
        with self._conexion.cursor() as cur:
            cur.execute("INSERT INTO consultas_clima (ciudad, pais, temperatura, humedad, descripcion, codigo) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (c.ciudad.lower(), c.pais, c.temperatura, c.humedad, c.descripcion, c.codigo_condicion))

    def ultimo_clima(self, ciudad):
        with self._conexion.cursor() as cur:
            return cur.execute("SELECT * FROM consultas_clima WHERE ciudad = ? ORDER BY id_consulta DESC LIMIT 1",
                               (ciudad.lower(),)).fetchone()

    def historial_clima(self, limite=5):
        with self._conexion.cursor() as cur:
            return cur.execute("SELECT * FROM consultas_clima ORDER BY id_consulta DESC LIMIT ?",
                               (limite,)).fetchall()

    # ----- tipo de cambio -----
    def guardar_tasa(self, base, destino, tasa):
        with self._conexion.cursor() as cur:
            cur.execute("INSERT INTO tipos_cambio (base, destino, tasa) VALUES (?, ?, ?)", (base, destino, tasa))

    def ultima_tasa(self, base, destino):
        with self._conexion.cursor() as cur:
            return cur.execute("SELECT * FROM tipos_cambio WHERE base = ? AND destino = ? "
                               "ORDER BY id_tasa DESC LIMIT 1", (base, destino)).fetchone()

    def historial_tasas(self, limite=5):
        with self._conexion.cursor() as cur:
            return cur.execute("SELECT * FROM tipos_cambio ORDER BY id_tasa DESC LIMIT ?", (limite,)).fetchall()
