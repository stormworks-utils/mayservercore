# MSC server_config and script.lua generator

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


def make_config(path: Path, extract=True):
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
    if not server_profile.exists():
        server_profile.mkdir(parents=True)
    tree: ET.ElementTree = ET.ElementTree(xml_config)
    ET.indent(tree, '    ')
    yield server_profile
    tree.write(server_profile / Path('conf') / 'server_config.xml', xml_declaration=True, encoding='UTF-8')
    log.info("Config generation complete")
    yield profile_path


def make_module(path: Path):
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
    for module in modules:
        generated_modules.append(module_gen.generate(module, settings[module], modules))
    return generated_modules


def generate(path: Path, extract=True, http_port=1000, update=False):
    log = Logger("Addon compiler")
    try:
        log.info("Started module compiler")
        first_run=localinfo.first_run()
        if first_run and not update:
            log.warn("First startup detected, overriding update flag")
            update=True
            localinfo.disable_first_run()
        compiled_modules = ""
        final=False
        for i in make_config(path, extract):
            if final:
                profile_path=i
            else:
                server_path=i
                try:
                    serverutils.makedir(server_path)
                except Exception:
                    log.warn("Unable to complete directory creation")
                if update:
                    serverutils.update(server_path)
                final = True
        modules = make_module(profile_path)
        to_handle = {}
        callbacks = {}
        functions = {}

        log.info("Compiling modules")
        for module in modules:
            code, calls, handles, c_func, name, desc = module
            compiled_modules += f'''--{name}: {desc}
    
    {code.strip()}
    
    '''
            for oname in calls.keys():
                names = calls[oname]
                for name in names:
                    if oname in callbacks.keys():
                        callbacks[oname].append(name)
                    else:
                        callbacks.update({oname: [name]})
            for oname in handles.keys():
                names = handles[oname]
                for name in names:
                    if oname in to_handle.keys():
                        to_handle[oname].append(name)
                    else:
                        to_handle.update({oname: [name]})
            for oname in c_func.keys():
                names = c_func[oname]
                for name in names:
                    if oname in functions.keys():
                        functions[oname].append(name)
                    else:
                        functions.update({oname: [name]})
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
            http = handlers.generate_handler('httpget', {'PORT':http_port}, [{'PREFIX':x.split('_')[1], 'NAME':x} for x in functions['httpGet']])
            script += http
        if 'httpReply' in to_handle.keys():
            http = handlers.generate_handler('httpreply', {'PORT':http_port}, [{'PREFIX':x.split('_')[1], 'NAME':x} for x in to_handle['httpReply']])
            script += http
        try:
            serverutils.makedir(server_path)
        except Exception:
            log.warn("Unable to complete directory creation")
        with open(f'{server_path}/bin/rom/data/missions/mscmodules/script.lua', 'w') as x:
            x.write(script)
        log.info("Discovering module python files")

        with open(profile_path / 'settings.json') as file:
            try:
                settings = json.load(file)['settings_msc']['modules']
            except json.JSONDecodeError:
                error_handler.handleFatal(log, "Invalid profile.")
        modules = []
        for i in settings.keys():
            if settings[i]['enabled']:
                modules.append(i)
        exts={}

        for module in modules:
            has_ext=(Path('modules')/module/Path('module.py')).exists()
            if has_ext:
                log.info(f"Found extension for \"{module}\"")
                files=mdvalid.discover_extra_files(module)
                code=mdvalid.get_code(module,files)
                functions=[]
                imports=[]
                ext_has_handler=False
                for i in code:
                    mods, funcs, has_handler = mdvalid.get_libs_and_functions(i)
                    functions+=funcs
                    imports+=mods
                    ext_has_handler=ext_has_handler or has_handler
                if not ext_has_handler:
                    log.warn(f'Python extension for module "{module}" does not contain an MSC data handler.')
                if len(functions)>0:
                    log.warn(f"Module \"{module}\" uses {len(functions)} possibly malicious functions")
                    log.warn("("+", ".join(functions)+")")
                if len(imports)>0:
                    log.warn(f"Module \"{module}\" uses {len(imports)} external libraries")
                    log.warn("("+", ".join(imports)+")")
                log.info(f"Installing extension(s) for \"{module}\"")
                for file in files:
                    log.info(f"    Copying {file}...")
                    shutil.copyfile(f'modules/{module}/{file}', f'{server_path}/py/{module}_{file}')
        f'{server_path}/py/app.py'
        return str(server_path).split('/')
    except Exception as exc:
        error_handler.handleFatal(log, f"Unhandled generator failure ({exc}).")