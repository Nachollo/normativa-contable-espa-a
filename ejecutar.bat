@echo off
chcp 65001 > nul
title Sistema de Auditoría
color 0E

echo =====================================================
echo        SISTEMA DE AUDITORIA - MENU PRINCIPAL
echo =====================================================
echo.

:: Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [AVISO] Ejecuta primero instalar.bat
    pause
    exit /b 1
)

:menu
echo.
echo Seleccione una opción:
echo.
echo [1] Generar papeles de trabajo (auditoría completa)
echo [2] Generar paquete final con informe
echo [3] Cargar contabilidad desde Excel
echo [4] Ver ayuda de comandos
echo [5] Crear ejecutable (.exe)
echo [6] Salir
echo.
set /p opcion="Opción: "

if "%opcion%"=="1" goto generar_papeles
if "%opcion%"=="2" goto generar_paquete
if "%opcion%"=="3" goto cargar_contabilidad
if "%opcion%"=="4" goto ayuda
if "%opcion%"=="5" goto crear_exe
if "%opcion%"=="6" goto salir

echo Opción no válida
goto menu

:generar_papeles
echo.
set /p anio="Año del ejercicio (ej: 2023): "
set /p tipo="Tipo de entidad (mercantil/cooperativa/fundacion): "
echo.
echo Generando papeles de trabajo...
echo (Presione Ctrl+C para detener en cualquier momento)
echo.
python main_audit.py --generate-audit-papers %anio% --entity-type %tipo%
echo.
echo Papeles generados en la carpeta "papeles_trabajo"
pause
goto menu

:generar_paquete
echo.
set /p anio="Año del ejercicio (ej: 2023): "
set /p nombre="Nombre del cliente: "
set /p cif="CIF del cliente: "
echo.
echo Generando paquete final...
echo (Presione Ctrl+C para detener en cualquier momento)
echo.
python main_audit.py --generate-final-package %anio% --client-name "%nombre%" --client-cif "%cif%"
echo.
echo Paquete generado en la carpeta "papeles_trabajo"
pause
goto menu

:cargar_contabilidad
echo.
echo Coloca tus archivos Excel en la carpeta "input_documents"
echo y luego presiona Enter para cargarlos.
pause
python main_audit.py --load-accounting
echo.
echo Contabilidad cargada
pause
goto menu

:ayuda
echo.
python main_audit.py --help
pause
goto menu

:crear_exe
echo.
echo Instalando PyInstaller...
pip install pyinstaller
echo.
echo Creando ejecutable (esto puede tardar varios minutos)...
pyinstaller --onefile --name SistemaAuditoria main_audit.py
echo.
echo Ejecutable creado en: dist\SistemaAuditoria.exe
pause
goto menu

:salir
echo.
echo Hasta luego!
exit /b 0
