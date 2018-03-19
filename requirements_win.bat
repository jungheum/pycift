@echo off
setlocal enabledelayedexpansion

::-----------------------------------------------------------------------------------------------
goto comment
    Pre-requirements for pycift
:comment
::-----------------------------------------------------------------------------------------------

:: Install Google Chrome
echo ===================================================
echo Your machine should have Google Chrome
echo ===================================================


:: Install ChromeDriver
echo ===================================================
echo Downloading ChromeDriver ...
echo ===================================================
set url=http://chromedriver.storage.googleapis.com/LATEST_RELEASE
set filename=CD_LATEST_RELEASE
PowerShell -Command "(New-Object Net.WebClient).DownloadFile('%url%', '%filename%')"
set /p LATEST=<%filename%
if exist %filename% (del /a %filename%)

echo The latest version of ChromeDrive is %LATEST%
set url=http://chromedriver.storage.googleapis.com/%LATEST%/chromedriver_win32.zip
set filename=chromedriver_win32.zip
PowerShell -Command "(New-Object Net.WebClient).DownloadFile('%url%', '%filename%')"

echo Decompressing the downloaded file (%filename%)


echo Removing the downloaded file (%filename%)



:: Install dependencies
echo ===================================================
echo Installing Selenium and python dependencies ...
echo ===================================================
::sudo apt-get install python3-pip
::pip3 install --upgrade pip
::pip3 install pyvirtualdisplay selenium
::pip3 install python-dateutil peewee requests construct
