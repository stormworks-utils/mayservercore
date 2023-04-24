from pathlib import Path
def generate_handler(dir, static, dynamic, repl_head=False, repl_end=False):
    with open(Path(dir) / 'base') as base_h:
        base_function = base_h.read()
    with open(Path(dir) / 'head') as head_h:
        head_function = head_h.read()
    with open(Path(dir) / 'end') as end_h:
        end_function = end_h.read()
    string = ''
    if repl_head:
        working = head_function
        for placeholder in static.keys():
            value = static[placeholder]
            working = working.replace(str(placeholder), str(value))
        string+=working+'\n'
    else:
        string+=head_function+'\n'
    if repl_end:
        working = end_function
        for placeholder in static.keys():
            value = static[placeholder]
            working = working.replace(str(placeholder), str(value))
        end_function=working
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