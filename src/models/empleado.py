"""
Modelo para Empleado
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from models.persona import Persona


@dataclass
class Empleado:
    """Modelo para empleados del negocio"""
    
    id_empleado: Optional[int] = None
    id_persona: Optional[int] = None
    id_rol: Optional[int] = None
    usuario: str = ""
    password_hash: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    salario: float = 0.0
    puesto: Optional[str] = None
    estado: bool = True  # BOOLEAN: True=activo, False=inactivo
    
    # Datos de persona y rol (denormalizados)
    persona: Optional[Persona] = None
    nombre_rol: Optional[str] = None
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del empleado"""
        if self.persona:
            return self.persona.nombre_completo
        return ""
    
    def validar(self) -> tuple[bool, str]:
        """
        Valida los datos del empleado
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if self.persona:
            es_valido, mensaje = self.persona.validar()
            if not es_valido:
                return False, mensaje
        
        if not self.usuario or not self.usuario.strip():
            return False, "El usuario es obligatorio"
        
        if len(self.usuario) < 3:
            return False, "El usuario debe tener al menos 3 caracteres"
        
        if self.salario < 0:
            return False, "El salario no puede ser negativo"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        data = {
            'id_empleado': self.id_empleado,
            'id_persona': self.id_persona,
            'id_rol': self.id_rol,
            'usuario': self.usuario,
            'password_hash': self.password_hash,
            'fecha_contratacion': self.fecha_contratacion,
            'salario': self.salario,
            'puesto': self.puesto,
            'estado': self.estado,
            'nombre_rol': self.nombre_rol
        }
        
        if self.persona:
            data['persona'] = self.persona.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Empleado':
        """Crea una instancia desde un diccionario"""
        persona = None
        if 'persona' in data:
            persona = Persona.from_dict(data['persona'])
        elif all(k in data for k in ['nombre', 'apellido']):
            persona = Persona(
                id_persona=data.get('id_persona'),
                nombre=data.get('nombre', ''),
                apellido=data.get('apellido', ''),
                dpi_nit=data.get('dpi_nit', ''),
                telefono=data.get('telefono'),
                email=data.get('email'),
                direccion=data.get('direccion'),
                estado=bool(data.get('estado', True))
            )
        
        # Convertir fecha_contratacion si es string
        fecha_contratacion = data.get('fecha_contratacion')
        if isinstance(fecha_contratacion, str):
            try:
                fecha_contratacion = datetime.strptime(fecha_contratacion, '%Y-%m-%d').date()
            except:
                fecha_contratacion = None
        
        return cls(
            id_empleado=data.get('id_empleado'),
            id_persona=data.get('id_persona'),
            id_rol=data.get('id_rol'),
            usuario=data.get('usuario', ''),
            password_hash=data.get('password_hash'),
            fecha_contratacion=fecha_contratacion,
            salario=data.get('salario', 0.0),
            puesto=data.get('puesto'),
            estado=bool(data.get('estado', True)),
            persona=persona,
            nombre_rol=data.get('nombre_rol')
        )
