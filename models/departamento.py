import math
import re
from models.entidadbase import EntidadBase

class Departamento(EntidadBase):
    def __init__(self, id_depto, nombre, id_gerente=None):
        self._id_depto = self._validar_id(id_depto, "id_depto")
        self.nombre = nombre
        self.id_gerente = id_gerente

    @property
    def id_depto(self):
        return self._id_depto

    @id_depto.setter
    def id_depto(self, valor):
        self._id_depto = self._validar_id(valor, "id_depto")

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = self._validar_texto(valor, "El nombre del departamento")

    @property
    def id_gerente(self):
        return self._id_gerente

    @id_gerente.setter
    def id_gerente(self, valor):
        self._id_gerente = self._validar_id(valor, "id_gerente")

    def editar_departamento(self, nuevo_nombre: str) -> None:
        self.nombre = nuevo_nombre

    def __str__(self):
        gerente = self._id_gerente if self._id_gerente else "sin gerente"
        return f"[Depto {self._id_depto}] {self._nombre} (gerente: {gerente})"