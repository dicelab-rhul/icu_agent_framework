from icu_exceptions import ICUAbstractMethodException


class ICUEventPerception():
    def __init__(self, raw_event: str, metadata: dict):
        self._raw_event: str = raw_event
        self._metadata: dict = metadata
        self._parse()

    def _parse(self) -> None:
        raise ICUAbstractMethodException()

    def get_generator_name(self) -> str:
        return ""

    def get_timestamp(self) -> int:
        return -1

    def get_event_type(self) -> str:
        return ""

    def serialise(self) -> dict:
        raise ICUAbstractMethodException()


class ICUTrackingWidgetEventPerception(ICUEventPerception):
    def __init__(self, raw_event: str, metadata: dict):
        super().__init__(raw_event, metadata)

    def _parse(self) -> None:
        # Should not be needed (old code).
        pass

    def get_delta_x(self) -> int:
        return -1

    def get_delta_y(self) -> int:
        return -1

    def serialise(self) -> dict:
        return {"data": self._raw_event, "metadata": self._metadata}


class ICUWarningLightEventPerception(ICUEventPerception):
    def __init__(self, raw_event: str, metadata: dict):
        super().__init__(raw_event, metadata)

    def _parse(self) -> None:
        # Should not be needed (old code).
        pass

    def get_light_status(self) -> str:
        return ""

    def serialise(self) -> dict:
         return {"data": self._raw_event, "metadata": self._metadata}


class ICUScaleEventPerception(ICUEventPerception):
    def __init__(self, raw_event: str, metadata: dict):
        super().__init__(raw_event, metadata)

    def _parse(self) -> None:
        # Should not be needed (old code).
        pass

    def get_scale_delta(self) -> int:
        return -1

    def serialise(self) -> dict:
         return {"data": self._raw_event, "metadata": self._metadata}


class ICUPumpEventPerception(ICUEventPerception):
    def __init__(self, raw_event: str, metadata: dict):
        super().__init__(raw_event, metadata)

    def _parse(self) -> None:
       # Should not be needed (old code).
        pass

    def get_transferred_amount(self) -> float:
        return -1.0

    def serialise(self) -> dict:
        return {"data": {}, "metadata": {}}

class ICUSpeechEventPerception(ICUEventPerception):
    def __init__(self, raw_event: str, metadata: dict):
        super().__init__(raw_event, metadata)

    def _parse(self) -> None:
        # Should not be needed (old code).
        pass

    def serialise(self) -> dict:
         return {"data": self._raw_event, "metadata": self._metadata}