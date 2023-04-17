import ast
import os
from pathlib import Path

import error_handler
import logger

marks=['exec', 'eval', 'open', '__import__', 'import']
def get_libs_and_functions(code):
    log=logger.Logger("Extension validator")
    code_ast=ast.parse(code)
    modules=[]
    functions=[]
    has_handler=False
    for node in ast.walk(code_ast):
        if type(node)==ast.FunctionDef:
            if node.name=='handler':
                if len(node.args.args)==1:
                    has_handler=True
        if type(node)==ast.Import:
            names=node.names
            for i in names:
                modules.append(i.name)
        if type(node)==ast.ImportFrom:
            modules.append(node.module)
        if type(node)==ast.Call:
            try:
                func=node.func

                if func.id=='getattr':
                    if len(node.args)>1 and node.args[1].id=='__builtins__':
                        error_handler.handleSkippable(log, "Module is either incredibly strangely designed or intentionally malicious.")
                if func.id in marks:
                    functions.append(func.id)
            except AttributeError:
                pass
        if type(node)==ast.Assign:
            func=node.value
            if 'id' in func.__dict__.keys() and func.id in marks:
                functions.append(func)
        if type(node)==ast.Attribute:
            try:
                if node.value.id=='__builtins__' and node.attr in marks:
                    functions.append(node.attr)
            except AttributeError:
                pass

    return list(set(modules)), list(set(functions)), has_handler

def discover_extra_files(module):
    files=[]
    for i in os.walk(Path('modules')/module):
        files=i[2]
    files=[file for file in files if file.split(".")[1]=='py']
    return files

def get_code(module, files):
    code=[]
    modpath=Path("modules")/module
    for i in files:
        with open(modpath/i,'r') as file:
            code.append(file.read())
    return code