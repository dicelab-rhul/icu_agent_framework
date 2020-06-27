__author__ = "cloudstrife9999"

class ICUFeedback():
    def __init__(self, agent_id: str, dst: str, shape_to_display="red_box"):
        self._feedback: dict = {
            "src": agent_id,
            "dst": dst, # TODO: the name of `dst` must match the ICU semantics, rather than the icu_agent_framework semantics. 
            "reason": None, # TODO: maybe use this field, or remove it completely.
            "data": {
                "warning_to_display": shape_to_display
            }
        }

    def get(self) -> dict:
        return self._feedback
