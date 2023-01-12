import json

from logger import Logger
import error_handler
from luaparser import ast, astnodes
log=Logger('abstractor')
import random

def generate(settings):
    log.info('Started generator for abstraction layer')
    log.info('Loading layer')
    try:
        with open("abstractor/vehicles/abstract.lua",'r') as abstraction_fs:
            abstraction_full=abstraction_fs.read()
    except :
        error_handler.handleFatal(log,"Unable to fetch abstracts")

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

    for i in abstraction_full.split():
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


    vel=ast.parse(abstraction_full)

    _recursive_generate(vel, prefix, id)
    print("PRINT")
    _recursive_print(vel)
    print()
    print(ast.to_lua_source(vel))

def _recursive_generate(ast_code, prefix, id):
    if type(ast_code) == list:
        for i in ast_code:
            _recursive_generate(i, prefix, id)
    else:
        if type(ast_code) == astnodes.Block or type(ast_code) == astnodes.Chunk:
            _recursive_generate(ast_code.body, prefix, id)
        elif type(ast_code)==astnodes.Assign:
            _recursive_generate(ast_code.targets, prefix, id)
            _recursive_generate(ast_code.values, prefix, id)
        elif type(ast_code)==astnodes.Name:
            if ast_code.id[:2]=='__':
                #protected var
                ast_code.id=prefix+ast_code.id[2:]
            elif ast_code.id[:1]=='_':
                #protected var
                ast_code.id=id+'_'+ast_code.id[1:]
        elif type(ast_code)==astnodes.Function:
            _recursive_generate(ast_code.name, prefix, id)
            _recursive_generate(ast_code.body, prefix, id)
            _recursive_generate(ast_code.args, prefix, id)
        elif 'Op' in str(type(ast_code)) and 'luaparser.astnodes.' in str(type(ast_code)):
            _recursive_generate(ast_code.left, prefix, id)
            _recursive_generate(ast_code.right, prefix, id)
        elif type(ast_code)==astnodes.Call:
            _recursive_generate(ast_code.func, prefix, id)
        try:
            print(ast_code.__dict__)
        except:
            pass
        print(str(type(ast_code)))
def _recursive_print(ast_code):
    if type(ast_code) == list:
        for i in ast_code:
            _recursive_print(i)
    else:
        print(type(ast_code))
        if type(ast_code) == astnodes.Block or type(ast_code) == astnodes.Chunk:
            _recursive_print(ast_code.body)
        elif type(ast_code)==astnodes.Assign:
            _recursive_print(ast_code.targets)
        elif type(ast_code)==astnodes.Name:
            print(ast_code.id)
        if type(ast_code)==astnodes.Function:
            _recursive_print(ast_code.name)