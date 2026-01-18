; Script de Instalación ONYX MANAGER PRO 1.0
; CORREGIDO: Solución al Error 8 de SteamCMD (Rutas sin espacios)

#define MyAppName "Onyx Manager PRO"
#define MyAppVersion "1.0"
#define MyAppPublisher "Onyx Dev Team"
#define MyAppExeName "ONYX MANAGER.exe" 
#define ServerURL "http://201.239.29.194:7003/validar" 

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; --- CORRECCIÓN CRÍTICA ---
; Antes: DefaultDirName={sd}\{#MyAppName} -> Esto creaba "C:\Onyx Manager PRO" y rompía SteamCMD.
; Ahora: Forzamos una carpeta SIN ESPACIOS.
DefaultDirName={sd}\OnyxManagerPRO

DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\Instalador_Final
OutputBaseFilename=Instalar_Onyx_Manager_PRO_v1.0

; --- ESTÉTICA ONYX ---
SetupIconFile=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\favicon_io\favicon.ico
WizardImageFile=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\favicon_io\onyx_side.bmp
WizardSmallImageFile=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\favicon_io\onyx_small.bmp
WizardStyle=modern

Compression=lzma
SolidCompression=yes
DisableReadyPage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Nota: La ruta "Source" es de donde toma los archivos TU PC (puede tener espacios).
; "DestDir" es donde se instalan (ahora sin espacios gracias a DefaultDirName).
Source: "C:\Users\stink\Desktop\VOID_SCUM_MANAGER\dist\ONYX MANAGER\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\favicon_io\favicon.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\favicon_io\favicon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent shellexec

; =====================================================================
; VERIFICACIÓN DE LICENCIA (DRM)
; =====================================================================
[Code]
var
  InputPage: TInputQueryWizardPage;
  LicenseVerified: Boolean;

procedure InitializeWizard;
begin
  LicenseVerified := False;
  InputPage := CreateInputQueryPage(wpWelcome,
    'Verificación de Licencia Onyx',
    'Sistema de Seguridad',
    'Bienvenido al instalador oficial de Onyx Manager PRO.' + #13#10 + 
    'Por favor, valida tu compra para continuar.');
  InputPage.Add('Introduce tu Clave de Producto:', False);
end;

function CheckLicenseOnline(Key: String): Boolean;
var
  WinHttpReq: Variant;
  JsonBody: String;
  Response: String;
begin
  Result := False;
  try
    WinHttpReq := CreateOleObject('WinHttp.WinHttpRequest.5.1');
    WinHttpReq.Open('POST', '{#ServerURL}', False);
    WinHttpReq.SetRequestHeader('Content-Type', 'application/json');
    JsonBody := '{"clave": "' + Key + '"}';
    WinHttpReq.Send(JsonBody);
    
    if WinHttpReq.Status = 200 then
    begin
      Response := WinHttpReq.ResponseText;
      if Pos('success', Response) > 0 then Result := True;
    end;
  except
    MsgBox('Error conectando al Servidor de Licencias.' + #13#10 + 
           'Verifica que el servidor (server.py) esté activo.', mbError, MB_OK);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = InputPage.ID then
  begin
    if InputPage.Values[0] = '' then
    begin
      MsgBox('Por favor escribe una clave.', mbError, MB_OK);
      Result := False;
    end
    else
    begin
      WizardForm.Enabled := False;
      try
        if CheckLicenseOnline(InputPage.Values[0]) then
        begin
          MsgBox('¡Licencia Verificada! Bienvenido.', mbInformation, MB_OK);
          LicenseVerified := True;
          Result := True;
        end
        else
        begin
          MsgBox('ACCESO DENEGADO: Clave inválida o ya utilizada.', mbCriticalError, MB_OK);
          Result := False;
        end;
      finally
        WizardForm.Enabled := True;
      end;
    end;
  end;
end;