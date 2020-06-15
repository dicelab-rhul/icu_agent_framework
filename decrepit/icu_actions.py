__author__ = "cloudstrife9999"

from json import dumps

from icu_agent.icu_message import ICUMessage
from icu_exceptions import ICUAbstractMethodException


class ICUAction():
    def __init__(self, name: str):
        self.__name:  str = name

    def get_name(self) -> str:
        return self.__name

    def get_details(self) -> dict:
        raise ICUAbstractMethodException()

    def encode(self) -> str:
        return dumps(obj=self.encode_to_dict())

    def encode_to_dict(self) -> dict:
        return {
            "class_name": self.__class__.__name__,
            "name": self.get_name(),
            "details": self.get_details()
        }

    @staticmethod
    def from_encoded_form(encoded: dict) -> "ICUAction":
        return globals()[encoded["class_name"]].from_encoded_form(encoded=encoded)


class ICUPullAction(ICUAction):
    def __init__(self, expected_generator: str):
        super().__init__("pull")
        self.__details: dict = {"expected_generator": expected_generator}

    def get_details(self):
        return self.__details

    @staticmethod
    def from_encoded_form(encoded: dict) -> "ICUPullAction":
        expected_generator: str = encoded["details"]["expected_generator"]

        return ICUPullAction(expected_generator=expected_generator)


class ICUFeedbackAction(ICUAction):
    def __init__(self, feedback: dict):
        super().__init__("feed_back")
        self.__feedback = feedback

    def get_details(self):
        return self.__feedback

    @staticmethod
    def from_encoded_form(encoded: dict) -> "ICUFeedbackAction":
        feedback: dict = encoded["details"]["feedback"]

        return ICUFeedbackAction(feedback=feedback)

class ICUStayIdleAction(ICUAction):
    def __init__(self):
        super().__init__("stay_idle")

    def get_details(self):
        return {}

    @staticmethod
    def from_encoded_form(encoded: dict) -> "ICUStayIdleAction":
        return ICUStayIdleAction()


class ICUSpeakAction(ICUAction):
    def __init__(self, message: ICUMessage, recipient_ids: set):
        super().__init__("speak")
        self.__message: ICUMessage = message
        self.__recipient_ids: set = recipient_ids

    def get_details(self):
        message: object = self.__message.serialize()

        return {
            "message": message,
            "message_type": str(type(message)),
            "recipient_ids": self.__recipient_ids
        }

    @staticmethod
    def from_encoded_form(encoded: dict) -> "ICUSpeakAction":
        encoded_message: object = encoded["details"]["message"]
        recipient_ids: set = encoded["details"]["recipient_ids"]

        message: ICUMessage = ICUMessage(data=encoded_message)

        return ICUSpeakAction(message=message, recipient_ids=recipient_ids)
