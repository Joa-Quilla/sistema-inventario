"""
Repositorio para operaciones CRUD de Categorías
"""
from typing import List, Optional, Dict, Any
from database.connection import DatabaseConnection
from models.categoria import Categoria


class CategoriaRepository:
    """Repositorio para gestión de categorías"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def crear(self, categoria: Categoria) -> Dict[str, Any]:
        """
        Crea una nueva categoría
        
        Args:
            categoria: Objeto Categoria a crear
            
        Returns:
            Dict con 'success' (bool), 'message' (str), 'id_categoria' (int si success=True)
        """
        try:
            # Validar
            es_valido, mensaje = categoria.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            # Verificar que no exista una categoría con el mismo nombre
            existe = self.obtener_por_nombre(categoria.nombre)
            if existe:
                return {'success': False, 'message': f'Ya existe una categoría con el nombre "{categoria.nombre}"'}
            
            query = """
                INSERT INTO categorias (nombre, descripcion, estado)
                VALUES (%s, %s, %s)
                RETURNING id_categoria, created_at as fecha_creacion
            """
            
            estado_bool = categoria.estado == 'activa'
            result = self.db.execute_query(
                query,
                (categoria.nombre, categoria.descripcion, estado_bool),
                fetch='one'
            )
            
            if result:
                return {
                    'success': True,
                    'message': 'Categoría creada exitosamente',
                    'id_categoria': result['id_categoria'],
                    'fecha_creacion': result['fecha_creacion']
                }
            else:
                return {'success': False, 'message': 'Error al crear la categoría'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def obtener_por_id(self, id_categoria: int) -> Optional[Categoria]:
        """Obtiene una categoría por su ID"""
        query = """
            SELECT 
                id_categoria, 
                nombre, 
                descripcion, 
                CASE WHEN estado THEN 'activa' ELSE 'inactiva' END as estado,
                created_at as fecha_creacion
            FROM categorias
            WHERE id_categoria = %s
        """
        
        result = self.db.execute_query(query, (id_categoria,), fetch='one')
        
        if result:
            return Categoria.from_dict(result)
        return None
    
    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        """Obtiene una categoría por su nombre"""
        query = """
            SELECT 
                id_categoria, 
                nombre, 
                descripcion, 
                CASE WHEN estado THEN 'activa' ELSE 'inactiva' END as estado,
                created_at as fecha_creacion
            FROM categorias
            WHERE LOWER(nombre) = LOWER(%s)
        """
        
        result = self.db.execute_query(query, (nombre,), fetch='one')
        
        if result:
            return Categoria.from_dict(result)
        return None
    
    def listar(self, solo_activas: bool = False, busqueda: str = None) -> List[Categoria]:
        """
        Lista todas las categorías
        
        Args:
            solo_activas: Si True, solo retorna categorías activas
            busqueda: Término de búsqueda opcional (busca en nombre y descripción)
        """
        query = """
            SELECT 
                id_categoria, 
                nombre, 
                descripcion, 
                CASE WHEN estado THEN 'activa' ELSE 'inactiva' END as estado,
                created_at as fecha_creacion
            FROM categorias
            WHERE 1=1
        """
        params = []
        
        if solo_activas:
            query += " AND estado = TRUE"
        
        if busqueda:
            query += " AND (LOWER(nombre) LIKE LOWER(%s) OR LOWER(descripcion) LIKE LOWER(%s))"
            params.extend([f'%{busqueda}%', f'%{busqueda}%'])
        
        query += " ORDER BY nombre ASC"
        
        result = self.db.execute_query(query, tuple(params) if params else None, fetch='all')
        
        if result:
            return [Categoria.from_dict(row) for row in result]
        return []
    
    def actualizar(self, categoria: Categoria) -> Dict[str, Any]:
        """
        Actualiza una categoría existente
        
        Args:
            categoria: Objeto Categoria con datos actualizados
            
        Returns:
            Dict con 'success' (bool) y 'message' (str)
        """
        try:
            # Validar
            es_valido, mensaje = categoria.validar()
            if not es_valido:
                return {'success': False, 'message': mensaje}
            
            if not categoria.id_categoria:
                return {'success': False, 'message': 'ID de categoría no especificado'}
            
            # Verificar que no exista otra categoría con el mismo nombre
            existe = self.db.execute_query(
                "SELECT id_categoria FROM categorias WHERE LOWER(nombre) = LOWER(%s) AND id_categoria != %s",
                (categoria.nombre, categoria.id_categoria),
                fetch='one'
            )
            if existe:
                return {'success': False, 'message': f'Ya existe otra categoría con el nombre "{categoria.nombre}"'}
            
            query = """
                UPDATE categorias
                SET nombre = %s,
                    descripcion = %s,
                    estado = %s
                WHERE id_categoria = %s
            """
            
            estado_bool = categoria.estado == 'activa'
            self.db.execute_query(
                query,
                (categoria.nombre, categoria.descripcion, estado_bool, categoria.id_categoria),
                fetch=False
            )
            
            return {'success': True, 'message': 'Categoría actualizada exitosamente'}
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def eliminar(self, id_categoria: int) -> Dict[str, Any]:
        """
        Elimina (desactiva) una categoría
        
        Args:
            id_categoria: ID de la categoría a eliminar
            
        Returns:
            Dict con 'success' (bool) y 'message' (str)
        """
        try:
            # Verificar si tiene productos asociados
            productos = self.db.execute_query(
                "SELECT COUNT(*) as total FROM productos WHERE id_categoria = %s",
                (id_categoria,),
                fetch='one'
            )
            
            if productos and productos['total'] > 0:
                # No eliminar físicamente, solo desactivar
                query = "UPDATE categorias SET estado = FALSE WHERE id_categoria = %s"
                self.db.execute_query(query, (id_categoria,), fetch=False)
                return {
                    'success': True,
                    'message': f'Categoría desactivada (tiene {productos["total"]} productos asociados)'
                }
            else:
                # Eliminar físicamente si no tiene productos
                query = "DELETE FROM categorias WHERE id_categoria = %s"
                self.db.execute_query(query, (id_categoria,), fetch=False)
                return {'success': True, 'message': 'Categoría eliminada exitosamente'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def contar_productos(self, id_categoria: int) -> int:
        """Cuenta cuántos productos tiene una categoría"""
        result = self.db.execute_query(
            "SELECT COUNT(*) as total FROM productos WHERE id_categoria = %s",
            (id_categoria,),
            fetch='one'
        )
        return result['total'] if result else 0
