import json

from logger import Logger
import error_handler
from luaparser import ast, astnodes
import random

callbacks=['onTick', 'onCreate', 'onDestroy','onCustomCommand', 'onChatMessage', 'onPlayerJoin', 'onPlayerSit', 'onCharacterSit', 'onCharacterUnsit', 'onCharacterPickup', 'onEquipmentPickup', 'onEquipmentDrop', 'onCreaturePickup', 'onPlayerRespawn', 'onPlayerLeave', 'onToggleMap', 'onPlayerDie', 'onVehicleSpawn', 'onVehicleLoad', 'onVehicleUnload', 'onVehicleTeleport', 'onVehicleDespawn', 'onSpawnAddonComponent', 'onVehicleDamaged', 'onFireExtinguished', 'onVehicleUnload', 'onForestFireSpawned', 'onForestFireExtinguised', 'onButtonPress', 'onObjectLoad', 'onObjectUnload', 'onTornado', 'onMeteor', 'onTsunami', 'onWhirlpool', 'onVolcano']
offhandle=['httpReply','onFirst']
c_function=[('server','httpGet')]

def generate(module,settings, modules):
    log = Logger('Module proccessor')
    log.info(f'Started generator for module "{module}"')
    log.info('Loading layer')
    try:
        with open(f"modules/{module}/module.lua", 'r') as module_fs:
            module_full=module_fs.read()
    except :
        error_handler.handleFatal(log,"Unable to fetch module")
    try:
        with open(f"modules/{module}/require.msc", 'r') as require_fs:
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

    for i in module_full.split("\n"):
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

    vel=ast.parse(module_full)
    log.info("AST generated")

    calls, handles, functions =_recursive_generate(vel, prefix, id, settings, callbacks, offhandle, c_function)
    log.info(f"Processing complete, found {len(calls)} callbacks, {len(functions)} special function calls, and {len(handles)} handlers.")
    code=ast.to_lua_source(vel)
    log.info("Module code generated")
    return code, calls, handles, functions, name, desc

def _recursive_generate(ast_code, prefix, id, settings, callnames, offnames, c_function):
    callbacks= {}
    offhandle={}
    functions={}
    tp=type(ast_code)
    if tp==list:
        for i in ast_code:
            cb, oh, fc = _recursive_generate(i, prefix, id, settings, callnames, offnames, c_function)
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
            for oname in fc.keys():
                names = fc[oname]
                for name in names:
                    if oname in functions.keys():
                        functions[oname].append(name)
                    else:
                        functions.update({oname: [name]})
    elif tp==astnodes.Name:
        if ast_code.id[:2]=='__':
            #protected var
            ast_code.id=prefix+ast_code.id[2:]
        elif ast_code.id[:1]=='_':
            #private var
            ast_code.id=id+'_'+ast_code.id[1:]
    elif tp==astnodes.Block:
        cb, oh, fc = _recursive_generate(ast_code.body, prefix, id, settings, callnames, offnames, c_function)
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
        for oname in fc.keys():
            names = fc[oname]
            for name in names:
                if oname in functions.keys():
                    functions[oname].append(name)
                else:
                    functions.update({oname: [name]})
    elif tp == astnodes.Chunk:
        cb, oh, fc = _recursive_generate(ast_code.body, prefix, id, settings, callnames, offnames, c_function)
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
        for oname in fc.keys():
            names = fc[oname]
            for name in names:
                if oname in functions.keys():
                    functions[oname].append(name)
                else:
                    functions.update({oname: [name]})
    elif tp == astnodes.Index:
        idx, value = ast_code.idx, ast_code.value
        if type(idx)==astnodes.Name and type(value)==astnodes.Name:
            idx, value = idx.id, value.id
            for a,b in c_function:
                if idx==b and value==a:
                    oname = idx
                    name = 'mscfunction_' + prefix + idx
                    ast_code.value.id="mschttp"
                    ast_code.idx.id=name
                    if oname in functions.keys():
                        functions[oname].append(name)
                    else:
                        functions.update({oname: [name]})
    elif tp == astnodes.Assign:
        for i in ast_code.targets:
            cb, oh, fc = _recursive_generate(i, prefix, id, settings, callnames, offnames, c_function)
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
            for oname in fc.keys():
                names = fc[oname]
                for name in names:
                    if oname in functions.keys():
                        functions[oname].append(name)
                    else:
                        functions.update({oname: [name]})
        for ind, i in enumerate(ast_code.values):
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
                    print(val, type(val))
                    if type(val)==bool or val in ['true', 'false']:
                        if val in ['true', 'false']:
                            val=val=='true'
                        if val:
                            ast_code.values[ind]=astnodes.TrueExpr()
                        else:
                            ast_code.values[ind]=astnodes.FalseExpr()
                    if type(val) in [int, float] or (type(val)==str and val.replace('.','',1).isdigit()):
                        if type(val)==str:
                            val=float(val)
                        ast_code.values[ind] = astnodes.Number(val)
                    else:
                        i.s=str(val)
            else:
                cb, oh, fc = _recursive_generate(i, prefix, id, settings, callnames, offnames, c_function)
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
                for oname in fc.keys():
                    names = fc[oname]
                    for name in names:
                        if oname in functions.keys():
                            functions[oname].append(name)
                        else:
                            functions.update({oname: [name]})
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
            if name in offnames:
                oname=name
                name='offhandle_'+prefix+name
                if oname in offhandle.keys():
                    offhandle[oname].append(name)
                else:
                    offhandle.update({oname:[name]})
                ast_code.name.id = name
        for i in ast_code.__dict__.values():
            if not type(i)==list:
                i=[i]
            for j in i:
                if 'luaparser.astnodes.' in str(type(j)):
                    cb, oh, fc =_recursive_generate(j, prefix, id, settings, callnames, offnames, c_function)
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
                    for oname in fc.keys():
                        names = fc[oname]
                        for name in names:
                            if oname in functions.keys():
                                functions[oname].append(name)
                            else:
                                functions.update({oname: [name]})
    return callbacks, offhandle, functions