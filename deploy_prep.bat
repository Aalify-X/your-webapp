@echo off
echo Preparing for deployment...

REM Clean up Python cache files
echo Removing Python cache files...
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"

REM Remove .pyc files
echo Removing .pyc files...
del /s /q *.pyc

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

REM Install backend requirements
echo Installing backend requirements...
cd backend
pip install -r requirements.txt
cd ..

REM Prepare frontend
echo Preparing frontend...
cd frontend
npm install
cd ..

REM Git operations
echo Preparing Git repository...
git add .
git commit -m "Deployment preparation: Clean environment and update dependencies"
git push origin main

echo Deployment preparation complete!