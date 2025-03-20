import asyncio
import pickle
import logging
from collections import Counter

from p2p.levin_protocol import LevinProtocol
from p2p.messages import P2P_Handshake, P2P_SupportedFlags, P2P_COMMANDS
from psf import Section


async def shutdown(task: asyncio.Task):
    logging.info(f"Cancelling task {task.get_name()}")
    task.cancel()
    try:
        await asyncio.gather(task)
    except asyncio.exceptions.CancelledError:
        logging.info("Task cancelled.")


class NetworkDiscovery:
    def __init__(self):
        self.peers_queue: asyncio.Queue = asyncio.Queue()
        self.known_peers: Counter = Counter()
        self.working_peers: Counter = Counter()
        self.stop_discovery: bool = False
        self.workers = []

    def add_seed_peers(self, seed_peers: Counter):
        for peer in seed_peers:
            self.peers_queue.put_nowait(peer)
            self.known_peers.update([peer])

    async def add_new_peer(self, new_peer: tuple):
        if not self.stop_discovery and new_peer not in self.known_peers:
            self.known_peers.update([new_peer])
            self.peers_queue.put_nowait(new_peer)

    async def get_peers(self, peer):
        async with LevinProtocol(*peer) as lp:
            if lp is None:
                return
            handshake = P2P_Handshake()
            await lp.send_async(handshake)
            header, payload = await lp.get_message_async()
            if not header:
                logging.debug(f"Server {peer} didn't return data")
                return
            if header.command == P2P_COMMANDS.SUPPORT_FLAGS_REQUEST:
                await lp.send_async(P2P_SupportedFlags())
                header, payload = await lp.get_message_async()
            if header.command != P2P_COMMANDS.HANDSHAKE_RESPONSE:
                return
        res = Section()
        length = res.deserialize(bytearray(payload))
        if length != header.length:
            logging.debug("Levin message length mismatch")
            return
        self.working_peers.update([peer])
        try:
            peer_list = res.get("local_peerlist_new", [])
            for adr in peer_list:
                try:
                    ip = adr["adr"]["addr"].get("m_ip") or adr["adr"]["addr"].get("addr")
                    port = adr["adr"]["addr"]["m_port"]
                    await self.add_new_peer((ip, port))
                except KeyError:
                    logging.warning("Invalid peer address format")
        except Exception as e:
            logging.error(f"Error processing peer list: {e}")

    async def worker(self):
        while not self.stop_discovery:
            peer = None
            try:
                peer = await asyncio.wait_for(self.peers_queue.get(), timeout=3)
                logging.info(
                    f"Queue size: {self.peers_queue.qsize()}, known: {len(self.known_peers)}, working: {len(self.working_peers)}"
                )
            except asyncio.exceptions.TimeoutError:
                break
            finally:
                if peer is not None:
                    self.peers_queue.task_done()
            try:
                await self.get_peers(peer)
            except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
                raise
            except Exception:
                pass

    async def discover(self):
        # Repeat the discovery loop several times
        for _ in range(100):
            try:
                self.workers = [asyncio.create_task(self.worker()) for _ in range(500)]
                await asyncio.gather(*self.workers)
            except asyncio.exceptions.CancelledError:
                logging.info("Discovery cancelled")
                self.stop()
                await asyncio.gather(*self.workers, return_exceptions=True)
                while True:
                    try:
                        self.peers_queue.get_nowait()
                        self.peers_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                raise  # Bubbling the cancellation
            finally:
                await self.peers_queue.join()
                await self.save_peers()
                self.add_seed_peers(self.working_peers)

    def load_peers(self):
        logging.info("Loading peers from disk...")
        try:
            with open("known.pkl", "rb") as file:
                self.known_peers = pickle.load(file)
            with open("working.pkl", "rb") as file:
                self.working_peers = pickle.load(file)
        except FileNotFoundError:
            pass

    async def save_peers(self):
        logging.info("Saving peers to disk...")
        with open("known.pkl", "wb") as file:
            pickle.dump(self.known_peers, file)
        with open("working.pkl", "wb") as file:
            pickle.dump(self.working_peers, file)

    def stop(self):
        self.stop_discovery = True
