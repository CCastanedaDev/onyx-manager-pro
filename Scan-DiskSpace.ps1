# Scan-DiskSpace.ps1
# Script de solo lectura para escanear y analizar espacio consumido por cachés de desarrollo y temporales en Windows.

$ErrorActionPreference = "SilentlyContinue"

# Función para formatear el tamaño en MB o GB
function Format-Size {
    param([double]$Bytes)
    if ($Bytes -ge 1GB) {
        return "$([Math]::Round($Bytes / 1GB, 2)) GB"
    } elseif ($Bytes -ge 1MB) {
        return "$([Math]::Round($Bytes / 1MB, 2)) MB"
    } else {
        return "$([Math]::Round($Bytes / 1KB, 2)) KB"
    }
}

# Función para obtener el tamaño de un directorio
function Get-FolderSize {
    param([string]$Path)
    if (Test-Path $Path) {
        $files = Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue
        $size = ($files | Measure-Object -Property Length -Sum).Sum
        if ($size) { return $size }
    }
    return 0
}

# Función para buscar carpetas de dependencias inactivas (node_modules, venv, .venv, etc.)
function Get-InactiveDevFolders {
    param(
        [string]$RootPath,
        [int]$DaysInactive = 90
    )
    
    $results = @()
    if (-not (Test-Path $RootPath)) { return $results }
    
    Write-Host "Buscando entornos virtuales y node_modules inactivos en: $RootPath (Inactivos por > $DaysInactive días)..." -ForegroundColor Cyan
    
    # Excluimos directorios del sistema y aplicaciones del usuario para agilizar
    $excludeNames = @("AppData", "OneDrive", "Searches", "Contacts", "Links", "Saved Games", "Favorites", "MicrosoftEdgeBackups", "Documents\WindowsPowerShell")
    $subdirs = Get-ChildItem -Path $RootPath -Directory -ErrorAction SilentlyContinue | Where-Object { $excludeNames -notcontains $_.Name }
    
    $targetFolders = @()
    foreach ($dir in $subdirs) {
        $targetFolders += Get-ChildItem -Path $dir.FullName -Recurse -Directory -Filter "node_modules" -ErrorAction SilentlyContinue
        $targetFolders += Get-ChildItem -Path $dir.FullName -Recurse -Directory -Filter "venv" -ErrorAction SilentlyContinue
        $targetFolders += Get-ChildItem -Path $dir.FullName -Recurse -Directory -Filter ".venv" -ErrorAction SilentlyContinue
    }

    $cutoffDate = (Get-Date).AddDays(-$DaysInactive)

    foreach ($folder in $targetFolders) {
        $files = Get-ChildItem $folder.FullName -Recurse -File -ErrorAction SilentlyContinue
        $lastWrite = $files | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty LastWriteTime

        # Si la carpeta está vacía o su último cambio es anterior a la fecha de corte
        if (-not $lastWrite -or $lastWrite -lt $cutoffDate) {
            $size = Get-FolderSize -Path $folder.FullName
            if ($size -gt 1MB) { # Mostrar solo si pesa más de 1MB para no saturar
                $results += [PSCustomObject]@{
                    Path         = $folder.FullName
                    Size         = $size
                    FormattedSize = Format-Size $size
                    LastModified = if ($lastWrite) { $lastWrite } else { $folder.LastWriteTime }
                }
            }
        }
    }
    return $results
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "INICIANDO ESCANEO DE ESPACIO EN DISCO (SOLO LECTURA)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Lista de rutas de cachés conocidas
$CachesToCheck = @{
    "NPM Cache"             = "$env:APPDATA\npm-cache"
    "PIP (Python) Cache"    = "$env:LOCALAPPDATA\pip\Cache"
    "UV (Python Fast) Cache"= "$env:LOCALAPPDATA\uv\cache"
    "PyInstaller Cache"     = "$env:LOCALAPPDATA\pyinstaller"
    "Gradle Cache"          = "$env:USERPROFILE\.gradle\caches"
    "NuGet Packages"        = "$env:USERPROFILE\.nuget\packages"
    "Cargo (Rust) Registry" = "$env:USERPROFILE\.cargo\registry"
    "Cargo (Rust) Git"      = "$env:USERPROFILE\.cargo\git"
    "Go Modules Cache"      = "$env:USERPROFILE\go\pkg\mod"
    "Windows Temp"          = "C:\Windows\Temp"
    "Windows User Temp"     = $env:TEMP
    "Windows Delivery Opt"  = "C:\Windows\SoftwareDistribution\Download"
    "Chrome Cache"          = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
    "Edge Cache"            = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
    "Downloads Folder"      = "$env:USERPROFILE\Downloads"
}

Write-Host "`n[1/2] Analizando cachés y carpetas de sistema..." -ForegroundColor Yellow
$CacheResults = @()
foreach ($cache in $CachesToCheck.GetEnumerator()) {
    if (Test-Path $cache.Value) {
        Write-Host "Escaneando $($cache.Key)..." -ForegroundColor Gray
        $size = Get-FolderSize -Path $cache.Value
        if ($size -gt 0) {
            $CacheResults += [PSCustomObject]@{
                "Nombre" = $cache.Key
                "Ruta"   = $cache.Value
                "Tamaño" = Format-Size $size
                "Bytes"  = $size
            }
        }
    }
}

# 2. Buscar carpetas de proyectos inactivas
Write-Host "`n[2/2] Buscando carpetas de desarrollo obsoletas (node_modules, venvs)..." -ForegroundColor Yellow
$ProjectRoot = "$env:USERPROFILE"
$InactiveFolders = Get-InactiveDevFolders -RootPath $ProjectRoot -DaysInactive 90

# Mostrar resultados
Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "RESULTADOS DEL ANÁLISIS" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

Write-Host "`n--- Cachés de desarrollo y carpetas del sistema detectadas ---" -ForegroundColor Cyan
if ($CacheResults.Count -gt 0) {
    $CacheResults | Sort-Object Bytes -Descending | Format-Table -Property Nombre, Tamaño, Ruta
} else {
    Write-Host "No se detectaron datos en las cachés configuradas o no tienen un tamaño medible." -ForegroundColor Gray
}

if ($InactiveFolders.Count -gt 0) {
    Write-Host "`n--- Carpetas inactivas de proyectos (venv, node_modules) (>90 días sin uso) ---" -ForegroundColor Cyan
    $InactiveFolders | Sort-Object Size -Descending | Format-Table -Property FormattedSize, LastModified, Path
} else {
    Write-Host "`nNo se encontraron entornos virtuales o node_modules inactivos (>90 días) con tamaño significativo." -ForegroundColor Gray
}

Write-Host "`nNota: Este script no ha borrado nada. Consulta las recomendaciones para limpiar de forma segura." -ForegroundColor Yellow
