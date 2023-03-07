

def generate_http_calls(calls,port):
    with open('httpgen/base.lua') as base_h:
        base_function=base_h.read()
    with open('httpgen/head.lua') as head_h:
        string=head_h.read()
    for name in calls:
        prefix=name.split('_',1)[1]
        string+=base_function.replace('NAME', name).replace('PREFIX', prefix).replace('PORT', str(port))
        string+='\n'
    return string