from DBconnection import connection
from shapely.geometry import Point, LineString
from shapely.wkb import loads as loadWKB, dumps as dumpWKB

node_cursor = connection.cursor()
edge_cursor = connection.cursor()

# get a list of nodes (node_id) with degree = 2
node_cursor.execute("""
	WITH streets AS (
		SELECT node_1, node_2
		FROM street_edges 
		WHERE 
			f+r > 5 OR
			(highway='path' AND bicycle='designated') OR
			highway in (
				'residential','unclassified',
				'tertiary','secondary','primary',
				'cycleway','pedestrian'
			)
	), nodes AS (
		SELECT node_1 AS nid FROM streets
		UNION ALL
		SELECT node_2 AS nid FROM streets
	), node_degree AS (
		SELECT nid, COUNT(*) AS degree 
		FROM nodes GROUP BY nid
	) SELECT nid FROM node_degree WHERE degree = 2
	LIMIT 25;
""")
nodes = node_cursor.fetchall()
print(len(nodes),'to check/merge')

keys = ['uid', 'way_id', 'node_1', 'node_2', 'f', 'r', 'edge']
for node_id, in nodes:
	# get the two edges connected to the given node
	print('\tnode_id =',node_id)
	edge_cursor.execute("""
		SELECT uid, way_id, node_1, node_2, f, r, edge
		FROM street_edges 
		WHERE %(node_id)s IN (node_1,node_2)
		LIMIT 2;
	""",{ 'node_id': node_id } );
	# parse as dicts
	edges = [ dict(zip(keys,edge)) for edge in edge_cursor.fetchall() ]
	e1,e2 = edges[0],edges[1]
	# only accept perfect matches
	if e1['way_id'] != e2['way_id']: continue
	if e1['f'] != e2['f']: continue
	if e1['r'] != e2['r']: continue
	print('\t\tmatch found!')
	c1 = loadWKB( e1['edge'], hex=True ).coords
	c2 = loadWKB( e2['edge'], hex=True ).coords
	if e1['node_2'] == e2['node_1']: 
		n1,n2 = e1['node_1'],e2['node_2']
		newGeom = LineString( c1[:len(c1)-1] + list(c2) )
	elif e2['node_2'] == e1['node_1']:
		n1,n2 = e2['node_1'],e1['node_2']
		newGeom = LineString( c2[:len(c1)-1] + list(c1) )
	else: 
		print('as yet unhandled exception')
		break 
	# insert the new edge and delete the others
	"""
		DELETE FROM street_edges WHERE uid IN (%(edge1_id)s,%(edge2_id)s);
		INSERT INTO street_edges () VALUES ()
	""",{
		# to delete
		'edge1_id':e1['uid'], 'edge2_id':e2['uid'],
		# to insert
		'way_id': e1['way_id'],
		'node_1': n1, 'node_2': n2,
		'f': e1['f'], 'r': e1['r'],
		'geom': dumpWKB(newGeom,hex=True)
	}



