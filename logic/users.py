import oddasr.odd_asr_config as config

import io
import json

g_data = {'user':'Admin','pwd':'Odd_Asr'}

def _load(path):
    try:
        f = io.open(path , "r")
        all = f.read()
        j = json.loads(all)
        g_data['user'] = j['user']
        g_data['pwd'] = j['pwd']
    except:
        pass

_load(config.Users)

def _save(path ):
    f = io.open(path , 'w')
    all = json.dumps(g_data)
    f.write(all)

def check_user(user,pwd):
    if g_data['user'] == user and g_data['pwd'] == pwd:
        return True
    else:
        return False
    
def modify_user(user,oldpwd,newpwd):
    if g_data['user'] != user or g_data['pwd'] != oldpwd:
        return False
    else:
        g_data['user'] = user
        g_data['pwd'] = newpwd
        _save(config.Users)
        return True
