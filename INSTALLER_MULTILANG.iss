; Script de Instalación ONYX MANAGER PRO 1.0 (MULTI-LENGUAJE)

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
DefaultDirName={sd}\OnyxManagerPRO
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\Instalador_Final
OutputBaseFilename=Instalar_Onyx_Manager_PRO_v1.0_MULTILANG
SetupIconFile=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\favicon_io\favicon.ico
WizardImageFile=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\favicon_io\onyx_side.bmp
WizardSmallImageFile=C:\Users\stink\Desktop\VOID_SCUM_MANAGER\favicon_io\onyx_small.bmp
WizardStyle=modern
Compression=lzma
SolidCompression=yes
DisableReadyPage=no
ShowLanguageDialog=yes

[Languages]
; Official Inno Setup Languages (Standard Filenames)
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "japanese"; MessagesFile: "compiler:Default.isl,installer_langs\Japanese.isl"
; Chinese & Hindi might not be present by default, using Default/English as base if specific files fail, 
; but assuming standard pack is installed. Taking a risk on ChineseSimplified.isl.
; If it fails, I will revert to Default.isl for them.
Name: "chinese"; MessagesFile: "compiler:Default.isl,installer_langs\Chinese.isl"
Name: "hindi"; MessagesFile: "compiler:Default.isl,installer_langs\Hindi.isl"

[CustomMessages]
; --- SPANISH (Default) ---
spanish.LicTitle=Verificación de Licencia Onyx
spanish.LicSubTitle=Sistema de Seguridad
spanish.LicIntro=Bienvenido al instalador oficial de Onyx Manager PRO.%nPor favor, valida tu compra para continuar.
spanish.LicLabel=Introduce tu Clave de Producto:
spanish.LicError=Error conectando al Servidor de Licencias.
spanish.LicSuccess=¡Licencia Verificada! Bienvenido.
spanish.LicInvalid=ACCESO DENEGADO: Clave inválida o ya utilizada.
spanish.LicEmpty=Por favor escribe una clave.

; --- ENGLISH ---
english.LicTitle=Onyx License Verification
english.LicSubTitle=Security System
english.LicIntro=Welcome to the official Onyx Manager PRO installer.%nPlease validate your purchase to continue.
english.LicLabel=Enter your Product Key:
english.LicError=Error connecting to License Server.
english.LicSuccess=License Verified! Welcome.
english.LicInvalid=ACCESS DENIED: Invalid or already used key.
english.LicEmpty=Please enter a key.

; --- PORTUGUESE ---
portuguese.LicTitle=Verificação de Licença Onyx
portuguese.LicSubTitle=Sistema de Segurança
portuguese.LicIntro=Bem-vindo ao instalador oficial do Onyx Manager PRO.%nPor favor, valide sua compra para continuar.
portuguese.LicLabel=Insira sua Chave do Produto:
portuguese.LicError=Erro ao conectar ao Servidor de Licenças.
portuguese.LicSuccess=Licença Verificada! Bem-vindo.
portuguese.LicInvalid=ACESSO NEGADO: Chave inválida ou já utilizada.
portuguese.LicEmpty=Por favor, insira uma chave.

; --- RUSSIAN ---
russian.LicTitle=Проверка лицензии Onyx
russian.LicSubTitle=Система безопасности
russian.LicIntro=Добро пожаловать в официальный установщик Onyx Manager PRO.%nПожалуйста, подтвердите покупку, чтобы продолжить.
russian.LicLabel=Введите ключ продукта:
russian.LicError=Ошибка подключения к серверу лицензий.
russian.LicSuccess=Лицензия подтверждена! Добро пожаловать.
russian.LicInvalid=ДОСТУП ЗАПРЕЩЕН: Неверный или использованный ключ.
russian.LicEmpty=Пожалуйста, введите ключ.

; --- GERMAN ---
german.LicTitle=Onyx Lizenzüberprüfung
german.LicSubTitle=Sicherheitssystem
german.LicIntro=Willkommen beim offiziellen Onyx Manager PRO Installer.%nBitte validieren Sie Ihren Kauf, um fortzufahren.
german.LicLabel=Geben Sie Ihren Produktschlüssel ein:
german.LicError=Fehler bei der Verbindung zum Lizenzserver.
german.LicSuccess=Lizenz verifiziert! Willkommen.
german.LicInvalid=ZUGRIFF VERWEIGERT: Ungültiger oder bereits verwendeter Schlüssel.
german.LicEmpty=Bitte geben Sie einen Schlüssel ein.

; --- FRENCH ---
french.LicTitle=Vérification de Licence Onyx
french.LicSubTitle=Système de Sécurité
french.LicIntro=Bienvenue dans l'installateur officiel d'Onyx Manager PRO.%nVeuillez valider votre achat pour continuer.
french.LicLabel=Entrez votre Clé Produit :
french.LicError=Erreur de connexion au serveur de licences.
french.LicSuccess=Licence Vérifiée ! Bienvenue.
french.LicInvalid=ACCÈS REFUSÉ : Clé invalide ou déjà utilisée.
french.LicEmpty=Veuillez entrer une clé.

; --- CHINESE ---
chinese.LicTitle=Onyx 许可证验证
chinese.LicSubTitle=安全系统
chinese.LicIntro=欢迎使用 Onyx Manager PRO 官方安装程序。%n请验证您的购买以继续。
chinese.LicLabel=输入您的产品密钥：
chinese.LicError=连接许可证服务器通过出错。
chinese.LicSuccess=许可证已验证！欢迎。
chinese.LicInvalid=访问被拒绝：密钥无效或已被使用。
chinese.LicEmpty=请输入密钥。

; --- JAPANESE ---
japanese.LicTitle=Onyx ライセンス確認
japanese.LicSubTitle=セキュリティシステム
japanese.LicIntro=Onyx Manager PRO 公式インストーラーへようこそ。%n続行するには購入を検証してください。
japanese.LicLabel=プロダクトキーを入力してください：
japanese.LicError=ライセンスサーバーへの接続エラー。
japanese.LicSuccess=ライセンスが確認されました！ようこそ。
japanese.LicInvalid=アクセス拒否：無効または既に使用されているキーです。
japanese.LicEmpty=キーを入力してください。

; --- HINDI (Using English fallback for main UI, but custom for these) ---
hindi.LicTitle=Onyx लाइसेंस सत्यापन
hindi.LicSubTitle=सुरक्षा प्रणाली
hindi.LicIntro=आधिकारिक Onyx Manager PRO इंस्टॉलर में आपका स्वागत है।%nजारी रखने के लिए कृपया अपनी खरीद को मान्य करें।
hindi.LicLabel=अपनी उत्पाद कुंजी दर्ज करें:
hindi.LicError=लाइसेंस सर्वर से कनेक्ट करने में त्रुटि।
hindi.LicSuccess=लाइसेंस सत्यापित! स्वागत है।
hindi.LicInvalid=पहुंच अस्वीकृत: अमान्य या पहले से उपयोग की गई कुंजी।
hindi.LicEmpty=कृपया एक कुंजी दर्ज करें।

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\stink\Desktop\VOID_SCUM_MANAGER\dist\ONYX MANAGER\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\favicon_io\favicon.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\favicon_io\favicon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
var
  InputPage: TInputQueryWizardPage;
  LicenseVerified: Boolean;

procedure InitializeWizard;
begin
  LicenseVerified := False;
  InputPage := CreateInputQueryPage(wpWelcome,
    ExpandConstant('{cm:LicTitle}'),
    ExpandConstant('{cm:LicSubTitle}'),
    ExpandConstant('{cm:LicIntro}'));
  InputPage.Add(ExpandConstant('{cm:LicLabel}'), False);
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
    MsgBox(ExpandConstant('{cm:LicError}') + #13#10 + 
           'Server Check (py) must be active.', mbError, MB_OK);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = InputPage.ID then
  begin
    if InputPage.Values[0] = '' then
    begin
      MsgBox(ExpandConstant('{cm:LicEmpty}'), mbError, MB_OK);
      Result := False;
    end
    else
    begin
      WizardForm.Enabled := False;
      try
        if CheckLicenseOnline(InputPage.Values[0]) then
        begin
          MsgBox(ExpandConstant('{cm:LicSuccess}'), mbInformation, MB_OK);
          LicenseVerified := True;
          Result := True;
        end
        else
        begin
          MsgBox(ExpandConstant('{cm:LicInvalid}'), mbCriticalError, MB_OK);
          Result := False;
        end;
      finally
        WizardForm.Enabled := True;
      end;
    end;
  end;
end;
