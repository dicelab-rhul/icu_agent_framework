__author__ = "cloudstrife9999"

from typing import Optional

from icu_agent.icu_actions import ICUAction, ICUFeedbackAction


class ICUMindGoal():
    def __init__(self) -> None:
        self._need_to_feedback: bool = False
        self.__feedback: dict = {}
        self.__next_action: Optional[ICUAction] = None

    def set_feedback(self, feedback: dict) -> None:
        self.__feedback: dict = feedback

        if self.can_feedback():
            self.__next_action = ICUFeedbackAction(feedback=feedback)
        else:
            self.__next_action = None

    def get_feedback(self) -> dict:
        return self.__feedback

    def can_feedback(self) -> bool:
        return len(self.__feedback) > 0

    def get_next_action(self) -> Optional[ICUAction]:
        return self.__next_action

    def stay_idle(self) -> None:
        self.set_feedback(feedback={})
