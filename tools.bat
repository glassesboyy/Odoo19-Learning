@echo off
if "%1"=="activate" (
    call .\venv\Scripts\activate
) else if "%1"=="deactivate" (
    call .\venv\Scripts\deactivate
) else (
    echo Gunakan:
    echo tools activate
    echo tools deactivate
)