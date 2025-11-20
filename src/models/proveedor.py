"""
Modelo para Proveedor
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Proveedor:
    """Modelo para proveedores del negocio (según BD real)"""
    
    id_proveedor: Optional[int] = None
    nombre_empresa: str = ""
    id_persona_contacto: Optional[int] = None
    telefono_empresa: str = ""
    email_empresa: Optional[str] = None
    direccion_empresa: Optional[str] = None
    nit_empresa: Optional[str] = None
    sitio_web: Optional[str] = None
    tipo_proveedor: Optional[str] = None
    terminos_pago: Optional[str] = None
    estado: bool = True
    fecha_registro: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Datos denormalizados del contacto (para mostrar en UI)
    contacto_nombre: Optional[str] = None
    contacto_apellido: Optional[str] = None
    contacto_telefono: Optional[str] = None
    contacto_email: Optional[str] = None
    
    @property
    def nombre_contacto_completo(self) -> str:
        """Retorna el nombre completo del contacto"""
        if self.contacto_nombre and self.contacto_apellido:
            return f"{self.contacto_nombre} {self.contacto_apellido}"
        elif self.contacto_nombre:
            return self.contacto_nombre
        return "Sin contacto"
    
    def validar(self) -> tuple[bool, str]:
        """
        Valida los datos del proveedor
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if not self.nombre_empresa or not self.nombre_empresa.strip():
            return False, "El nombre de la empresa es obligatorio"
        
        if not self.telefono_empresa or not self.telefono_empresa.strip():
            return False, "El teléfono de la empresa es obligatorio"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        return {
            'id_proveedor': self.id_proveedor,
            'nombre_empresa': self.nombre_empresa,
            'id_persona_contacto': self.id_persona_contacto,
            'telefono_empresa': self.telefono_empresa,
            'email_empresa': self.email_empresa,
            'direccion_empresa': self.direccion_empresa,
            'nit_empresa': self.nit_empresa,
            'sitio_web': self.sitio_web,
            'tipo_proveedor': self.tipo_proveedor,
            'terminos_pago': self.terminos_pago,
            'estado': self.estado,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contacto_nombre': self.contacto_nombre,
            'contacto_apellido': self.contacto_apellido,
            'contacto_telefono': self.contacto_telefono,
            'contacto_email': self.contacto_email
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Proveedor':
        """Crea una instancia desde un diccionario"""
        # Parsear fechas si vienen como string
        fecha_registro = data.get('fecha_registro')
        if isinstance(fecha_registro, str):
            fecha_registro = datetime.fromisoformat(fecha_registro.replace('Z', '+00:00'))
        
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        return cls(
            id_proveedor=data.get('id_proveedor'),
            nombre_empresa=data.get('nombre_empresa', ''),
            id_persona_contacto=data.get('id_persona_contacto'),
            telefono_empresa=data.get('telefono_empresa', ''),
            email_empresa=data.get('email_empresa'),
            direccion_empresa=data.get('direccion_empresa'),
            nit_empresa=data.get('nit_empresa'),
            sitio_web=data.get('sitio_web'),
            tipo_proveedor=data.get('tipo_proveedor'),
            terminos_pago=data.get('terminos_pago'),
            estado=data.get('estado', True),
            fecha_registro=fecha_registro,
            created_at=created_at,
            updated_at=updated_at,
            contacto_nombre=data.get('contacto_nombre'),
            contacto_apellido=data.get('contacto_apellido'),
            contacto_telefono=data.get('contacto_telefono'),
            contacto_email=data.get('contacto_email')
        )
