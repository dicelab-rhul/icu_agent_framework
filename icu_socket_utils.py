__author__ = "cloudstrife9999"

from socket import socket, timeout
from struct import pack, unpack


def send_utf8_str(s: socket, content: str) -> bool:
    try:
        l: int = len(content)
        length: bytes = pack(">I", l)
        ll: int = len(length)
        l_length: bytes = pack("b", ll)
        data: bytes = bytes(content, "utf-8")

        s.send(l_length)
        s.send(length)
        s.send(data)

        return True
    except Exception:
        return False


def read_utf8_str(s: socket, read_timeout: int=-1) -> str:
    try:
        if read_timeout != -1:
            s.settimeout(read_timeout)

        l_length: bytes = s.recv(1)
        ll: int = unpack("b", l_length)[0]
        length: bytes = s.recv(ll)
        l: int = unpack(">I", length)[0]
        data: bytes = s.recv(l)

        return data.decode("utf-8")
    except timeout:
        return ""
