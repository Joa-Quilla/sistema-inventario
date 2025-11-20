"""
Repositorio para gestión de configuración del sistema
"""
from typing import Dict, Any, Optional


class ConfiguracionRepository:
    """Repositorio para configuración del sistema (datos en memoria)"""
    
    # Configuración por defecto (datos ficticios en memoria)
    _configuracion = {
        'nombre_empresa': {
            'valor': 'Mi Empresa',
            'descripcion': 'Nombre de la empresa',
            'tipo': 'texto'
        },
        'nit_empresa': {
            'valor': '12345678-9',
            'descripcion': 'NIT de la empresa',
            'tipo': 'texto'
        },
        'direccion_empresa': {
            'valor': 'Ciudad de Guatemala',
            'descripcion': 'Dirección de la empresa',
            'tipo': 'texto'
        },
        'telefono_empresa': {
            'valor': '2222-2222',
            'descripcion': 'Teléfono de la empresa',
            'tipo': 'texto'
        },
        'email_empresa': {
            'valor': 'info@empresa.com',
            'descripcion': 'Email de la empresa',
            'tipo': 'email'
        },
        'iva': {
            'valor': '12',
            'descripcion': 'Porcentaje de IVA',
            'tipo': 'numero'
        },
        'moneda': {
            'valor': 'Q',
            'descripcion': 'Símbolo de moneda',
            'tipo': 'texto'
        },
        'prefijo_factura': {
            'valor': 'FACT',
            'descripcion': 'Prefijo para número de factura',
            'tipo': 'texto'
        },
        'stock_minimo_alerta': {
            'valor': '10',
            'descripcion': 'Stock mínimo para alertas',
            'tipo': 'numero'
        },
        'dias_vencimiento_factura': {
            'valor': '30',
            'descripcion': 'Días de vencimiento de facturas',
            'tipo': 'numero'
        }
    }
    
    @staticmethod
    def obtener_configuracion() -> Dict[str, Any]:
        """
        Obtiene toda la configuración del sistema
        Returns:
            Dict con todos los parámetros de configuración
        """
        return {
            'success': True,
            'configuracion': ConfiguracionRepository._configuracion.copy()
        }
    
    @staticmethod
    def actualizar_configuracion(parametros: Dict[str, str]) -> Dict[str, Any]:
        """
        Actualiza múltiples parámetros de configuración
        Args:
            parametros: Diccionario con clave-valor de parámetros a actualizar
        Returns:
            Dict con success y message
        """
        try:
            for clave, valor in parametros.items():
                if clave in ConfiguracionRepository._configuracion:
                    ConfiguracionRepository._configuracion[clave]['valor'] = valor
            
            return {'success': True, 'message': 'Configuración actualizada correctamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error al actualizar configuración: {str(e)}'}
    
    @staticmethod
    def obtener_valor(clave: str) -> Optional[str]:
        """
        Obtiene el valor de un parámetro específico
        Args:
            clave: Clave del parámetro
        Returns:
            Valor del parámetro o None
        """
        if clave in ConfiguracionRepository._configuracion:
            return ConfiguracionRepository._configuracion[clave]['valor']
        return None
