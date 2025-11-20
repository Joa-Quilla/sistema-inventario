import flet as ft
from repositories.proveedor_repository import ProveedorRepository
from models.proveedor import Proveedor
from utils.theme import VoltTheme


class ProveedoresView:
    def __init__(self, page: ft.Page, on_back=None):
        self.page = page
        self.on_back = on_back
        self.proveedor_repo = ProveedorRepository()
        
        # Estado
        self.proveedores = []
        
        # Paginación
        self.pagina_actual = 1
        self.items_por_pagina = 5
        
        # Búsqueda
        self.busqueda_actual = ""
        
        # Referencias a controles
        self.tabla_proveedores = None
        self.paginacion_container = None
        self.campo_busqueda = None
        self.modal = None
        
        # Para formulario
        self.campo_nombre_empresa = None
        self.campo_telefono_empresa = None
        self.campo_email_empresa = None
        self.campo_direccion_empresa = None
        self.campo_nit_empresa = None
        self.campo_sitio_web = None
        self.dropdown_tipo_proveedor = None
        self.campo_terminos_pago = None
        
        self.proveedor_editando = None
    
    def build(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=VoltTheme.PRIMARY,
                    on_click=lambda _: self.page.go("/dashboard") if not self.on_back else self.on_back(),
                    tooltip="Volver al Dashboard"
                ),
                ft.Text(
                    "Gestión de Proveedores",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
            ]),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        # Barra de búsqueda y acciones
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar por empresa o NIT...",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_busqueda_change,
            expand=True
        )
        
        barra_acciones = ft.Container(
            content=ft.Row([
                self.campo_busqueda,
                ft.ElevatedButton(
                    "Nuevo Proveedor",
                    icon=ft.Icons.ADD,
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.abrir_modal_nuevo()
                ),
            ], spacing=10),
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Tabla de proveedores
        self.tabla_proveedores = ft.Column(
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        )
        
        tabla_container = ft.Container(
            content=self.tabla_proveedores,
            bgcolor=ft.Colors.WHITE,
            padding=20,
            expand=True
        )
        
        # Paginación
        self.paginacion_container = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        paginacion_wrapper = ft.Container(
            content=self.paginacion_container,
            padding=20,
            bgcolor=ft.Colors.WHITE
        )
        
        # Layout principal
        content = ft.Column([
            header,
            barra_acciones,
            tabla_container,
            paginacion_wrapper
        ], spacing=0, expand=True)
        
        # Cargar datos iniciales
        self.cargar_proveedores()
        
        return content
    
    def on_busqueda_change(self, e):
        """Maneja el cambio en el campo de búsqueda"""
        self.busqueda_actual = e.control.value
        self.pagina_actual = 1
        self.cargar_proveedores()
    
    def cargar_proveedores(self):
        """Carga la lista de proveedores desde la base de datos"""
        try:
            busqueda = self.busqueda_actual if self.busqueda_actual else None
            self.proveedores = self.proveedor_repo.listar_todos(busqueda=busqueda)  # Cambio a listar_todos
            self.actualizar_tabla()
            self.actualizar_paginacion()
        except Exception as e:
            print(f"[ERROR] Al cargar proveedores: {str(e)}")
            self.mostrar_mensaje("Error", f"Error al cargar proveedores: {str(e)}", "error")
    
    def actualizar_tabla(self):
        """Actualiza la tabla de proveedores con los datos paginados"""
        self.tabla_proveedores.controls.clear()
        
        # Header de la tabla
        header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("Empresa", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=2),
                ft.Container(ft.Text("NIT", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Teléfono", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Tipo", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE), expand=1),
                ft.Container(ft.Text("Estado", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
                ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), expand=1),
            ]),
            bgcolor=VoltTheme.PRIMARY,
            padding=15,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        self.tabla_proveedores.controls.append(header)
        
        # Calcular índices de paginación
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        proveedores_pagina = self.proveedores[inicio:fin]
        
        # Filas de proveedores
        if not proveedores_pagina:
            self.tabla_proveedores.controls.append(
                ft.Container(
                    content=ft.Text("No hay proveedores registrados", size=14, color=ft.Colors.GREY_600),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        else:
            for proveedor in proveedores_pagina:
                fila = self.crear_fila_proveedor(proveedor)
                self.tabla_proveedores.controls.append(fila)
        
        self.page.update()
    
    def crear_fila_proveedor(self, proveedor: Proveedor):
        """Crea una fila de la tabla para un proveedor"""
        # Badge de estado
        if proveedor.estado:
            estado_badge = ft.Container(
                content=ft.Text("Activo", size=10, color=ft.Colors.WHITE),
                bgcolor=VoltTheme.SUCCESS,
                padding=ft.padding.symmetric(horizontal=10, vertical=3),
                border_radius=15
            )
        else:
            estado_badge = ft.Container(
                content=ft.Text("Inactivo", size=10, color=ft.Colors.WHITE),
                bgcolor=VoltTheme.DANGER,
                padding=ft.padding.symmetric(horizontal=10, vertical=3),
                border_radius=15
            )
        
        fila = ft.Container(
            content=ft.Row([
                ft.Container(
                    ft.Text(proveedor.nombre_empresa, size=13),
                    expand=2
                ),
                ft.Container(
                    ft.Text(proveedor.nit_empresa or "N/A", size=13),
                    expand=1
                ),
                ft.Container(
                    ft.Text(proveedor.telefono_empresa, size=13),
                    expand=1
                ),
                ft.Container(
                    ft.Text(proveedor.tipo_proveedor or "General", size=13),
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
                            icon_size=18,
                            icon_color=VoltTheme.INFO,
                            tooltip="Ver Detalle",
                            on_click=lambda _, p=proveedor: self.ver_detalle_proveedor(p)
                        ),
                        ft.IconButton(
                            icon="edit",
                            icon_size=18,
                            icon_color=VoltTheme.WARNING,
                            tooltip="Editar",
                            on_click=lambda _, p=proveedor: self.abrir_modal_editar(p)
                        ),
                        ft.IconButton(
                            icon="power_settings_new" if proveedor.estado else "check_circle",
                            icon_size=18,
                            icon_color=VoltTheme.DANGER if proveedor.estado else VoltTheme.SUCCESS,
                            tooltip="Desactivar" if proveedor.estado else "Activar",
                            on_click=lambda _, p=proveedor: self.cambiar_estado_proveedor(p)
                        ),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    expand=1,
                    alignment=ft.alignment.center
                ),
            ]),
            padding=15,
            border=ft.border.only(bottom=ft.BorderSide(1, VoltTheme.BORDER_COLOR))
        )
        
        return fila
    
    def actualizar_paginacion(self):
        """Actualiza los controles de paginación"""
        self.paginacion_container.controls.clear()
        
        total_paginas = (len(self.proveedores) + self.items_por_pagina - 1) // self.items_por_pagina
        
        if total_paginas <= 1:
            self.page.update()
            return
        
        # Botón anterior
        self.paginacion_container.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                disabled=self.pagina_actual == 1,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual > 1 else VoltTheme.TEXT_SECONDARY,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual - 1)
            )
        )
        
        # Números de página
        for i in range(1, total_paginas + 1):
            es_actual = i == self.pagina_actual
            self.paginacion_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        str(i), 
                        size=14, 
                        weight=ft.FontWeight.BOLD if es_actual else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if es_actual else VoltTheme.TEXT_PRIMARY
                    ),
                    width=35,
                    height=35,
                    bgcolor=VoltTheme.PRIMARY if es_actual else ft.Colors.TRANSPARENT,
                    border=ft.border.all(1, VoltTheme.PRIMARY) if not es_actual else None,
                    border_radius=5,
                    alignment=ft.alignment.center,
                    on_click=lambda _, pagina=i: self.cambiar_pagina(pagina) if not es_actual else None,
                    ink=True if not es_actual else False
                )
            )
        
        # Botón siguiente
        self.paginacion_container.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                disabled=self.pagina_actual == total_paginas,
                icon_color=VoltTheme.PRIMARY if self.pagina_actual < total_paginas else VoltTheme.TEXT_SECONDARY,
                on_click=lambda _: self.cambiar_pagina(self.pagina_actual + 1)
            )
        )
        
        self.page.update()
    
    def cambiar_pagina(self, nueva_pagina):
        """Cambia a la página especificada"""
        self.pagina_actual = nueva_pagina
        self.actualizar_tabla()
        self.actualizar_paginacion()
    
    def abrir_modal_nuevo(self):
        """Abre el modal para crear un nuevo proveedor"""
        self.proveedor_editando = None
        self._crear_modal_formulario("Nuevo Proveedor")
    
    def abrir_modal_editar(self, proveedor: Proveedor):
        """Abre el modal para editar un proveedor"""
        self.proveedor_editando = proveedor
        self._crear_modal_formulario("Editar Proveedor", proveedor)
    
    def _crear_modal_formulario(self, titulo: str, proveedor: Proveedor = None):
        """Crea el modal del formulario de proveedor"""
        # Campos del formulario
        self.campo_nombre_empresa = ft.TextField(
            label="Nombre de la Empresa *",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            value=proveedor.nombre_empresa if proveedor else ""
        )
        
        self.campo_nit_empresa = ft.TextField(
            label="NIT",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional",
            value=proveedor.nit_empresa if proveedor else ""
        )
        
        self.campo_telefono_empresa = ft.TextField(
            label="Teléfono *",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            value=proveedor.telefono_empresa if proveedor else ""
        )
        
        self.campo_email_empresa = ft.TextField(
            label="Email",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional",
            value=proveedor.email_empresa if proveedor else ""
        )
        
        self.campo_direccion_empresa = ft.TextField(
            label="Dirección",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            multiline=True,
            min_lines=2,
            max_lines=3,
            hint_text="Opcional",
            value=proveedor.direccion_empresa if proveedor else ""
        )
        
        self.campo_sitio_web = ft.TextField(
            label="Sitio Web",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Opcional",
            value=proveedor.sitio_web if proveedor else ""
        )
        
        self.dropdown_tipo_proveedor = ft.Dropdown(
            label="Tipo de Proveedor",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            options=[
                ft.dropdown.Option("General"),
                ft.dropdown.Option("Mayorista"),
                ft.dropdown.Option("Minorista"),
                ft.dropdown.Option("Fabricante"),
                ft.dropdown.Option("Distribuidor"),
                ft.dropdown.Option("Importador"),
            ],
            value=proveedor.tipo_proveedor if proveedor else "General"
        )
        
        self.campo_terminos_pago = ft.TextField(
            label="Términos de Pago",
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            hint_text="Ej: 30 días, Contado, etc.",
            value=proveedor.terminos_pago if proveedor else ""
        )
        
        # Contenido del modal con scroll
        modal_content = ft.Container(
            content=ft.Column([
                ft.Text(
                    titulo,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                self.campo_nombre_empresa,
                self.campo_nit_empresa,
                
                ft.Row([
                    ft.Column([self.campo_telefono_empresa], expand=1),
                    ft.Column([self.campo_email_empresa], expand=1),
                ], spacing=10),
                
                self.campo_direccion_empresa,
                self.campo_sitio_web,
                
                ft.Row([
                    ft.Column([self.dropdown_tipo_proveedor], expand=1),
                    ft.Column([self.campo_terminos_pago], expand=1),
                ], spacing=10),
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            width=900,
            height=450,
            border_radius=10
        )
        
        # Botones fuera del scroll
        botones = ft.Container(
            content=ft.Row([
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda _: self.cerrar_modal()
                ),
                ft.ElevatedButton(
                    "Guardar",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.guardar_proveedor()
                ),
            ], alignment=ft.MainAxisAlignment.END, spacing=10),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.only(left=30, right=30, bottom=20),
            width=900
        )
        
        # Contenedor principal
        contenedor_principal = ft.Column([
            modal_content,
            botones
        ], spacing=0)
        
        self.modal = ft.AlertDialog(
            modal=True,
            content=contenedor_principal
        )
        
        self.page.open(self.modal)
    
    def guardar_proveedor(self):
        """Guarda o actualiza un proveedor"""
        # Limpiar errores previos
        self.campo_nombre_empresa.error_text = None
        self.campo_telefono_empresa.error_text = None
        self.campo_email_empresa.error_text = None
        self.page.update()
        
        # Validaciones
        if not self.campo_nombre_empresa.value or not self.campo_nombre_empresa.value.strip():
            self.campo_nombre_empresa.error_text = "El nombre de la empresa es obligatorio"
            self.page.update()
            return
        
        if not self.campo_telefono_empresa.value or not self.campo_telefono_empresa.value.strip():
            self.campo_telefono_empresa.error_text = "El teléfono es obligatorio"
            self.page.update()
            return
        
        # Validar email (formato si se proporciona)
        if self.campo_email_empresa.value and self.campo_email_empresa.value.strip():
            if "@" not in self.campo_email_empresa.value or "." not in self.campo_email_empresa.value:
                self.campo_email_empresa.error_text = "Formato de email inválido"
                self.page.update()
                return
        
        try:
            # Crear objeto Proveedor
            proveedor = Proveedor(
                id_proveedor=self.proveedor_editando.id_proveedor if self.proveedor_editando else None,
                nombre_empresa=self.campo_nombre_empresa.value.strip(),
                nit_empresa=self.campo_nit_empresa.value.strip() if self.campo_nit_empresa.value else None,
                telefono_empresa=self.campo_telefono_empresa.value.strip(),
                email_empresa=self.campo_email_empresa.value.strip() if self.campo_email_empresa.value else None,
                direccion_empresa=self.campo_direccion_empresa.value.strip() if self.campo_direccion_empresa.value else None,
                sitio_web=self.campo_sitio_web.value.strip() if self.campo_sitio_web.value else None,
                tipo_proveedor=self.dropdown_tipo_proveedor.value,
                terminos_pago=self.campo_terminos_pago.value.strip() if self.campo_terminos_pago.value else None,
                estado=self.proveedor_editando.estado if self.proveedor_editando else True
            )
            
            # Guardar en BD
            if self.proveedor_editando:
                resultado = self.proveedor_repo.actualizar(proveedor)
            else:
                resultado = self.proveedor_repo.crear(proveedor)
            
            if resultado.get('success'):
                accion = "actualizado" if self.proveedor_editando else "creado"
                self.mostrar_mensaje("Éxito", f"Proveedor {accion} exitosamente", "success")
                self.cerrar_modal()
                self.cargar_proveedores()
            else:
                mensaje_error = resultado.get('message', 'Error al guardar el proveedor')
                
                # Detectar error de NIT duplicado
                if 'duplicate' in mensaje_error.lower() or 'unique' in mensaje_error.lower() or 'nit_empresa' in mensaje_error.lower():
                    self.mostrar_mensaje("NIT Duplicado", 
                        "El NIT ingresado ya está registrado para otro proveedor. Por favor ingrese un NIT diferente.", 
                        "warning")
                else:
                    self.mostrar_mensaje("Error", mensaje_error, "error")
                
        except Exception as e:
            error_msg = str(e)
            
            # Detectar error de NIT duplicado en la excepción
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower() or 'nit_empresa' in error_msg.lower():
                self.mostrar_mensaje("NIT Duplicado", 
                    "El NIT ingresado ya está registrado para otro proveedor. Por favor ingrese un NIT diferente.", 
                    "warning")
            else:
                self.mostrar_mensaje("Error", f"Error al guardar el proveedor: {error_msg}", "error")
    
    def ver_detalle_proveedor(self, proveedor: Proveedor):
        """Muestra el detalle completo de un proveedor"""
        # Cargar datos completos
        proveedor_completo = self.proveedor_repo.obtener_por_id(proveedor.id_proveedor)
        
        if not proveedor_completo:
            self.mostrar_mensaje("Error", "No se pudo cargar el detalle del proveedor", "error")
            return
        
        # Contenido del detalle
        detalle_content = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Detalle del Proveedor",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=VoltTheme.PRIMARY
                ),
                ft.Divider(color=VoltTheme.BORDER_COLOR),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Empresa:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(proveedor_completo.nombre_empresa, size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("NIT:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(proveedor_completo.nit_empresa or "N/A", size=13),
                    ], expand=1),
                ]),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Teléfono:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(proveedor_completo.telefono_empresa, size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Email:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(proveedor_completo.email_empresa or "N/A", size=13),
                    ], expand=1),
                ]),
                
                ft.Column([
                    ft.Text("Dirección:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(proveedor_completo.direccion_empresa or "N/A", size=13),
                ]),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Sitio Web:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(proveedor_completo.sitio_web or "N/A", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Tipo:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(proveedor_completo.tipo_proveedor or "General", size=13),
                    ], expand=1),
                ]),
                
                ft.Column([
                    ft.Text("Términos de Pago:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(proveedor_completo.terminos_pago or "N/A", size=13),
                ]),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Estado:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text("Activo" if proveedor_completo.estado else "Inactivo", size=13),
                    ], expand=1),
                    ft.Column([
                        ft.Text("Fecha Registro:", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(
                            proveedor_completo.fecha_registro.strftime("%d/%m/%Y") if proveedor_completo.fecha_registro else "N/A",
                            size=13
                        ),
                    ], expand=1),
                ]),
                
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            width=800,
            height=400,
            border_radius=10
        )
        
        # Botón cerrar fuera del scroll
        boton_cerrar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Cerrar",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.cerrar_modal()
                ),
            ], alignment=ft.MainAxisAlignment.END),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.only(left=30, right=30, bottom=20),
            width=800
        )
        
        # Contenedor principal
        contenedor_detalle = ft.Column([
            detalle_content,
            boton_cerrar
        ], spacing=0)
        
        self.modal = ft.AlertDialog(
            modal=True,
            content=contenedor_detalle
        )
        
        self.page.open(self.modal)
    
    def cambiar_estado_proveedor(self, proveedor: Proveedor):
        """Activa o desactiva un proveedor"""
        nuevo_estado = not proveedor.estado
        accion = "activar" if nuevo_estado else "desactivar"
        
        def confirmar(_):
            try:
                proveedor.estado = nuevo_estado
                resultado = self.proveedor_repo.actualizar(proveedor)
                
                if resultado.get('success'):
                    self.mostrar_mensaje("Éxito", f"Proveedor {accion}do exitosamente", "success")
                    self.cerrar_modal()
                    self.cargar_proveedores()
                else:
                    self.mostrar_mensaje("Error", resultado.get('message', f'Error al {accion} el proveedor'), "error")
                    
            except Exception as e:
                self.mostrar_mensaje("Error", f"Error al {accion} el proveedor: {str(e)}", "error")
        
        confirmacion = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Confirmar {accion.capitalize()}"),
            content=ft.Text(f"¿Está seguro que desea {accion} el proveedor '{proveedor.nombre_empresa}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.cerrar_modal()),
                ft.ElevatedButton(
                    accion.capitalize(),
                    bgcolor=VoltTheme.SUCCESS if nuevo_estado else VoltTheme.DANGER,
                    color=ft.Colors.WHITE,
                    on_click=confirmar
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.modal = confirmacion
        self.page.open(self.modal)
    
    def cerrar_modal(self):
        """Cierra el modal actual"""
        if self.modal:
            self.page.close(self.modal)
            self.modal = None
    
    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        """Muestra un mensaje estilo SweetAlert"""
        icon_map = {
            "success": ft.Icons.CHECK_CIRCLE,
            "error": ft.Icons.ERROR,
            "warning": ft.Icons.WARNING,
            "info": ft.Icons.INFO
        }
        
        color_map = {
            "success": VoltTheme.SUCCESS,
            "error": VoltTheme.DANGER,
            "warning": VoltTheme.WARNING,
            "info": VoltTheme.INFO
        }
        
        icono = icon_map.get(tipo, ft.Icons.INFO)
        color = color_map.get(tipo, VoltTheme.INFO)
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(icono, color=color, size=30),
                ft.Text(titulo, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            content=ft.Text(mensaje),
            actions=[
                ft.ElevatedButton(
                    "Aceptar",
                    bgcolor=VoltTheme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self.page.close(dialogo)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.open(dialogo)
