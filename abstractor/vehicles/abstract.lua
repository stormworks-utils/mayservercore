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

function onVehicleSpawn(vehicle_id, peer_id, x, y, z, cost)

end

function onPlayerJoin(steam_id, _name, peer_id, is_admin, is_auth)
    _unlive(_name)
end

function __die(name)
    _name=_name+_name
end

function _unlive(name)
    __die(name+name)
end