__author__ = "cloudstrife9999"

from icu_agent.icu_db_manager import ICUDBManager
from icu_agent.icu_belief import ICUBelief
from icu_agent.icu_agent_goal import ICUMindGoal
from icu_exceptions import ICUAbstractMethodException


class ICUMindWorkingMemory():
    def __init__(self, belief: ICUBelief,):
        self.init(belief=belief)      

    def init(self, belief: ICUBelief) -> None:
        self.__belief: ICUBelief = belief
        self.__goal: ICUMindGoal = ICUMindGoal()

    def get_belief(self) -> ICUBelief:
        return self.__belief

    def get_goal(self) -> ICUMindGoal:
        return self.__goal


class ICUMindStorage():
    def __init__(self, storage_type: str):
        self.__storage_type: str = storage_type

    def get_storage_type(self) -> str:
        return self.__storage_type

    def store(self, key_path: list, val) -> bool:
        raise ICUAbstractMethodException()

    def get(self, key_path: list) -> object:
        raise ICUAbstractMethodException()

    def replace(self, key_path: list, new_val) -> bool:
        raise ICUAbstractMethodException()

    def exists(self, key_path: list) -> bool:
        raise ICUAbstractMethodException()


class ICUMindInternalStorage(ICUMindStorage):
    def __init__(self):
        super().__init__(storage_type="internal")

        self.__storage = {}

    def store(self, key_path: list, val) -> bool:
        return self.__put(key_path=key_path[:-1], last_key=key_path[-1], val=val, overwrite=False)

    def get(self, key_path: list) -> object:
        if key_path is None or len(key_path) == 0:
            return False

        tmp: dict = self.__storage

        for key in key_path:
            if not tmp[key]:
                return None
            else:
                tmp = tmp[key]

        return tmp

    def replace(self, key_path: list, new_val) -> bool:
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

    def __put(self, key_path: list, last_key, val, overwrite: bool) -> bool:
        if key_path is None or last_key is None:
            return False
        
        tmp: dict = self.__storage

        for key in key_path:
            if not tmp[key]:
                tmp[key] = {}
                
            tmp = tmp[key]

        tmp[last_key] = val

        return True


class ICUMindExternalStorage(ICUMindStorage):
    def __init__(self, db_manager: ICUDBManager):
        super().__init__(storage_type="external")

        self.__db_manager = db_manager

    def store(self, key_path, val) -> bool:
        try:
            self.__db_manager.insert(self.__db_manager.get_collection_name(), val)

            return True
        except Exception:
            return False

    def get(self, query: dict) -> object:
        return self.__db_manager.get_results(self.__db_manager.get_collection_name(), query)

    def replace(self, query: dict, new_val) -> bool:
        try:
            self.__db_manager.update(self.__db_manager.get_collection_name(), query, new_val)

            return True
        except Exception:
            return False

    def exists(self, query: dict) -> bool:
        return self.__db_manager.count(self.__db_manager.get_collection_name(), query) != 0
