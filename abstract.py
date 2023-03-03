import json

from logger import Logger
import error_handler
from luaparser import ast, astnodes
import random

callbacks=['onTick', 'onCreate', 'onDestroy','onCustomCommand', 'onChatMessage', 'onPlayerJoin', 'onPlayerSit', 'onCharacterSit', 'onCharacterUnsit', 'onCharacterPickup', 'onEquipmentPickup', 'onEquipmentDrop', 'onCreaturePickup', 'onPlayerRespawn', 'onPlayerLeave', 'onToggleMap', 'onPlayerDie', 'onVehicleSpawn', 'onVehicleLoad', 'onVehicleUnload', 'onVehicleTeleport', 'onVehicleDespawn', 'onSpawnAddonComponent', 'onVehicleDamaged', 'httpReply', 'onFireExtinguished', 'onVehicleUnload', 'onForestFireSpawned', 'onForestFireExtinguised', 'onButtonPress', 'onObjectLoad', 'onObjectUnload', 'onTornado', 'onMeteor', 'onTsunami', 'onWhirlpool', 'onVolcano']
offhandle=['httpReply']

def generate(module,settings, modules):
    log = Logger('Module proccessor')
    log.info(f'Started generator for abstraction module "{module}"')
    log.info('Loading layer')
    try:
        with open(f"abstractor/{module}/abstract.lua",'r') as abstraction_fs:
            abstraction_full=abstraction_fs.read()
    except :
        error_handler.handleFatal(log,"Unable to fetch abstracts")
    try:
        with open(f"abstractor/{module}/require.msc",'r') as require_fs:
            requires=require_fs.readlines()
    except :
        error_handler.handleFatal(log,"Unable to fetch requirements")

    for i in requires:
        inver=False
        incom=False
        setting, mod, default=i.split(':')
        if setting[0]=='!':
            setting=setting[1:]
            inver=True
        if setting[0]=='#':
            setting=setting[1:]
            incom=True
        target_setting = setting.split('.')
        try:
            val = settings
            for j in target_setting:
                val = val[j]
        except:
            val = default
        if (val and not inver) or (inver and not val):
            if incom:
                error_handler.handleFatal(log, f"Module {module} is incompatible with another active module ({mod})")
            else:
                if not mod in modules:
                    error_handler.handleFatal(log, f"Module {module} has unmet requirement ({mod})")

    log.info("Requirements validated")
    #create prefix for private vars/functions to make sure theyre not accessible
    prf=''
    for i in range(10):
        ncl=random.randint(1,3)
        if ncl==1:
            prf+=str(random.randint(0,9))
        if ncl==2:
            prf+=chr(random.randint(65,90))
        if ncl==3:
            prf+=chr(random.randint(97,122))
    prefix=prf+'_'

    log.info("Starting stage one parse")
    #parse MSC flags
    name='None'
    desc='None'
    id=prefix #MODID is used for hidden var prefixes, so if no MODID is given, use prefix to avoid collisions

    for i in abstraction_full.split("\n"):
        if i[:5]=='--###':
            tagfull=i[5:].split(':',1)
            tag=tagfull[0]
            data=tagfull[1]
            if tag=='NAME':
                name=data
            elif tag=='DESC':
                desc=data
            elif tag=='MODID':
                id=data
                prefix=prefix+id+'_'
    log.info("Starting stage two parse")

    vel=ast.parse(abstraction_full)
    log.info("AST generated")

    calls, handles=_recursive_generate(vel, prefix, id, settings, callbacks, offhandle)
    log.info(f"Processing complete, found {len(calls)} callbacks and {len(handles)} handlers.")
    code=ast.to_lua_source(vel)
    log.info("Abstractor code generated")
    return code, calls, handles, name, desc

def _recursive_generate(ast_code, prefix, id, settings, callnames, offnames):
    callbacks= {}
    offhandle={}
    tp=type(ast_code)
    if tp==list:
        for i in ast_code:
            cb, oh = _recursive_generate(i, prefix, id, settings, callnames, offnames)
            for oname in cb.keys():
                names = cb[oname]
                for name in names:
                    if oname in callbacks.keys():
                        callbacks[oname].append(name)
                    else:
                        callbacks.update({oname: [name]})
            for oname in oh.keys():
                names = oh[oname]
                for name in names:
                    if oname in offhandle.keys():
                        offhandle[oname].append(name)
                    else:
                        offhandle.update({oname: [name]})
    elif tp==astnodes.Name:
        if ast_code.id[:2]=='__':
            #protected var
            ast_code.id=prefix+ast_code.id[2:]
        elif ast_code.id[:1]=='_':
            #private var
            ast_code.id=id+'_'+ast_code.id[1:]
    elif tp==astnodes.Block:
        cb, oh = _recursive_generate(ast_code.body, prefix, id, settings, callnames, offnames)
        for oname in cb.keys():
            names = cb[oname]
            for name in names:
                if oname in callbacks.keys():
                    callbacks[oname].append(name)
                else:
                    callbacks.update({oname: [name]})
        for oname in oh.keys():
            names = oh[oname]
            for name in names:
                if oname in offhandle.keys():
                    offhandle[oname].append(name)
                else:
                    offhandle.update({oname: [name]})
    elif tp == astnodes.Chunk:
        cb, oh = _recursive_generate(ast_code.body, prefix, id, settings, callnames, offnames)
        for oname in cb.keys():
            names = cb[oname]
            for name in names:
                if oname in callbacks.keys():
                    callbacks[oname].append(name)
                else:
                    callbacks.update({oname: [name]})
        for oname in oh.keys():
            names = oh[oname]
            for name in names:
                if oname in offhandle.keys():
                    offhandle[oname].append(name)
                else:
                    offhandle.update({oname: [name]})
    elif tp == astnodes.Assign:
        for i in ast_code.targets:
            cb, oh = _recursive_generate(i, prefix, id, settings, callnames, offnames)
            for oname in cb.keys():
                names = cb[oname]
                for name in names:
                    if oname in callbacks.keys():
                        callbacks[oname].append(name)
                    else:
                        callbacks.update({oname: [name]})
            for oname in oh.keys():
                names = oh[oname]
                for name in names:
                    if oname in offhandle.keys():
                        offhandle[oname].append(name)
                    else:
                        offhandle.update({oname: [name]})
        for i in ast_code.values:
            if type(i)==astnodes.String:
                if i.s[:9]=='###CONFIG':
                    x=i.s.split(':')
                    target_setting=x[1].split('.')
                    try:
                        val=settings
                        for j in target_setting:
                            val=val[j]
                    except:
                        val=x[2]
                    i.s=str(val).lower()
            else:
                cb, oh = _recursive_generate(i, prefix, id, settings, callnames, offnames)
                for oname in cb.keys():
                    names = cb[oname]
                    for name in names:
                        if oname in callbacks.keys():
                            callbacks[oname].append(name)
                        else:
                            callbacks.update({oname: [name]})
                for oname in oh.keys():
                    names = oh[oname]
                    for name in names:
                        if oname in offhandle.keys():
                            offhandle[oname].append(name)
                        else:
                            offhandle.update({oname: [name]})
    else:
        if tp==astnodes.Function:
            name=ast_code.name.id
            if name.strip() in callnames:
                oname=name
                name='callback_'+prefix+name
                if oname in callbacks.keys():
                    callbacks[oname].append(name)
                else:
                    callbacks.update({oname:[name]})
                ast_code.name.id = name
            if name in offhandle:
                oname=name
                name='offhandle_'+prefix+name
                offhandle.append(name)
                if oname in callbacks.keys():
                    callbacks[oname].append(name)
                else:
                    callbacks.update({oname:[name]})
                ast_code.name.id = name
        for i in ast_code.__dict__.values():
            if not type(i)==list:
                i=[i]
            for j in i:
                if 'luaparser.astnodes.' in str(type(j)):
                    cb, oh=_recursive_generate(j, prefix, id, settings, callnames, offnames)
                    for oname in cb.keys():
                        names = cb[oname]
                        for name in names:
                            if oname in callbacks.keys():
                                callbacks[oname].append(name)
                            else:
                                callbacks.update({oname: [name]})
                    for oname in oh.keys():
                        names = oh[oname]
                        for name in names:
                            if oname in offhandle.keys():
                                offhandle[oname].append(name)
                            else:
                                offhandle.update({oname: [name]})
    return callbacks, offhandle