import asyncio
import logging
from p2p.messages import LevinMessage


class LevinProtocol:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None

    async def connect_async(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout=5
            )
            return True
        except asyncio.TimeoutError as e:
            logging.debug(f"Connection to {self.ip}:{self.port} timed out: {e}")
        except ConnectionResetError as e:
            logging.debug(f"Connection reset {self.ip}:{self.port}: {e}")
        except Exception as e:
            logging.debug(f"Error connecting to {self.ip}:{self.port}: {e}")
            raise e
        return False

    async def send_async(self, message: LevinMessage) -> None:
        if self.writer:
            self.writer.write(message.serialize())
            await self.writer.drain()

    async def get_message_async(self):
        if self.reader:
            try:
                header_data = await asyncio.wait_for(
                    self.reader.readexactly(LevinMessage.HEADER_SIZE), timeout=5
                )
                header = LevinMessage.deserialize(memoryview(header_data))
                payload = await asyncio.wait_for(
                    self.reader.readexactly(header.length), timeout=5
                )
                return header, payload
            except asyncio.IncompleteReadError:
                logging.debug(f"Incomplete read from {self.ip}:{self.port}")
        return None, None

    async def close(self) -> None:
        if self.writer:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), timeout=3)

    async def __aenter__(self):
        if await self.connect_async():
            return self
        return None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.close()
        except Exception as e:
            logging.debug(f"Error closing connection to {self.ip}:{self.port}: {e}")
            raise e
