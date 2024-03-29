# MSC server_config and script.lua generator
import os
import traceback
import zipfile
import serverutils
from logger import Logger
import shutil
import json
import localinfo
import error_handler
import modules as module_gen
from pathlib import Path
import xml.etree.ElementTree as ET
import handlers
import pymodulevalidator as mdvalid

callback_args = {"onTick": ["game_ticks"], "onCreate": ['is_world_create'], 'onDestroy': [],
                 "onCustomCommand": ['full_message', 'user_peer_id', 'is_admin', 'is_auth', 'command'],
                 'onChatMessage': ['peer_id', 'sender_name', 'message'],
                 'onPlayerJoin': ['steam_id', 'name', 'peer_id', 'is_admin', 'is_auth'],
                 'onPlayerSit': ['peer_id', 'vehicle_id', 'seat_name'],
                 'onPlayerUnsit': ['peer_id', 'vehicle_id', 'seat_name'],
                 'onCharacterSit': ['object_id', 'vehicle_id', 'seat_name'],
                 'onCharacterUnsit': ['object_id', 'vehicle_id', 'seat_name'],
                 'onCharacterPickup': ['object_id_actor', 'object_id_target'],
                 'onEquipmentPickup': ['object_id_actor', 'object_id_target', 'EQUIPMENT_ID'],
                 'onEquipmentDrop': ['object_id_actor', 'object_id_target', 'EQUIPMENT_ID'],
                 'onCreaturePickup': ['object_id_actor', 'object_id_target', 'CREATURE_TYPE'],
                 'onPlayerRespawn': ['peer_id'],
                 'onPlayerLeave': ['steam_id', 'name', 'peer_id', 'is_admin', 'is_auth'],
                 'onToggleMap': ['peer_id', 'is_open'],
                 'onPlayerDie': ['steam_id', 'name', 'peer_id', 'is_admin', 'is_auth'],
                 'onVehicleSpawn': ['vehicle_id', 'peer_id', 'x', 'y', 'z', 'cost'],
                 'onVehicleDespawn': ['vehicle_id', 'peer_id'],
                 'onVehicleLoad': ['vehicle_id'],
                 'onVehicleUnload': ['vehicle_id'],
                 'onVehicleTeleport': ['vehicle_id', 'peer_id', 'x', 'y', 'z'],
                 'onObjectLoad': ['object_id'],
                 'onObjectUnload': ['object_id'],
                 'onButtonPress': ['vehicle_id', 'peer_id', 'button_name', 'is_pressed'],
                 'onSpawnAddonComponent': ['object_id/vehicle_id', 'component_name', 'TYPE_STRING', 'addon_index'],
                 'onVehicleDamaged': ['vehicle_id', 'damage_amount', 'voxel_x', 'voxel_y', 'voxel_z', 'body_index'],
                 'onFireExtinguished': ['fire_x', 'fire_y', 'fire_z'],
                 'onForestFireSpawned': ['fire_objective_id', 'fire_x', 'fire_y', 'fire_z'],
                 'onForestFireExtinguished': ['fire_objective_id', 'fire_x', 'fire_y', 'fire_z'],
                 'onTornado': ['transform'],
                 'onMeteor': ['transform', 'magnitude'],
                 'onTsunami': ['transform', 'magnitude'],
                 'onWhirlpool': ['transform', 'magnitude'],
                 'onVolcano': ['transform']}


def make_config(path: Path, extract=True) -> tuple[Path, Path]:
    log = Logger("Configuration")
    profile_path: Path = path
    if extract:
        profile_path = Path(path.stem)
    log.info("Starting stage 1 configuration")
    if extract:
        log.info("Extracting MSC profile")
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(profile_path)
        except:
            error_handler.handleFatal(log, "Unable to extract MSC profile")
    else:
        log.info("Skipping extraction")
    log.info("Loading configuration")
    profile_path = profile_path / 'profile'

    with open(profile_path / 'settings.json') as file:
        try:
            settings = json.load(file)
        except json.JSONDecodeError:
            error_handler.handleFatal(log, "Invalid profile.")
    settings_version = float(settings['properties']['version'])
    if settings_version < localinfo.version():
        log.warn(f"Profile version out of date! (msc {localinfo.version()}, prof {settings_version})")
    if settings_version > localinfo.version():
        log.warn(f"MSC version out of date! (msc {localinfo.version()}, prof {settings_version})")

    log.info("Building server_config.xml")
    xml_config: ET.Element = ET.Element('server_data', attrib={'port': '25564'})

    for k, v in settings["settings_server"].items():
        xml_config.attrib[k] = str(v)
    admin_config: ET.SubElement = ET.SubElement(xml_config, 'admins')
    for i in settings['settings_msc']['admins']:
        ET.SubElement(admin_config, 'id', attrib={'value': i})
    ET.SubElement(xml_config, 'authorized')
    ET.SubElement(xml_config, 'blacklist')
    ET.SubElement(xml_config, 'whitelist')
    playlists_config: ET.SubElement = ET.SubElement(xml_config, 'playlists')
    ET.SubElement(playlists_config, 'path', attrib={'path': 'rom/data/missions/mscmodules'})
    for k, v in settings["default_addons"].items():
        if v:
            if "dlc" in k:
                ET.SubElement(playlists_config, 'path', attrib={'path': f'rom/data/missions/{k}'})
            else:
                ET.SubElement(playlists_config, 'path', attrib={'path': f'rom/data/missions/default_{k}'})
    for k in settings["extra_addons"]:
        ET.SubElement(playlists_config, 'path', attrib={'path': f'rom/data/missions/{k}'})

    log.info("server_config.xml generated")
    server_profile: Path = Path('servers') / settings['properties']['server_shorthand']
    serverutils.makedir(server_profile)
    tree: ET.ElementTree = ET.ElementTree(xml_config)
    ET.indent(tree, '    ')
    tree.write(server_profile / 'conf' / 'server_config.xml', xml_declaration=True, encoding='UTF-8')
    log.info("Config generation complete")
    return server_profile, profile_path

def load_extras(profile: Path,log: Logger):
    log.info('Loading extra addons')
    with open(profile / 'settings.json') as file:
        try:
            settings = json.load(file)
        except json.JSONDecodeError:
            error_handler.handleFatal(log, "Invalid profile.")
    path=Path('servers')/settings['properties']['server_shorthand']
    addons=settings['extra_addons']
    for i in addons:
        log.info(f'Copying {i}')
        if (profile/i).exists():
            if (path/'bin'/'rom'/'data'/'missions'/i).exists():
                shutil.rmtree(path/'bin'/'rom'/'data'/'missions'/i)
            shutil.copytree(profile/i,path/'bin'/'rom'/'data'/'missions'/i)
        else:
            error_handler.handleSkippable(log,f'Addon "{i}" cannot be found')

def make_modules(path: Path):
    log = Logger("Module generator")
    log.info("Starting stage 2 configuration")
    log.info("Loading modules configuration")
    with open(path / 'settings.json') as file:
        try:
            settings = json.load(file)['settings_msc']['modules']
        except json.JSONDecodeError:
            error_handler.handleFatal(log, "Invalid profile.")
    modules = []
    generated_modules = []
    for i in settings.keys():
        if settings[i]['enabled']:
            modules.append(i)
    modulealias=module_gen.discover_modules(log)
    for module in modules:
        generated_modules.append(module_gen.generate(module, modulealias[module], settings[module], modules))
    return generated_modules


def generate(path: Path, extract=True, http_port=1000, update=False, write_full_traceback=False):
    log = Logger("Addon compiler")
    try:
        log.info("Started module compiler")
        compiled_modules = ""
        server_path, profile_path = make_config(path, extract)
        if update or not (server_path / 'bin' / 'server.exe').exists():
            if not update:
                log.warn("Server not found, forcing update")
            serverutils.update(server_path)
        modules = make_modules(profile_path)
        to_handle = {}
        callbacks = {}
        functions = {}
        modulealias_reverse = module_gen.discover_modules(log)
        modulealias = {modulealias_reverse[i]: i for i in modulealias_reverse.keys()}
        log.info("Compiling modules")
        moduleprefixes={}
        for module in modules:
            code, calls, handles, c_func, name, desc, prefix, file_name, msettings, pylibs = module
            moduleprefixes.update({prefix:name})
            if name == '':
                continue
            compiled_modules += f'''--{name}: {desc}
    
    {code.strip()}
    
    '''
            for oname in calls.keys():
                names = calls[oname]
                for name_t in names:
                    if oname in callbacks.keys():
                        callbacks[oname].append(name)
                    else:
                        callbacks.update({oname: [name_t]})
            for oname in handles.keys():
                names = handles[oname]
                for name_t in names:
                    if oname in to_handle.keys():
                        to_handle[oname].append(name_t)
                    else:
                        to_handle.update({oname: [name_t]})
            for oname in c_func.keys():
                names = c_func[oname]
                for name_t in names:
                    if oname in functions.keys():
                        functions[oname].append(name_t)
                    else:
                        functions.update({oname: [name_t]})
        compiled_modules = compiled_modules.strip()
        callback_defs = "\n\n--callback setup\n\n"

        for callback in callbacks.keys():
            arguments = callback_args[callback]
            calls = callbacks[callback]
            callback_defs += handlers.generate_handler('generic_callback',{'CALLBACK_NAME':callback,'PARAMETERS':','.join(arguments)},[{'CALLBACK':name} for name in calls], repl_head=True)

        callback_defs = callback_defs
        script = ''
        script += compiled_modules
        script += callback_defs
        if 'httpGet' in functions.keys():
            http = handlers.generate_handler('httpget', {'PORT': http_port}, [
                {'PREFIX': x.split('_')[1], 'NAME': moduleprefixes[x.split('_')[1]].replace(' ','_'), 'PREFIXED': x} for x in
                functions['httpGet']])
            script += http
        if 'httpReply' in to_handle.keys():
            http = handlers.generate_handler('httpreply', {'PORT': http_port}, [
                {'PREFIX': x.split('_')[1].replace(' ','_'), 'NAME': moduleprefixes[x.split('_')[1]].replace(' ','_'), 'PREFIXED': x.replace(' ','_')} for x in
                to_handle['httpReply']])
            script += http
        load_extras(profile_path, log)
        log.info("Clearing existing python extensions")
        (server_path / 'py' / 'persistent').mkdir(parents=True, exist_ok=True)
        shutil.move(f'{server_path}/py/persistent/',f'{server_path}/persistent/')
        shutil.rmtree(f'{server_path}/py/')
        try:
            serverutils.makedir(server_path)
        except Exception:
            log.warn("Unable to complete directory creation")
        shutil.move( f'{server_path}/persistent/',f'{server_path}/py/')
        with open(f'{server_path}/bin/rom/data/missions/mscmodules/script.lua', 'w') as x:
            x.write(script)
        log.info("Discovering module python files")
        with open(profile_path / 'settings.json') as file:
            try:
                settings = json.load(file)['settings_msc']['modules']
            except json.JSO_DecodeError:
                error_handler.handleFatal(log, "Invalid profile.")
        module_names = []
        for i in settings.keys():
            if settings[i]['enabled']:
                module_names.append(i)
        extensions = []
        extended_modules = []
        for module in modules:
            code, calls, handles, c_func, name, desc, prefix, file_name, msettings, pylibs = module
            has_ext = (file_name / Path('module.py')).exists()
            if has_ext:
                extensions.append(prefix)
                log.info(f"Found extension for \"{name}\"")
                files = mdvalid.discover_extra_files(file_name)
                code = mdvalid.get_code(file_name, files)
                functions = []
                imports = []
                ext_has_handler = False
                for i in code:
                    mods, funcs, has_handler = mdvalid.get_libs_and_functions(i)
                    functions += funcs
                    imports += mods
                    ext_has_handler = ext_has_handler or has_handler
                if not ext_has_handler:
                    log.warn(f'Python extension for module "{name}" does not contain a valid handler function.')
                else:
                    extended_modules.append(name.replace(' ','_'))
                if len(functions) > 0:
                    log.warn(f"Module \"{name}\" uses {len(functions)} possibly malicious functions")
                    log.warn("(" + ", ".join(functions) + ")")
                if len(imports) > 0:
                    log.warn(f"Module \"{name}\" uses {len(imports)} external libraries")
                    log.warn("(" + ", ".join(imports) + ")")
                log.info(f"Installing extension(s) for \"{name}\"")
                for file in files:
                    log.info(f"Copying {file}")
                    shutil.copyfile(f'{file_name}/{file}', f'{server_path}/py/{name.replace(" ","_")}_{file}')
        log.info('Building HTTP server')
        svr = handlers.generate_handler('flask_handler', {'MODULE_LIST': str(extended_modules), 'PORT': http_port}, [],
                                        repl_head=True)
        with open(f'{server_path}/py/server.py', 'w') as file:
            file.write(svr)

        log.info('Writing python configuration')
        needed_pylibs=[]
        for module in modules:
            code, calls, handles, c_func, name, desc, prefix, file_name, msettings, pylibs = module
            with open(f'{server_path}/py/{name.replace(" ","_")}_conf.json','w') as f:
                json.dump(settings[name],f)
            #name,msettings
            for i in pylibs:
                needed_pylibs.append(i)

        needed_pylibs=list(set(needed_pylibs))

        log.info('Creating persistent data directories')
        loadedmods=[]
        for i in modules:
            name=i[4]
            (server_path / 'py' / 'persistent' / name.replace(' ', '_')).mkdir(parents=True, exist_ok=True)
            loadedmods.append(name)
        with open(server_path/'conf'/'modules.json','w') as modfile:
            json.dump(loadedmods,modfile)
        for i in os.scandir((server_path / 'py' / 'persistent')):
            if i.is_file():
                os.remove(i)
            else:
                if i.name not in [j.replace(' ','_') for j in module_names]:
                    shutil.rmtree(i)

        log.info('Creating server virtualenv')
        server_name=server_path.name
        serverutils.makevenv(server_name)

        log.info('Installing python modules')
        for i in needed_pylibs:
            log.info(f'Installing {i}')
            serverutils.pipInstall(server_name,i)

        log.info('Server generation complete')
        return str(server_path).split('/')
    except Exception as exc:
        if write_full_traceback:
            traceback.print_exc()
        error_handler.handleFatal(log, f"Unhandled generator failure ({exc}).")