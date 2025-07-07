@echo off
REM Script de configuration automatique pour School Timetable Generator
REM Ce script lance setup.py avec Python

echo.
echo ============================================================
echo   SCHOOL TIMETABLE GENERATOR - CONFIGURATION
echo ============================================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python 3.11+ depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Exécuter le script de configuration
echo Lancement du script de configuration...
echo.
python "%~dp0setup.py"

REM Vérifier le résultat
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: La configuration a échoué
    pause
    exit /b 1
)

echo.
echo Configuration terminée avec succès!
echo.
pause 