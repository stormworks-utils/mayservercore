--###NAME:PVP
--###DESC:PVP system to allow disabling vehicle and player damage for certain people
--###MODID:def_pvp

_player_changeable="###CONFIG:player_changeable:false"
_admin_changeable="###CONFIG:admin_changeable:false"
_default="###CONFIG:default:false"
_vehicles_enabled="###CONFIG:vehicles:false"

_vehicles={}

function __toggle(a)
    return not a
end

function _toggle_pvp(__id)
    _vehicles[__id]['pvp']=__toggle(_vehicles[_id]['pvp'])
    server.httpGet()
end

function onTick()
end