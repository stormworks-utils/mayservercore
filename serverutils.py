import json
import platform
import shutil
import subprocess
from pathlib import Path
from logger import Logger
import os
import re
SERVER_MATCH=re.compile('^server(?:64)?.exe$')

def _get_os():
    return platform.system()


def update_game(path: Path, game_id: int):
    executable: str = rf'utils\steamclient\steamcmd.exe' if _get_os() == 'Windows' else 'steamcmd'
    command: list[str] = [executable, '+force_install_dir', str(path), '+login', 'anonymous', '+app_update', f'{game_id} validate', '+exit']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    # in theory, line should always be the last line of the commands output, but for whatever reason, it is not being
    # updated regularly. If it where, this would allow a much more fancy progress bar
    while line := proc.stdout.read():
        ...
def update(server: Path):
    log = Logger("Server updater")
    server = server.absolute() / 'bin'
    log.info('Updating Stormworks')
    update_game(server, 1247090)
    if _get_os() == 'Linux':
        proton = server / 'proton'
        log.info('Updating Proton Experimental')
        update_game(proton, 1493710)


def makedir(server: Path):
    server.mkdir(parents=True, exist_ok=True)
    (server / 'bin').mkdir(exist_ok=True)
    (server / 'py').mkdir(exist_ok=True)
    (server / 'conf').mkdir(exist_ok=True)
    (server / 'bin' / 'rom' / 'data' / 'missions' / 'mscmodules').mkdir(parents=True, exist_ok=True)

def runserver(server):
    if _get_os() == "Windows":
        subprocess.Popen(f'servers\\{server}\\bin\\server64.exe +server_dir ..\\..\\{server}\\conf\\',cwd=f'servers\\{server}\\bin\\')
    else:
        subprocess.Popen(rf'./servers/{server}/bin/server64.exe +server_dir ../../{server}/conf/',cwd=f'servers/{server}/bin/')

def getServerPID(server):
    if _get_os() == "Windows":
        os.system('WMIC path win32_process get Caption,Processid,Commandline>temp') #get processes with their args and pids
        with open('temp') as f:
            procs=f.read().replace(chr(0),'').split('\n') #load the results
        os.remove('temp') #remove temp file
        procs=[[j for j in i.split(' ') if j!=''] for i in procs if i!=''] #remove padding and split into args
        procs=[i for i in procs if len(i)==5] #remove all processes without args
        procs=[i for i in procs if SERVER_MATCH.match(i[0])] #find servers

        for i in procs:
            if server in i[3]:
                return i[-1]

def killserver(server):
    pid=getServerPID(server)
    if pid:
        if _get_os() == "Windows":
            subprocess.Popen(f'taskkill /PID {pid} /F')

def isServerRunning(server):
    return getServerPID(server) or False

def clearPersistent(server,module:str):
    server = Path('servers') / server
    shutil.rmtree(server / 'py' / 'persistent' / module.replace(' ','_'))
    (server / 'py' / 'persistent' / module.replace(' ', '_')).mkdir()

def getPersistent(server,module:str):
    server = Path('servers') / server
    persistents=[]
    for i in os.walk((server / 'py' / 'persistent' / module.replace(' ','_'))):
        dir=i[0]
        files=i[2]
        for j in files:
            persistents.append(dir+'\\'+j)
    return persistents

def getModules(server):
    server=Path('servers')/server
    with open(server/'conf'/'modules.json') as modfile:
        return json.load(modfile)
