import os
import platform
import subprocess
from pathlib import Path

def _get_os():
    return platform.system()

def update(server):
    if _get_os()=="Windows":
        os.system(rf'utils\update_bin.bat {server}')
    else:
        os.system(f'./utils/update_bin.sh {server}')


def makedir(server: Path):
    server.mkdir(parents=True, exist_ok=True)
    (server / 'bin').mkdir(exist_ok=True)
    (server / 'py').mkdir(exist_ok=True)
    (server / 'bin' / 'rom' / 'data' / 'missions' / 'mscmodules').mkdir(parents=True, exist_ok=True)

def runserver(server):
    if _get_os() == "Windows":
        subprocess.Popen(rf'servers\{server}\bin\server64.exe +server_dir \{server}\conf\\')
    else:
        subprocess.Popen(rf'./servers/{server}/bin/server64.exe +server_dir ./{server}/conf/')