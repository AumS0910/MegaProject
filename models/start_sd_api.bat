@echo off
echo Starting Stable Diffusion WebUI with API enabled...

:: Replace this path with your actual Stable Diffusion installation path
cd /d "D:\MegaProject\stable-diffusion-webui"

:: Start with API enabled
webui.bat --api

pause
