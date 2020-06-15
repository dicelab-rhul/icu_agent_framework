from socket import socket

from typing import Iterator

from icu_socket_utils import read_utf8_str


class ICUSensor():
    def activate(self, socket_with_env: socket) -> None:
        self._socket_with_env = socket_with_env

    def perceive(self, timeout: int) -> str:
        return read_utf8_str(s=self._socket_with_env, read_timeout=timeout)

    def perceive_n(self, limit, timeout: int) -> Iterator:
        for _ in range(limit):
            yield self.perceive(timeout=timeout)

    # This is risky, as it will likely never terminate if there are many events.
    def perceive_all(self, timeout: int) -> Iterator:
        while True:
            yield self.perceive(timeout=timeout)

    def interface(self) -> socket:
        return self._socket_with_env