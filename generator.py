# MSC server_config and script.lua generator

import zipfile
from logger import Logger
import sys
import json
import localinfo
import os
import error_handler
import modules as module_gen

callback_args = {"onTick": ["game_ticks"], "onCreate": ['is_world_create'], 'onDestroy': [],
                 "onCustomCommand": ['full_message', 'user_peer_id', 'is_admin', 'is_auth', 'command'],
                 'onChatMessage':['peer_id', 'sender_name', 'message'],
                 'onPlayerJoin':['steam_id', 'name', 'peer_id', 'is_admin', 'is_auth'],
                 'onPlayerSit':['peer_id', 'vehicle_id', 'seat_name'],
                 'onPlayerUnsit':['peer_id', 'vehicle_id', 'seat_name'],
                 'onCharacterSit':['object_id', 'vehicle_id', 'seat_name'],
                 'onCharacterUnsit':['object_id', 'vehicle_id', 'seat_name'],
                 'onCharacterPickup':['object_id_actor', 'object_id_target'],
                 'onEquipmentPickup':['object_id_actor', 'object_id_target', 'EQUIPMENT_ID'],
                 'onEquipmentDrop':['object_id_actor', 'object_id_target', 'EQUIPMENT_ID'],
                 'onCreaturePickup':['object_id_actor', 'object_id_target', 'CREATURE_TYPE'],
                 'onPlayerRespawn':['peer_id'],
                 'onPlayerLeave':['steam_id', 'name', 'peer_id', 'is_admin', 'is_auth'],
                 'onToggleMap':['peer_id', 'is_open'],
                 'onPlayerDie':['steam_id', 'name', 'peer_id', 'is_admin', 'is_auth'],
                 'onVehicleSpawn':['vehicle_id', 'peer_id', 'x', 'y', 'z', 'cost'],
                 'onVehicleDespawn':['vehicle_id', 'peer_id'],
                 'onVehicleLoad':['vehicle_id'],
                 'onVehicleUnload':['vehicle_id'],
                 'onVehicleTeleport':['vehicle_id', 'peer_id', 'x', 'y', 'z'],
                 'onObjectLoad':['object_id'],
                 'onObjectUnload':['object_id'],
                 'onButtonPress':['vehicle_id', 'peer_id', 'button_name', 'is_pressed'],
                 'onSpawnAddonComponent':['object_id/vehicle_id', 'component_name', 'TYPE_STRING', 'addon_index'],
                 'onVehicleDamaged':['vehicle_id', 'damage_amount', 'voxel_x', 'voxel_y', 'voxel_z', 'body_index'],
                 'onFireExtinguished':['fire_x', 'fire_y', 'fire_z'],
                 'onForestFireSpawned':['fire_objective_id', 'fire_x', 'fire_y', 'fire_z'],
                 'onForestFireExtinguished':['fire_objective_id', 'fire_x', 'fire_y', 'fire_z'],
                 'onTornado':['transform'],
                 'onMeteor':['transform', 'magnitude'],
                 'onTsunami':['transform', 'magnitude'],
                 'onWhirlpool':['transform', 'magnitude'],
                 'onVolcano':['transform']}


def make_config(path, extract=True):
    log = Logger("Configuration file generator")
    profilepath = path.split(".")[0]
    log.info("Starting stage 1 configuration")
    if extract:
        log.info("Extracting MSC profile")
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(profilepath)
        except:
            error_handler.handleFatal(log, "Unable to extract MSC profile")
    else:
        log.info("Skipping extraction")
    log.info("Loading configuration")
    profilepath = profilepath + '/profile'

    with open(profilepath + "/settings.json") as file:
        try:
            settings = json.load(file)
        except json.JSONDecodeError:
            error_handler.handleFatal(log, "Invalid profile.")
    if float(settings['properties']['version']) < localinfo.version():
        log.warn(f"Profile version out of date! (msc {localinfo.version()}, prof {settings['properties']['version']})")
    if float(settings['properties']['version']) > localinfo.version():
        log.warn(f"MSC version out of date! (msc {localinfo.version()}, prof {settings['properties']['version']})")
    log.info("Building server_config.xml")
    admins = settings['settings_msc']['admins']

    newsetts = '''
<?xml version="1.0" encoding="UTF-8"?>
<server_data port="25564" '''

    for k in settings["settings_server"].keys():
        v = settings["settings_server"][k]
        newsetts += f'{k}="{v}" '
    newsetts += '''>\n<admins>\n'''
    for i in admins:
        newsetts += f'<id value = "{i}"/>\n'
    newsetts += '''</admins>\n<authorized/>\n<blacklist/>\n<whitelist/>\n<playlists>\n'''
    for k in settings["default_addons"].keys():
        v = settings["default_addons"][k]
        if v:
            if "dlc" in k:
                newsetts += f'<path path="rom/data/missions/{k}"/>\n'
            else:
                newsetts += f'<path path="rom/data/missions/default_{k}"/>\n'
    for k in settings["extra_addons"]:
        newsetts += f'<path path="rom/data/missions/{k}"/>\n'

    newsetts += '''</playlists>
</server_data>'''
    log.info("server_config.xml generated")
    if not os.path.exists(f"servers/{settings['properties']['server_shorthand']}/"):
        os.makedirs(f"servers/{settings['properties']['server_shorthand']}/")
    with open(f"servers/{settings['properties']['server_shorthand']}/server_config.xml", "w") as config:
        config.write(newsetts.strip())
    log.info("Config generation complete")
    print(profilepath)
    return profilepath

def make_module(path):
    log = Logger("Module generator")
    log.info("Starting stage 2 configuration")
    log.info("Loading modules configuration")
    with open(path + "/settings.json") as file:
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


def generate(path, extract=True):
    log = Logger("Addon compiler")
    compiled_modules = ""
    path=make_config(path, extract)
    modules = make_module(path)
    to_handle = {}
    callbacks = {}
    for module in modules:
        code, calls, handles, name, desc = module
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
    compiled_modules = compiled_modules.strip()
    callback_defs = "--callback setup\n\n"
    for callback in callbacks.keys():
        arguments=callback_args[callback]
        argument_string=', '.join(arguments)
        calls = callbacks[callback]
        callback_defs += f'function {callback}({argument_string})\n'
        for call in calls:
            callback_defs += f'    {call}({argument_string})\n'
        callback_defs += 'end\n\n'
    callback_defs = callback_defs.strip()