import flet as ft
from datetime import datetime, date
import math
from services.empleado_service import EmpleadoService
from models.empleado import Empleado
from utils.theme import VoltTheme


class EmpleadosView:
    """Vista para gestión de Empleados"""
    
    def __init__(self, page: ft.Page, empleado):
        self.page = page
        self.empleado = empleado
        self.empleado_service = EmpleadoService()
        
        # Estado
        self.empleados = []
        self.roles = []
        self.pagina_actual = 1
        self.items_por_pagina = 5
        self.total_paginas = 1
        self.busqueda_actual = ""
        self.filtro_estado_actual = ""
        self.filtro_rol_actual = None
        
        # Referencias a controles
        self.tabla = None
        self.campo_busqueda = None
        self.filtro_estado = None
        self.filtro_rol = None
        self.paginacion_container = None
        self.modal = None
        
        # Cargar roles
        self.cargar_roles()
    
    def build(self):
        """Construye la interfaz de empleados"""
        # Título
        titulo = ft.Container(
            content=ft.Column([
                ft.Text("Empleados", size=28, weight=ft.FontWeight.BOLD, color=VoltTheme.TEXT_PRIMARY),
                ft.Text("Gestión de empleados del sistema", size=14, color=VoltTheme.TEXT_SECONDARY)
            ], spacing=5),
            padding=ft.padding.only(left=20, top=20, bottom=10)
        )
        
        # Barra de búsqueda y filtros
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar por nombre, usuario o DPI...",
            prefix_icon=ft.Icons.SEARCH,
            width=400,
            border_color=VoltTheme.BORDER_COLOR,
            on_submit=lambda _: self.buscar()
        )
        
        self.filtro_estado = ft.Dropdown(
            label="Estado",
            width=150,
            border_color=VoltTheme.BORDER_COLOR,
            options=[
                ft.dropdown.Option(key="", text="Todos"),
                ft.dropdown.Option(key="activo", text="Activo"),
                ft.dropdown.Option(key="inactivo", text="Inactivo")
            ],
            value="",
            on_change=lambda _: self.buscar()
        )
        
        self.filtro_rol = ft.Dropdown(
            label="Rol",
            width=180,
            border_color=VoltTheme.BORDER_COLOR,
            on_change=lambda _: self.buscar()
        )
        
        # Cargar roles para el filtro
        self.cargar_roles()
        
        barra_busqueda = ft.Container(
            content=ft.Row([
                self.campo_busqueda,
                self.filtro_estado,
                self.filtro_rol,
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_color=VoltTheme.PRIMARY,
                    tooltip="Recargar",
                    on_click=lambda _: self.limpiar_filtros()
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Nuevo Empleado",
                    icon=ft.Icons.ADD,
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.abrir_modal_nuevo()
                )
            ], spacing=10),
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Tabla
        self.tabla_empleados = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        )
        
        tabla_container = ft.Container(
            content=self.tabla_empleados,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, VoltTheme.BORDER_COLOR),
            expand=True,
            padding=ft.padding.symmetric(horizontal=20)
        )
        
        # Paginación
        self.paginacion_container = ft.Container(
            content=ft.Row([], alignment=ft.MainAxisAlignment.CENTER),
            padding=20
        )
        
        # Cargar datos iniciales
        self.cargar_empleados()
        
        return ft.Column([
            titulo,
            barra_busqueda,
            tabla_container,
            self.paginacion_container
        ], spacing=10, expand=True)
    
    def cargar_roles(self):
        """Carga la lista de roles"""
        self.roles = self.empleado_service.obtener_roles()
        if self.filtro_rol:
            opciones = [ft.dropdown.Option(key="", text="Todos")]
            opciones.extend([
                ft.dropdown.Option(key=str(rol['id_rol']), text=rol['nombre'])
                for rol in self.roles
            ])
            self.filtro_rol.options = opciones
            self.filtro_rol.value = ""
    
    def cargar_empleados(self):
        """Carga la lista de empleados"""
        resultado = self.empleado_service.listar_empleados(
            pagina=self.pagina_actual,
            limite=self.items_por_pagina,
            busqueda=self.busqueda_actual,
            filtro_estado=self.filtro_estado_actual,
            filtro_rol=self.filtro_rol_actual
        )
        
        self.empleados = resultado.get('empleados', [])
        self.total_paginas = resultado.get('paginas', 1)
        
        self.actualizar_tabla()
        self.actualizar_paginacion()
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los datos"""
        self.tabla_empleados.controls.clear()
        
        # Header de la tabla
        header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("Nombre Completo", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=2),
                ft.Container(ft.Text("Usuario", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=2),
                ft.Container(ft.Text("Rol", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Puesto", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=2),
            ]),
            bgcolor=VoltTheme.PRIMARY,
            padding=15,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        self.tabla_empleados.controls.append(header)
        
        # Filas de empleados
        if not self.empleados:
            self.tabla_empleados.controls.append(
                ft.Container(
                    content=ft.Text("No hay empleados registrados", size=14, color=ft.Colors.GREY_600),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for emp in self.empleados:
                fila = self.crear_fila_empleado(emp)
                self.tabla_empleados.controls.append(fila)
        
        if self.page:
            self.page.update()
    
    def crear_fila_empleado(self, emp):
        """Crea una fila de la tabla para un empleado"""
        # Color según estado BOOLEAN
        estado_color = VoltTheme.SUCCESS if emp.estado else VoltTheme.DANGER
        estado_texto = "Activo" if emp.estado else "Inactivo"
        
        # Badge de estado
        estado_badge = ft.Container(
            content=ft.Text(estado_texto, size=10, color=ft.Colors.WHITE),
            bgcolor=estado_color,
            padding=ft.padding.symmetric(horizontal=10, vertical=3),
            border_radius=15
        )
        
        fila = ft.Container(
            content=ft.Row([
                ft.Container(
                    ft.Text(emp.nombre_completo, size=13),
                    expand=2
                ),
                ft.Container(
                    ft.Text(emp.usuario, size=13),
                    expand=2
                ),
                ft.Container(
                    ft.Text(emp.nombre_rol or "Sin rol", size=13, color=VoltTheme.TEXT_SECONDARY),
                    expand=1
                ),
                ft.Container(
                    ft.Text(emp.puesto or "N/A", size=13),
                    expand=1
                ),
                ft.Container(
                    estado_badge,
                    expand=1,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Row([
                        ft.IconButton(
                            icon="visibility",
                            icon_color=VoltTheme.INFO,
                            tooltip="Ver detalles",
                            icon_size=18,
                            on_click=lambda _, e=emp: self.ver_detalle(e.id_empleado)
                        ),
                        ft.IconButton(
                            icon="edit",
                            icon_color=VoltTheme.WARNING,
                            tooltip="Editar",
                            icon_size=18,
                            on_click=lambda _, e=emp: self.abrir_modal_editar(e.id_empleado)
                        ),
                        ft.IconButton(
                            icon="key",
                            icon_color=VoltTheme.PRIMARY,
                            tooltip="Cambiar contraseña",
                            icon_size=18,
                            on_click=lambda _, e=emp: self.abrir_modal_cambiar_password(e.id_empleado)
                        ),
                        ft.IconButton(
                            icon="power_settings_new" if emp.estado else "check_circle",
                            icon_color=VoltTheme.DANGER if emp.estado else VoltTheme.SUCCESS,
                            tooltip="Desactivar" if emp.estado else "Activar",
                            icon_size=18,
                            on_click=lambda _, e=emp: self.confirmar_cambio_estado(None, e, not e.estado)
                        )
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    expand=2,
                    alignment=ft.alignment.center
                ),
            ]),
            padding=15,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        return fila
    
    def actualizar_paginacion(self):
        """Actualiza los controles de paginación"""
        botones = []
        
        # Botón anterior
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual - 1),
                disabled=self.pagina_actual == 1,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual > 1 else VoltTheme.TEXT_SECONDARY
            )
        )
        
        # Números de página
        inicio = max(1, self.pagina_actual - 2)
        fin = min(self.total_paginas, inicio + 4)
        
        if fin - inicio < 4:
            inicio = max(1, fin - 4)
        
        for i in range(inicio, fin + 1):
            if i == self.pagina_actual:
                botones.append(
                    ft.Container(
                        content=ft.Text(str(i), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=VoltTheme.PRIMARY,
                        width=35,
                        height=35,
                        border_radius=5,
                        alignment=ft.alignment.center
                    )
                )
            else:
                botones.append(
                    ft.TextButton(
                        text=str(i),
                        on_click=lambda _, p=i: self.cambiar_pagina(p)
                    )
                )
        
        # Botón siguiente
        botones.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual + 1),
                disabled=self.pagina_actual == self.total_paginas,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual < self.total_paginas else VoltTheme.TEXT_SECONDARY
            )
        )
        
        self.paginacion_container.content = ft.Row(botones, alignment=ft.MainAxisAlignment.CENTER)
        if self.page:
            self.page.update()
    
    def cambiar_pagina(self, nueva_pagina):
        """Cambia a otra página"""
        if 1 <= nueva_pagina <= self.total_paginas:
            self.pagina_actual = nueva_pagina
            self.cargar_empleados()
    
    def buscar(self):
        """Realiza búsqueda con filtros"""
        self.busqueda_actual = self.campo_busqueda.value or ""
        self.filtro_estado_actual = self.filtro_estado.value or ""
        
        # Manejar filtro de rol
        if self.filtro_rol.value and self.filtro_rol.value != "":
            try:
                self.filtro_rol_actual = int(self.filtro_rol.value)
            except (ValueError, TypeError):
                self.filtro_rol_actual = None
        else:
            self.filtro_rol_actual = None
            
        self.pagina_actual = 1
        self.cargar_empleados()
    
    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga"""
        self.campo_busqueda.value = ""
        self.filtro_estado.value = ""
        self.filtro_rol.value = ""
        self.busqueda_actual = ""
        self.filtro_estado_actual = ""
        self.filtro_rol_actual = None
        self.pagina_actual = 1
        self.cargar_empleados()
        if self.page:
            self.page.update()
    
    def abrir_modal_nuevo(self):
        """Abre el modal para crear un nuevo empleado"""
        # Campos del formulario
        campo_nombres = ft.TextField(label="Nombres *", border_color=VoltTheme.BORDER_COLOR)
        campo_apellidos = ft.TextField(label="Apellidos *", border_color=VoltTheme.BORDER_COLOR)
        campo_num_doc = ft.TextField(label="DPI/NIT *", border_color=VoltTheme.BORDER_COLOR)
        campo_telefono = ft.TextField(label="Teléfono", border_color=VoltTheme.BORDER_COLOR)
        campo_email = ft.TextField(label="Email", border_color=VoltTheme.BORDER_COLOR)
        campo_direccion = ft.TextField(
            label="Dirección",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_usuario = ft.TextField(label="Usuario *", border_color=VoltTheme.BORDER_COLOR)
        campo_password = ft.TextField(
            label="Contraseña *",
            password=True,
            can_reveal_password=True,
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_rol = ft.Dropdown(
            label="Rol *",
            options=[
                ft.dropdown.Option(key=str(rol['id_rol']), text=rol['nombre'])
                for rol in self.roles
            ],
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_puesto = ft.TextField(label="Puesto", border_color=VoltTheme.BORDER_COLOR)
        campo_salario = ft.TextField(
            label="Salario *",
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0.00",
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_fecha = ft.TextField(
            label="Fecha Contratación *",
            hint_text="YYYY-MM-DD",
            value=date.today().strftime("%Y-%m-%d"),
            border_color=VoltTheme.BORDER_COLOR
        )
        
        def guardar():
            try:
                # Validar campos requeridos
                if not all([campo_nombres.value, campo_apellidos.value, campo_num_doc.value,
                           campo_usuario.value, campo_password.value, campo_rol.value]):
                    self.mostrar_alerta("Error", "Complete todos los campos requeridos", VoltTheme.WARNING)
                    return
                
                # Validar fecha
                try:
                    fecha_contratacion = datetime.strptime(campo_fecha.value, "%Y-%m-%d").date()
                except:
                    self.mostrar_alerta("Error", "Formato de fecha inválido (use YYYY-MM-DD)", VoltTheme.WARNING)
                    return
                
                # Crear empleado
                datos = {
                    'nombres': campo_nombres.value,
                    'apellidos': campo_apellidos.value,
                    'numero_documento': campo_num_doc.value,
                    'telefono': campo_telefono.value,
                    'email': campo_email.value,
                    'direccion': campo_direccion.value,
                    'usuario': campo_usuario.value,
                    'password': campo_password.value,
                    'id_rol': int(campo_rol.value),
                    'puesto': campo_puesto.value,
                    'salario': float(campo_salario.value),
                    'fecha_contratacion': fecha_contratacion
                }
                
                resultado = self.empleado_service.crear_empleado(datos)
                
                if resultado['success']:
                    self.mostrar_alerta("Éxito", "Empleado creado exitosamente", VoltTheme.SUCCESS)
                    self.cerrar_modal()
                    self.cargar_empleados()
                else:
                    self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
                    
            except Exception as e:
                self.mostrar_alerta("Error", f"Error: {str(e)}", VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON_ADD, color=VoltTheme.PRIMARY, size=30),
                    ft.Text("Nuevo Empleado", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text("Datos Personales", weight=ft.FontWeight.BOLD, size=16),
                ft.Row([campo_nombres, campo_apellidos], spacing=10),
                campo_num_doc,
                ft.Row([campo_telefono, campo_email], spacing=10),
                campo_direccion,
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text("Datos de Empleado", weight=ft.FontWeight.BOLD, size=16),
                ft.Row([campo_usuario, campo_password], spacing=10),
                ft.Row([campo_rol, campo_puesto], spacing=10),
                ft.Row([campo_salario, campo_fecha], spacing=10),
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
            ], spacing=15, tight=True, scroll=ft.ScrollMode.AUTO),
            padding=20,
            width=700,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def abrir_modal_editar(self, id_empleado):
        """Abre el modal para editar un empleado"""
        empleado = self.empleado_service.obtener_empleado(id_empleado)
        if not empleado:
            self.mostrar_alerta("Error", "Empleado no encontrado", VoltTheme.DANGER)
            return
        
        # Campos del formulario con datos actuales
        campo_nombres = ft.TextField(label="Nombres *", value=empleado.persona.nombre, border_color=VoltTheme.BORDER_COLOR)
        campo_apellidos = ft.TextField(label="Apellidos *", value=empleado.persona.apellido, border_color=VoltTheme.BORDER_COLOR)
        campo_num_doc = ft.TextField(label="DPI/NIT *", value=empleado.persona.dpi_nit or "", border_color=VoltTheme.BORDER_COLOR)
        campo_telefono = ft.TextField(label="Teléfono", value=empleado.persona.telefono or "", border_color=VoltTheme.BORDER_COLOR)
        campo_email = ft.TextField(label="Email", value=empleado.persona.email or "", border_color=VoltTheme.BORDER_COLOR)
        campo_direccion = ft.TextField(
            label="Dirección",
            value=empleado.persona.direccion or "",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_usuario = ft.TextField(label="Usuario *", value=empleado.usuario, border_color=VoltTheme.BORDER_COLOR)
        campo_rol = ft.Dropdown(
            label="Rol *",
            options=[
                ft.dropdown.Option(key=str(rol['id_rol']), text=rol['nombre'])
                for rol in self.roles
            ],
            value=str(empleado.id_rol) if empleado.id_rol else None,
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_puesto = ft.TextField(label="Puesto", value=empleado.puesto or "", border_color=VoltTheme.BORDER_COLOR)
        campo_salario = ft.TextField(
            label="Salario *",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(empleado.salario),
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_fecha = ft.TextField(
            label="Fecha Contratación *",
            hint_text="YYYY-MM-DD",
            value=empleado.fecha_contratacion.strftime("%Y-%m-%d") if empleado.fecha_contratacion else "",
            border_color=VoltTheme.BORDER_COLOR
        )
        
        def actualizar():
            try:
                # Validar campos requeridos
                if not all([campo_nombres.value, campo_apellidos.value, campo_num_doc.value,
                           campo_usuario.value, campo_rol.value]):
                    self.mostrar_alerta("Error", "Complete todos los campos requeridos", VoltTheme.WARNING)
                    return
                
                # Validar fecha
                try:
                    fecha_contratacion = datetime.strptime(campo_fecha.value, "%Y-%m-%d").date()
                except:
                    self.mostrar_alerta("Error", "Formato de fecha inválido (use YYYY-MM-DD)", VoltTheme.WARNING)
                    return
                
                # Actualizar empleado
                datos = {
                    'nombres': campo_nombres.value,
                    'apellidos': campo_apellidos.value,
                    'numero_documento': campo_num_doc.value,
                    'telefono': campo_telefono.value,
                    'email': campo_email.value,
                    'direccion': campo_direccion.value,
                    'usuario': campo_usuario.value,
                    'id_rol': int(campo_rol.value),
                    'puesto': campo_puesto.value,
                    'salario': float(campo_salario.value),
                    'fecha_contratacion': fecha_contratacion,
                    'estado': empleado.estado  # Mantener el estado actual
                }
                
                resultado = self.empleado_service.actualizar_empleado(id_empleado, datos)
                
                if resultado['success']:
                    self.mostrar_alerta("Éxito", "Empleado actualizado exitosamente", VoltTheme.SUCCESS)
                    self.cerrar_modal()
                    self.cargar_empleados()
                else:
                    self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
                    
            except Exception as e:
                self.mostrar_alerta("Error", f"Error: {str(e)}", VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EDIT, color=VoltTheme.WARNING, size=30),
                    ft.Text("Editar Empleado", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text("Datos Personales", weight=ft.FontWeight.BOLD, size=16),
                ft.Row([campo_nombres, campo_apellidos], spacing=10),
                campo_num_doc,
                ft.Row([campo_telefono, campo_email], spacing=10),
                campo_direccion,
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text("Datos de Empleado", weight=ft.FontWeight.BOLD, size=16),
                ft.Row([campo_usuario, campo_rol], spacing=10),
                ft.Row([campo_puesto, campo_salario], spacing=10),
                campo_fecha,
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
            ], spacing=15, tight=True, scroll=ft.ScrollMode.AUTO),
            padding=20,
            width=700,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def ver_detalle(self, id_empleado):
        """Muestra los detalles completos de un empleado"""
        empleado = self.empleado_service.obtener_empleado(id_empleado)
        if not empleado:
            self.mostrar_alerta("Error", "Empleado no encontrado", VoltTheme.DANGER)
            return
        
        # Color del estado
        estado_color = VoltTheme.SUCCESS if empleado.estado else VoltTheme.DANGER
        estado_texto = "Activo" if empleado.estado else "Inactivo"
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=VoltTheme.INFO, size=30),
                    ft.Text("Detalle de Empleado", size=20, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("Información General", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.WHITE),
                        ft.Row([
                            ft.Column([
                                ft.Text("ID:", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(str(empleado.id_empleado), color=ft.Colors.WHITE)
                            ]),
                            ft.Container(width=50),
                            ft.Column([
                                ft.Text("Estado:", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(estado_texto, color=estado_color, weight=ft.FontWeight.BOLD)
                            ])
                        ])
                    ], spacing=10),
                    bgcolor=VoltTheme.SECONDARY,
                    padding=15,
                    border_radius=5
                ),
                
                ft.Text("Datos Personales", weight=ft.FontWeight.BOLD, size=16),
                ft.Row([
                    ft.Column([
                        ft.Text("Nombres:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.persona.nombre)
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Apellidos:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.persona.apellido)
                    ])
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("DPI/NIT:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.persona.dpi_nit or "N/A")
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Teléfono:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.persona.telefono or "N/A")
                    ])
                ]),
                ft.Column([
                    ft.Text("Email:", weight=ft.FontWeight.BOLD),
                    ft.Text(empleado.persona.email or "N/A")
                ]),
                ft.Column([
                    ft.Text("Dirección:", weight=ft.FontWeight.BOLD),
                    ft.Text(empleado.persona.direccion or "N/A")
                ]),
                
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text("Datos de Empleado", weight=ft.FontWeight.BOLD, size=16),
                ft.Row([
                    ft.Column([
                        ft.Text("Usuario:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.usuario)
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Rol:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.nombre_rol or "Sin rol")
                    ])
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("Puesto:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.puesto or "N/A")
                    ]),
                ]),
                ft.Row([
                    ft.Column([
                        ft.Text("Salario:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Q {empleado.salario:,.2f}")
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Fecha Contratación:", weight=ft.FontWeight.BOLD),
                        ft.Text(empleado.fecha_contratacion.strftime("%d/%m/%Y") if empleado.fecha_contratacion else "N/A")
                    ])
                ]),
                
                ft.Row([
                    ft.TextButton("Cerrar", on_click=lambda _: self.cerrar_modal())
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=15, tight=True, scroll=ft.ScrollMode.AUTO),
            padding=20,
            width=600,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def abrir_modal_cambiar_password(self, id_empleado):
        """Abre modal para cambiar contraseña"""
        empleado = self.empleado_service.obtener_empleado(id_empleado)
        if not empleado:
            self.mostrar_alerta("Error", "Empleado no encontrado", VoltTheme.DANGER)
            return
        
        campo_password = ft.TextField(
            label="Nueva Contraseña *",
            password=True,
            can_reveal_password=True,
            border_color=VoltTheme.BORDER_COLOR
        )
        campo_confirmar = ft.TextField(
            label="Confirmar Contraseña *",
            password=True,
            can_reveal_password=True,
            border_color=VoltTheme.BORDER_COLOR
        )
        
        def cambiar():
            if not campo_password.value or not campo_confirmar.value:
                self.mostrar_alerta("Error", "Complete ambos campos", VoltTheme.WARNING)
                return
            
            if campo_password.value != campo_confirmar.value:
                self.mostrar_alerta("Error", "Las contraseñas no coinciden", VoltTheme.WARNING)
                return
            
            resultado = self.empleado_service.cambiar_password(id_empleado, campo_password.value)
            
            if resultado['success']:
                self.mostrar_alerta("Éxito", "Contraseña actualizada exitosamente", VoltTheme.SUCCESS)
                self.cerrar_modal()
            else:
                self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.KEY, color=VoltTheme.PRIMARY, size=30),
                    ft.Text(f"Cambiar Contraseña - {empleado.nombre_completo}", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                campo_password,
                campo_confirmar,
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Cambiar",
                        icon=ft.Icons.SAVE,
                        bgcolor=VoltTheme.PRIMARY,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: cambiar()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=450,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def confirmar_cambio_estado(self, e, empleado, nuevo_estado: bool):
        """Confirma el cambio de estado de un empleado"""
        accion = "desactivar" if not nuevo_estado else "activar"
        
        def confirmar():
            resultado = self.empleado_service.cambiar_estado(empleado.id_empleado, nuevo_estado)
            
            if resultado['success']:
                self.mostrar_alerta("Éxito", f"Empleado {accion}do exitosamente", VoltTheme.SUCCESS)
                self.cerrar_modal()
                self.cargar_empleados()
            else:
                self.mostrar_alerta("Error", resultado['message'], VoltTheme.DANGER)
        
        contenido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=VoltTheme.WARNING, size=40),
                    ft.Text(f"¿Confirmar {accion}ción?", size=18, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Divider(height=1, color=VoltTheme.BORDER_COLOR),
                ft.Text(f"¿Está seguro que desea {accion} este empleado?"),
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                    ft.ElevatedButton(
                        "Confirmar",
                        icon=ft.Icons.CHECK,
                        bgcolor=VoltTheme.DANGER if not nuevo_estado else VoltTheme.SUCCESS,
                        color=ft.Colors.WHITE,
                        on_click=lambda _: confirmar()
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=15, tight=True),
            padding=20,
            width=400,
            bgcolor=ft.Colors.WHITE
        )
        
        self.modal = ft.AlertDialog(modal=True, content=contenido)
        self.page.open(self.modal)
    
    def mostrar_alerta(self, titulo, mensaje, tipo):
        """Muestra una alerta"""
        if tipo == VoltTheme.SUCCESS:
            icono = ft.Icons.CHECK_CIRCLE
        elif tipo == VoltTheme.WARNING:
            icono = ft.Icons.WARNING
        else:
            icono = ft.Icons.ERROR
        
        alerta = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(icono, color=tipo),
                ft.Text(titulo)
            ]),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda _: self.page.close(alerta))
            ]
        )
        self.page.open(alerta)
    
    def cerrar_modal(self):
        """Cierra el modal actual"""
        if self.modal:
            self.page.close(self.modal)
            self.modal = None
