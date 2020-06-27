__author__ = "cloudstrife9999"


from multiprocessing import Process
from typing import Optional, Tuple, Iterator
from time import sleep
from contextlib import redirect_stdout
from sys import version_info
from os import devnull

if version_info.major + version_info.minor / 10 < 3.7:
    from time import time
else:
    from time import time_ns as time

from icu import start as start_application_simulator, ExternalEventSink, ExternalEventSource
from icu.event import Event
from icu.process import PipedMemory

# BEGIN OF POTENTIALLY UNNEDED CODE #

from psychopy.iohub import launchHubServer

class EyeTrackerProcess(Process):
    def __init__(self, target, args=[]):
        super().__init__(target=target, args=args, group=None)

    def run(self) -> None:
        try:
            self.__run_eye_tracker()
        except Exception:
            print("{}: stopped.".format(type(self).__name__))


    def __run_eye_tracker(self, duration=5, calibrate_system=True, sample_rate=40) -> None:
         with self.__connect_eyetracker(sample_rate=sample_rate) as io:
            tracker = io.devices.tracker
            
            if calibrate_system:
                self.__calibrate(tracker)
            
            for event in self.__stream(tracker, duration):
                print(event) #do some stuff


    def __connect_eyetracker(self, sample_rate = 300):    
        iohub_config = {'eyetracker.hw.tobii.EyeTracker':
            {'name': 'tracker',
            'runtime_settings': {'sampling_rate': sample_rate}}
            }
        
        io = launchHubServer(**iohub_config)    

        return io

    def __calibrate(self, tracker) -> None:
        r = tracker.runSetupProcedure()
        
        if r:
            print('calibration success')
        else:
            print('calibration unsuccessful')

    def __stream(self, tracker, duration) -> Iterator:
        tracker.setRecordingState(True)

        stime = time()
        while time()-stime < duration:
            for e in tracker.getEvents(asType='dict'):
                #logic to remove bad samples
                yield (e['left_gaze_x'], e['left_gaze_y'], e['time'])

# END OF POTENTIALLY UNNEDED CODE #

class ICUApplicationSimulator():
    def __init__(self, verbose=False):
        self.__verbose: bool = verbose
        self.__source: ExternalEventSource = ExternalEventSource()
        self.__sink: ExternalEventSink = ExternalEventSink()
        self.__p: Optional[Process] = None
        self.__m: Optional[PipedMemory] = None

    def get_proc(self) -> Optional[Process]:
        return self.__p

    def get_mem(self) -> Optional[PipedMemory]:
        return self.__m

    def start(self, *args, **kwargs) -> None:
        if self.__verbose:
            self.__p, self.__m = start_application_simulator(sinks=[self.__sink], sources=[self.__source])
        else:
            with open(devnull, "w") as f:
                with redirect_stdout(f):
                    self.__p, self.__m = start_application_simulator(sinks=[self.__sink], sources=[self.__source])

    def get_event(self) -> Event:
        if self.__sink.empty():
            return Event.empty_event()
        else:
            return self.__sink.get()

    def push_feedback(self, feedback: dict) -> None:
        # This is to prevent a race condition.
        while self.__p is None:
            continue

        to_send: Tuple = (feedback["src"], feedback["dst"], feedback["data"])

        print("Sending {} to ICU.".format(feedback))

        self.__source.source(src=to_send[0], dst=to_send[1], data=to_send[2])


# THIS IS ONLY FOR DEBUG. THE REAL __main__ is in main.py.
if __name__ == "__main__":
    sim = ICUApplicationSimulator()
    sim.start()

    while sim.get_proc().is_alive():
        sleep(0.01)
        event: Event = None

        while event is None:
            event = sim.get_event()

        print(event)
