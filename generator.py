# MSC server_config and script.lua generator

import zipfile
from logger import Logger
import sys
import json
import localinfo
import error_handler
import modules as module_gen
from pathlib import Path
import xml.etree.ElementTree as ET
import httpgen

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
    log = Logger("Configuration file generator")
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
    tree.write(server_profile / 'server_config.xml', xml_declaration=True, encoding='UTF-8')
    log.info("Config generation complete")
    return profile_path


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


def generate(path: Path, extract=True, http_port=1000):
    log = Logger("Addon compiler")
    compiled_modules = ""
    profile_path = make_config(path, extract)
    modules = make_module(profile_path)
    print(modules)
    to_handle = {}
    callbacks = {}
    functions = {}
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
        argument_string = ', '.join(arguments)
        calls = callbacks[callback]
        callback_defs += f'function {callback}({argument_string})\n'
        for call in calls:
            callback_defs += f'    {call}({argument_string})\n'
        callback_defs += 'end\n\n'
    callback_defs = callback_defs
    script = ''
    script += compiled_modules
    script += callback_defs
    if 'httpGet' in functions.keys():
        http = httpgen.generate_http_calls(functions['httpGet'], http_port)
        script += http
    with open('test.lua', 'w') as x:
        x.write(script)