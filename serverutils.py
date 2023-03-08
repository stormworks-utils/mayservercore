import os
import platform

def _get_os():
    return platform.platform()

def update(server):
    if _get_os()=="Windows":
        os.system(rf'utils\update_bin.bat {server}')
    else:
        os.system(f'./utils/update_bin.sh {server}')

def makedir(server):
    if not os.path.exists(f'servers/{server}/'):
        os.mkdir(f'servers/{server}/')
    if not os.path.exists(f'servers/{server}/bin'):
        os.mkdir(f'servers/{server}/bin')
    if not os.path.exists(f'servers/{server}/conf'):
        os.mkdir(f'servers/{server}/conf')

def runserver(server):
    if _get_os() == "Windows":
        os.system(rf'servers\{server}\bin\server64.exe +server_dir \servers\{server}\conf\\')
    else:
        os.system(rf'./servers/{server}/bin/server64.exe +server_dir /servers/{server}/conf/')