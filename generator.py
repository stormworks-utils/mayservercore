# MSC server_config and script.lua generator

import zipfile
from logger import Logger
import sys
import json
import localinfo
import os
import error_handler
import abstract

log=Logger("server configuration")

def make_config(path, extract=True, install=True):
    profilepath = path.split(".")[0]
    log.info("Starting stage 1 configuration")
    if not install:
        log.warn("Installation disabled!")
    if extract:
        log.info("Extracting MSC profile")
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(profilepath)
        except:
            error_handler.handleFatal(log,"Unable to extract MSC profile")
    else:
        log.info("Skipping extraction")
    log.info("Loading configuration")
    profilepath=profilepath+'/profile'

    with open(profilepath+"/settings.json") as file:
        try:
            settings=json.load(file)
        except json.JSONDecodeError:
            error_handler.handleFatal(log,"Invalid profile.")
    if float(settings['properties']['version'])<localinfo.version():
        log.warn(f"Profile version out of date! (msc {localinfo.version()}, prof {settings['properties']['version']})")
    if float(settings['properties']['version'])>localinfo.version():
        log.warn(f"MSC version out of date! (msc {localinfo.version()}, prof {settings['properties']['version']})")
    log.info("Building server_config.xml")
    admins=settings['settings_msc']['admins']

    newsetts='''
<?xml version="1.0" encoding="UTF-8"?>
<server_data port="25564" '''

    for k in settings["settings_server"].keys():
        v=settings["settings_server"][k]
        newsetts+=f'{k}="{v}" '
    newsetts+='''>\n<admins>\n'''
    for i in admins:
        newsetts+=f'<id value = "{i}"/>\n'
    newsetts+='''</admins>\n<authorized/>\n<blacklist/>\n<whitelist/>\n<playlists>\n'''
    for k in settings["default_addons"].keys():
        v = settings["default_addons"][k]
        if v:
            if "dlc" in k:
                newsetts+=f'<path path="rom/data/missions/{k}"/>\n'
            else:
                newsetts += f'<path path="rom/data/missions/default_{k}"/>\n'
    for k in settings["extra_addons"]:
        newsetts += f'<path path="rom/data/missions/{k}"/>\n'

    newsetts+='''</playlists>
</server_data>'''
    log.info("server_config.xml generated")
    if install:
        log.info("Installing...")
        with open(os.getenv('APPDATA')+"/Stormworks/server_config.xml","w") as config:
            config.write(newsetts.strip())
    else:
        log.info("Install skipped, saving to workdir...")
        with open("server_config.xml","w") as config:
            config.write(newsetts.strip())
    log.info("Generator complete")

def make_abstract(path):
    log.info("Starting stage 2 configuration")
    log.info("Loading abstractor configuration")
    with open(path+"/profile/settings.json") as file:
        try:
            settings=json.load(file)['settings_msc']['modules']
        except json.JSONDecodeError:
            error_handler.handleFatal(log,"Invalid profile.")
    modules=[]
    for i in settings.keys():
        if settings[i]['enabled']:
            modules.append(i)
    for module in modules:
            abstract.generate(module,settings[module], modules)