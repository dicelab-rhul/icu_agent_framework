__author__ = "cloudstrife9999"

class ICURawPerception():
    def __init__(self, raw_perception_data: str, perception_metadata: dict):
        self.__raw_perception_data: str = raw_perception_data
        self.__perception_metadata: dict = perception_metadata

    def serialise(self) -> dict:
        return {"raw_data": self.__raw_perception_data, "metadata": self.__perception_metadata}

    def get_perception_data(self) -> str:
        return self.__raw_perception_data

    def get_perception_metadata(self) -> dict:
        return self.__perception_metadata
