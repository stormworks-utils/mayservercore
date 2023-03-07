from pathlib import Path
def generate_handler(dir, static, dynamic):
    with open(Path(dir) / 'base.lua') as base_h:
        base_function = base_h.read()
    with open(Path(dir) / 'head.lua') as head_h:
        head_function = head_h.read()
    with open(Path(dir) / 'end.lua') as end_h:
        end_function = end_h.read()
    string = head_function+'\n'
    for dyn in dynamic:
        working = base_function
        for placeholder in static.keys():
            value = static[placeholder]
            working = working.replace(str(placeholder), str(value))
        for placeholder in dyn.keys():
            value = dyn[placeholder]
            working = working.replace(str(placeholder), str(value))
        string+=working+'\n'
    string+=end_function+'\n'
    return string