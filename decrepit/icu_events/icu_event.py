class ICUEvent():
    def __init__(self, raw: dict) -> None:
        self.__src = raw["src"]
        self.__dst = raw["dst"]
        self.__begin = raw["begin"]
        self.__end = raw["end"]
        self.__type = raw["type"]
        self.__data = raw["data"]

    def __init__(self, application_simulator_event: tuple) -> None:
        self.__begin = application_simulator_event[0]
        self.__end = self.__begin
        self.__type = application_simulator_event[1]
        self.__src = application_simulator_event[2][0]
        self.__dst = application_simulator_event[2][1]
        self.__data = application_simulator_event[3]

    def get_src(self):
        return self.__src

    def get_dst(self):
        return self.__dst

    def get_begin(self):
        return self.__begin

    def get_end(self):
        return self.__end

    def get_type(self):
        return self.__type

    def get_data(self):
        return self.__data