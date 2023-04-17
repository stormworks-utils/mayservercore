import os
import platform
import subprocess

def _get_os():
    return platform.system()

def update(server):
    if _get_os()=="Windows":
        os.system(rf'utils\update_bin.bat {server}')
    else:
        os.system(f'./utils/update_bin.sh {server}')

def makedir(server):
    if not os.path.exists(f'{server}/'):
        os.mkdir(f'{server}/')
    if not os.path.exists(f'{server}/bin'):
        os.mkdir(f'{server}/bin')
    if not os.path.exists(f'{server}/py'):
        os.mkdir(f'{server}/py')
    if not os.path.exists(f'{server}/conf'):
        os.mkdir(f'{server}/conf')
    if not os.path.exists(f'{server}/bin/rom/data/missions/mscmodules/'):
        os.mkdir(f'{server}/bin/rom/data/missions/mscmodules/')

def runserver(server):
    if _get_os() == "Windows":
        subprocess.Popen(rf'servers\{server}\bin\server64.exe +server_dir \{server}\conf\\')
    else:
        subprocess.Popen(rf'./servers/{server}/bin/server64.exe +server_dir ./{server}/conf/')