# from akadata import EdgeScape
import pickle
from collections import Counter
import folium
from folium.plugins import MarkerCluster, HeatMap


# Adding functions
def update_peers_info(peers, name):
    nodes = [(ip, port) for ip, port in peers]
    edge = EdgeScape()
    node_info = []
    for ip, port in nodes:
        if ip:
            try:
                res = edge.ip_lookup(ip, timeout=1)
                res['port'] = port
                node_info.append(res)
            except BaseException as e:
                print((ip, port))

    with open(f"./MoneroNetwork/{name}.list.pkl", "wb") as file:
        pickle.dump(node_info, file)


def ip_in_network(ip):
    for node in known_node_info:
        if node.get('ip') == ip:
            return node
    return False


def get_nodes_by_domain(domain, working=False):
    if working:
        return [node for node in working_node_info if domain in node.get('domain', '')]
    else:
        return [node for node in known_node_info if domain in node.get('domain', '')]


try:
    with open("./MoneroNetwork/known.pkl", "rb") as file:
        known_peers: Counter = pickle.load(file)
    with open("./MoneroNetwork/working.pkl", "rb") as file:
        working_peers: Counter = pickle.load(file)
except FileNotFoundError as e:
    pass

update_peers_info(known_peers, 'known_node_info')
update_peers_info(working_peers, 'working_node_info')

print(f'{len(resolved_nodes)} out of {len(node_info)} was resolved using Akamai EdgeScape')

with open("./MoneroNetwork/known_node_info.list.pkl", "rb") as file:
    known_node_info = pickle.load(file)
with open("./MoneroNetwork/working_node_info.list.pkl", "rb") as file:
    working_node_info = pickle.load(file)

resolved_nodes = []
known_locations = []
working_locations = []
for node in known_node_info:
    if isinstance(node['lat'], float) and isinstance(node['long'], float):
        resolved_nodes.append(node)
        known_locations.append([node['lat'], node['long']])

for node in working_node_info:
    if isinstance(node['lat'], float) and isinstance(node['long'], float):
        working_locations.append([node['lat'], node['long']])

monero_map = folium.Map(zoom_start=2)
HeatMap(locations, radius=15, blur=10).add_to(monero_map)
for loc in working_locations:
    folium.CircleMarker(location=loc, radius=3, color='red', fill=True, fill_color='red').add_to(monero_map)

monero_map