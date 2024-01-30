@echo off
REM Set the path to the TranscriptionApp directory in the user's Documents folder
set DEST_DIR=%USERPROFILE%\Documents\TranscriptionApp

REM Activate the virtual environment
call "%DEST_DIR%\TranscriptionApp\Scripts\activate.bat"

REM Run main.py
python "%DEST_DIR%\main.py"

REM Optional: Deactivate the virtual environment after running the script
REM call deactivate

echo Execution completed!
pause
