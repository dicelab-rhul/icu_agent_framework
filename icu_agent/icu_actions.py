__author__ = "cloudstrife9999"

from json import dumps

from icu_exceptions import ICUAbstractMethodException

class ICUAction():
    def __init__(self, name: str) -> None:
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

class ICUFeedbackAction(ICUAction):
    def __init__(self, feedback: dict) -> None:
        super().__init__("feed_back")
        self.__feedback: dict = feedback

    def get_details(self) -> dict:
        return self.__feedback

    @staticmethod
    def from_encoded_form(encoded: dict) -> "ICUFeedbackAction":
        feedback: dict = encoded["details"]["feedback"]

        return ICUFeedbackAction(feedback=feedback)
