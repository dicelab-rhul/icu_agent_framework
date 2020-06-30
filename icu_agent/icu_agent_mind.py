__author__ = "cloudstrife9999"

from icu_agent.icu_agent_goal import ICUMindGoal
from uuid import uuid4
from typing import Type, Optional

from icu_agent.icu_actions import ICUAction
from icu_agent.icu_memory import ICUMindStorage, ICUMindWorkingMemory
from icu_agent.icu_belief import ICUBelief, ICUPumpBelief, ICUScaleBelief, ICUWarningLightBelief, ICUTrackingWidgetBelief, build_icu_belief
from icu_exceptions import ICUAbstractMethodException


class ICUTeleoreactiveMind():
    def __init__(self, managed_group: str, managed_group_info: dict, storage: ICUMindStorage, backup_previous_perceptions: bool):
        self.__id = str(uuid4())
        self.__storage: ICUMindStorage = storage
        self.__working_memory: ICUMindWorkingMemory = self.__init_working_memory(managed_group=managed_group, managed_group_info=managed_group_info)
        self.__backup_previous_perceptions: bool = backup_previous_perceptions

    def __init_working_memory(self, managed_group: str, managed_group_info: dict) -> ICUMindWorkingMemory:
        belief: ICUBelief = build_icu_belief(agent_id=self.__id, managed_group=managed_group, managed_group_info=managed_group_info)
        
        return ICUMindWorkingMemory(belief=belief)

    def perceive(self, perception: dict) -> None:
        '''
        Updates the mind working memory with the new perception.
        '''
        data: dict = perception["data"]
        metadata: dict = perception["metadata"]

        self.__working_memory.get_belief().register_new_perception(perception_data=data, perception_metdata=metadata)

    def revise(self) -> None:
        '''
        Backs up the current perception for the future, and updates the mind belief.
        '''
        if self.__backup_previous_perceptions:
            self.__backup_current_perception()
        
        self.__working_memory.get_belief().reason()

    def __backup_current_perception(self) -> None:
        backup: dict = self.__working_memory.get_belief().get_backup()
        self.__storage.store([backup["_id"]], backup)

    def decide(self) -> None:
        '''
        Checks whether the goal has been accomplished, in which case, it decides to stay idle.
        Otherwise, the beliefs are queried, and the goal updated with the next action.
        '''
        raise ICUAbstractMethodException()

    def _consider_sending_feedback(self, belief: ICUBelief, goal: ICUMindGoal, dst: list=[]) -> None:
        if not belief.is_user_looking():
            self._generate_and_send_feedback(goal=goal, dst=dst)
        elif belief.grace_period_expired():
            self._generate_and_send_feedback(goal=goal, dst=dst)
        else:
            goal.stay_idle()

    def _generate_and_send_feedback(self, goal: ICUMindGoal, dst: list) -> None:
        self.__working_memory.get_belief().generate_feedback(dst=dst)

        feedback: dict = self.__working_memory.get_belief().get_next_feedback().get()

        goal.set_feedback(feedback=feedback)

    def execute(self) -> Optional[ICUAction]:
        '''
        Begins the execution process by returning the next action of the goal.
        '''
        return self.__working_memory.get_goal().get_next_action()

    def get_id(self) -> str:
        return self.__id

    def get_storage(self) -> ICUMindStorage:
        return self.__storage

    def get_working_memory(self) -> ICUMindWorkingMemory:
        return self.__working_memory

    def _cast_belief(self, belief: ICUBelief, real_type: Type) -> Type:
        if isinstance(belief, real_type):
            tmp: real_type = belief

            return tmp
        else:
            raise TypeError()

    def _is_perception_speech(self, metadata: dict) -> bool:
        return "event" in metadata.keys() and metadata["event"] == "speech"


class ICUTrackingWidgetMind(ICUTeleoreactiveMind):
    def __init__(self, managed_group, managed_group_info, storage, backup_previous_perceptions):
        super().__init__(managed_group, managed_group_info, storage, backup_previous_perceptions)

    def decide(self) -> None:
        belief: ICUTrackingWidgetBelief = self._cast_belief(belief=self.get_working_memory().get_belief(), real_type=ICUTrackingWidgetBelief)
        goal: ICUMindGoal = self.get_working_memory().get_goal()
        dst: list = ["Target:0"]

        if belief.is_visual_indicator_already_on():
            goal.stay_idle()
        elif belief.is_x_too_small():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=dst)
        elif belief.is_x_too_big():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=dst)
        elif belief.is_y_too_small():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=dst)
        elif belief.is_y_too_big():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=dst)
        else:
           goal.stay_idle()


class ICUScaleMind(ICUTeleoreactiveMind):
    def __init__(self, managed_group, managed_group_info, storage, backup_previous_perceptions):
        super().__init__(managed_group, managed_group_info, storage, backup_previous_perceptions)

    def decide(self) -> None:
        belief: ICUScaleBelief = self._cast_belief(belief=self.get_working_memory().get_belief(), real_type=ICUScaleBelief)
        goal: ICUMindGoal = self.get_working_memory().get_goal()

        if belief.is_visual_indicator_already_on():
            goal.stay_idle()
        elif belief.is_too_high():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=belief.get_all_scales_with_too_high_level())
        elif belief.is_too_low():
            self._consider_sending_feedback(belief=belief, goal=goal,  dst=belief.get_all_scales_with_too_low_level())
        else:
            goal.stay_idle()


class ICUPumpMind(ICUTeleoreactiveMind):
    def __init__(self, managed_group, managed_group_info, storage, backup_previous_perceptions):
        super().__init__(managed_group, managed_group_info, storage, backup_previous_perceptions)

    def decide(self) -> None:
        belief: ICUPumpBelief = self._cast_belief(belief=self.get_working_memory().get_belief(), real_type=ICUPumpBelief)
        goal: ICUMindGoal = self.get_working_memory().get_goal()

        if belief.is_visual_indicator_already_on():
            goal.stay_idle()
        elif belief.is_level_unacceptable():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=belief.get_tanks_with_unacceptable_level())
        else:
            goal.stay_idle()


class ICUWarningLightMind(ICUTeleoreactiveMind):
    def __init__(self, managed_group, managed_group_info, storage, backup_previous_perceptions):
        super().__init__(managed_group, managed_group_info, storage, backup_previous_perceptions)

    def decide(self) -> None:
        belief: ICUWarningLightBelief = self._cast_belief(belief=self.get_working_memory().get_belief(), real_type=ICUWarningLightBelief)
        goal: ICUMindGoal = self.get_working_memory().get_goal()

        if belief.is_visual_indicator_already_on():
            goal.stay_idle()
        elif belief.is_red_light_on():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=["WarningLight:1"])
        elif belief.is_green_light_off():
            self._consider_sending_feedback(belief=belief, goal=goal, dst=["WarningLight:0"])
        else:
            goal.stay_idle()
