import json
import struct
import ipaddress
from enum import IntEnum
from typing import Dict, Tuple
from time import time


class SERIALIZE_TYPE(IntEnum):
    UNKNOWN = 0
    INT64 = 1
    INT32 = 2
    INT16 = 3
    INT8 = 4
    UINT64 = 5
    UINT32 = 6
    UINT16 = 7
    UINT8 = 8
    DOUBLE = 9
    STRING = 10
    BOOL = 11
    OBJECT = 12
    ARRAY = 13
    ARRAY_FLAG = 0x80


class Element:
    def __init__(self, value, _type: int = SERIALIZE_TYPE.UNKNOWN):
        self._type = _type
        self.value = value

    def __iter__(self):
        return iter((self._type, self.value))


class PortableStorageEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Element):
            return obj.value
        if isinstance(obj, Section):
            return obj._storage  # let the Section decide how to serialize itself
        if isinstance(obj, bytearray):
            return obj.hex()
        return json.JSONEncoder.default(self, obj)


def int_to_ip(value):
    try:
        ip_addr = ipaddress.ip_address(value)
        if isinstance(ip_addr, ipaddress.IPv6Address):
            ip_addr = ip_addr.ipv4_mapped
        return str(ip_addr)
    except ValueError:
        return None


class Section:
    def __init__(self):
        self._storage: Dict[str, Element] = {}

    def fmt(self, _type: SERIALIZE_TYPE):
        match _type:
            case SERIALIZE_TYPE.INT64:
                return "q"
            case SERIALIZE_TYPE.INT32:
                return "i"
            case SERIALIZE_TYPE.INT16:
                return "h"
            case SERIALIZE_TYPE.INT8:
                return "b"
            case SERIALIZE_TYPE.UINT64:
                return "Q"
            case SERIALIZE_TYPE.UINT32:
                return "I"
            case SERIALIZE_TYPE.UINT16:
                return "H"
            case SERIALIZE_TYPE.UINT8:
                return "B"
            case SERIALIZE_TYPE.DOUBLE:
                return "d"
            case SERIALIZE_TYPE.BOOL:
                return "B"
        return None

    def auto_type(self, value) -> Element:
        _type = SERIALIZE_TYPE.UNKNOWN
        match value:
            case int() if value < 0:
                length = (value.bit_length() + 7) // 8 or 1
                match length:
                    case 1:
                        _type = SERIALIZE_TYPE.INT8
                    case 2:
                        _type = SERIALIZE_TYPE.INT16
                    case length if length in range(3, 5):
                        _type = SERIALIZE_TYPE.INT32
                    case length if length in range(5, 9):
                        _type = SERIALIZE_TYPE.INT64
            case int() if value >= 0:
                length = (value.bit_length() + 7) // 8 or 1
                match length:
                    case 1:
                        _type = SERIALIZE_TYPE.UINT8
                    case 2:
                        _type = SERIALIZE_TYPE.UINT16
                    case length if length in range(3, 5):
                        _type = SERIALIZE_TYPE.UINT32
                    case length if length in range(5, 9):
                        _type = SERIALIZE_TYPE.UINT64
            case float():
                _type = SERIALIZE_TYPE.DOUBLE
            case str():
                _type = SERIALIZE_TYPE.STRING
            case bytes():
                _type = SERIALIZE_TYPE.STRING
            case bool():
                _type = SERIALIZE_TYPE.BOOL
            case list() if value and all(isinstance(x, type(value[0])) for x in value):
                _type = self.auto_type(value[0])._type | SERIALIZE_TYPE.ARRAY_FLAG
            case Section():
                _type = SERIALIZE_TYPE.OBJECT
            case dict():
                _type = SERIALIZE_TYPE.OBJECT
                s = Section()
                for k, v in value.items():
                    s.add_element(k, v)
                value = s
        return Element(value, _type)

    def add_element(self, name: str, elem: Element):
        if elem._type == SERIALIZE_TYPE.UNKNOWN:
            elem = self.auto_type(elem.value)
        self._storage[name] = elem

    def pack_number(self, value: int, signed=False):
        length = (value.bit_length() + 7) // 8 or 1
        fmt = ""
        match length:
            case 1:
                fmt = "b" if signed else "B"
            case 2:
                fmt = "h" if signed else "H"
            case length if length in range(3, 5):
                fmt = "i" if signed else "I"
            case length if length in range(5, 9):
                fmt = "q" if signed else "Q"
        return struct.pack(fmt, value)

    def to_variant_number(self, value) -> Tuple[str, int]:
        fmt_list = ["B", "H", "I", "Q"]
        value <<= 2
        n_bytes = next((n for n in [1, 2, 4, 8]
                        if n >= ((value.bit_length() + 7) // 8 or 1)), None)
        size = [1, 2, 4, 8].index(n_bytes)
        value |= size
        return (fmt_list[size], value)

    def from_variant_number(self, data: memoryview) -> Tuple[int, int]:
        idx = data[0] & 0x3
        num = int.from_bytes(data[: [1, 2, 4, 8][idx]], byteorder="little") >> 2
        return num, [1, 2, 4, 8][idx]

    def _elem_serialize(self, _type, value):
        serialized_data = b""
        match _type:
            case _ if (_type & SERIALIZE_TYPE.ARRAY_FLAG) == SERIALIZE_TYPE.ARRAY_FLAG:
                serialized_data += struct.pack(*self.to_variant_number(len(value)))
                for v in value:
                    serialized_data += self._elem_serialize(_type & ~SERIALIZE_TYPE.ARRAY_FLAG, v)
            case SERIALIZE_TYPE.OBJECT:
                serialized_data += value._section_serialize()
            case SERIALIZE_TYPE.STRING:
                serialized_data += struct.pack(*self.to_variant_number(len(value)))
                serialized_data += struct.pack(f"{len(value)}s", value)
            case _:
                fmt = self.fmt(_type)
                if fmt:
                    serialized_data += struct.pack(fmt, value)
                else:
                    raise ValueError(f"Cannot serialize ({_type}, {value})")
        return serialized_data

    def _section_serialize(self):
        serialized_data = struct.pack(*self.to_variant_number(len(self._storage)))
        for key, elem in self._storage.items():
            _type, value = elem._type, elem.value
            serialized_data += struct.pack(f"B{len(key)}s", len(key), key.encode())
            serialized_data += struct.pack("B", _type)
            serialized_data += self._elem_serialize(_type, value)
        return serialized_data

    def serialize(self) -> bytes:
        partA = 0x01011101
        partB = 0x01020101
        version = 1
        serialized_data = struct.pack("IIB", partA, partB, version)
        serialized_data += self._section_serialize()
        return serialized_data

    def _elem_deserialize(self, _type, data: memoryview):
        offset = 0
        match _type:
            case _ if (_type & SERIALIZE_TYPE.ARRAY_FLAG) == SERIALIZE_TYPE.ARRAY_FLAG:
                n, o = self.from_variant_number(data[offset:])
                offset += o
                v = []
                for _ in range(n):
                    elem, o = self._elem_deserialize(_type & ~SERIALIZE_TYPE.ARRAY_FLAG, data[offset:])
                    v.append(elem)
                    offset += o
                return v, offset
            case SERIALIZE_TYPE.OBJECT:
                s = Section()
                offset += s._section_deserialize(data[offset:])
                return s, offset
            case SERIALIZE_TYPE.STRING:
                n, o = self.from_variant_number(data[offset:])
                offset += o
                s = data[offset: offset + n]
                offset += n
                return s, offset
            case _:
                fmt = self.fmt(_type)
                if fmt:
                    size = struct.calcsize(fmt)
                    v = struct.unpack_from(fmt, data, offset)[0]
                    offset += size
                    return v, offset
                else:
                    raise ValueError(f"Cannot deserialize ({_type}, {data[offset:]})")

    def _section_deserialize(self, data: memoryview):
        n_elem, offset = self.from_variant_number(data)
        for _ in range(n_elem):
            key_len = data[offset]
            offset += 1
            key_name, _type = struct.unpack_from(f"{key_len}sB", data, offset)
            offset += key_len + 1
            v, o = self._elem_deserialize(_type, data[offset:])
            offset += o
            # monero‐specific adjustments:
            if key_name == b"m_ip":
                v = int_to_ip(v)
            elif key_name == b"id" and isinstance(v, int):
                v = v.to_bytes(8, "little").hex()
            elif key_name == b"addr" and _type == SERIALIZE_TYPE.STRING:
                v = int_to_ip(v.tobytes())
            elif _type == SERIALIZE_TYPE.STRING:
                string = ""
                try:
                    string = v.tobytes().decode()
                except UnicodeDecodeError:
                    pass
                v = v.hex() + " (" + string + ")"
            self.add_element(key_name.decode(), Element(v, _type))
        return offset

    def deserialize(self, value: bytearray):
        assert isinstance(value, bytearray), f"Expected bytearray, got {type(value).__name__}"
        data = memoryview(value)
        offset = 0
        if len(data) < 10:
            return 0
        partA, partB, version = struct.unpack_from("IIB", data)
        offset += struct.calcsize("IIB")
        if partA != 0x01011101 or partB != 0x01020101 or version != 1:
            print("Not valid portable storage format header")
            return offset
        offset += self._section_deserialize(data[offset:])
        return offset

    def get(self, key: str, default=None, get_elem=False):
        try:
            if get_elem:
                return self._storage[key]
            else:
                return self._storage[key].value
        except KeyError:
            return default

    def __str__(self):
        return json.dumps(self._storage, cls=PortableStorageEncoder)

    def __getitem__(self, key: str):
        return self._storage[key].value

    def __setitem__(self, key: str, elem: Element):
        self._storage[key] = elem

    def __delitem__(self, key: str):
        del self._storage[key]
