__author__ = "cloudstrife9999"

class ICUMessage():
    def __init__(self, data: object):
        self.__data: object = data

    def serialize(self) -> object:
        # TODO: check that it is actually serialisable.
        return self.__data
