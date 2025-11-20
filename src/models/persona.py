"""
Modelo base para Persona (entidad centralizada)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Persona:
    """Modelo base para personas (clientes, empleados, proveedores)"""
    
    id_persona: Optional[int] = None
    nombre: str = ""
    apellido: str = ""
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    dpi_nit: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    estado: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo"""
        return f"{self.nombre} {self.apellido or ''}".strip()
    
    def validar(self) -> tuple[bool, str]:
        """
        Valida los datos de la persona
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if not self.nombre or not self.nombre.strip():
            return False, "El nombre es obligatorio"
        
        if not self.apellido or not self.apellido.strip():
            return False, "El apellido es obligatorio"
        
        # Email opcional pero si existe debe ser válido
        if self.email and '@' not in self.email:
            return False, "El formato del email es inválido"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        return {
            'id_persona': self.id_persona,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'telefono': self.telefono,
            'email': self.email,
            'direccion': self.direccion,
            'dpi_nit': self.dpi_nit,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'estado': self.estado,
            'created_at': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'updated_at': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Persona':
        """Crea una instancia desde un diccionario"""
        # Parsear fechas
        fecha_registro = None
        if data.get('fecha_registro'):
            val = data['fecha_registro']
            if isinstance(val, datetime):
                fecha_registro = val
            elif isinstance(val, str):
                fecha_registro = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        fecha_creacion = None
        if data.get('created_at'):
            val = data['created_at']
            if isinstance(val, datetime):
                fecha_creacion = val
            elif isinstance(val, str):
                fecha_creacion = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        fecha_actualizacion = None
        if data.get('updated_at'):
            val = data['updated_at']
            if isinstance(val, datetime):
                fecha_actualizacion = val
            elif isinstance(val, str):
                fecha_actualizacion = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        return cls(
            id_persona=data.get('id_persona'),
            nombre=data.get('nombre', ''),
            apellido=data.get('apellido', ''),
            telefono=data.get('telefono'),
            email=data.get('email'),
            direccion=data.get('direccion'),
            dpi_nit=data.get('dpi_nit'),
            fecha_registro=fecha_registro,
            estado=bool(data.get('estado', True)),
            fecha_creacion=fecha_creacion,
            fecha_actualizacion=fecha_actualizacion
        )
