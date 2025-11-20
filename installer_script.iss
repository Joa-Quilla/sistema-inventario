; Script de Inno Setup para Sistema de Inventario
; Genera un instalador profesional para Windows

#define MyAppName "Sistema de Inventario"
#define MyAppVersion "1.0"
#define MyAppPublisher "Universidad - Ingeniería de Software II"
#define MyAppExeName "Sistema_Inventario.exe"

[Setup]
; Información de la aplicación
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Sistema Inventario
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Ruta del icono
SetupIconFile=icon.ico
; Archivo de salida
OutputDir=.
OutputBaseFilename=Sistema_Inventario_Setup
; Compresión
Compression=lzma
SolidCompression=yes
; Permisos de administrador
PrivilegesRequired=admin
; Interfaz moderna
WizardStyle=modern
; Información de versión
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Sistema de Gestión de Inventario

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Archivos del programa
Source: "Sistema_Inventario_v1.0\Sistema_Inventario.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Sistema_Inventario_v1.0\setup_database.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "Sistema_Inventario_v1.0\Sistema_inventario.sql"; DestDir: "{app}"; Flags: ignoreversion
Source: "Sistema_Inventario_v1.0\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "Sistema_Inventario_v1.0\MANUAL_INSTALACION.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
; Accesos directos
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Manual de Instalación"; Filename: "{app}\MANUAL_INSTALACION.md"
Name: "{group}\Configurar Base de Datos"; Filename: "python"; Parameters: """{app}\setup_database.py"""; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Configurar la base de datos PRIMERO
Filename: "python"; Parameters: """{app}\setup_database.py"""; WorkingDir: "{app}"; Description: "Configurar base de datos PostgreSQL"; Flags: postinstall shellexec skipifsilent waituntilterminated
; Ejecutar la aplicación DESPUÉS
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: postinstall skipifsilent nowait

[Code]
var
  PostgreSQLPage: TOutputMsgWizardPage;

function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function IsPostgreSQLInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('psql', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

procedure InitializeWizard;
begin
  // Página de advertencia sobre requisitos
  PostgreSQLPage := CreateOutputMsgPage(wpWelcome,
    'Requisitos del Sistema', 
    'Componentes necesarios para ejecutar la aplicación',
    'Este sistema requiere:' + #13#10 + #13#10 +
    '• PostgreSQL 12 o superior' + #13#10 +
    '• Python 3.8 o superior (para configuración de BD)' + #13#10 + #13#10 +
    'La instalación verificará estos componentes en la siguiente página.');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ErrorMessage: String;
begin
  Result := True;
  
  if CurPageID = PostgreSQLPage.ID then
  begin
    ErrorMessage := '';
    
    // Verificar Python
    if not IsPythonInstalled then
      ErrorMessage := ErrorMessage + '• Python no está instalado' + #13#10;
    
    // Verificar PostgreSQL
    if not IsPostgreSQLInstalled then
      ErrorMessage := ErrorMessage + '• PostgreSQL no está instalado' + #13#10;
    
    if ErrorMessage <> '' then
    begin
      if MsgBox('Se detectaron los siguientes problemas:' + #13#10 + #13#10 + 
                ErrorMessage + #13#10 +
                '¿Desea continuar de todas formas?' + #13#10 + #13#10 +
                'Nota: Deberá instalar estos componentes antes de usar la aplicación.',
                mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
      end;
    end
    else
    begin
      MsgBox('✓ Todos los requisitos están instalados correctamente.', mbInformation, MB_OK);
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
