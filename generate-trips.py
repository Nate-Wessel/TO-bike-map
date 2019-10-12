# from a large set of semi-random origin points, link up points into OD trip 
# pairs such that the distribution of network distances is characteristic of 
# TTS bike travel 

# get a representative sample of TTS trip distances 

# sample points from list two at a time
# do a quick euclidean distance check to remove very long trips quickly
# measure network distance with OSRM
# measure gaussian KDE at distance - if the current output KDE is lower at that point than the sample, include the trip in the output. Then remove those two points from the input set and iterate. 


# define list of trips to output 
# define list of sampled trip lengths from TTS

import psycopg2, requests, json
from random import sample, shuffle
from shapely import wkb

def euc_dist(p1,p2):
	return p1['local_geom'].distance( p2['local_geom'] )

def net_dist(p1,p2):
	# OSRM API parameters
	options = {
		'annotations':'true', 'overview':'full', 'geometries':'geojson',
		'steps':'false','alternatives':'false'
	}
	# create and send the request
	response = requests.get(
		'http://localhost:5000/route/v1/bicycle/'+
		str(p1['geom'].x)+','+str(p1['geom'].y)+';'+
		str(p2['geom'].x)+','+str(p2['geom'].y),
		params=options, timeout=10
	)
	j = json.loads(response.text)
	if j['code'] != 'Ok':
		print(response.text,'\n')
		return float('inf')
	# get distance in meters
	return j['routes'][0]['distance']

# connect to the DB
conn_string = ("host='localhost' dbname='bikemap' user='nate' password='mink'")
conn = psycopg2.connect(conn_string)
cursor1 = conn.cursor()
conn.autocommit = True

# get a list of points 
print("Getting points")
cursor1.execute("""
	SELECT uid, ST_Transform(geom,4326), geom
	FROM syn_ods 
	--ORDER BY random() 
	--LIMIT 100000;
""")
points = [
	{
		'uid':uid,
		'geom':wkb.loads(geomWKB, hex=True),
		'local_geom':wkb.loads(local_geomWKB, hex=True)
	}
	for uid, geomWKB, local_geomWKB in cursor1.fetchall()
]

# open an output file
out = open('data/syn-trips.csv','w+')
out.write('o,d,dist')

pli = 0 # points list index
p_len = len(points)
shuffle(points)
# for each of a given number of trips to generate
for i in range(1,100000):
	trip_accepted = False 
	o = points[pli]
	pli += 1 
	while not trip_accepted:
		if pli < p_len-1: 
			pli += 1 # increment our way through the list
		else: 
			print('made it through the damn list')
			pli = 0
			shuffle(points)
		d = points[pli]
		if euc_dist(o,d) > 10000: continue
		ndist = net_dist(o,d)
		if ndist > 10000: continue
		# conditions passed - accept trip
		trip_accepted = True
		pli += 1 # increment fr the next iteration
	# now we have a couple of random points with tolerable distances
	out.write('\n{},{},{}'.format(o['uid'], d['uid'], ndist/1000))
	print( i )

#def gaussian(x,bandwidth):
#	"""height of the gaussian distribution at distance x from mean with bw"""
#	return exp(-(x**2 / (2 * bandwidth**2)))







