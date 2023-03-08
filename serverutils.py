import os

def update(server):
    os.system(rf'utils\update_bin.bat {server}')

def makedir(server):
    if not os.path.exists(f'servers/{server}/'):
        os.mkdir(f'servers/{server}/')
    if not os.path.exists(f'servers/{server}/bin'):
        os.mkdir(f'servers/{server}/bin')
    if not os.path.exists(f'servers/{server}/conf'):
        os.mkdir(f'servers/{server}/conf')

def runserver(server):
    os.system(rf'servers\{server}\bin\server64.exe +server_dir \servers\{server}\conf\\')