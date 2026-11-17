@echo off
setlocal EnableExtensions
:: ============================================================================
::  Sincronizador ERP -> Web (Supabase)
::
::  Uso:
::    sincronizar.bat          manual: muestra todo en pantalla y pausa si falla
::    sincronizar.bat /auto    tarea programada: sin pausas, deja un log en logs\
::
::  Solo LEE el ERP. El catalogo nuevo pasa a ser la base de comparacion
::  recien cuando la subida a Supabase termina bien; si falla, la proxima
::  corrida vuelve a comparar contra el ultimo catalogo bueno.
:: ============================================================================

:: --- CONFIGURACION (editar si cambian las rutas) ----------------------------
set "DATOS=C:\a\datos"
set "DIAS_HISTORIAL=60"
set "DIAS_CAMBIOS=30"
set "DIAS_LOGS=90"
:: ----------------------------------------------------------------------------

set "SCRIPTS=%~dp0"
set "HISTORIAL=%SCRIPTS%historial"
set "LOGS=%SCRIPTS%logs"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

:: Python: el instalado por el usuario si existe (el alias de WindowsApps
:: puede no andar en una tarea programada); si no, el del PATH.
set "PYTHON=python"
if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PYTHON=%LOCALAPPDATA%\Python\bin\python.exe"

:: Fecha y hora sin depender de la configuracion regional
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmm"') do set "STAMP=%%i"

if not exist "%HISTORIAL%" mkdir "%HISTORIAL%"
if not exist "%LOGS%" mkdir "%LOGS%"

if /i "%~1"=="/auto" (
    call "%~f0" /run > "%LOGS%\sync_%STAMP%.log" 2>&1
    exit /b %errorlevel%
)
if /i "%~1"=="/run" goto :sincronizar

:: Modo manual
call :sincronizar
if errorlevel 1 (
    echo.
    echo  La sincronizacion fallo. Revisa los mensajes de arriba.
    pause
    exit /b 1
)
timeout /t 5 >nul
exit /b 0

:: ============================================================================
:sincronizar
echo === Sincronizador ERP ^> Web  %STAMP% ===
echo Python: %PYTHON%

:: Catalogo anterior: el mas reciente que se sincronizo bien
set "ANTERIOR="
for /f "delims=" %%f in ('dir /b /o-n "%HISTORIAL%\catalogo_*.xlsx" 2^>nul') do (
    if not defined ANTERIOR set "ANTERIOR=%HISTORIAL%\%%f"
)

set "PENDIENTE=%HISTORIAL%\pendiente_%STAMP%.xlsx"
set "NUEVO=%HISTORIAL%\catalogo_%STAMP%.xlsx"
set "CAMBIOS=%SCRIPTS%cambios_%STAMP%.xlsx"

echo.
echo [1/3] Exportando catalogo del ERP...
"%PYTHON%" "%SCRIPTS%exportar_catalogo.py" --datos "%DATOS%" --salida "%PENDIENTE%"
if errorlevel 1 (
    echo ERROR en la exportacion. Verifica que "%DATOS%" sea accesible.
    exit /b 1
)

echo.
if defined ANTERIOR (
    echo [2/3] Detectando cambios respecto a %ANTERIOR%
    "%PYTHON%" "%SCRIPTS%detectar_cambios.py" --datos "%DATOS%" --anterior "%ANTERIOR%" --salida "%CAMBIOS%"
    if errorlevel 1 (
        echo ERROR al detectar cambios.
        del "%PENDIENTE%" 2>nul
        exit /b 1
    )
) else (
    echo [2/3] Primera ejecucion: se sube el catalogo completo.
    set "CAMBIOS=%PENDIENTE%"
)

echo.
echo [3/3] Sincronizando con Supabase...
"%PYTHON%" "%SCRIPTS%sincronizar_db.py" --cambios "%CAMBIOS%"
if errorlevel 1 (
    echo ERROR en la sincronizacion. Revisa el .env y la conexion a internet.
    echo El catalogo de esta corrida NO queda como base; la proxima vuelve a comparar contra el anterior.
    del "%PENDIENTE%" 2>nul
    exit /b 1
)

move /y "%PENDIENTE%" "%NUEVO%" >nul

:: Respaldo semanal de Supabase (solo si el ultimo tiene 7 dias o mas).
:: Si falla, la sincronizacion ya quedo hecha; se informa como error para
:: que se vea en el log y se reintenta en la proxima corrida.
echo.
echo [extra] Respaldo semanal de Supabase...
"%PYTHON%" "%SCRIPTS%respaldar_supabase.py" --si-pasaron-dias 7
set "ERROR_RESPALDO=%errorlevel%"

:: Limpieza: archivos viejos (forfiles da error si no hay nada que borrar)
forfiles /p "%HISTORIAL%" /m catalogo_*.xlsx /d -%DIAS_HISTORIAL% /c "cmd /c del @path" >nul 2>&1
forfiles /p "%HISTORIAL%" /m pendiente_*.xlsx /d -2 /c "cmd /c del @path" >nul 2>&1
forfiles /p "%SCRIPTS%." /m cambios_*.xlsx /d -%DIAS_CAMBIOS% /c "cmd /c del @path" >nul 2>&1
forfiles /p "%LOGS%" /m sync_*.log /d -%DIAS_LOGS% /c "cmd /c del @path" >nul 2>&1

echo.
echo === Sincronizacion completada. Base nueva: %NUEVO% ===
if not "%ERROR_RESPALDO%"=="0" (
    echo ERROR: el respaldo semanal fallo. Se reintenta en la proxima corrida.
    exit /b 1
)
exit /b 0
