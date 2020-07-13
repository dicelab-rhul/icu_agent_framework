__author__ = "cloudstrife9999"

class ICUException(Exception):
    pass


class ICUAbstractMethodException(ICUException):
    def __init__(self) -> None:
        super().__init__("Abstract method.")


class ICUUnsupportedOperationException(ICUException):
    pass


class ICUInconsistentStateException(ICUException):
    def __init__(self) -> None:
        super().__init__("Inconsistent state.")
