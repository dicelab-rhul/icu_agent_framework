__author__ = "cloudstrife9999"

def highlight(agent_id: str, dst: list):
    
    return ICUFeedback(agent_id, dst, data=dict(label="highlight"))

def arrow(agent_id: str, dst:str="Overlay:0"):
    raise NotImplementedError()

class ICUFeedback():
    def __init__(self, agent_id: str, dst: list, data: dict):
        self._feedback: dict = {"src": agent_id, "dst": dst, "data": data}

    def get(self) -> dict:
        return self._feedback
