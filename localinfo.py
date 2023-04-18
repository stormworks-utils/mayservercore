import json

with open('localinfo.json') as infofile:
    info=json.load(infofile)

def version():
    return info['version']

def first_run():
    return info['first_run']

def disable_first_run():
    info['first_run']=False
    save_info()

def save_info():
    with open('localinfo.json','w') as infofile:
        json.dump(info, infofile)