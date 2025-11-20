-- ========================================
-- SISTEMA DE INVENTARIO - BASE DE DATOS
-- PostgreSQL 12+
-- ========================================

-- Conectarse a la base de datos
-- \c sistema_inventario;

-- Eliminar tablas si existen (para recrear limpio)
DROP TABLE IF EXISTS logs_sistema CASCADE;
DROP TABLE IF EXISTS movimientos_caja CASCADE;
DROP TABLE IF EXISTS detalle_ventas CASCADE;
DROP TABLE IF EXISTS ventas CASCADE;
DROP TABLE IF EXISTS detalle_compras CASCADE;
DROP TABLE IF EXISTS compras CASCADE;
DROP TABLE IF EXISTS cajas CASCADE;
DROP TABLE IF EXISTS historial_precios CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;
DROP TABLE IF EXISTS roles_permisos CASCADE;
DROP TABLE IF EXISTS permisos CASCADE;
DROP TABLE IF EXISTS proveedores CASCADE;
DROP TABLE IF EXISTS empleados CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS personas CASCADE;

-- ========================================
-- TABLA: PERSONAS (CENTRALIZADA)
-- ========================================
CREATE TABLE personas (
    id_persona SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    direccion TEXT,
    dpi_nit VARCHAR(20) UNIQUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_personas_nombre_apellido ON personas(nombre, apellido);
CREATE INDEX idx_personas_email ON personas(email);
CREATE INDEX idx_personas_dpi ON personas(dpi_nit);

COMMENT ON TABLE personas IS 'Tabla centralizada para evitar duplicación de datos personales';

-- ========================================
-- TABLA: ROLES
-- ========================================

CREATE TABLE roles (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    estado BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE roles IS 'Define los roles disponibles en el sistema';

-- ========================================
-- TABLA: CLIENTES
-- ========================================

CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE REFERENCES personas(id_persona) ON DELETE RESTRICT,
    tipo_cliente VARCHAR(20) DEFAULT 'minorista',
    limite_credito DECIMAL(10,2) DEFAULT 0,
    descuento_habitual DECIMAL(5,2) DEFAULT 0,
    fecha_primera_compra DATE,
    total_compras DECIMAL(12,2) DEFAULT 0,
    estado BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clientes_persona ON clientes(id_persona);
CREATE INDEX idx_clientes_tipo ON clientes(tipo_cliente);

COMMENT ON TABLE clientes IS 'Contiene solo datos específicos del rol de cliente';

-- ========================================
-- TABLA: EMPLEADOS
-- ========================================
CREATE TABLE empleados (
    id_empleado SERIAL PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE REFERENCES personas(id_persona) ON DELETE RESTRICT,
    id_rol INT NOT NULL REFERENCES roles(id_rol),
    puesto VARCHAR(50) NOT NULL,
    salario DECIMAL(10,2),
    fecha_contratacion DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_terminacion DATE,
    estado BOOLEAN DEFAULT true,
    usuario VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    ultimo_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_empleados_persona ON empleados(id_persona);
CREATE INDEX idx_empleados_rol ON empleados(id_rol);
CREATE INDEX idx_empleados_usuario ON empleados(usuario);
CREATE INDEX idx_empleados_estado ON empleados(estado);

COMMENT ON TABLE empleados IS 'Contiene solo datos específicos del rol de empleado';

-- ========================================
-- TABLA: PROVEEDORES
-- ========================================
CREATE TABLE proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    nombre_empresa VARCHAR(150) NOT NULL UNIQUE,
    id_persona_contacto INT REFERENCES personas(id_persona) ON DELETE SET NULL,
    telefono_empresa VARCHAR(20) NOT NULL,
    email_empresa VARCHAR(100),
    direccion_empresa TEXT,
    nit_empresa VARCHAR(20) UNIQUE,
    sitio_web VARCHAR(100),
    tipo_proveedor VARCHAR(50),
    terminos_pago VARCHAR(50),
    estado BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_proveedores_empresa ON proveedores(nombre_empresa);
CREATE INDEX idx_proveedores_nit ON proveedores(nit_empresa);
CREATE INDEX idx_proveedores_contacto ON proveedores(id_persona_contacto);

COMMENT ON TABLE proveedores IS 'Representa empresas proveedoras con persona de contacto';

-- ========================================
-- TABLA: PERMISOS
-- ========================================
CREATE TABLE permisos (
    id_permiso SERIAL PRIMARY KEY,
    modulo VARCHAR(50) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(modulo, accion)
);

CREATE INDEX idx_permisos_modulo ON permisos(modulo);

COMMENT ON TABLE permisos IS 'Define permisos específicos para cada módulo del sistema';

-- ========================================
-- TABLA: ROLES_PERMISOS (Relación N:N)
-- ========================================
CREATE TABLE roles_permisos (
    id_rol_permiso SERIAL PRIMARY KEY,
    id_rol INT NOT NULL REFERENCES roles(id_rol) ON DELETE CASCADE,
    id_permiso INT NOT NULL REFERENCES permisos(id_permiso) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(id_rol, id_permiso)
);

CREATE INDEX idx_roles_permisos_rol ON roles_permisos(id_rol);
CREATE INDEX idx_roles_permisos_permiso ON roles_permisos(id_permiso);

COMMENT ON TABLE roles_permisos IS 'Asigna permisos a roles (muchos a muchos)';

-- ========================================
-- TABLA: CATEGORIAS
-- ========================================
CREATE TABLE categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    estado BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categorias_nombre ON categorias(nombre);

-- ========================================
-- TABLA: PRODUCTOS
-- ========================================
CREATE TABLE productos (
    id_producto SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    id_categoria INT REFERENCES categorias(id_categoria) ON DELETE SET NULL,
    precio_costo DECIMAL(10,2) NOT NULL,
    precio_venta DECIMAL(10,2) NOT NULL,
    margen_ganancia DECIMAL(5,2),
    stock_actual INT DEFAULT 0,
    stock_minimo INT DEFAULT 10,
    unidad_medida VARCHAR(20) DEFAULT 'unidad',
    lote VARCHAR(50),
    fecha_vencimiento DATE,
    ubicacion VARCHAR(50),
    estado BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_productos_codigo ON productos(codigo);
CREATE INDEX idx_productos_nombre ON productos(nombre);
CREATE INDEX idx_productos_categoria ON productos(id_categoria);
CREATE INDEX idx_productos_estado ON productos(estado);

-- ========================================
-- TABLA: HISTORIAL_PRECIOS
-- ========================================
CREATE TABLE historial_precios (
    id_historial SERIAL PRIMARY KEY,
    id_producto INT NOT NULL REFERENCES productos(id_producto) ON DELETE CASCADE,
    precio_costo_anterior DECIMAL(10,2),
    precio_venta_anterior DECIMAL(10,2),
    precio_costo_nuevo DECIMAL(10,2),
    precio_venta_nuevo DECIMAL(10,2),
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_empleado INT REFERENCES empleados(id_empleado) ON DELETE SET NULL
);

CREATE INDEX idx_historial_producto ON historial_precios(id_producto);
CREATE INDEX idx_historial_fecha ON historial_precios(fecha_cambio);

COMMENT ON TABLE historial_precios IS 'Auditoría de cambios de precios de productos';

-- ========================================
-- TABLA: CAJAS
-- ========================================
CREATE TABLE cajas (
    id_caja SERIAL PRIMARY KEY,
    id_empleado INT NOT NULL REFERENCES empleados(id_empleado),
    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre TIMESTAMP,
    monto_inicial DECIMAL(10,2) NOT NULL,
    monto_final DECIMAL(10,2),
    total_ventas DECIMAL(10,2) DEFAULT 0,
    total_ingresos DECIMAL(10,2) DEFAULT 0,
    total_egresos DECIMAL(10,2) DEFAULT 0,
    diferencia DECIMAL(10,2),
    estado VARCHAR(20) DEFAULT 'abierta',
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cajas_apertura ON cajas(fecha_apertura);
CREATE INDEX idx_cajas_cierre ON cajas(fecha_cierre);
CREATE INDEX idx_cajas_empleado ON cajas(id_empleado);
CREATE INDEX idx_cajas_estado ON cajas(estado);

-- ========================================
-- TABLA: COMPRAS
-- ========================================
CREATE TABLE compras (
    id_compra SERIAL PRIMARY KEY,
    numero_factura VARCHAR(50) UNIQUE,
    id_proveedor INT NOT NULL REFERENCES proveedores(id_proveedor),
    id_empleado INT NOT NULL REFERENCES empleados(id_empleado),
    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) NOT NULL,
    estado VARCHAR(20) DEFAULT 'completada',
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_compras_fecha ON compras(fecha_compra);
CREATE INDEX idx_compras_proveedor ON compras(id_proveedor);
CREATE INDEX idx_compras_factura ON compras(numero_factura);

-- ========================================
-- TABLA: DETALLE_COMPRAS
-- ========================================
CREATE TABLE detalle_compras (
    id_detalle_compra SERIAL PRIMARY KEY,
    id_compra INT NOT NULL REFERENCES compras(id_compra) ON DELETE CASCADE,
    id_producto INT NOT NULL REFERENCES productos(id_producto),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_detalle_compras_compra ON detalle_compras(id_compra);
CREATE INDEX idx_detalle_compras_producto ON detalle_compras(id_producto);

-- ========================================
-- TABLA: VENTAS
-- ========================================
CREATE TABLE ventas (
    id_venta SERIAL PRIMARY KEY,
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    id_cliente INT REFERENCES clientes(id_cliente) ON DELETE SET NULL,
    id_empleado INT NOT NULL REFERENCES empleados(id_empleado),
    id_caja INT REFERENCES cajas(id_caja),
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10,2) NOT NULL,
    descuento DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    metodo_pago VARCHAR(20) DEFAULT 'efectivo',
    estado VARCHAR(20) DEFAULT 'completada',
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ventas_fecha ON ventas(fecha_venta);
CREATE INDEX idx_ventas_factura ON ventas(numero_factura);
CREATE INDEX idx_ventas_cliente ON ventas(id_cliente);
CREATE INDEX idx_ventas_empleado ON ventas(id_empleado);
CREATE INDEX idx_ventas_caja ON ventas(id_caja);

-- ========================================
-- TABLA: DETALLE_VENTAS
-- ========================================
CREATE TABLE detalle_ventas (
    id_detalle_venta SERIAL PRIMARY KEY,
    id_venta INT NOT NULL REFERENCES ventas(id_venta) ON DELETE CASCADE,
    id_producto INT NOT NULL REFERENCES productos(id_producto),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_detalle_ventas_venta ON detalle_ventas(id_venta);
CREATE INDEX idx_detalle_ventas_producto ON detalle_ventas(id_producto);

-- ========================================
-- TABLA: MOVIMIENTOS_CAJA
-- ========================================
CREATE TABLE movimientos_caja (
    id_movimiento SERIAL PRIMARY KEY,
    id_caja INT NOT NULL REFERENCES cajas(id_caja) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ingreso', 'egreso')),
    concepto VARCHAR(100) NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_empleado INT NOT NULL REFERENCES empleados(id_empleado),
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_movimientos_caja ON movimientos_caja(id_caja);
CREATE INDEX idx_movimientos_tipo ON movimientos_caja(tipo);
CREATE INDEX idx_movimientos_fecha ON movimientos_caja(fecha_movimiento);

-- ========================================
-- TABLA: LOGS_SISTEMA
-- ========================================
CREATE TABLE logs_sistema (
    id_log SERIAL PRIMARY KEY,
    id_empleado INT REFERENCES empleados(id_empleado) ON DELETE SET NULL,
    accion VARCHAR(50) NOT NULL,
    tabla_afectada VARCHAR(50),
    id_registro INT,
    descripcion TEXT,
    ip_address VARCHAR(45),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_empleado ON logs_sistema(id_empleado);
CREATE INDEX idx_logs_accion ON logs_sistema(accion);
CREATE INDEX idx_logs_fecha ON logs_sistema(fecha);
CREATE INDEX idx_logs_tabla ON logs_sistema(tabla_afectada);

COMMENT ON TABLE logs_sistema IS 'Auditoría de acciones realizadas en el sistema';

-- ========================================
-- DATOS INICIALES: ROLES
-- ========================================
INSERT INTO roles (nombre, descripcion) VALUES
('Administrador', 'Acceso total al sistema, gestión completa'),
('Gerente', 'Gestión de inventario, ventas, compras y reportes'),
('Vendedor', 'Realiza ventas y consulta productos'),
('Cajero', 'Manejo de caja, ventas y cierre de caja');

-- ========================================
-- DATOS INICIALES: PERMISOS
-- ========================================
INSERT INTO permisos (modulo, accion, descripcion) VALUES
-- Clientes
('clientes', 'crear', 'Crear nuevos clientes'),
('clientes', 'leer', 'Ver información de clientes'),
('clientes', 'actualizar', 'Modificar datos de clientes'),
('clientes', 'eliminar', 'Eliminar clientes'),

-- Productos
('productos', 'crear', 'Crear nuevos productos'),
('productos', 'leer', 'Ver información de productos'),
('productos', 'actualizar', 'Modificar productos'),
('productos', 'eliminar', 'Eliminar productos'),

-- Ventas
('ventas', 'crear', 'Realizar ventas'),
('ventas', 'leer', 'Ver historial de ventas'),
('ventas', 'anular', 'Anular ventas'),

-- Compras
('compras', 'crear', 'Registrar compras'),
('compras', 'leer', 'Ver historial de compras'),
('compras', 'actualizar', 'Modificar compras'),
('compras', 'anular', 'Anular compras'),

-- Empleados
('empleados', 'crear', 'Crear empleados/usuarios'),
('empleados', 'leer', 'Ver información de empleados'),
('empleados', 'actualizar', 'Modificar empleados'),
('empleados', 'eliminar', 'Eliminar empleados'),

-- Proveedores
('proveedores', 'crear', 'Registrar proveedores'),
('proveedores', 'leer', 'Ver proveedores'),
('proveedores', 'actualizar', 'Modificar proveedores'),
('proveedores', 'eliminar', 'Eliminar proveedores'),

-- Categorías
('categorias', 'crear', 'Crear categorías'),
('categorias', 'leer', 'Ver categorías'),
('categorias', 'actualizar', 'Modificar categorías'),
('categorias', 'eliminar', 'Eliminar categorías'),

-- Cajas
('cajas', 'abrir', 'Abrir caja'),
('cajas', 'cerrar', 'Cerrar caja'),
('cajas', 'ver', 'Ver movimientos de caja'),

-- Reportes
('reportes', 'cierre_caja', 'Generar reporte de cierre de caja'),
('reportes', 'ventas_dia', 'Reporte de ventas del día'),
('reportes', 'ventas_mes', 'Reporte de ventas del mes'),
('reportes', 'compras', 'Reporte de compras'),
('reportes', 'inventario', 'Reporte de inventario y existencias'),
('reportes', 'clientes', 'Reporte de cartera de clientes'),
('reportes', 'proveedores', 'Reporte de proveedores'),
('reportes', 'empleados', 'Reporte de empleados'),

-- Configuración
('configuracion', 'acceder', 'Acceder a configuración del sistema'),
('configuracion', 'modificar', 'Modificar configuración del sistema');

-- ========================================
-- ASIGNAR TODOS LOS PERMISOS A ADMINISTRADOR
-- ========================================
INSERT INTO roles_permisos (id_rol, id_permiso)
SELECT 1, id_permiso FROM permisos;

-- ========================================
-- ASIGNAR PERMISOS A GERENTE
-- ========================================
INSERT INTO roles_permisos (id_rol, id_permiso)
SELECT 2, id_permiso FROM permisos 
WHERE modulo IN ('clientes', 'productos', 'ventas', 'compras', 'proveedores', 'categorias', 'cajas', 'reportes')
AND accion NOT IN ('eliminar');

-- ========================================
-- ASIGNAR PERMISOS A VENDEDOR
-- ========================================
INSERT INTO roles_permisos (id_rol, id_permiso)
SELECT 3, id_permiso FROM permisos 
WHERE (modulo = 'ventas' AND accion IN ('crear', 'leer'))
   OR (modulo = 'productos' AND accion = 'leer')
   OR (modulo = 'clientes' AND accion IN ('crear', 'leer', 'actualizar'))
   OR (modulo = 'cajas' AND accion = 'ver');

-- ========================================
-- ASIGNAR PERMISOS A CAJERO
-- ========================================
INSERT INTO roles_permisos (id_rol, id_permiso)
SELECT 4, id_permiso FROM permisos 
WHERE (modulo = 'ventas' AND accion IN ('crear', 'leer'))
   OR (modulo = 'productos' AND accion = 'leer')
   OR (modulo = 'clientes' AND accion IN ('leer'))
   OR (modulo = 'cajas')
   OR (modulo = 'reportes' AND accion IN ('cierre_caja', 'ventas_dia'));

-- ========================================
-- DATOS INICIALES: CATEGORÍAS EJEMPLO
-- ========================================
INSERT INTO categorias (nombre, descripcion) VALUES
('Electrónica', 'Productos electrónicos y tecnología'),
('Alimentos', 'Productos alimenticios'),
('Bebidas', 'Bebidas en general'),
('Limpieza', 'Productos de limpieza e higiene'),
('Otros', 'Productos varios');

-- ========================================
-- CREAR USUARIO ADMINISTRADOR POR DEFECTO
-- ========================================
-- Primero crear la persona
INSERT INTO personas (nombre, apellido, email, dpi_nit, telefono, direccion) VALUES
('Administrador', 'Sistema', 'admin@sistema.com', '0000000000000', '00000000', 'Oficina Principal');

-- Luego crear el empleado admin (password: admin123 - SHA256)
INSERT INTO empleados (id_persona, id_rol, puesto, salario, usuario, password, estado) VALUES
(1, 1, 'Administrador del Sistema', 0, 'admin', 
 '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', true);

-- ========================================
-- TRIGGERS Y FUNCIONES
-- ========================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a las tablas principales
CREATE TRIGGER trigger_personas_updated_at
    BEFORE UPDATE ON personas
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_empleados_updated_at
    BEFORE UPDATE ON empleados
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_proveedores_updated_at
    BEFORE UPDATE ON proveedores
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_productos_updated_at
    BEFORE UPDATE ON productos
    FOR EACH ROW EXECUTE FUNCTION actualizar_updated_at();

-- Función para calcular margen de ganancia automáticamente
CREATE OR REPLACE FUNCTION calcular_margen_ganancia()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.precio_costo > 0 THEN
        NEW.margen_ganancia = ((NEW.precio_venta - NEW.precio_costo) / NEW.precio_costo) * 100;
    ELSE
        NEW.margen_ganancia = 0;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calcular_margen
    BEFORE INSERT OR UPDATE ON productos
    FOR EACH ROW EXECUTE FUNCTION calcular_margen_ganancia();

-- Función para registrar cambios de precio
CREATE OR REPLACE FUNCTION registrar_cambio_precio()
RETURNS TRIGGER AS $$
BEGIN
    IF (OLD.precio_costo != NEW.precio_costo OR OLD.precio_venta != NEW.precio_venta) THEN
        INSERT INTO historial_precios (
            id_producto, 
            precio_costo_anterior, 
            precio_venta_anterior,
            precio_costo_nuevo,
            precio_venta_nuevo
        ) VALUES (
            NEW.id_producto,
            OLD.precio_costo,
            OLD.precio_venta,
            NEW.precio_costo,
            NEW.precio_venta
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_historial_precios
    AFTER UPDATE ON productos
    FOR EACH ROW EXECUTE FUNCTION registrar_cambio_precio();

-- ========================================
-- VISTAS ÚTILES
-- ========================================

-- Vista de personas con sus roles
CREATE OR REPLACE VIEW vista_personas_roles AS
SELECT 
    p.id_persona,
    p.nombre,
    p.apellido,
    p.email,
    p.telefono,
    p.dpi_nit,
    CASE WHEN c.id_cliente IS NOT NULL THEN 'Cliente' END as rol_cliente,
    CASE WHEN e.id_empleado IS NOT NULL THEN 'Empleado' END as rol_empleado,
    CASE WHEN pr.id_persona_contacto = p.id_persona THEN 'Contacto Proveedor' END as rol_contacto,
    p.estado
FROM personas p
LEFT JOIN clientes c ON p.id_persona = c.id_persona
LEFT JOIN empleados e ON p.id_persona = e.id_persona
LEFT JOIN proveedores pr ON p.id_persona = pr.id_persona_contacto;

-- Vista de productos con stock bajo
CREATE OR REPLACE VIEW vista_productos_stock_bajo AS
SELECT 
    p.id_producto,
    p.codigo,
    p.nombre,
    c.nombre as categoria,
    p.stock_actual,
    p.stock_minimo,
    (p.stock_minimo - p.stock_actual) as unidades_faltantes
FROM productos p
LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
WHERE p.stock_actual <= p.stock_minimo
AND p.estado = true
ORDER BY p.stock_actual ASC;

-- Vista de ventas del día
CREATE OR REPLACE VIEW vista_ventas_hoy AS
SELECT 
    v.id_venta,
    v.numero_factura,
    CONCAT(pe.nombre, ' ', pe.apellido) as cliente,
    CONCAT(emp.nombre, ' ', emp.apellido) as empleado,
    v.fecha_venta,
    v.total,
    v.metodo_pago,
    v.estado
FROM ventas v
LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
LEFT JOIN personas pe ON c.id_persona = pe.id_persona
LEFT JOIN empleados e ON v.id_empleado = e.id_empleado
LEFT JOIN personas emp ON e.id_persona = emp.id_persona
WHERE DATE(v.fecha_venta) = CURRENT_DATE
ORDER BY v.fecha_venta DESC;

-- ========================================
-- VERIFICACIÓN FINAL
-- ========================================
SELECT 'Base de datos creada exitosamente' as mensaje;

-- Mostrar resumen de tablas creadas
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Mostrar cantidad de registros iniciales
SELECT 
    'roles' as tabla, COUNT(*) as registros FROM roles
UNION ALL
SELECT 'permisos', COUNT(*) FROM permisos
UNION ALL
SELECT 'roles_permisos', COUNT(*) FROM roles_permisos
UNION ALL
SELECT 'categorias', COUNT(*) FROM categorias
UNION ALL
SELECT 'personas', COUNT(*) FROM personas
UNION ALL
SELECT 'empleados', COUNT(*) FROM empleados;