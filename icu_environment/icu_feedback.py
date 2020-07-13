__author__ = "cloudstrife9999"



class ICUFeedback():
    def __init__(self, agent_id: str, dst: list, data: dict) -> None:
        self._feedback: dict = {"src": agent_id, "dst": dst, "data": data}

    def get(self) -> dict:
        return self._feedback

    @staticmethod
    def highlight(agent_id: str, dst: list) -> "ICUFeedback":
        dst = ["Highlight:{0}".format(d) for d in dst]
        return ICUFeedback(agent_id, dst, data=dict(label="highlight"))

    @staticmethod
    def arrow(agent_id: str, dst:str="Overlay:0") -> "ICUFeedback":
        raise NotImplementedError()