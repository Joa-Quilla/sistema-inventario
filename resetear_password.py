"""
Script para resetear contraseñas de usuarios
"""
import hashlib
from src.database import DatabaseConnection

def hash_password(password: str) -> str:
    """Encripta una contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    db = DatabaseConnection()
    
    print("=" * 60)
    print("RESETEAR CONTRASEÑA DE USUARIO")
    print("=" * 60)
    
    # Listar usuarios
    query = """
        SELECT 
            e.id_empleado,
            e.usuario,
            r.nombre as rol,
            p.nombre,
            p.apellido
        FROM empleados e
        JOIN personas p ON e.id_persona = p.id_persona
        LEFT JOIN roles r ON e.id_rol = r.id_rol
        WHERE e.estado = true
        ORDER BY e.id_empleado
    """
    
    usuarios = db.execute_query(query)
    
    if not usuarios:
        print("\n⚠️  No hay usuarios activos en la base de datos")
        return
    
    print("\nUsuarios disponibles:\n")
    for i, u in enumerate(usuarios, 1):
        print(f"{i}. {u['usuario']} - {u['nombre']} {u['apellido']} ({u['rol']})")
    
    print("\nIngrese el número del usuario (o 0 para salir): ", end="")
    try:
        opcion = int(input().strip())
        
        if opcion == 0:
            print("Saliendo...")
            return
        
        if opcion < 1 or opcion > len(usuarios):
            print("❌ Opción inválida")
            return
        
        usuario_seleccionado = usuarios[opcion - 1]
        
        print(f"\nUsuario seleccionado: {usuario_seleccionado['usuario']}")
        print("Ingrese la nueva contraseña: ", end="")
        nueva_password = input().strip()
        
        if len(nueva_password) < 4:
            print("❌ La contraseña debe tener al menos 4 caracteres")
            return
        
        # Actualizar contraseña
        password_hash = hash_password(nueva_password)
        update_query = """
            UPDATE empleados 
            SET password = %s 
            WHERE id_empleado = %s
        """
        
        db.execute_query(update_query, (password_hash, usuario_seleccionado['id_empleado']), fetch=False)
        
        print(f"\n✅ Contraseña actualizada exitosamente")
        print(f"\nCredenciales:")
        print(f"   Usuario: {usuario_seleccionado['usuario']}")
        print(f"   Contraseña: {nueva_password}")
        
    except ValueError:
        print("❌ Debe ingresar un número")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
