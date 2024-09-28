from abc import ABCMeta, abstractmethod
from gui.main_loop import MainLoop


class GraphicsObject(metaclass=ABCMeta):
    """
    This is an abstract class that its instances are things that will be drawn on the screen, for example the images of
    the computer, the packets the lines that connect the computers and the buttons.

    They have to have a `draw`, a `move` and a `load` method.
    When a graphics object is created, it inserts itself into the main loop of the program.
    Every call of the main loop function will call its `draw` and `move` methods.
    The `draw` should contain the drawing of the object while the `move` should contain its movement. Reasonable I would say.

    If this object has an iterable attribute in the name `child_graphics_objects`, when this object is unregistered, all of the
    GraphicsObjects in that iterable are unregistered as well.
    """
    def __init__(self, x=None, y=None, do_render=True, centered=False, is_in_background=False, is_pressable=False):
        """
        Initiates a graphics object and registers it to the main loop.
        :param x: x coordinate
        :param y: y coordinate
        :param do_render: whether the GraphicsObject is rendered or not.
        :param centered: whether the coordinates of object are in the middle of the sprite or the bottom left point.
        :param is_in_background: whether the object is drawn in the back or the front of the other objects.
        :param is_pressable: whether or not this object can be clicked on.
        """
        self.x = x
        self.y = y
        self.do_render = do_render
        self.centered = centered
        self.is_pressable = is_pressable

        self.is_button = False
        self.is_computer = False
        self.is_packet = False
        self.is_image = False
        self.is_connection = False

        if self.do_render:
            MainLoop.instance.register_graphics_object(self, is_in_background)

    @property
    def location(self):
        """
        The location property of the `GraphicsObject`.
        :return: (self.x, self.y)
        """
        return self.x, self.y

    @location.setter
    def location(self, new_location):
        self.x, self.y = new_location

    @property
    def can_be_viewed(self):
        return hasattr(self, "start_viewing") and hasattr(self, "end_viewing")

    def is_mouse_in(self):
        """
        Returns whether or not the mouse is located inside this graphics object.
        :return: None
        """
        return False

    def load(self):
        """
        The function that should load the object.
        It is called only once at the start of the object's lifetime.
        :return: None
        """
        pass

    @abstractmethod
    def draw(self):
        """
        This method should be overridden in any subclasses.
        It should handle the drawing of the object to the screen, it will be called every loop of the program.
        :return: None
        """
        pass

    def move(self):
        """
        This method should be overridden in any subclasses.
        It should handle the moving of the object on the screen, it will be called every loop of the program.
        :return: None
        """
        pass

    def __repr__(self):
        """The string representation of the graphics object"""
        rendered = 'rendered' if self.do_render else 'non-rendered'
        centered = 'centered' if self.centered else 'non-centered'
        return ' '.join([rendered, centered]) + f" GraphicsObject(x={self.x}, y={self.y})"
