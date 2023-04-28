import platform
import subprocess
from pathlib import Path
from logger import Logger


def _get_os():
    return platform.system()


def update_game(path: Path, game_id: int):
    executable: str = rf'utils\steamclient\steamcmd.exe' if _get_os() == 'Windows' else 'steamcmd'
    command: list[str] = [executable, '+force_install_dir', str(path), '+login', 'anonymous', '+app_update', f'{game_id} validate', '+exit']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    # in theory, line should always be the last line of the commands output, but for whatever reason, it is not being
    # updated regularly. If it where, this would allow a much more fancy progress bar
    while line := proc.stdout.readline():
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
        subprocess.Popen(rf'servers\{server}\bin\server64.exe +server_dir \{server}\conf\\')
    else:
        subprocess.Popen(rf'./servers/{server}/bin/server64.exe +server_dir ./{server}/conf/')