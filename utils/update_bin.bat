@echo off
set server=utils\steamclient\steamcmd.exe +force_install_dir %server% +login anonymous +app_update 1247090 validate +exit