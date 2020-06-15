__author__ = "cloudstrife9999"

from pymongo import MongoClient
from json import load


class ICUDBManager():
    def __init__(self, config_file_path: str):
        self.__config_file_path: str = config_file_path
        self.__db_name: str = ""
        self.__collection: str = ""
        self.__client: MongoClient = self.__get_connection()

    def __get_connection(self) -> MongoClient:
        info: tuple = self.__load_db_info(json_file_path=self.__config_file_path)

        self.__db_name = info[2]
        self.__collection = info[3]

        return MongoClient(host=info[0], port=int(info[1]), username=info[4], password=info[5], authMechanism="SCRAM-SHA-256")

    @staticmethod
    def __load_db_info(json_file_path: str) -> tuple:
        try:
            with open(json_file_path) as i_f:
                data: dict = load(i_f)

                return data["hostname"], data["port"], data["db_name"], data["collection"], data["username"], data["password"]
        except Exception:
            raise IOError()

    def get_results(self, collection, query):
        return self.__client[self.__db_name][collection].find(query)

    def count(self, collection, query):
        return self.__client[self.__db_name][collection].count(query)

    def insert(self, collection, to_insert: dict) -> None:
        self.__client[collection].inert_one(to_insert)

    def insert_all(self, collection, to_insert: list) -> None:
        for elm in to_insert:
            self.insert(collection, elm)

    def update(self, collection, query, updated) -> None:
        self.__client[collection].update_one(query, updated)

    def get_db_name(self) -> str:
        return self.__db_name

    def get_collection_name(self) -> str:
        return self.__collection
