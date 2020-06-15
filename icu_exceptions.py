__author__ = "cloudstrife9999"

class ICUException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ICUAbstractMethodException(ICUException):
    def __init__(self):
        super().__init__("Abstract method.")


class ICUUnsupportedOperationException(ICUException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ICUInconsistentStateException(ICUException):
    def __init__(self):
        super().__init__("Inconsistent state.")
