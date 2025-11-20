"""
Script para verificar y crear usuarios de prueba
"""
import hashlib
from src.database import DatabaseConnection

def hash_password(password: str) -> str:
    """Encripta una contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    db = DatabaseConnection()
    
    print("=" * 60)
    print("VERIFICACIÓN DE USUARIOS EN LA BASE DE DATOS")
    print("=" * 60)
    
    # Consultar todos los usuarios
    query = """
        SELECT 
            e.id_empleado,
            e.usuario,
            e.estado as empleado_activo,
            r.nombre as rol,
            p.nombre,
            p.apellido,
            p.estado as persona_activa
        FROM empleados e
        JOIN personas p ON e.id_persona = p.id_persona
        LEFT JOIN roles r ON e.id_rol = r.id_rol
        ORDER BY e.id_empleado
    """
    
    usuarios = db.execute_query(query)
    
    if not usuarios:
        print("\n⚠️  No hay usuarios en la base de datos")
    else:
        print(f"\n✅ Se encontraron {len(usuarios)} usuarios:\n")
        print(f"{'ID':<5} {'Usuario':<15} {'Nombre':<25} {'Rol':<15} {'Estado Emp':<12} {'Estado Per':<12}")
        print("-" * 100)
        for u in usuarios:
            print(f"{u['id_empleado']:<5} {u['usuario']:<15} {u['nombre']} {u['apellido']:<25} {u['rol']:<15} {'✅ Activo' if u['empleado_activo'] else '❌ Inactivo':<12} {'✅ Activo' if u['persona_activa'] else '❌ Inactivo':<12}")
    
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE ROLES")
    print("=" * 60)
    
    query_roles = "SELECT id_rol, nombre, descripcion FROM roles ORDER BY id_rol"
    roles = db.execute_query(query_roles)
    
    if not roles:
        print("\n⚠️  No hay roles en la base de datos")
    else:
        print(f"\n✅ Se encontraron {len(roles)} roles:\n")
        for r in roles:
            print(f"ID: {r['id_rol']} - {r['nombre']} ({r['descripcion']})")
    
    print("\n" + "=" * 60)
    print("¿Deseas crear usuarios de prueba? (s/n): ", end="")
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        crear_usuarios_prueba(db, roles)

def crear_usuarios_prueba(db, roles):
    """Crea usuarios de prueba si no existen"""
    
    # Buscar roles por nombre
    rol_admin = next((r for r in roles if r['nombre'].lower() == 'administrador'), None)
    rol_vendedor = next((r for r in roles if r['nombre'].lower() == 'vendedor'), None)
    rol_cajero = next((r for r in roles if r['nombre'].lower() == 'cajero'), None)
    
    if not rol_admin or not rol_vendedor or not rol_cajero:
        print("\n❌ Error: No se encontraron los roles necesarios (Administrador, Vendedor, Cajero)")
        return
    
    usuarios_crear = [
        {
            'usuario': 'admin',
            'password': 'admin123',
            'id_rol': rol_admin['id_rol'],
            'puesto': 'Administrador del Sistema',
            'nombre': 'Administrador',
            'apellido': 'Sistema',
            'dpi': '1234567890101',
            'email': 'admin@sistema.com',
            'telefono': '12345678'
        },
        {
            'usuario': 'vendedor1',
            'password': 'vendedor123',
            'id_rol': rol_vendedor['id_rol'],
            'puesto': 'Vendedor',
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'dpi': '1234567890102',
            'email': 'vendedor@sistema.com',
            'telefono': '12345679'
        },
        {
            'usuario': 'cajero1',
            'password': 'cajero123',
            'id_rol': rol_cajero['id_rol'],
            'puesto': 'Cajero',
            'nombre': 'María',
            'apellido': 'García',
            'dpi': '1234567890103',
            'email': 'cajero@sistema.com',
            'telefono': '12345680'
        }
    ]
    
    print("\n" + "=" * 60)
    print("CREANDO USUARIOS DE PRUEBA")
    print("=" * 60 + "\n")
    
    for user_data in usuarios_crear:
        try:
            # Verificar si el usuario ya existe
            check_query = "SELECT id_empleado FROM empleados WHERE usuario = %s"
            existe = db.execute_query(check_query, (user_data['usuario'],))
            
            if existe:
                print(f"⚠️  Usuario '{user_data['usuario']}' ya existe - omitiendo...")
                continue
            
            # Verificar si la persona ya existe
            check_persona = "SELECT id_persona FROM personas WHERE dpi = %s"
            persona_existe = db.execute_query(check_persona, (user_data['dpi'],))
            
            if persona_existe:
                id_persona = persona_existe[0]['id_persona']
                print(f"   Usando persona existente con DPI {user_data['dpi']}")
            else:
                # Crear persona
                insert_persona = """
                    INSERT INTO personas (nombre, apellido, dpi, email, telefono, direccion, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, true)
                    RETURNING id_persona
                """
                resultado_persona = db.execute_query(
                    insert_persona,
                    (user_data['nombre'], user_data['apellido'], user_data['dpi'], 
                     user_data['email'], user_data['telefono'], 'Dirección de prueba')
                )
                id_persona = resultado_persona[0]['id_persona']
            
            # Crear empleado
            password_hash = hash_password(user_data['password'])
            insert_empleado = """
                INSERT INTO empleados (id_persona, id_rol, usuario, password, puesto, estado)
                VALUES (%s, %s, %s, %s, %s, true)
                RETURNING id_empleado
            """
            resultado_empleado = db.execute_query(
                insert_empleado,
                (id_persona, user_data['id_rol'], user_data['usuario'], password_hash, user_data['puesto'])
            )
            
            print(f"✅ Usuario '{user_data['usuario']}' creado exitosamente")
            print(f"   Contraseña: {user_data['password']}")
            print(f"   Rol: {user_data['puesto']}")
            
        except Exception as e:
            print(f"❌ Error creando usuario '{user_data['usuario']}': {e}")
    
    print("\n" + "=" * 60)
    print("USUARIOS DE PRUEBA DISPONIBLES:")
    print("=" * 60)
    print("\n1. Usuario: admin")
    print("   Contraseña: admin123")
    print("   Rol: Administrador\n")
    print("2. Usuario: vendedor1")
    print("   Contraseña: vendedor123")
    print("   Rol: Vendedor\n")
    print("3. Usuario: cajero1")
    print("   Contraseña: cajero123")
    print("   Rol: Cajero\n")

if __name__ == "__main__":
    main()
