@echo off
set server=%1
utils\steamclient\steamcmd.exe +force_install_dir "%server%\" +login anonymous +app_update 1247090 validate +exit