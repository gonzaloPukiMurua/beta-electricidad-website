@echo off
chcp 65001 >nul
title Sincronizador ERP → Web

:: ============================================================
::  CONFIGURACIÓN — editá estas rutas si cambian
:: ============================================================
set DATOS=C:\a\datos
set CARPETA_SCRIPTS=%~dp0
set CARPETA_HISTORIAL=%CARPETA_SCRIPTS%historial

:: ============================================================
::  NO EDITAR A PARTIR DE AQUÍ
:: ============================================================
echo.
echo ╔══════════════════════════════════════════╗
echo ║     Sincronizador ERP ^> Web             ║
echo ║     %date%  %time:~0,5%                  ║
echo ╚══════════════════════════════════════════╝
echo.

:: Crear carpeta historial si no existe
if not exist "%CARPETA_HISTORIAL%" mkdir "%CARPETA_HISTORIAL%"

:: Buscar el catálogo anterior (el más reciente en historial)
set ANTERIOR=
for /f "delims=" %%f in ('dir /b /o-d "%CARPETA_HISTORIAL%\catalogo_*.xlsx" 2^>nul') do (
    if not defined ANTERIOR set ANTERIOR=%CARPETA_HISTORIAL%\%%f
)

:: Nombre del nuevo catálogo con fecha y hora
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set FECHA=%%c%%b%%a
for /f "tokens=1-2 delims=:" %%a in ("%time:~0,5%") do set HORA=%%a%%b
set HORA=%HORA: =0%
set NUEVO_CATALOGO=%CARPETA_HISTORIAL%\catalogo_%FECHA%_%HORA%.xlsx
set CAMBIOS=%CARPETA_SCRIPTS%cambios_%FECHA%_%HORA%.xlsx

:: ── PASO 1: Exportar catálogo actual ──────────────────────
echo [1/3] Exportando catalogo del ERP...
python "%CARPETA_SCRIPTS%exportar_catalogo.py" --datos "%DATOS%" --salida "%NUEVO_CATALOGO%"
if errorlevel 1 (
    echo.
    echo  ERROR en la exportacion. Verificá que la carpeta datos sea accesible.
    pause & exit /b 1
)

:: ── PASO 2: Detectar cambios ──────────────────────────────
echo.
if defined ANTERIOR (
    echo [2/3] Detectando cambios respecto a: %ANTERIOR%
    python "%CARPETA_SCRIPTS%detectar_cambios.py" --datos "%DATOS%" --anterior "%ANTERIOR%" --salida "%CAMBIOS%"
) else (
    echo [2/3] Primera ejecucion — se usara el catalogo completo como base.
    set CAMBIOS=%NUEVO_CATALOGO%
)
if errorlevel 1 (
    echo.
    echo  ERROR al detectar cambios.
    pause & exit /b 1
)

:: ── PASO 3: Sincronizar con Supabase ─────────────────────
echo.
echo [3/3] Sincronizando con la base de datos web...
python "%CARPETA_SCRIPTS%sincronizar_db.py" --cambios "%CAMBIOS%"
if errorlevel 1 (
    echo.
    echo  ERROR en la sincronizacion con Supabase.
    echo  Verificá el archivo .env y la conexion a internet.
    pause & exit /b 1
)

:: ── RESUMEN ───────────────────────────────────────────────
echo.
echo ╔══════════════════════════════════════════╗
echo ║   Sincronizacion completada              ║
echo ╚══════════════════════════════════════════╝
echo.
echo  Catalogo guardado en historial:
echo  %NUEVO_CATALOGO%
if exist "%CAMBIOS%" (
    echo  Archivo de cambios:
    echo  %CAMBIOS%
)
echo.
timeout /t 5
