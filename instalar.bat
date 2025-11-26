@echo off
chcp 65001 > nul
title Sistema de Auditoría - Instalador
color 0A

echo =====================================================
echo     SISTEMA DE AUDITORIA - INSTALADOR AUTOMATICO
echo =====================================================
echo.

:: Verificar si Python está instalado
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no está instalado.
    echo.
    echo Por favor descarga e instala Python desde:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalación marca la opción
    echo "Add Python to PATH"
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

echo [OK] Python encontrado
python --version
echo.

:: Crear entorno virtual
echo Creando entorno virtual...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudo crear el entorno virtual
    pause
    exit /b 1
)
echo [OK] Entorno virtual creado
echo.

:: Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activado
echo.

:: Instalar dependencias
echo Instalando dependencias (esto puede tardar unos minutos)...
pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

:: Crear carpetas necesarias
if not exist "input_documents" mkdir input_documents
if not exist "papeles_trabajo" mkdir papeles_trabajo
if not exist "logs" mkdir logs
echo [OK] Carpetas creadas
echo.

echo =====================================================
echo     INSTALACION COMPLETADA EXITOSAMENTE
echo =====================================================
echo.
echo Para usar el sistema:
echo.
echo 1. Coloca tus archivos Excel en la carpeta "input_documents"
echo.
echo 2. Ejecuta "ejecutar.bat" o usa los comandos:
echo    python main_audit.py --generate-audit-papers 2023 --entity-type mercantil
echo    python main_audit.py --generate-final-package 2023 --client-name "Empresa SA" --client-cif "A12345678"
echo.
echo 3. Los papeles de trabajo se generarán en "papeles_trabajo"
echo.
echo Presiona Ctrl+C en cualquier momento para detener el proceso (botón de emergencia)
echo.
pause
