__author__ = "cloudstrife9999"

from typing import List, Iterator
from multiprocessing import  Process
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from json import dumps, loads
from sys import exit

from icu_agent.icu_agent import ICUManagerAgent
from icu_agent.icu_agent_factory import build_manager_agent
from icu_socket_utils import send_utf8_str, read_utf8_str
from icu_environment.icu_application_simulator import ICUApplicationSimulator

from icu.event import Event

'''
Environment life cycle:

1) The configuration is loaded.
2) The server socket (w.r.t. agents) is initialised.
3) For each event generator group (see config file) a new agent is spawned.
4) The ICU application simulator is created and booted, together with the eye tracker.
5) The agent listerner processes are created, one for each agent. They wait for feedback, and forward it to the ICU simulator
    - wait for feedback
    - send the received feedback to the ICU
6) The environment dispatcher is created, and put into a loop (see __pull_and_dispatch()):
    - pull an event
    - decode the event type
    - dispatch the event to its intended recipients
        - if the event comes from the eye tracker, or it is a highlight event, then it is broadcasted
        - otherwise, the event is only sent to the appropriate agent

'''

class ICUEnvironmentDispatcher(Process):
    def __init__(self, target, args=[]):
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
        except Exception:
            exit(-1) #TODO: implement a clean exit.

class ICUAgentListener(Process):
    def __init__(self, target, args=[]):
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
        except Exception:
            exit(-1) #TODO: implement a clean exit.

class ICUEnvironment():
    def __init__(self, config: dict) -> None:
        self.__config: dict = config
        self.__manager_agents: List[ICUManagerAgent] = []
        self.__manager_agent_interfaces: dict = {}
        self.__server_socket: socket
        self.__init_server()
        self.__build_agents()
        self.__agent_listeners: list = []
        self.__build_agent_listeners()
        self.__icu: ICUApplicationSimulator = ICUApplicationSimulator()
        self.__icu.start()
        self.__dispatcher: ICUEnvironmentDispatcher = ICUEnvironmentDispatcher(target=self.__pull_and_dispatch)
        self.__dispatcher.start()

    def __init_server(self) -> None:
        with socket(AF_INET, SOCK_STREAM) as s:
            try:
                s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                s.bind((self.__config["environment"]["hostname"], self.__config["environment"]["port"]))

                self.__server_socket = s

                print("Environment started.\n")
            except IOError:
                pass # TODO:

    def __build_agents(self) -> None:
        event_generator_groups: dict = self.__config["systems"]

        for k, v in event_generator_groups.items():
            agent: ICUManagerAgent = build_manager_agent(managed_group=k, managed_group_info=v, env_interface=(self.__config["environment"]["hostname"], self.__config["environment"]["port"]))
            self.__manager_agents.append(agent)

            # Note: there is no race condition here, because the agent will indefinitely retry to connect upon failure.
            agent.start()
            socket_with_agent, _ = self.__server_socket.accept()

            self.__manager_agent_interfaces[k] = socket_with_agent

    def __build_agent_listeners(self):
        for _, agent_interface in self.__manager_agent_interfaces.items():
            self.__agent_listeners.append(ICUAgentListener(target=self.__forward_feedback, args=[agent_interface]))

    def __forward_feedback(self, agent_interface: socket):
        raw: str = read_utf8_str(s=agent_interface)
        feedback: dict = loads(s=raw)

        assert "src" in feedback and "dst" in feedback and "data" in feedback

        self.__icu.push_feedback(feedback=feedback)


    def __pull_and_dispatch(self) -> None:
        while True:
            event: Event = self.__icu.get_event()
            event_generator_group: str = self.__get_event_generator_group(src=event.src, dst=event.dst)

            if event_generator_group in ("eye_tracker", "highlight"):
                self.__broadcast_event(event=event)
            else:
                self.__notify_agent_with_event(managed_group=event_generator_group, event=event)

    def __get_event_generator_group(self, src, dst) -> str:
        if "Highlight" in src:
            return "highlight"
        elif "FuelTank" in src or "FuelTankMain" in src or "Pump" in src:
            return "pumps_and_tanks"
        elif "Target" in dst:
            return "tracking_widget"
        elif "WarningLight" in src:
            return "warning_lights"
        elif "Scale" in src:
            return "scales"
        else:
            return "eye_tracker"

    def __broadcast_event(self, event: Event) -> None:
        for event_generator_group in self.__manager_agent_interfaces:
            self.__notify_agent_with_event(managed_group=event_generator_group, event=event)

    def notify_agent_with_events(self, managed_group: str, events: Iterator[Event]) -> None:
        for event in events:
            self.__notify_agent_with_event(managed_group=managed_group, event=event)

    def __notify_agent_with_event(self, managed_group: str, event: Event) -> None:
        event_data: dict = event.serialise()
        perception_data: dict = self.__build_perception_from_event(event_data=event_data, managed_group=managed_group)

        self.__notify_agent(managed_group=managed_group, perception_data=perception_data)

    def __build_perception_from_event(self, event_data: dict, managed_group: str) -> dict:
        return {"data": event_data, "metadata": {"event": "pull", "success": True, "src": managed_group}}

    def __notify_agent(self, managed_group: str, perception_data: dict) -> None:
        send_utf8_str(s=self.__manager_agent_interfaces[managed_group], content=dumps(perception_data))
