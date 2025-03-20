import asyncio
import os
import socket
import logging
from collections import Counter
import argparse
import config
from network_discovery import NetworkDiscovery, shutdown
from generate_map import generate_map

args = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def main():
    discovery = NetworkDiscovery()
    discovery.load_peers()
    if discovery.working_peers:
        discovery.add_seed_peers(discovery.working_peers)
    else:
        seeds: Counter[tuple[str, int]] = Counter()
        if args.network == "monero":
            # Use known Monero DNS seeds for initial state
            monero_seed_nodes_dns = [
                "moneroseeds.se",
                "moneroseeds.ae.org",
                "moneroseeds.ch",
                "moneroseeds.li",
            ]

            for seed_dns in monero_seed_nodes_dns:
                try:
                    _, _, ipaddrlist = socket.gethostbyname_ex(seed_dns)
                    seeds.update([(ip, 18080) for ip in ipaddrlist])
                except Exception as e:
                    logging.error(f"DNS lookup failed for {seed_dns}: {e}")
        elif args.network == "safex":
            # Source:
            # https://github.com/safex/safexcore/blob/2d8452fb46cab11f184df2977dc9e701edacaed2/src/p2p/net_node.inl#L431
            seeds.update([("178.128.126.76", 17401),
                          ("178.128.126.75", 17401),
                          ("178.128.126.69", 17401),
                          ("159.65.72.114", 17401),
                          ("206.189.70.207", 17401),
                          ("178.128.166.139", 17401),
                          ("188.166.153.184", 17401),
                          ("142.93.171.239", 17401),
                          ])
        elif args.network == "custom":
            seeds.update([(args.node, args.port)])
        else:
            raise NotImplementedError("The network type is not supported")

        discovery.add_seed_peers(seeds)
    discover_task = asyncio.create_task(discovery.discover())
    try:
        await discover_task
    except (KeyboardInterrupt, asyncio.CancelledError):
        await shutdown(discover_task)


def cleanup():
    files = ["./known.pkl", "./known.list.pkl", "./working.pkl", "./working.list.pkl"]
    for f in files:
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except FileNotFoundError:
            print(f"File not found: {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A blockchain network crawler for networks based on the cryptonote P2P, like monero."
    )

    parser.add_argument(
        "network",
        choices=["monero", "safex", "custom"],
        help="Pick the network you want to crawl."
    )

    parser.add_argument(
        "-n", "--node",
        type=str,
        help="Specify the IPv4 address of a seed node."
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        help="Specify the port number of the seed node."
    )

    # network_id is part of the handshake, for example Monero network id can be found here:
    # https://github.com/monero-project/monero/blob/662d246cd5a8666c7b4a9bd1a1e3e26792116dad/src/cryptonote_config.h#L229
    parser.add_argument(
        "--network-id",
        type=str,
        default="1230f171610441611731008216a1a110",
        help="Add the hex string id of the network."
    )

    parser.add_argument(
        "--cleanup",
        action='store_true',
        help="Whether cleanup cached files or not."
    )

    args = parser.parse_args()
    if args.cleanup:
        cleanup()

    # Source:
    # https://github.com/safex/safexcore/blob/2d8452fb46cab11f184df2977dc9e701edacaed2/src/cryptonote_config.h#L249
    if args.network == "safex":
        args.network_id = "73616665786d6f6f6e6c616d626f3478"  # safexmoonlambo4x
    elif args.network == "custom" and (args.node is None or args.port is None):
        parser.error("You must provide the seed node ip and port.")
    config.NETWORK_ID = args.network_id
    asyncio.run(main())
    generate_map(name=args.network)
