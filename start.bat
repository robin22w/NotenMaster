@echo off
setlocal enabledelayedexpansion

title NotenMaster
REM Aktivieren der Conda-Umgebung  !Add PATH: C:\Users\robin\Anaconda3\Scripts and run "conda init" once
call conda activate S2_KI

REM Aufrufen des Python-Skripts und Übergeben der Datei als Argument
python src/main_gui.py "%~1"

REM Deaktivieren Sie die Conda-Umgebung nach Abschluss des Skripts
call conda deactivate

REM Warten, um das Ergebnis anzuzeigen (kann nach Bedarf angepasst werden)
exit