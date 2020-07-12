from  typing import Iterator, Tuple, Dict


class ICURectangle():
    '''
    top_left(x,y)       top_right(x,y)
    bottom_left(x,y)    bottom_right(x,y)

    center(x,y) is the average of all the corners. Decimal values are rounded down.

    Security assertions detect negative coordinates, 0 width, and 0 height.
    '''
    def __init__(self, top_left: Tuple[int, int], top_right: Tuple[int, int], bottom_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> None:
        self.__top_left: Tuple[int, int] = top_left
        self.__top_right: Tuple[int, int] = top_right
        self.__bottom_left: Tuple[int, int] = bottom_left
        self.__bottom_right: Tuple[int, int] = bottom_right
        self.__center: Tuple[int, int] = ((top_left[0] + top_right[0] + bottom_left[0] + bottom_right[0]) // 4, (top_left[1] + top_right[2] + bottom_left[1] + bottom_right[1]) // 4)

        assert self.__top_left[0] >=0
        assert self.__top_left[1] >=0
        assert self.__top_right[0] > self.__top_left[0]
        assert self.__top_right[1] >=0
        assert self.__bottom_left[0] >=0
        assert self.__bottom_left[1] > self.__top_left[1]
        assert self.__bottom_right[0] > self.__bottom_left[0]
        assert self.__bottom_right[1] > self.__top_right[1]

    def get_top_left_coordinates(self) -> Tuple[int, int]:
        return self.__top_left

    def get_top_right_coordinates(self) -> Tuple[int, int]:
        return self.__top_right

    def get_bottom_left_coordinates(self) -> Tuple[int, int]:
        return self.__bottom_left

    def get_bottom_right_coordinates(self) -> Tuple[int, int]:
        return self.__bottom_right

    def get_center_coordinates(self) -> Tuple[int, int]:
        return self.__center


class ICUWIdget():
    '''
    E.g.:
        pumps_and_tanks --> wigdet
        each pump is a subwidget
        each tank is a subwidget

        scales --> widget
        each scale is a subwidget

        warning_lights --> widget
        each warning light is a subwidget

        tracking_widget --> widget
    '''
    def __init__(self, reference_points: ICURectangle, subcomponents: Dict[str, "ICUWIdget"]) -> None:
        self.__reference_points: ICURectangle = reference_points
        self.__subcomponents: Dict[str, ICUWIdget] = subcomponents

    def get_subcomponents(self) -> Dict[str, "ICUWIdget"]:
        return self.__subcomponents

    def get_subcomponents_iterator(self) -> Iterator:
        for subcomponent in self.__subcomponents.values():
            yield subcomponent

    def get_subcomponent(self, name: str) -> "ICUWIdget":
        return self.__subcomponents[name]

    def get_reference_points(self) -> ICURectangle:
        return self.__reference_points

    def get_top_left_coordinates(self) -> Tuple[int, int]:
        return self.get_reference_points().get_top_left_coordinates()

    def get_top_right_coordinates(self) -> Tuple[int, int]:
        return self.get_reference_points().get_top_right_coordinates()

    def get_bottom_left_coordinates(self) -> Tuple[int, int]:
        return self.get_reference_points().get_bottom_left_coordinates()

    def get_bottom_right_coordinates(self) -> Tuple[int, int]:
        return self.get_reference_points().get_bottom_right_coordinates()

    def get_center_coordinates(self) -> Tuple[int, int]:
        return self.get_reference_points().get_center_coordinates()
