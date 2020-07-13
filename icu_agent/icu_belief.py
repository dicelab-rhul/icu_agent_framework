__author__ = "cloudstrife9999"

from sys import version_info

if version_info.major + version_info.minor / 10 < 3.7:
    from time import time
else:
    from time import time_ns as time

from icu_environment.icu_feedback import ICUFeedback
from icu_exceptions import ICUException, ICUAbstractMethodException


class ICUBelief():
    def __init__(self, agent_id: str, managed_group: str, managed_group_info: dict) -> None:
        # TODO: these are magic numbers. They  should be read via the shared memory, and customised for each widget.
        # TODO: check icu_gui_utils.icu_widgets for a tentative implementation of widget (and sub-widgets) coordinates.
        self._managed_group_left_border: int = 0
        self._managed_group_right_border: int = 800
        self._managed_group_top_border: int = 0
        self._managed_group_bottom_border: int = 600
        self._managed_group_center_x: int = 400
        self._managed_group_center_y: int = 300

        self.__agent_id: str = agent_id
        self._managed_group: str = managed_group
        self._managed_group_info: dict = managed_group_info
        self._managed_event_generators: list = self._unpack_event_generators()
        self._initial_state: dict = self._unpack_initial_state()
        self._current_state: dict = self._initial_state
        self.__grace_period_ns: int = self._managed_group_info["default_grace_period"]
        self.__latest_perception_data: dict = {}
        self.__latest_perception_metadata: dict = {}
        self.__latest_perception_messages: list = []
        self._visual_indicator_on: bool = False
        self.__non_compliant_since: int = 0
        self._user_eyes_location: tuple = (0, 0)

    def get_managed_group(self) -> str:
        return self._managed_group
        
    def register_new_perception(self, perception_data: dict, perception_metdata: dict) -> None:
        if perception_metdata and perception_data:
            self.__latest_perception_metadata = perception_metdata

            if self.__is_event_speech():
                speech: dict = {k: v for k, v in perception_data.items()}
                speech["message"] = perception_data["message"]

                self.__latest_perception_messages.append(speech)
            else:
                self.__latest_perception_data = perception_data

    def __is_event_speech(self) -> bool:
        return "event" in self.__latest_perception_metadata.keys() and self.__latest_perception_metadata["event"] == "speech"

    def reason(self) -> None:
        self._update_current_state()

    def get_agent_id(self) -> str:
        return self.__agent_id

    def get_latest_perception_data(self) -> dict:
        return self.__latest_perception_data

    def get_latest_perception_metadata(self) -> dict:
        return self.__latest_perception_metadata

    def get_backup(self) -> dict:
        return {
            "_id": time(),
            "data": self.__latest_perception_data,
            "metadata": self.__latest_perception_metadata,
            "received_messages": self.__latest_perception_messages
        }

    def _update_current_state(self) -> None:
        raise ICUAbstractMethodException()

    def generate_feedback(self, dst: list) -> None:
        agent_id: str = self.get_agent_id()
        feedback: ICUFeedback = ICUFeedback.highlight(agent_id=agent_id, dst=dst)
        self._set_next_feedback(feedback)

    def _set_next_feedback(self, feedback: ICUFeedback) -> None:
        self.__next_feedback = feedback
    
    def get_next_feedback(self) -> ICUFeedback:
        return self.__next_feedback

    def _unpack_event_generators(self) -> list:
        raise ICUAbstractMethodException()

    def _unpack_initial_state(self) -> dict:
        raise ICUAbstractMethodException()

    def is_visual_indicator_already_on(self) -> bool:
        return self._visual_indicator_on

    def grace_period_expired(self) -> bool:
        return time() > self.__non_compliant_since + self.__grace_period_ns

    # TODO: I am not sure this method works as intended.
    def is_user_looking(self) -> bool:
        x, y = self._user_eyes_location

        assert isinstance(x, int) and isinstance(y, int)

        # Remember that (0, 0) represents the top-left point.
        return x > self._managed_group_left_border and x < self._managed_group_right_border and y > self._managed_group_top_border and y < self._managed_group_bottom_border


class ICUWarningLightBelief(ICUBelief):
    def _unpack_event_generators(self) -> list:
        return [generator for generator in filter(lambda k: "light" in k, self._managed_group_info)]

    def _unpack_initial_state(self) -> dict:
        return {generator: self._managed_group_info[generator] for generator in self._managed_event_generators}

    def is_red_light_on(self) -> bool:
        return self._current_state["red_light"]["state"] == "on"

    def is_red_light_off(self) -> bool:
        return self._current_state["red_light"]["state"] == "off"

    def is_green_light_on(self) -> bool:
        return self._current_state["green_light"]["state"] == "on"

    def is_green_light_off(self) -> bool:
        return self._current_state["green_light"]["state"] == "off"

    def _update_current_state(self) -> None:
        latest_perception_metadata: dict = self.get_latest_perception_metadata()
        latest_perception_data: dict = self.get_latest_perception_data()

        if latest_perception_data is None or len(latest_perception_data.keys()) == 0: # We do not need to change the state.
            return

        # TODO: I am not sure this works as intended (i.e., what does the highlight event represent?)
        if latest_perception_metadata["src_group"] == "highlight":
            self._visual_indicator_on = not self._visual_indicator_on
        elif latest_perception_metadata["src_group"] == "eye_tracker":
            self._user_eyes_location = latest_perception_data["data"]["x"], latest_perception_data["data"]["y"]
        elif latest_perception_metadata["src_group"] == "warning_lights":
            self.__update_lights(perception_data=latest_perception_data["data"], src=latest_perception_metadata["src"])

    def __update_lights(self, perception_data: dict, src: str) -> None:
        if perception_data["label"] == "switch":
            if src == "WarningLight:0": # green light
                self._current_state["green_light"]["state"] = "off"
            elif src == "WarningLight:1": # green light
                self._current_state["red_light"]["state"] = "on"
        elif perception_data["label"] == "click":
            if src == "WarningLight:0": # green light
                self._current_state["green_light"]["state"] = "on"
            elif src == "WarningLight:1": # green light
                self._current_state["red_light"]["state"] = "off"

class ICUScaleBelief(ICUBelief):
    def _unpack_event_generators(self) -> list:
        return [generator for generator in filter(lambda k: "Scale" in k, self._managed_group_info)]

    def _unpack_initial_state(self) -> dict:
        return {generator: self._managed_group_info[generator] for generator in self._managed_event_generators}

    def is_too_low(self) -> bool:
        for scale in filter(lambda k: "Scale" in k, self._current_state):
            if self._current_state[scale]["state"] < 0: # TODO: I am not sure this is the right condition.
                return True
        return False

    def is_too_high(self) -> bool:
        for scale in filter(lambda k: "Scale" in k, self._current_state):
            if self._current_state[scale]["state"] > 0: # TODO: I am not sure this is the right condition.
                return True
        return False

    def is_out_of_bounds(self) -> bool:
        return self.is_too_high() or self.is_too_low()

    def get_all_scales_with_too_high_level(self) -> list:
        scales: list = []

        for scale in filter(lambda k: "Scale" in k, self._current_state):
            if self._current_state[scale]["state"] > 0: # TODO: I am not sure this is the right condition.
                scales.append(scale)

        return scales

    def get_all_scales_with_too_low_level(self) -> list:
        scales: list = []

        for scale in filter(lambda k: "Scale" in k, self._current_state):
            if self._current_state[scale]["state"] < 0: # TODO: I am not sure this is the right condition.
                scales.append(scale)

        return scales

    def _update_current_state(self) -> None:
        latest_perception_metadata: dict = self.get_latest_perception_metadata()
        latest_perception_data: dict = self.get_latest_perception_data()

        if latest_perception_data is None or len(latest_perception_data.keys()) == 0: # We do not need to change the state.
            return

        # TODO: I am not sure this works as intended (i.e., what does the highlight event represent?)
        if latest_perception_metadata["src_group"] == "highlight":
            self._visual_indicator_on = not self._visual_indicator_on
        elif latest_perception_metadata["src_group"] == "eye_tracker":
            self._user_eyes_location = latest_perception_data["data"]["x"], latest_perception_data["data"]["y"]
        elif latest_perception_metadata["src_group"] == "scales":
            self.__update_scales(perception_data=latest_perception_data["data"], src=latest_perception_metadata["src"])

    def __update_scales(self, perception_data: dict, src: str) -> None:
        if perception_data["label"] == "slide":
            self._current_state[src]["state"] += perception_data["slide"]
        elif perception_data["label"] == "click":
            self._current_state[src]["state"] = 0

class ICUPumpBelief(ICUBelief):
    def _unpack_event_generators(self) -> list:
        return [generator for generator in filter(lambda k: "pumps" in k or "tanks" in k, self._managed_group_info)]

    def _unpack_initial_state(self) -> dict:
        return {generator: self._managed_group_info[generator] for generator in self._managed_event_generators}

    def is_level_unacceptable(self) -> bool:
        for tank in filter(lambda tank: self._current_state["tanks"][tank]["state_matters"], self._current_state["tanks"]):
            if self._current_state["tanks"][tank] == "unacceptable":
                return True

        return False

    def get_tanks_with_unacceptable_level(self) -> list:
        return [filter(lambda tank: self._current_state["tanks"][tank]["state_matters"], self._current_state["tanks"])]

    def _update_current_state(self) -> None:
        latest_perception_metadata: dict = self.get_latest_perception_metadata()
        latest_perception_data: dict = self.get_latest_perception_data()

        if latest_perception_data is None or len(latest_perception_data.keys()) == 0: # We do not need to change the state.
            return

        # TODO: I am not sure this works as intended (i.e., what does the highlight event represent?)
        if latest_perception_metadata["src_group"] == "highlight":
            self._visual_indicator_on = not self._visual_indicator_on
        elif latest_perception_metadata["src_group"] == "eye_tracker":
            self._user_eyes_location = latest_perception_data["data"]["x"], latest_perception_data["data"]["y"]
        elif latest_perception_metadata["src_group"] == "pumps_and_tanks":
            self.__update_tanks(perception_data=latest_perception_data["data"], src=latest_perception_metadata["src"])

    def __update_tanks(self, perception_data: dict, src: str) -> None:
        if perception_data["label"] == "fuel":
            if perception_data["acceptable"] == "yes": # TODO: I am not sure the label semantics is correct.
                 self._current_state[src]["state"] = "acceptable"
            elif perception_data["acceptable"] == "no":
                self._current_state[src]["state"] = "unacceptable"

class ICUTrackingWidgetBelief(ICUBelief):
    def _unpack_event_generators(self) -> list:
        return [generator for generator in filter(lambda k: "target" in k, self._managed_group_info)]

    def _unpack_initial_state(self) -> dict:
        return {generator: self._managed_group_info[generator] for generator in self._managed_event_generators}

    def is_x_too_small(self) -> bool:
        return self._current_state["target"]["state"]["x"] < self._managed_group_center_x - self._current_state["target"]["max_acceptable_delta_x"]

    def is_x_too_big(self) -> bool:
        return self._current_state["target"]["state"]["x"] > self._managed_group_center_x + self._current_state["target"]["max_acceptable_delta_x"]

    def is_y_too_small(self) -> bool:
        return self._current_state["target"]["state"]["y"] < self._managed_group_center_y - self._current_state["target"]["max_acceptable_delta_y"]

    def is_y_too_big(self) -> bool:
        return self._current_state["target"]["state"]["y"] > self._managed_group_center_y + self._current_state["target"]["max_acceptable_delta_y"]

    def is_x_out_of_bounds(self) -> bool:
        return self.is_x_too_small() or self.is_x_too_big()

    def is_y_out_of_bounds(self) -> bool:
        return self.is_y_too_small() or self.is_y_too_big()

    def is_out_of_bounds(self, coordinate: str) -> bool:
        if coordinate == "x":
            return self.is_x_out_of_bounds()
        elif coordinate == "y":
            return self.is_y_out_of_bounds()
        else:
            raise ICUException("Unrecognised coordinate: {}.".format(coordinate))

    def is_something_out_of_bounds(self) -> bool:
        return self.is_x_out_of_bounds() or self.is_y_out_of_bounds()

    def _update_current_state(self) -> None:
        latest_perception_metadata: dict = self.get_latest_perception_metadata()
        latest_perception_data: dict = self.get_latest_perception_data()

        if latest_perception_data is None or len(latest_perception_data.keys()) == 0: # We do not need to change the state.
            return

        # TODO: I am not sure this works as intended (i.e., what does the highlight event represent?)
        if latest_perception_metadata["src_group"] == "highlight":
            self._visual_indicator_on = not self._visual_indicator_on
        elif latest_perception_metadata["src_group"] == "eye_tracker":
            self._user_eyes_location = latest_perception_data["data"]["x"], latest_perception_data["data"]["y"]
        elif latest_perception_metadata["src_group"] == "tracking_widget":
            self.__update_target(perception_data=latest_perception_data["data"])

    def __update_target(self, perception_data: dict) -> None:
        if perception_data["label"] == "move":
            self._current_state["target"]["state"]["x"] += perception_data["dx"]
            self._current_state["target"]["state"]["y"] += perception_data["dy"]

def build_icu_belief(agent_id: str, managed_group: str, managed_group_info: dict) -> ICUBelief:
    if managed_group == "scales":
        return ICUScaleBelief(agent_id=agent_id, managed_group=managed_group, managed_group_info=managed_group_info)
    elif managed_group == "pumps_and_tanks":
        return ICUPumpBelief(agent_id=agent_id, managed_group=managed_group, managed_group_info=managed_group_info)
    elif managed_group == "tracking_widget":
        return ICUTrackingWidgetBelief(agent_id=agent_id, managed_group=managed_group, managed_group_info=managed_group_info)
    elif managed_group == "warning_lights":
        return ICUWarningLightBelief(agent_id=agent_id, managed_group=managed_group, managed_group_info=managed_group_info)
    else:
        raise ICUException("Unsupported generator: {}.".format(managed_group))
