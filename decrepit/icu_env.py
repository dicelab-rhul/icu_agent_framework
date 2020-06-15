__author__ = "cloudstrife9999"


'''
THIS CLASS IS A RELIC OF OLD TIMES.
SOONER OR LATER A MERCILESS GARBAGE COLLECTOR WILL REAP IT AWAY...
'''

from multiprocessing import Process, Queue
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from json import dumps, loads
from typing import Iterable, Iterator

from icu_agent.icu_agent import ICUManagerAgent
from icu_agent.icu_agent_factory import ICUAgentFactory
from icu_environment.icu_application_simulator import ICUApplicationSimulator
from icu_exceptions import ICUException
from icu_socket_utils import read_utf8_str, send_utf8_str

from icu.event import Event

class ICUActionManager(Process):
    def __init__(self, target, args):
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
        except Exception:
            print("{} action manager: stopped.".format(type(self).__name__))


class ICUEventManager(Process):
    def __init__(self, target, args):
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
        except Exception:
            print("{} event manager: stopped.".format(type(self).__name__))

class ICUEnvironment():
    def __init__(self, host: str="127.0.0.1", port: int=1890, event_generator_names: list=[]):
        self.__event_generator_names: list = event_generator_names
        self.__agent_pool: list = []
        self.__agent_managers: list = []
        self.__event_queues: dict = {}
        self.__event_manager: ICUEventManager
        self.__host: str = host
        self.__port: int = port
        self.__start_application_simulator()
        self.__stop: bool = False
        self.__initial_state: dict = {}

    @staticmethod
    def from_state(state: dict) -> "ICUEnvironment":
        host: str = state["environment"]["hostname"]
        port: int = state["environment"]["port"]
        event_generator_names: list = state["environment"]["event_generator_names"]

        return ICUEnvironment(host=host, port=port, event_generator_names=event_generator_names)

    def get_event_generator_names(self) -> list:
        return self.__event_generator_names

    def get_agent_pool(self) -> list:
        return self.__agent_pool

    def get_hostname(self) -> str:
        return self.__host

    def get_port(self) -> int:
        return self.__port

    def get_initial_state(self) -> dict:
        return self.__initial_state

    def __start_application_simulator(self) -> None:
        self.__application_simulator: ICUApplicationSimulator = ICUApplicationSimulator()
        self.__application_simulator.start()

    def __pull_and_multiplex(self) -> None:
        while not self.__stop:
            event: Event = self.__application_simulator.get_event()
            event_generator: str = self.__extract_event_generator(src=event.src, dst=event.dst)
            
            if event_generator not in self.__event_queues:
                self.__event_queues[event_generator] = Queue()

            self.__event_queues[event_generator].put()

    def __extract_event_generator(self, src, dst) -> str:
        if "FuelTank" in src or "Pump" in src:
            return "Pump"
        elif "Target" in dst:
            return "TrackingWidget"
        elif "WarningLight" in src:
            return "WarningLight"
        elif "Scale" in src:
            return "Scale"
        else:
            return "EyeTracker"
            

    def __loop(self, server_socket: socket) -> None:
        self.__event_manager = ICUEventManager(target=self.__pull_and_multiplex, args=[])

        while not self.__stop:
            server_socket.listen()
            conn, _ = server_socket.accept()

            # As Python does not support parallel execution with threads, we use processes instead.
            # Each process handles the connection with one agent.
            p: ICUActionManager = ICUActionManager(target=self.__manage_agent, args=(conn,))

            self.__agent_managers.append(p)
            
            p.start()

        print("Environment: not proceeding with the loop.")

    def init_server_socket(self) -> None:
        with socket(AF_INET, SOCK_STREAM) as s:
            try:
                s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                s.bind((self.__host, self.__port))

                print("Environment started.\n")

                try:
                    self.__loop(server_socket=s)
                except KeyboardInterrupt:
                    self.__interrupt_and_cleanup(s=s)
                    print("Environment stopped.")
            except Exception as e:
                self.__interrupt_and_cleanup(s=s)
                print("\nThe environment just crashed due to an uncatched '%s'. Bye!" % e)

    def __interrupt_and_cleanup(self, s: socket) -> None:
        self.__stop = True
        self.__kill_agent_managers()
        
        s.close()

    def  __kill_agent_managers(self) -> None:
        for agent_manager in self.__agent_managers:
            agent_manager.kill()
            
            while agent_manager.is_alive():
                continue

    def init_agent_pool(self, event_generators_initial_state: dict) -> None:
        self.__initial_state = event_generators_initial_state

        for event_generator in event_generators_initial_state["event_generators"]:
            name: str = event_generator["name"]
            event_generator_initial_state: dict = event_generator["state"]
            agent: ICUManagerAgent = ICUAgentFactory.build_agent(event_generator_initial_state, self.__host, self.__port, name)
            
            self.__agent_pool.append(agent)
        
        self.__start_agents()

    def init_agent_pool_from_state(self, state: dict) -> None:
        self.__initial_state = state["environment"]["initial_state"]

        for agent_state in state["agents"]:
            agent: ICUManagerAgent = ICUManagerAgent.from_state(agent_state=agent_state)
            self.__agent_pool.append(agent)

        self.__start_agents()

    def __start_agents(self) -> None:
        for agent in self.__agent_pool:
            agent.start()

    def __manage_agent(self, client_socket: socket) -> None:
        while True:
            action: dict = self.__decode_action(client_socket=client_socket)
            name: str = "_" + type(self).__name__ + "__" + action["name"]
            data, metadata = getattr(self, name)(action)

            self.__notify_agent(data, metadata, client_socket)

    def __decode_action(self, client_socket: socket) -> dict:
        while True:
            raw: str = read_utf8_str(s=client_socket)

            if raw != "":
                break
        
        return loads(raw)

    def __notify_agent(self, data: object, metadata: dict, client_socket: socket) -> None:
        if isinstance(data, Iterator):
            for datum in data:
                perception: dict = {"metadata": metadata, "data": datum}
                serialised: str = dumps(obj=perception)
                # Sends the serialised event to the socket of the sensor
                send_utf8_str(s=client_socket, content=serialised)
        else:
            perception: dict = {"metadata": metadata, "data": data}
            serialised: str = dumps(obj=perception)
            # Sends the serialised event to the socket of the sensor
            send_utf8_str(s=client_socket, content=serialised)


    def __pull(self, action: dict) -> Iterator:
        expected_generator: str = action["details"]["expected_generator"]

        if ":" in expected_generator:
            expected_generator = expected_generator.split(":")[0]

        #pulled_data: object = self.__application_simulator.pull(expected_generator=expected_generator)
        for q in self.__event_queues["EyeTracker"], self.__event_queues[expected_generator]:
            if not q.empty():
                yield (q.get(), {"event": "pull", "success": True})

    def __feed_back(self, action: dict) -> tuple:
        feedback: dict = action["details"]
        self.__application_simulator.push_feedback(feedback=feedback)

        return ({}, {"event": "feedback", "fed_back": 1})

    def __stay_idle(self, action: dict) -> tuple:
        return ({}, {"event": "idle"})

    def __speak(self, action: dict) -> tuple:
        message: object = action["details"]["message"]
        recipient_ids: set = action["details"]["recipient_ids"]

        if isinstance(message, str):
            return self.__tell_string(message=message, recipient_ids=recipient_ids)
        elif isinstance(message, (list, set, dict)):
            return self.__tell_json(message=message, recipient_ids=recipient_ids)
        else:
            return ({}, {"event": "speech", "message": message, "recipients": recipient_ids, "success": False, "reason": "unsupported message type"})

    def __tell_string(self, message: str, recipient_ids: set) -> tuple:
        try:
            for agent in self.__get_speech_recipients(recipient_ids=recipient_ids):
                self.__notify_agent(data={"message": message}, metadata={"event": "speech"}, client_socket=agent.get_listening_interface())

            return ({}, {"event": "speech", "message": message, "recipients": recipient_ids, "success": True})
        except Exception as e:
            #TODO: measure the success at the agent granularity (rather than all-or-nothing).
            return ({}, {"event": "speech", "message": message, "recipients": recipient_ids, "success": False, "reason": str(e)})

    def __tell_json(self, message: object, recipient_ids: set) -> tuple:
        m: dict = {}

        if isinstance(message, dict):
            m = message
        elif isinstance(message, (list, set)):
            m["parts"] = []

            for elm in m:
                m["parts"].append(elm)

        return self.__tell_string(message=dumps(m), recipient_ids=recipient_ids)

    def __get_speech_recipients(self, recipient_ids: set) -> Iterable[ICUManagerAgent]:
        return filter(lambda agent: agent.get_id() in recipient_ids, self.__agent_pool)
