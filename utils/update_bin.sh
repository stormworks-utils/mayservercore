# Stormworks
steamcmd +force_install_dir "$1" +login anonymous +app_update 1247090 validate +exit
# Proton Experimental
mkdir "$1/proton"
steamcmd +force_install_dir "$1/proton" +login anonymous +app_update 1493710 validate +exit
