"""
Vista para gestión de Roles y Permisos
"""
import flet as ft
from services.rol_service import RolService
from utils.theme import VoltTheme


class RolesView:
    """Vista para la gestión de roles y permisos"""
    
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.rol_service = RolService()
        self.roles = []
        self.permisos_por_modulo = {}
        self.modal = None
        
    def build(self):
        """Construye la interfaz de roles"""
        # Título
        titulo = ft.Container(
            content=ft.Column([
                ft.Text("Roles y Permisos", size=28, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                ft.Text("Gestión de roles y permisos del sistema", size=14, color=VoltTheme.TEXT_SECONDARY)
            ], spacing=5),
            padding=ft.padding.only(left=20, top=20, bottom=10)
        )
        
        # Barra superior
        barra_superior = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Nuevo Rol",
                    icon=ft.Icons.ADD,
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.abrir_modal_nuevo()
                )
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Tabla
        self.tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Descripción", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Empleados", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE))
            ],
            rows=[],
            border=ft.border.all(0, ft.Colors.TRANSPARENT),
            horizontal_lines=ft.BorderSide(1, VoltTheme.BORDER_COLOR),
            heading_row_color=VoltTheme.SECONDARY,
            heading_row_height=50,
            data_row_min_height=70,
            column_spacing=30,
            width=2000
        )
        
        tabla_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.tabla,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    border=ft.border.all(1, VoltTheme.BORDER_COLOR),
                    padding=0
                )
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=ft.padding.symmetric(horizontal=20)
        )
        
        # Cargar datos
        self.cargar_roles()
        
        return ft.Column([
            titulo,
            barra_superior,
            tabla_container
        ], spacing=10, expand=True)
    
    def cargar_roles(self):
        """Carga la lista de roles"""
        self.roles = self.rol_service.listar_roles()
        self.permisos_por_modulo = self.rol_service.listar_permisos_por_modulo()
        self.actualizar_tabla()
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los datos"""
        self.tabla.rows.clear()
        
        for rol in self.roles:
            self.tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(rol['nombre'], size=13, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(rol.get('descripcion') or "Sin descripción", size=13, color=VoltTheme.TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(str(rol.get('total_empleados', 0)), size=13)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon="key",
                                    icon_color=VoltTheme.PRIMARY,
                                    tooltip="Gestionar permisos",
                                    icon_size=18,
                                    on_click=lambda _, r=rol: self.abrir_modal_permisos(r)
                                ),
                                ft.IconButton(
                                    icon="edit",
                                    icon_color=VoltTheme.WARNING,
                                    tooltip="Editar",
                                    icon_size=18,
                                    on_click=lambda _, r=rol: self.abrir_modal_editar(r)
                                ),
                                ft.IconButton(
                                    icon="delete",
                                    icon_color=VoltTheme.DANGER,
                                    tooltip="Eliminar",
                                    icon_size=18,
                                    on_click=lambda _, r=rol: self.confirmar_eliminar(r),
                                    disabled=rol['nombre'] == 'Administrador'
                                )
                            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER)
                        )
                    ]
                )
            )
        
        if self.page:
            self.page.update()
    
    def abrir_modal_nuevo(self):
        """Abre el modal para crear un nuevo rol"""
        campo_nombre = ft.TextField(label="Nombre *", border_color=VoltTheme.BORDER_COLOR)
        campo_descripcion = ft.TextField(
            label="Descripción",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=VoltTheme.BORDER_COLOR
        )
        
        def guardar():
            if not campo_nombre.value:
                self.mostrar_snackbar("El nombre es obligatorio", VoltTheme.DANGER)
                return
            
            resultado = self.rol_service.crear_rol(
                nombre=campo_nombre.value,
                descripcion=campo_descripcion.value
            )
            
            if resultado['success']:
                self.mostrar_snackbar(resultado['message'], VoltTheme.SUCCESS)
                self.cerrar_modal()
                self.cargar_roles()
            else:
                self.mostrar_snackbar(resultado['message'], VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE, color=VoltTheme.PRIMARY, size=30),
                    ft.Text("Nuevo Rol", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                campo_nombre,
                campo_descripcion,
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Guardar",
                        icon=ft.Icons.SAVE,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: guardar()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=500,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def abrir_modal_editar(self, rol):
        """Abre el modal para editar un rol"""
        campo_nombre = ft.TextField(
            label="Nombre *",
            value=rol['nombre'],
            border_color=VoltTheme.BORDER_COLOR,
            disabled=rol['nombre'] == 'Administrador'
        )
        campo_descripcion = ft.TextField(
            label="Descripción",
            value=rol.get('descripcion') or "",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=VoltTheme.BORDER_COLOR
        )
        
        def actualizar():
            if not campo_nombre.value:
                self.mostrar_snackbar("El nombre es obligatorio", VoltTheme.DANGER)
                return
            
            resultado = self.rol_service.actualizar_rol(
                id_rol=rol['id_rol'],
                nombre=campo_nombre.value,
                descripcion=campo_descripcion.value
            )
            
            if resultado['success']:
                self.mostrar_snackbar(resultado['message'], VoltTheme.SUCCESS)
                self.cerrar_modal()
                self.cargar_roles()
            else:
                self.mostrar_snackbar(resultado['message'], VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EDIT, color=VoltTheme.WARNING, size=30),
                    ft.Text("Editar Rol", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                campo_nombre,
                campo_descripcion,
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Actualizar",
                        icon=ft.Icons.SAVE,
                        bgcolor=VoltTheme.WARNING,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: actualizar()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=500,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def abrir_modal_permisos(self, rol):
        """Abre el modal para gestionar permisos del rol"""
        # Obtener permisos actuales del rol
        permisos_actuales = self.rol_service.obtener_permisos_rol(rol['id_rol'])
        
        # Crear matriz de checkboxes
        checkboxes = {}
        filas_matriz = []
        
        # Encabezados
        header = ft.Row([
            ft.Container(ft.Text("Módulo", weight=ft.FontWeight.BOLD), width=150),
            ft.Container(ft.Text("Leer", weight=ft.FontWeight.BOLD), width=80, alignment=ft.alignment.center),
            ft.Container(ft.Text("Crear", weight=ft.FontWeight.BOLD), width=80, alignment=ft.alignment.center),
            ft.Container(ft.Text("Actualizar", weight=ft.FontWeight.BOLD), width=100, alignment=ft.alignment.center),
            ft.Container(ft.Text("Eliminar", weight=ft.FontWeight.BOLD), width=80, alignment=ft.alignment.center)
        ])
        filas_matriz.append(header)
        filas_matriz.append(ft.Divider(height=1, color=VoltTheme.BORDER_COLOR))
        
        # Orden de módulos
        orden_modulos = ['productos', 'clientes', 'proveedores', 'compras', 'ventas', 'cajas', 'empleados', 'reportes', 'roles']
        
        for modulo in orden_modulos:
            if modulo in self.permisos_por_modulo:
                permisos_modulo = self.permisos_por_modulo[modulo]
                fila_checks = [ft.Container(ft.Text(modulo.capitalize(), size=13), width=150)]
                
                # Crear checkboxes por acción
                for accion in ['leer', 'crear', 'actualizar', 'eliminar']:
                    permiso = next((p for p in permisos_modulo if p['accion'] == accion), None)
                    if permiso:
                        cb = ft.Checkbox(
                            value=permiso['id_permiso'] in permisos_actuales,
                            scale=0.9
                        )
                        checkboxes[permiso['id_permiso']] = cb
                        width = 100 if accion == 'actualizar' else 80
                        fila_checks.append(ft.Container(cb, width=width, alignment=ft.alignment.center))
                    else:
                        width = 100 if accion == 'actualizar' else 80
                        fila_checks.append(ft.Container(ft.Text("-", color=VoltTheme.TEXT_SECONDARY), width=width, alignment=ft.alignment.center))
                
                filas_matriz.append(ft.Row(fila_checks))
        
        def guardar_permisos():
            # Obtener permisos seleccionados
            permisos_seleccionados = [
                id_permiso for id_permiso, cb in checkboxes.items() if cb.value
            ]
            
            resultado = self.rol_service.asignar_permisos(rol['id_rol'], permisos_seleccionados)
            
            if resultado['success']:
                self.mostrar_snackbar(resultado['message'], VoltTheme.SUCCESS)
                self.cerrar_modal()
            else:
                self.mostrar_snackbar(resultado['message'], VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.KEY, color=VoltTheme.PRIMARY, size=30),
                    ft.Text(f"Permisos de {rol['nombre']}", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Container(
                    content=ft.Column(filas_matriz, spacing=10, scroll=ft.ScrollMode.AUTO),
                    height=400
                ),
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Guardar Permisos",
                        icon=ft.Icons.SAVE,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: guardar_permisos()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=600,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def confirmar_eliminar(self, rol):
        """Confirma la eliminación de un rol"""
        def eliminar():
            resultado = self.rol_service.eliminar_rol(rol['id_rol'])
            
            if resultado['success']:
                self.mostrar_snackbar(resultado['message'], VoltTheme.SUCCESS)
                self.cerrar_modal()
                self.cargar_roles()
            else:
                self.mostrar_snackbar(resultado['message'], VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=VoltTheme.DANGER, size=40),
                    ft.Text("¿Confirmar eliminación?", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text(f"¿Está seguro que desea eliminar el rol '{rol['nombre']}'?"),
                ft.Text("Esta acción no se puede deshacer.", color=VoltTheme.DANGER, size=12),
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Eliminar",
                        icon=ft.Icons.DELETE,
                        bgcolor=VoltTheme.DANGER,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: eliminar()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=400,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def cerrar_modal(self):
        """Cierra el modal actual"""
        if self.modal:
            self.page.close(self.modal)
            self.modal = None
    
    def mostrar_snackbar(self, mensaje: str, color):
        """Muestra un mensaje snackbar"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
