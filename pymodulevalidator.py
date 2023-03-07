import ast
marks=['exec', 'eval', 'open', '__import__']
def get_libs_and_functions(code):
    code_ast=ast.parse(code)
    modules=[]
    functions=[]
    for node in ast.walk(code_ast):
        if type(node)==ast.Import:
            names=node.names
            for i in names:
                modules.append(i.name)
        if type(node)==ast.ImportFrom:
            modules.append(node.module)
        if type(node)==ast.Call:
            func=node.func
            if func.id in marks:
                functions.append(func.id)
    return modules, functions