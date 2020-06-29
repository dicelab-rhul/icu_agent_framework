__author__ = "cloudstrife9999"

from socket import socket, AF_INET, SOCK_STREAM
from json import loads
from multiprocessing import Process
from typing import Optional, Callable, Any
from time import sleep
from os import kill as kill_process
from signal import SIGKILL

from icu_agent.icu_agent_mind import ICUTeleoreactiveMind
from icu_agent.icu_actions import ICUAction
from icu_socket_utils import read_utf8_str, send_utf8_str


class ICUAgentProcess(Process):
    def __init__(self, agent_id: str, managed_generator: str, target: Optional[Callable[..., Any]]):
        super().__init__(target=target, group=None)

        self.__agent_id: str = agent_id
        self.__managed_generator: str = managed_generator

    def get_agent_id(self) -> str:
        return self.__agent_id

    def run(self) -> None:
        try:
            super().run()
        except KeyboardInterrupt:
            print("{} process: killed by a keyboard interrupt.".format(self.__agent_id))
        except Exception as e:
            print("{} {} (managing {}): stopped due to {}.".format(type(self).__name__, self.__agent_id, self.__managed_generator, e))

    def kill(self) -> None:
        # Python < 3.7 does not have multiprocess.Process.kill()
        if self.pid != None:
            kill_process(self.pid, SIGKILL)


class ICUAbstractAgent():
    def __init__(self, mind: ICUTeleoreactiveMind):
        self.__mind: ICUTeleoreactiveMind = mind

    def get_mind(self) -> ICUTeleoreactiveMind:
        return self.__mind

    def get_id(self) -> str:
        return self.__mind.get_id()

    def set_process(self, process: ICUAgentProcess) -> None:
        self.__process: ICUAgentProcess = process

    def get_process(self) -> ICUAgentProcess:
        return self.__process


class ICUManagerAgent(ICUAbstractAgent):
    def __init__(self, mind: ICUTeleoreactiveMind, actuators: list, sensors: list, env_hostname: str, env_port: int, verbose=False):
        super().__init__(mind=mind)

        self.__verbose: bool = verbose
        self.__finished: bool = False
        self.__env_hostname: str = env_hostname
        self.__env_port: int = env_port
        self.__env_socket: socket = socket(AF_INET, SOCK_STREAM)
        self.__connected: bool = False
        self.__sensors: list = sensors
        self.__actuators: list = actuators

    def get_env_hostname(self) -> str:
        return self.__env_hostname

    def get_env_port(self) -> int:
        return self.__env_port

    def kill(self) -> None:
        self.__finished = True

        if self.get_process() is not None:
            self.get_process().kill()

    def start(self) -> None:
        process: ICUAgentProcess = ICUAgentProcess(agent_id=self.get_id(), managed_generator=self.get_managed_group(), target=self.run)

        self.set_process(process=process)
        self.get_process().start()

    def __activate(self) -> None:
        while not self.__connected:
            try:
                sleep(0.5)
                self.__env_socket.connect((self.__env_hostname, self.__env_port))
                self.__connected = True
            except Exception as e:
                print(e)
                continue

        self.__actuators[0].activate(self.__env_socket)
        self.__sensors[0].activate(self.__env_socket)

    def run(self) -> None:
        try:
            self.__activate()

            print("Agent {} started! Ready to manage {}.".format(self.get_id(), self.get_managed_group()))

            cycle_number: int = 1

            while not self.__finished:
                cycle_number = self.__begin_new_cycle(cycle_number=cycle_number)
                self.__cycle_step(cycle_number=cycle_number)
        except KeyboardInterrupt:
            self.__env_socket.close()
            print("Agent {}: killed by a keyboard interrupt.".format(self.get_id()))
        except Exception as e:
            self.__env_socket.close()
            print("Agent {}: killed by {}.".format(self.get_id(), e))

    def __cycle_step(self, cycle_number: int) -> None:
        if cycle_number > 1:
            self.perceive()
            self.get_mind().revise()

        self.get_mind().decide()
        action: Optional[ICUAction] = self.get_mind().execute()

        if action != None:
            self.execute(action=action)
        elif self.__verbose:
            print("idle")

    def __begin_new_cycle(self, cycle_number: int) -> int:
        cycle_number += 1

        return cycle_number
    
    def get_managed_group(self) -> str:
        return self.get_mind().get_working_memory().get_belief().get_managed_group()

    def execute(self, action: ICUAction) -> None:
        print("Agent {} (managing {}): sending {} to the env.".format(self.get_id(), self.get_managed_group(), type(action)))

        self.__actuators[0].attempt(action)

    def perceive(self) -> None:
        done: bool = False

        while not done:
            raw: str = self.__sensors[0].perceive_one(timeout=1) # TODO: this is problematic. See TODO.md --> remove sockets.

            if raw == "":
                done = True
            else:
                if self.__verbose:
                    print("Agent {} (managing {}): received {}".format(self.get_id(), self.get_managed_group(), raw))
                
                perception: dict = loads(raw)
                
                self.get_mind().perceive(perception=perception)

    def get_listening_interface(self) -> socket:
        return self.__sensors[0].interface()


class ICUWorkerAgentSensor():
    def activate(self, socket_with_env: socket) -> None:
        self._socket_with_env = socket_with_env

    def perceive_one(self, timeout: int) -> str:
        return read_utf8_str(s=self._socket_with_env, read_timeout=timeout)

    def interface(self) -> socket:
        return self._socket_with_env


class ICUWorkerAgentActuator():
    def activate(self, socket_with_env: socket) -> None:
        self.__socket_with_env: socket = socket_with_env

    def attempt(self, action: ICUAction) -> None:
        raw: str = action.encode()
        send_utf8_str(s=self.__socket_with_env, content=raw)
