__author__ = "cloudstrife9999"

from multiprocessing import Process
from typing import Optional, Tuple
from time import sleep

from icu import start as start_application_simulator, ExternalEventSink, ExternalEventSource
from icu.event import Event
from icu.process import PipedMemory


class ICUApplicationSimulatorProcess(Process):
    def __init__(self, target, args):
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            super().run()
            #TODO: start the eye tracker.
        except Exception:
            print("{}: stopped.".format(type(self).__name__))


class ICUApplicationSimulator():
    def __init__(self):
        self.__source: ExternalEventSource = ExternalEventSource()
        self.__sink: ExternalEventSink = ExternalEventSink()
        self.__p: Optional[Process] = None
        self.__m: Optional[PipedMemory] = None

    def get_proc(self) -> Optional[Process]:
        return self.__p

    def get_mem(self) -> Optional[PipedMemory]:
        return self.__m

    def start(self, *args, **kwargs) -> None:
        self.__p, self.__m = start_application_simulator(sinks=[self.__sink], sources=[self.__source])

    def get_event(self) -> Event:
        if not self.__sink.empty():
            return self.__sink.get()

    '''
    def pull(self, expected_generator: str) -> object:
        if self.get_proc().is_alive():
            event: Event = None

            while event is None:
                event = sim.get_event()

            return event
    '''

    def has_data_to_pull(self, expected_generator: str) -> bool:
        return self.get_proc().is_alive()

    def push_feedback(self, feedback: dict) -> None:
        to_send: Tuple = (feedback["src"], feedback["dst"], feedback["data"])
        self.__source.source(src=to_send[0], dst=to_send[1], data=to_send[2])

        #print("Application simulator wrapper: received feedback: {}".format(feedback))


# THIS IS ONLY FOR DEBUG. THE REAL __main__ is in main.py.
if __name__ == "__main__":
    sim = ICUApplicationSimulator()
    sim.start()

    while sim.get_proc().is_alive():
        sleep(0.01)
        event: Event = None

        while event is None:
        #while event is None or event.src == "EyeTrackerStub":
        #while event is None or "Scale" not in event.src:
            event = sim.get_event()


        '''
        if event.src == "Pump":
            send_to_pump_subscriber()
        '''

        print(event)
