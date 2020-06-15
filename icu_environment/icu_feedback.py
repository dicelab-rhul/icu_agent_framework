__author__ = "cloudstrife9999"

class ICUFeedback():
    def __init__(self, agent_id: str, dst: str, shape_to_display="red_box"):
        self._feedback: dict = {
            "agent": agent_id,
            "target": dst,
            "reason": None,
            "warning_to_diaplay": shape_to_display
        }

    def get(self) -> dict:
        return self._feedback
