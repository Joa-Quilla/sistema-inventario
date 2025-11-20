"""
Vista de Login - Pantalla de inicio de sesión
Diseño basado en Volt Dashboard
"""
import flet as ft
from utils.theme import VoltTheme


class LoginView:
    """Vista de inicio de sesión"""
    
    def __init__(self, auth_service, on_login_success):
        self.auth_service = auth_service
        self.on_login_success = on_login_success
        
        # Controles
        self.txt_usuario = None
        self.txt_password = None
        self.btn_login = None
        self.loading = None
        self.mensaje_error = None

    def build(self):
        """Construye la interfaz de login estilo Volt Dashboard"""
        
        # Campo de usuario
        self.txt_usuario = ft.TextField(
            label="Usuario",
            hint_text="Ingrese su usuario",
            prefix_icon="person",
            autofocus=True,
            on_submit=lambda _: self.txt_password.focus(),
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            text_size=VoltTheme.FONT_SIZE_BASE,
            height=50,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12)
        )
        
        # Campo de contraseña
        self.txt_password = ft.TextField(
            label="Contraseña",
            hint_text="Ingrese su contraseña",
            prefix_icon="lock",
            password=True,
            can_reveal_password=True,
            on_submit=lambda _: self.iniciar_sesion(None),
            border_color=VoltTheme.BORDER_COLOR,
            focused_border_color=VoltTheme.PRIMARY,
            text_size=VoltTheme.FONT_SIZE_BASE,
            height=50,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12)
        )
        
        # Mensaje de error
        self.mensaje_error = ft.Container(
            content=ft.Row([
                ft.Icon("error", color=VoltTheme.DANGER, size=20),
                ft.Text(
                    "",
                    color=VoltTheme.DANGER,
                    size=VoltTheme.FONT_SIZE_SM,
                    weight=ft.FontWeight.W_500
                ),
            ], spacing=8),
            padding=12,
            bgcolor="#FEF2F2",
            border=ft.border.all(1, "#FEE2E2"),
            border_radius=VoltTheme.RADIUS_MD,
            visible=False
        )
        
        # Indicador de carga
        self.loading = ft.ProgressRing(
            width=24,
            height=24,
            stroke_width=3,
            color=VoltTheme.PRIMARY,
            visible=False
        )
        
        # Botón de login
        self.btn_login = ft.Container(
            content=ft.Row([
                ft.Icon("login", color=VoltTheme.TEXT_WHITE, size=20),
                ft.Text(
                    "Iniciar Sesión",
                    color=VoltTheme.TEXT_WHITE,
                    size=VoltTheme.FONT_SIZE_BASE,
                    weight=ft.FontWeight.W_600
                ),
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10),
            bgcolor=VoltTheme.PRIMARY,
            padding=ft.padding.symmetric(horizontal=24, vertical=14),
            border_radius=VoltTheme.RADIUS_MD,
            on_click=self.iniciar_sesion,
            ink=True
        )
        
       
        
        # Contenedor principal estilo Volt
        return ft.Container(
            content=ft.Row([
                # Columna izquierda - Branding (opcional, se puede ocultar)
                ft.Container(
                    content=ft.Column([
                        ft.Icon(
                            "inventory_2",
                            size=120,
                            color=VoltTheme.TEXT_WHITE
                        ),
                        ft.Text(
                            "Sistema de",
                            size=VoltTheme.FONT_SIZE_3XL,
                            weight=ft.FontWeight.BOLD,
                            color=VoltTheme.TEXT_WHITE
                        ),
                        ft.Text(
                            "Inventario",
                            size=VoltTheme.FONT_SIZE_4XL,
                            weight=ft.FontWeight.BOLD,
                            color=VoltTheme.TEXT_WHITE
                        ),
                        ft.Container(height=20),
                        ft.Text(
                            "Gestión completa de inventario,\nventas y compras",
                            size=VoltTheme.FONT_SIZE_BASE,
                            color=VoltTheme.TEXT_WHITE,
                            text_align=ft.TextAlign.CENTER,
                            opacity=0.9
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8
                    ),
                    expand=1,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=VoltTheme.GRADIENT_PRIMARY
                    ),
                    padding=40,
                    visible=True  # Cambiar a False para ocultar en pantallas pequeñas
                ),
                
                # Columna derecha - Formulario
                ft.Container(
                    content=ft.Column([
                        # Header
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    "Bienvenido de nuevo",
                                    size=VoltTheme.FONT_SIZE_2XL,
                                    weight=ft.FontWeight.BOLD,
                                    color=VoltTheme.TEXT_PRIMARY
                                ),
                                ft.Text(
                                    "Inicia sesión para continuar",
                                    size=VoltTheme.FONT_SIZE_BASE,
                                    color=VoltTheme.TEXT_SECONDARY
                                ),
                            ], spacing=4),
                            padding=ft.padding.only(bottom=32)
                        ),
                        
                        # Formulario
                        ft.Container(
                            content=ft.Column([
                                # Usuario
                                ft.Column([
                                    ft.Text(
                                        "Usuario",
                                        size=VoltTheme.FONT_SIZE_SM,
                                        weight=ft.FontWeight.W_600,
                                        color=VoltTheme.TEXT_PRIMARY
                                    ),
                                    self.txt_usuario,
                                ], spacing=6),
                                
                                ft.Container(height=4),
                                
                                # Contraseña
                                ft.Column([
                                    ft.Text(
                                        "Contraseña",
                                        size=VoltTheme.FONT_SIZE_SM,
                                        weight=ft.FontWeight.W_600,
                                        color=VoltTheme.TEXT_PRIMARY
                                    ),
                                    self.txt_password,
                                ], spacing=6),
                                
                                ft.Container(height=8),
                                
                                # Mensaje de error
                                self.mensaje_error,
                                
                                ft.Container(height=8),
                                
                                # Botón login con loading
                                ft.Stack([
                                    self.btn_login,
                                    ft.Container(
                                        content=self.loading,
                                        alignment=ft.alignment.center
                                    )
                                ]),
                                
                            ], spacing=0),
                            width=380
                        ),
                        
                        # Info credenciales
                        ft.Container(height=24),
                        
                        # Footer
                        ft.Container(
                            content=ft.Text(
                                "© 2025 Sistema de Inventario v1.0.0",
                                size=VoltTheme.FONT_SIZE_XS,
                                color=VoltTheme.TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER
                            ),
                            padding=ft.padding.only(top=40)
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0
                    ),
                    expand=1,
                    bgcolor=VoltTheme.BG_PRIMARY,
                    padding=40
                ),
            ], spacing=0, expand=True),
            expand=True
        )

    def iniciar_sesion(self, e, page):
        """Maneja el inicio de sesión"""
        # Validaciones
        if not self.txt_usuario.value or not self.txt_password.value:
            self.mostrar_error("Por favor complete todos los campos", page)
            return
        
        # Mostrar loading
        self.btn_login.disabled = True
        self.loading.visible = True
        self.mensaje_error.visible = False
        page.update()
        
        # Intentar login
        resultado = self.auth_service.login(
            self.txt_usuario.value.strip(),
            self.txt_password.value
        )
        
        # Ocultar loading
        self.btn_login.disabled = False
        self.loading.visible = False
        page.update()
        
        if resultado['success']:
            # Login exitoso
            self.limpiar_campos(page)
            self.on_login_success(resultado['empleado'])
        else:
            # Login fallido
            self.mostrar_error(resultado['message'], page)

    def mostrar_error(self, mensaje: str, page):
        """Muestra un mensaje de error"""
        # Actualizar el texto dentro del Row del mensaje_error
        self.mensaje_error.content.controls[1].value = mensaje
        self.mensaje_error.visible = True
        page.update()

    def limpiar_campos(self, page):
        """Limpia los campos del formulario"""
        self.txt_usuario.value = ""
        self.txt_password.value = ""
        self.mensaje_error.visible = False
        page.update()
