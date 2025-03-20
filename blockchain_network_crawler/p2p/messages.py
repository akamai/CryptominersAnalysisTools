import struct
from enum import Flag, Enum
from time import time
import config
from psf import Section, Element, SERIALIZE_TYPE


class P2P_COMMANDS(Enum):
    # Base values for different command categories
    __BASE_P2P__ = 1000
    __BASE_CRYPTONOTE__ = 2000

    # P2P (Admin) Commands
    HANDSHAKE_REQUEST = __BASE_P2P__ + 1
    HANDSHAKE_RESPONSE = __BASE_P2P__ + 1
    TIMED_SYNC_REQUEST = __BASE_P2P__ + 2
    TIMED_SYNC_RESPONSE = __BASE_P2P__ + 2
    PING_REQUEST = __BASE_P2P__ + 3
    PING_RESPONSE = __BASE_P2P__ + 3
    STAT_INFO_REQUEST = __BASE_P2P__ + 4
    STAT_INFO_RESPONSE = __BASE_P2P__ + 4
    NETWORK_STATE_REQUEST = __BASE_P2P__ + 5
    NETWORK_STATE_RESPONSE = __BASE_P2P__ + 5
    PEER_ID_REQUEST = __BASE_P2P__ + 6
    PEER_ID_RESPONSE = __BASE_P2P__ + 6
    SUPPORT_FLAGS_REQUEST = __BASE_P2P__ + 7
    SUPPORT_FLAGS_RESPONSE = __BASE_P2P__ + 7

    # Cryptonote Protocol Commands
    NEW_BLOCK = __BASE_CRYPTONOTE__ + 1
    NEW_TRANSACTIONS = __BASE_CRYPTONOTE__ + 2
    REQUEST_GET_OBJECTS = __BASE_CRYPTONOTE__ + 3
    RESPONSE_GET_OBJECTS = __BASE_CRYPTONOTE__ + 4
    REQUEST_CHAIN = __BASE_CRYPTONOTE__ + 6
    RESPONSE_CHAIN_ENTRY = __BASE_CRYPTONOTE__ + 7
    NEW_FLUFFY_BLOCK = __BASE_CRYPTONOTE__ + 8
    REQUEST_FLUFFY_MISSING_TX = __BASE_CRYPTONOTE__ + 9


class LevinMessage:
    class LEVIN_FLAGS(Flag):
        Q = 1 << 0  # Request flag
        S = 1 << 1  # Response flag
        B = 1 << 2  # Beginning of fragmented message
        E = 1 << 3  # End of fragmented message

    SIGNATURE = 0x0101010101012101
    FMT = "<QQ?IIII"
    HEADER_SIZE = struct.calcsize(FMT)
    VERSION = 1

    def __init__(
        self,
        signature=SIGNATURE,
        length=0,
        e_response=False,
        command=P2P_COMMANDS.HANDSHAKE_REQUEST,
        return_code=0,
        flags=0,
        version=VERSION,
    ):
        self.signature = signature
        self.length = length
        self.e_response = e_response
        self.command = command
        self.return_code = return_code
        self.flags = flags
        self.version = version

    def serialize(self, data: bytes) -> bytes:
        self.length = len(data)
        header = struct.pack(
            "<QQBIIII",
            self.signature,
            self.length,
            int(self.e_response),
            self.command.value,
            self.return_code,
            self.flags.value if hasattr(self.flags, "value") else self.flags,
            self.version,
        )
        return header + data

    @classmethod
    def deserialize(cls, data: memoryview) -> "LevinMessage":
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Data is too small for Levin message")
        signature, length, e_response, command, return_code, flags, version = struct.unpack_from(
            "<QQBIIII", data
        )
        if signature != cls.SIGNATURE:
            raise ValueError("Invalid Levin signature.")
        if version != cls.VERSION:
            raise ValueError("Unsupported version")
        return cls(
            signature,
            length,
            bool(e_response),
            P2P_COMMANDS(command),
            return_code,
            flags,
            version,
        )

    def __repr__(self):
        return (
            f"<LevinMessage command={self.command}, flags={self.flags}, version={self.version}>"
        )


class P2P_Handshake(LevinMessage):
    def __init__(self, payload: bytearray | None = None):
        super().__init__(
            command=P2P_COMMANDS.HANDSHAKE_REQUEST,
            e_response=True,
            flags=LevinMessage.LEVIN_FLAGS.Q,
        )
        self.payload = payload
        if self.payload is None:
            handshake_section = self.generate()
            self.payload = handshake_section.serialize()

    def serialize(self) -> bytes:
        return super().serialize(self.payload)

    def generate(self) -> Section:
        global args
        # Build basic node data
        node_data = Section()
        node_data.add_element(
            "network_id",
            Element(
                bytes.fromhex(config.NETWORK_ID),
                SERIALIZE_TYPE.STRING,
            ),
        )
        node_data.add_element("peer_id", Element(int(time()), SERIALIZE_TYPE.UINT64))
        node_data.add_element("my_port", Element(18080, SERIALIZE_TYPE.UINT32))
        node_data.add_element("rpc_port", Element(0, SERIALIZE_TYPE.UINT16))
        node_data.add_element("rpc_credits_per_hash", Element(0, SERIALIZE_TYPE.UINT32))
        node_data.add_element("support_flags", Element(1, SERIALIZE_TYPE.UINT32))

        # CORE_SYNC_DATA
        payload_data = Section()
        payload_data.add_element("current_height", Element(1, SERIALIZE_TYPE.UINT64))
        payload_data.add_element("cumulative_difficulty", Element(1, SERIALIZE_TYPE.UINT64))
        payload_data.add_element("cumulative_difficulty_top64", Element(0, SERIALIZE_TYPE.UINT64))
        payload_data.add_element(
            "top_id",
            Element(
                bytes.fromhex("418015bb9ae982a1975da7d79277c2705727a56894ba0fb246adaabb1f4632e3"),
                SERIALIZE_TYPE.STRING,
            ),
        )
        payload_data.add_element("top_version", Element(1, SERIALIZE_TYPE.UINT8))
        payload_data.add_element("pruning_seed", Element(0, SERIALIZE_TYPE.UINT32))

        handshake = Section()
        handshake.add_element("node_data", Element(node_data))
        handshake.add_element("payload_data", Element(payload_data))
        return handshake


class P2P_SupportedFlags(LevinMessage):
    def __init__(self, payload: bytearray | None = None):
        super().__init__(
            command=P2P_COMMANDS.SUPPORT_FLAGS_RESPONSE,
            e_response=True,
            flags=LevinMessage.LEVIN_FLAGS.S,
        )
        self.payload = payload
        if self.payload is None:
            support_flags_section = self.generate()
            self.payload = support_flags_section.serialize()

    def serialize(self) -> bytes:
        return super().serialize(self.payload)

    def generate(self) -> Section:
        support_flags = Section()
        support_flags.add_element("my_port", Element(1, SERIALIZE_TYPE.UINT32))
        return support_flags
