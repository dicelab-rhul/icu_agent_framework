__author__ = "cloudstrife9999"


from typing import Any

from icu_agent.icu_db_manager import ICUDBManager
from icu_agent.icu_belief import ICUBelief
from icu_agent.icu_agent_goal import ICUMindGoal
from icu_exceptions import ICUAbstractMethodException


class ICUMindWorkingMemory():
    def __init__(self, belief: ICUBelief) -> None:
        self.init(belief=belief)      

    def init(self, belief: ICUBelief) -> None:
        self.__belief: ICUBelief = belief
        self.__goal: ICUMindGoal = ICUMindGoal()

    def get_belief(self) -> ICUBelief:
        return self.__belief

    def get_goal(self) -> ICUMindGoal:
        return self.__goal


class ICUMindStorage():
    def __init__(self, storage_type: str) -> None:
        self.__storage_type: str = storage_type

    def get_storage_type(self) -> str:
        return self.__storage_type

    def store(self, key_path: list, val: Any) -> bool:
        raise ICUAbstractMethodException()

    def get(self, key_path: list) -> Any:
        raise ICUAbstractMethodException()

    def replace(self, key_path: list, new_val: Any) -> bool:
        raise ICUAbstractMethodException()

    def exists(self, key_path: list) -> bool:
        raise ICUAbstractMethodException()


class ICUMindInternalStorage(ICUMindStorage):
    def __init__(self) -> None:
        super().__init__(storage_type="internal")

        self.__storage = {}

    def store(self, key_path: list, val: Any) -> bool:
        return self.__put(key_path=key_path[:-1], last_key=key_path[-1], val=val, overwrite=False)

    def get(self, key_path: list) -> Any:
        if key_path is None or len(key_path) == 0:
            return False

        tmp: dict = self.__storage

        for key in key_path:
            if not tmp[key]:
                return None
            else:
                tmp = tmp[key]

        return tmp

    def replace(self, key_path: list, new_val: Any) -> bool:
        if key_path is None or len(key_path) == 0:
            return False

        return self.__put(key_path=key_path[:-1], last_key=key_path[-1], val=new_val, overwrite=True)

    def exists(self, key_path: list) -> bool:
        if key_path is None or len(key_path) == 0:
            return False

        tmp: dict = self.__storage

        for key in key_path:
            if not tmp[key]:
                return False
            else:
                tmp = tmp[key]

        return True

    def __put(self, key_path: list, last_key: str, val: Any, overwrite: bool) -> bool:
        if key_path is None or last_key is None:
            return False
        
        tmp: dict = self.__storage

        for key in key_path:
            if not tmp[key] or overwrite:
                tmp[key] = {}
                
            tmp = tmp[key]

        tmp[last_key] = val

        return True


class ICUMindExternalStorage(ICUMindStorage):
    def __init__(self, db_manager: ICUDBManager) -> None:
        super().__init__(storage_type="external")

        self.__db_manager: ICUDBManager = db_manager

    def store(self, key_path: list, val: Any) -> bool:
        try:
            # TODO: use key_path.
            self.__db_manager.insert(self.__db_manager.get_collection_name(), val)

            return True
        except Exception:
            return False

    def get(self, query: dict) -> Any:
        return self.__db_manager.get_results(self.__db_manager.get_collection_name(), query)

    def replace(self, query: dict, new_val: Any) -> bool:
        try:
            self.__db_manager.update(self.__db_manager.get_collection_name(), query, new_val)

            return True
        except Exception:
            return False

    def exists(self, query: dict) -> bool:
        return self.__db_manager.count(self.__db_manager.get_collection_name(), query) != 0
