import os
import platform
import subprocess

def _get_os():
    return platform.system()

def update(server):
    if _get_os()=="Windows":
        subprocess.Popen(rf'utils\update_bin.bat {server}')
    else:
        subprocess.Popen(f'./utils/update_bin.sh {server}')

def makedir(server):
    if not os.path.exists(f'servers/{server}/'):
        os.mkdir(f'servers/{server}/')
    if not os.path.exists(f'servers/{server}/bin'):
        os.mkdir(f'servers/{server}/bin')
    if not os.path.exists(f'servers/{server}/conf'):
        os.mkdir(f'servers/{server}/conf')

def runserver(server):
    if _get_os() == "Windows":
        subprocess.Popen(rf'servers\{server}\bin\server64.exe +server_dir \servers\{server}\conf\\')
    else:
        subprocess.Popen(rf'./servers/{server}/bin/server64.exe +server_dir /servers/{server}/conf/')