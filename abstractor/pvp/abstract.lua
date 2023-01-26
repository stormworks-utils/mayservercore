--###NAME:Vehicle manager
--###DESC:Vehicle management system or tracking vehicle ownership and other useful things.
--###MODID:def_vehicle

antisteal="###CONFIG:antisteal.enabled:false"
default_antisteal="###CONFIG:antisteal.default:false"
antisteal_pc='###CONFIG:antisteal.player_changeable:false'
antisteal_ac='###CONFIG:antisteal.admin_changeable:false'
spawnlimit='###CONFIG:spawncap.enabled:false'
default_spawnlimit='###CONFIG:spawncap.default:0'
spawnlimit_pc='###CONFIG:spawncap.player_changeable:false'
spawnlimit_ac='###CONFIG:spawncap.admin_changeable:false'
spawlimit_remove_old='###CONFIG:spawncap.destroy_old:false'

_vehicles={}

function __toggle(a)
    return not a
end

function _toggle_pvp(__id)
    _vehicles[__id]['pvp']=__toggle(_vehicles[_id]['pvp'])
end

function onTick()
end