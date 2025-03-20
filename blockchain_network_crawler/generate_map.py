import folium
from folium.plugins import HeatMap
from collections import Counter
import pickle
import asyncio
import aiohttp
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def fetch(batch, start):
    url = "https://ipv4.geojs.io/v1/ip/geo.json?ip="
    async with aiohttp.ClientSession() as session:
        payload = ",".join(ip[0] for ip in batch)
        try:
            async with session.get(url + payload, timeout=5) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return [(res.get("ip"), (res.get("latitude", 0), res.get("longitude", 0)))
                        for res in data]
        except Exception as e:
            logging.error(f"Error for batch {start} - {start + len(batch)}: {e}")
            return []


async def get_geolocations_batch(ip_list):
    tasks = [fetch(ip_list[i:i + 100], i) for i in range(0, len(ip_list), 100)]
    results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]


def generate(known_node_info, working_node_info, output_file):
    known_locations = []
    working_locations = []
    for node in known_node_info:
        try:
            lat = float(node[1][0])
            lon = float(node[1][1])
            known_locations.append([lat, lon])
        except ValueError:
            logging.warning(f"Node {node[0]} cannot be resolved to geolocation")

    for node in working_node_info:
        try:
            lat = float(node[1][0])
            lon = float(node[1][1])
            working_locations.append([lat, lon])
        except ValueError:
            logging.warning(f"Node {node[0]} cannot be resolved to geolocation")

    folium_map = folium.Map(zoom_start=2)
    HeatMap(known_locations, radius=15, blur=10).add_to(folium_map)
    for loc in working_locations:
        folium.CircleMarker(location=loc, radius=3, color='red', fill=True, fill_color='red').add_to(folium_map)

        # Save the generated heat map to an HTML file.
    folium_map.save(output_file)
    logging.info(f"Heat map saved as {output_file}")


def generate_map(name="network_map"):
    known_node_info = []
    working_node_info = []
    try:
        with open("./known.list.pkl", "rb") as geo_list:
            known_node_info = pickle.load(geo_list)
    except FileNotFoundError:
        with open("./known.pkl", "rb") as file:
            known_peers: Counter = pickle.load(file)
            known_node_info = asyncio.run(get_geolocations_batch(list(known_peers.keys())))
            with open(f"./known.list.pkl", "wb") as geo_list:
                pickle.dump(known_node_info, geo_list)

    try:
        with open("./working.list.pkl", "rb") as geo_list:
            working_node_info = pickle.load(geo_list)
    except FileNotFoundError:
        with open("./working.pkl", "rb") as file:
            working_peers: Counter = pickle.load(file)
            working_node_info = asyncio.run(get_geolocations_batch(list(working_peers.keys())))
            with open(f"./working.list.pkl", "wb") as geo_list:
                pickle.dump(working_node_info, geo_list)

    generate(known_node_info, working_node_info, f"{name}.html")
