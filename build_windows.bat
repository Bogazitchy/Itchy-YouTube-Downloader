@echo off
title ITCHY Video Downloader v2.0 - Build

echo.
echo  ITCHY YOUTUBE DOWNLOADER v2.0 - Windows Build
echo  ================================================
echo.

echo [1/4] Paketler kuruluyor...
pip install yt-dlp customtkinter pillow pyinstaller pystray winotify pypresence --quiet
if errorlevel 1 (
    echo HATA: pip install basarisiz!
    pause
    exit /b 1
)
echo Paketler OK

echo.
echo [2/4] ffmpeg kontrol ediliyor...
if not exist "ffmpeg.exe" (
    echo UYARI: ffmpeg.exe bulunamadi!
    echo https://github.com/BtbN/ffmpeg-builds/releases/latest
    pause
    exit /b 1
)
echo ffmpeg OK

echo.
echo [3/4] EXE olusturuluyor...
pyinstaller --onedir --windowed --name "ItchyDownloader" --icon="logo.ico" --add-data "logo.ico;." --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --hidden-import "customtkinter" --hidden-import "PIL" --hidden-import "yt_dlp" --hidden-import "pystray" --hidden-import "winsound" --hidden-import "winotify" --hidden-import "pypresence" --collect-all "customtkinter" --collect-all "yt_dlp" --collect-all "pystray" --collect-all "winotify" --noconfirm itchy.py
if errorlevel 1 (
    echo HATA: PyInstaller basarisiz!
    pause
    exit /b 1
)

echo.
echo [4/4] Tamamlandi!
echo.
echo EXE: dist\ItchyDownloader\ItchyDownloader.exe
echo Inno Setup ile setup.iss derleyerek kurulum sihirbazi olusturabilirsiniz.
echo.
pause
