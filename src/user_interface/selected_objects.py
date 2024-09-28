

class SelectedObjects:
    def __init__(self):
        self.__selected_object = None

    @property
    def selected_object(self):
        return self.__selected_object

    @selected_object.setter
    def selected_object(self, graphics_object):
        self.__selected_object = graphics_object
