"""
Modelo para Cliente
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from models.persona import Persona


@dataclass
class Cliente:
    """Modelo para clientes del negocio"""
    
    id_cliente: Optional[int] = None
    id_persona: Optional[int] = None
    tipo_cliente: str = "minorista"  # minorista, mayorista
    limite_credito: float = 0.0
    descuento_habitual: float = 0.0
    fecha_primera_compra: Optional[date] = None
    total_compras: float = 0.0
    estado: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    # Datos de persona (denormalizados para facilitar uso)
    persona: Optional[Persona] = None
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del cliente"""
        if self.persona:
            return f"{self.persona.nombre} {self.persona.apellido or ''}".strip()
        return ""
    
    @property
    def nit(self) -> Optional[str]:
        """Retorna el NIT desde persona.dpi_nit"""
        if self.persona:
            return self.persona.dpi_nit
        return None
    
    def validar(self) -> tuple[bool, str]:
        """
        Valida los datos del cliente
        
        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if self.persona:
            es_valido, mensaje = self.persona.validar()
            if not es_valido:
                return False, mensaje
        
        if self.limite_credito < 0:
            return False, "El límite de crédito no puede ser negativo"
        
        if self.descuento_habitual < 0 or self.descuento_habitual > 100:
            return False, "El descuento debe estar entre 0 y 100%"
        
        if self.tipo_cliente not in ["minorista", "mayorista"]:
            return False, "Tipo de cliente inválido (debe ser minorista o mayorista)"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario"""
        data = {
            'id_cliente': self.id_cliente,
            'id_persona': self.id_persona,
            'tipo_cliente': self.tipo_cliente,
            'limite_credito': self.limite_credito,
            'descuento_habitual': self.descuento_habitual,
            'fecha_primera_compra': self.fecha_primera_compra.isoformat() if self.fecha_primera_compra else None,
            'total_compras': self.total_compras,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
        
        if self.persona:
            data['persona'] = self.persona.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Cliente':
        """Crea una instancia desde un diccionario"""
        persona = None
        if 'persona' in data and data['persona']:
            persona = Persona.from_dict(data['persona'])
        elif 'nombre' in data:
            # Crear persona desde datos planos del JOIN
            # Parsear fecha_registro si viene
            fecha_registro = None
            if data.get('fecha_registro'):
                val = data['fecha_registro']
                if isinstance(val, datetime):
                    fecha_registro = val
                elif isinstance(val, str):
                    fecha_registro = datetime.fromisoformat(val.replace('Z', '+00:00'))
            
            persona = Persona(
                id_persona=data.get('id_persona'),
                nombre=data.get('nombre', ''),
                apellido=data.get('apellido', ''),
                telefono=data.get('telefono'),
                email=data.get('email'),
                direccion=data.get('direccion'),
                dpi_nit=data.get('dpi_nit'),
                fecha_registro=fecha_registro,
                estado=data.get('persona_estado', True)
            )
        
        # Parsear fechas
        fecha_primera_compra = None
        if data.get('fecha_primera_compra'):
            if isinstance(data['fecha_primera_compra'], date):
                fecha_primera_compra = data['fecha_primera_compra']
            elif isinstance(data['fecha_primera_compra'], str):
                from datetime import datetime as dt
                fecha_primera_compra = dt.fromisoformat(data['fecha_primera_compra']).date()
        
        fecha_creacion = None
        if data.get('created_at') or data.get('fecha_creacion'):
            val = data.get('created_at') or data.get('fecha_creacion')
            if isinstance(val, datetime):
                fecha_creacion = val
            elif isinstance(val, str):
                fecha_creacion = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        fecha_actualizacion = None
        if data.get('updated_at') or data.get('fecha_actualizacion'):
            val = data.get('updated_at') or data.get('fecha_actualizacion')
            if isinstance(val, datetime):
                fecha_actualizacion = val
            elif isinstance(val, str):
                fecha_actualizacion = datetime.fromisoformat(val.replace('Z', '+00:00'))
        
        return cls(
            id_cliente=data.get('id_cliente'),
            id_persona=data.get('id_persona'),
            tipo_cliente=data.get('tipo_cliente', 'minorista'),
            limite_credito=float(data.get('limite_credito', 0)),
            descuento_habitual=float(data.get('descuento_habitual', 0)),
            fecha_primera_compra=fecha_primera_compra,
            total_compras=float(data.get('total_compras', 0)),
            estado=bool(data.get('estado', True)),
            fecha_creacion=fecha_creacion,
            fecha_actualizacion=fecha_actualizacion,
            persona=persona
        )

