# from home
cd

# get new street data from the overpass API
wget -O scripts/osrm-backend/osm-data/gta.osm --post-file=bike-map/overpass/ways.txt https://overpass-api.de/api/interpreter

# import street data into postGIS
osm2pgsql --slim --hstore-all --prefix gta -d bikemap --style bike-map/osm2pgsql/ways.style scripts/osrm-backend/osm-data/gta.osm

# this makes a later query a little faster
psql -d bikemap -c "CREATE INDEX ON gta_nodes (id);"

# process the data for OSRM-backend (but don't run that)
cd scripts/osrm-backend
build/osrm-extract -p ~/bike-map/osrm-profiles/default-bicycle.lua osm-data/gta.osm
build/osrm-contract osm-data/gta.osrm
#build/osrm-routed osm-data/gta.osrm

# create edges table
cd ~/bike-map
psql -d bikemap -f create-edge-table-from-osm2pgsql-data.sql
