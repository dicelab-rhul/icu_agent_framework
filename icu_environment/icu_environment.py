__author__ = "cloudstrife9999"

from typing import List, Callable, Tuple
from multiprocessing import  Process
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from json import dumps, loads
from os import kill as kill_process
from signal import SIGKILL

from icu_agent.icu_agent import ICUManagerAgent
from icu_agent.icu_agent_factory import build_manager_agent
from icu_socket_utils import send_utf8_str, read_utf8_str
from icu_environment.icu_application_simulator import ICUApplicationSimulator
from icu_exceptions import ICUInconsistentStateException

from icu.event import Event

'''
Environment life cycle:

1) The configuration is loaded.
2) The server socket (w.r.t. agents) is initialised.
3) The ICU application simulator is created and booted, together with the eye tracker.
4) For each event generator group (see config file) a new agent is spawned.
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
    def __init__(self, target: Callable, args: tuple=()) -> None:
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
        except KeyboardInterrupt:
            print("Event dispatcher: killed by a keyboard interrupt.")
        except Exception as e:
            print("Event dispatcher: killed by {}.".format(e))

    def kill(self) -> None:
        # Python < 3.7 does not have multiprocess.Process.kill()
        if self.pid != None:
            kill_process(self.pid, SIGKILL)

class ICUAgentListener(Process):
    def __init__(self, target: Callable, args: tuple=()) -> None:
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
        except KeyboardInterrupt:
            print("Agent listener: killed by a keyboard interrupt.")
        except Exception as e:
            print("Agent listener: killed by {}.".format(e))

    def kill(self) -> None:
        # Python < 3.7 does not have multiprocess.Process.kill()
        if self.pid != None:
            kill_process(self.pid, SIGKILL)

class ICUEnvironment():
    def __init__(self, config: dict) -> None:
        self.__config: dict = config
        self.__manager_agents: List[ICUManagerAgent] = []
        self.__manager_agent_interfaces: dict = {}
        self.__server_socket: socket
        self.__init_server()
        self.__icu: ICUApplicationSimulator = ICUApplicationSimulator(verbose=self.__config["icu"]["verbose"])
        self.__icu.start()
        self.__build_agents()
        self.__agent_listeners: List[ICUAgentListener] = []
        self.__build_agent_listeners()
        self.__dispatcher: ICUEnvironmentDispatcher = ICUEnvironmentDispatcher(target=self.__pull_and_dispatch)
        self.__dispatcher.start()
        self.__wait()

    def __wait(self) -> None:
        try:
            while self.__icu.get_proc().is_alive():
                continue
        except KeyboardInterrupt:
            self.__clean_exit()
            print("Main environment process: killed by a keyboard interrupt.")
            return
        except Exception as e:
            self.__clean_exit()
            print("Main environment process: killed by {}.".format(e))
            return

    def __clean_exit(self) -> None:
        for listener in self.__agent_listeners:
            if listener is not None and listener.is_alive():
                listener.kill()

        self.__dispatcher.kill()

        for agent in self.__manager_agents:
            agent.kill()

        for s in self.__manager_agent_interfaces.values():
            s.close()

    def __init_server(self) -> None:
        try:
            s: socket = socket(AF_INET, SOCK_STREAM)
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            s.bind((self.__config["environment"]["env_binding_address"], self.__config["environment"]["env_port"]))
            s.listen(4) # TODO: magic number.

            self.__server_socket = s

            print("Environment started.\n")
        except KeyboardInterrupt:
            print("Main environment process: killed by a keyboard interrupt.")
        except IOError as e:
            self.__clean_exit()
            print("Main environment process: killed by {}.".format(e))

    def __build_agents(self) -> None:
        event_generator_groups: dict = self.__config["systems"]

        for k, v in event_generator_groups.items():
            env_interface: Tuple[str, int] = (self.__config["environment"]["env_hostname"], self.__config["environment"]["env_port"])
            verbose: bool = self.__config["agents"]["verbose_agents"]
            backup_previous_perceptions: bool = self.__config["agents"]["backup_previous_perceptions"]
            agent: ICUManagerAgent = build_manager_agent(managed_group=k, managed_group_info=v, env_interface=env_interface, verbose=verbose, backup_previous_perceptions=backup_previous_perceptions)
            self.__manager_agents.append(agent)

            # Note: there is no race condition here, because the agent will indefinitely retry to connect upon failure.
            agent.start()
            socket_with_agent, _ = self.__server_socket.accept()
            
            self.__manager_agent_interfaces[k] = socket_with_agent

    def __build_agent_listeners(self) -> None:
        for _, agent_interface in self.__manager_agent_interfaces.items():
            self.__agent_listeners.append(ICUAgentListener(target=self.__forward_feedback, args=[agent_interface]))

        for agent_listener in self.__agent_listeners:
            agent_listener.start()

    def __forward_feedback(self, agent_interface: socket) -> None:
        while True:
            raw: str = read_utf8_str(s=agent_interface)
            
            if raw is None or raw == "":
                continue

            feedback: dict = loads(s=raw)["details"]

            self.__icu.push_feedback(feedback=feedback)

    def __pull_and_dispatch(self) -> None:
        while True:
            event: Event = self.__icu.get_event()
            event_metadata: dict = self.__get_event_metadata(event=event)

            if self.__is_event_useless(event_metadata=event_metadata):
                continue

            event_data: dict = event.serialise()

            if event_metadata["src_group"] in ("eye_tracker", "highlight"):
                self.__broadcast_event(event_data=event_data, event_metadata=event_metadata)
            else:
                self.__notify_agent_with_event(event_data=event_data, event_metadata=event_metadata)

    def __is_event_useless(self, event_metadata: dict) -> bool:
        return event_metadata["src_group"] in ["empty", "unknown"]


    def __get_event_metadata(self, event: Event) -> dict:
        return {
            "event": "pull",
            "success": True,
            "src_group": self.__get_event_src_group(event=event),
            "src": self.__get_event_src(event=event)
        }

    def __get_event_src_group(self, event: Event) -> str:
        if event.src == "empty":
            return "empty"
        elif self.__is_highlighting_event(event=event):
            return "highlight"
        elif self.__is_pump_and_tank_system(event=event):
            return "pumps_and_tanks"
        elif self.__is_scale_system(event=event):
            return "scales"
        elif self.__is_tracking_widget(event=event):
            return "tracking_widget"
        elif self.__is_warning_light_system(event=event):
            return "warning_lights"
        elif self.__is_eye_tracking(event=event):
            return "eye_tracker"
        else:
            return "unknown"

    def __is_highlighting_event(self, event: Event) -> bool:
        return "Highlight" in event.src

    def __is_pump_and_tank_system(self, event: Event) -> bool:
        return event.src == "PumpEventGenerator" or "FuelTank" in event.src or "Pump" in event.src or "Pump" in event.dst

    def __is_scale_system(self, event: Event) -> bool:
        return event.src == "ScaleEventGenerator" or "Scale" in event.dst

    def __is_tracking_widget(self, event: Event) -> bool:
        return event.src == "TargetEventGenerator" or "TrackingWidget" in event.dst

    def __is_warning_light_system(self, event: Event) -> bool:
        return event.src == "WarningLightEventGenerator" or "WarningLight" in event.dst

    def __is_eye_tracking(self, event: Event) -> bool:
        return event.src == "EyeTrackerStub"

    def __get_event_src(self, event: Event) -> str:
        if self.__is_highlighting_event(event=event):
            return event.dst
        elif self.__is_pump_and_tank_system(event=event):
            return self.__extract_pumps_and_tanks_event_src(event=event)
        elif self.__is_scale_system(event=event):
            return event.dst
        elif self.__is_tracking_widget(event=event):
            return event.dst
        elif self.__is_warning_light_system(event=event):
            return event.dst
        elif self.__is_eye_tracking(event=event):
            return "eye_tracker"
        else:
            return "irrelevant"

    def __extract_pumps_and_tanks_event_src(self, event: Event) -> str:
        if "Pump" in event.src or "FuelTank" in event.src:
            return event.src
        elif "Pump" in event.dst:
            return event.dst
        else:
            raise ICUInconsistentStateException()

    def __broadcast_event(self, event_data: dict, event_metadata: dict) -> None:
        for _ in self.__manager_agent_interfaces:
            self.__notify_agent_with_event(event_data=event_data, event_metadata=event_metadata)

    def __notify_agent_with_event(self, event_data: dict, event_metadata: dict) -> None:
        perception_data: dict = {"data": event_data, "metadata": event_metadata}

        self.__notify_agent(perception_data=perception_data)

    def __notify_agent(self, perception_data: dict) -> None:
        src_group: str = perception_data["metadata"]["src_group"]

        if src_group in self.__manager_agent_interfaces:
            send_utf8_str(s=self.__manager_agent_interfaces[src_group], content=dumps(perception_data))
