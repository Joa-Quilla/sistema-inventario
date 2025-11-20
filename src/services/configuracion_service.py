"""
Servicio para gestión de configuración del sistema
"""
from repositories.configuracion_repository import ConfiguracionRepository
from typing import Dict, Any
import re


class ConfiguracionService:
    """Servicio para configuración del sistema"""
    
    def __init__(self):
        self.repository = ConfiguracionRepository()
    
    def obtener_configuracion(self) -> Dict[str, Any]:
        """Obtiene toda la configuración del sistema"""
        return self.repository.obtener_configuracion()
    
    def actualizar_configuracion(self, parametros: Dict[str, str]) -> Dict[str, Any]:
        """
        Actualiza la configuración del sistema con validaciones
        Args:
            parametros: Diccionario con parámetros a actualizar
        Returns:
            Dict con success y message
        """
        # Validar datos
        validacion = self._validar_parametros(parametros)
        if not validacion['success']:
            return validacion
        
        return self.repository.actualizar_configuracion(parametros)
    
    def _validar_parametros(self, parametros: Dict[str, str]) -> Dict[str, Any]:
        """Valida los parámetros antes de actualizar"""
        
        # Validar nombre de empresa
        if 'nombre_empresa' in parametros:
            if not parametros['nombre_empresa'].strip():
                return {'success': False, 'message': 'El nombre de la empresa es requerido'}
        
        # Validar NIT
        if 'nit_empresa' in parametros:
            nit = parametros['nit_empresa'].strip()
            if nit and not re.match(r'^\d{6,10}(-\d)?$', nit):
                return {'success': False, 'message': 'Formato de NIT inválido (ejemplo: 12345678-9)'}
        
        # Validar email
        if 'email_empresa' in parametros:
            email = parametros['email_empresa'].strip()
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return {'success': False, 'message': 'Formato de email inválido'}
        
        # Validar teléfono
        if 'telefono_empresa' in parametros:
            telefono = parametros['telefono_empresa'].strip()
            if telefono and not re.match(r'^[\d\-\(\)\s]{7,15}$', telefono):
                return {'success': False, 'message': 'Formato de teléfono inválido'}
        
        # Validar IVA (debe ser número entre 0 y 100)
        if 'iva' in parametros:
            try:
                iva = float(parametros['iva'])
                if iva < 0 or iva > 100:
                    return {'success': False, 'message': 'El IVA debe estar entre 0 y 100'}
            except ValueError:
                return {'success': False, 'message': 'El IVA debe ser un número válido'}
        
        # Validar stock mínimo
        if 'stock_minimo_alerta' in parametros:
            try:
                stock = int(parametros['stock_minimo_alerta'])
                if stock < 0:
                    return {'success': False, 'message': 'El stock mínimo no puede ser negativo'}
            except ValueError:
                return {'success': False, 'message': 'El stock mínimo debe ser un número entero'}
        
        # Validar días de vencimiento
        if 'dias_vencimiento_factura' in parametros:
            try:
                dias = int(parametros['dias_vencimiento_factura'])
                if dias < 1:
                    return {'success': False, 'message': 'Los días de vencimiento deben ser al menos 1'}
            except ValueError:
                return {'success': False, 'message': 'Los días de vencimiento deben ser un número entero'}
        
        return {'success': True}
    
    def obtener_valor(self, clave: str) -> str:
        """Obtiene el valor de un parámetro específico"""
        valor = self.repository.obtener_valor(clave)
        return valor if valor else ''
