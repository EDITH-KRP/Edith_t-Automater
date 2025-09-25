@echo off
title ExifTool Metadata Extraction Tool
color 0a

echo Starting ExifTool Interactive Interface...
echo.

cd /d "%~dp0"

python exiftool_prompt.py

pause