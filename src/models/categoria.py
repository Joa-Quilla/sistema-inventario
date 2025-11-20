"""
Modelo para Categoría de productos
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Categoria:
    """Modelo para categorías de productos"""
    
    id_categoria: Optional[int] = None
    nombre: str = ""
    descripcion: Optional[str] = None
    estado: str = "activa"  # activa, inactiva
    fecha_creacion: Optional[datetime] = None
    
    def validar(self) -> tuple[bool, str]:
        """
        Valida los datos de la categoría
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if not self.nombre or not self.nombre.strip():
            return False, "El nombre de la categoría es obligatorio"
        
        if len(self.nombre) < 3:
            return False, "El nombre debe tener al menos 3 caracteres"
        
        if self.estado not in ["activa", "inactiva"]:
            return False, "Estado inválido"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        return {
            'id_categoria': self.id_categoria,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Categoria':
        """Crea una instancia desde un diccionario"""
        return cls(
            id_categoria=data.get('id_categoria'),
            nombre=data.get('nombre', ''),
            descripcion=data.get('descripcion'),
            estado=data.get('estado', 'activa'),
            fecha_creacion=data.get('fecha_creacion')
        )
