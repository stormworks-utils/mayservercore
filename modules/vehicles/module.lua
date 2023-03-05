--###NAME:Vehicle manager
--###DESC:Vehicle management system for tracking vehicle ownership and other useful things.
--###MODID:def_vehicle

_antisteal="###CONFIG:antisteal.enabled:false"
_default_antisteal="###CONFIG:antisteal.default:false"
_antisteal_pc='###CONFIG:antisteal.player_changeable:false'
_antisteal_ac='###CONFIG:antisteal.admin_changeable:false'
_spawnlimit='###CONFIG:spawncap.enabled:false'
_default_spawnlimit='###CONFIG:spawncap.default:0'
_spawnlimit_pc='###CONFIG:spawncap.player_changeable:false'
_spawnlimit_ac='###CONFIG:spawncap.admin_changeable:false'
_spawlimit_remove_old='###CONFIG:spawncap.destroy_old:false'

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

server.httpGet()