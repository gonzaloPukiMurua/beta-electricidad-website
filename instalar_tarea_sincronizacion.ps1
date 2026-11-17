<#
  instalar_tarea_sincronizacion.ps1
  Registra en el Programador de tareas de Windows la sincronizacion diaria
  ERP -> Web para el usuario actual. Correrlo UNA vez en la PC que tiene
  acceso a la carpeta del ERP:

      powershell -ExecutionPolicy Bypass -File .\instalar_tarea_sincronizacion.ps1
      powershell -ExecutionPolicy Bypass -File .\instalar_tarea_sincronizacion.ps1 -Horarios 07:30,13:30

  Para quitarla:   Unregister-ScheduledTask -TaskName "Beta - Sincronizar ERP a Web"
  Para probarla:   Start-ScheduledTask -TaskName "Beta - Sincronizar ERP a Web"
  Logs:            carpeta logs\ junto a este script
#>
param(
    [string[]]$Horarios = @("07:30", "13:30")
)

$ErrorActionPreference = "Stop"
$nombre = "Beta - Sincronizar ERP a Web"
$bat    = Join-Path $PSScriptRoot "sincronizar.bat"
if (-not (Test-Path $bat)) { throw "No encuentro $bat" }

$accion = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"`"$bat`" /auto`"" -WorkingDirectory $PSScriptRoot
$disparadores = $Horarios | ForEach-Object { New-ScheduledTaskTrigger -Daily -At $_ }
$opciones = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
# Corre con el usuario actual mientras tenga la sesion iniciada (no pide contrasena).
$usuario = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparadores `
    -Settings $opciones -Principal $usuario `
    -Description "Exporta el catalogo del ERP (solo lectura) y sincroniza los cambios con Supabase." `
    -Force | Out-Null

Write-Host "Tarea '$nombre' registrada: todos los dias a las $($Horarios -join ', ')."
Write-Host "Si la PC esta apagada a esa hora, corre apenas se encienda."
Write-Host "Probala ahora con:  Start-ScheduledTask -TaskName '$nombre'"
