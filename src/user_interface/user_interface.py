from collections import namedtuple
from functools import reduce
from operator import concat

from pyglet.window import key

from consts import *
from exceptions import *
from src.main_loop import MainLoop
from src.main_window import MainWindow
from src.shape_drawing import draw_pause_rectangles, draw_rect
from src.user_interface.button import Button
from src.user_interface.popup_windows.popup_error import PopupError
from src.user_interface.popup_windows.popup_text_box import PopupTextBox
from src.user_interface.popup_windows.popup_window import PopupWindow
from src.user_interface.text_graphics import Text
from src.usefuls import with_args, called_in_order

from src.objects.ball import Ball


ObjectView = namedtuple("ObjectView", [
    "sprite",
    "text",
    "viewed_object",
])
"""
A ip_layer structure to represent the current viewing of a GraphicsObject on the side window in VIEW_MODE
- sprite is the little image that is shown
- text is a `Text` object of the information about the object
- viewed_object is a reference to the GraphicsObject that's viewed. 
"""


class UserInterface:
    """
    This class constructs the interface the user sees and uses.

    It contains all construction of buttons and of keyboard keys and their actions.
    All of the computers that are created and all packets and connections are all saved and handled in this class,
    since the methods that add and delete them are here.

    The selected and dragged objects (The ones that are surrounded with a white square and are moved by the mouse) are
    also save in this class.

    The `self.mode` variable determines in what mode the user interface is currently in.
    if the mode is `SIMULATION_MODE`, the regular menu is presented.
    if the mode is `CONNECTING_MODE` than the two next computers the user will press will become connected.
    the `VIEW_MODE` is when a computer's details are currently is_showing in the side window nicely.
    the `PINGING_MODE` is when we choose two computer to send a ping between.  (purple side window)
    the `DELETING_MODE` is when we delete a graphics object. (Brown side window)

    Only set the mode through the `set_mode` method!!!
    """
    WIDTH = SIDE_WINDOW_WIDTH  # pixels

    def __init__(self):
        """
        Initiates the UserInterface class!
        `key_to_action` is a dictionary from keys and their modifiers to actions to perform when that key is pressed.
        `button_arguments` is a list of arguments for `Button` objects that will be created after
        the `MainWindow` is initiated.

        `is_asking_for_string` tells whether or not a popup window is currently up and asking the user for input
        `popup_window` is that window.
        """
        self.key_to_action = {
            (key.SPACE, NO_MODIFIER): self.toggle_pause,
            (key.TAB, NO_MODIFIER): self.tab_through_selected,
            (key.TAB, SHIFT_MODIFIER): with_args(self.tab_through_selected, True),
            (key.ESCAPE, NO_MODIFIER): with_args(self.set_mode, SIMULATION_MODE),
            (key.N, NO_MODIFIER): self.create_ball,
            (key.T, NO_MODIFIER): self.toggle_screen_clearing,
        }

        self.action_at_press_by_mode = {
            SIMULATION_MODE: self.view_mode_at_press,
            VIEW_MODE: self.view_mode_at_press,
            DELETING_MODE: self.deleting_mode_at_press,
        }
        # ^ maps what to do when the screen is pressed in each `mode`.

        self.mode = SIMULATION_MODE

        self.selected_object = None
        self.dragged_object = None
        self.dragging_point = 0, 0

        self.object_view = None

        self.is_asking_for_string = False
        self.popup_windows = []
        self.__active_window = None

        self.button_arguments = [
            ((*DEFAULT_BUTTON_LOCATION(-1), lambda: None, "MAIN MENU:"), {}),

            ((*DEFAULT_BUTTON_LOCATION(0), self.delete_all,
              "delete all (^d)"), {"key": (key.D, CTRL_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(1), with_args(self.toggle_mode, DELETING_MODE),
              "delete (d)"), {"key": (key.D, NO_MODIFIER)}),
        ]
        self.buttons = {}
        self.showing_buttons_id = MAIN_BUTTONS_ID
        self.scrolled_view = None

        self.balls = []

    @property
    def active_window(self):
        return self.__active_window

    @active_window.setter
    def active_window(self, window):
        if self.active_window is not None:
            self.active_window.deactivate()

        if window is not None:
            window.activate()
        self.__active_window = window

    def show(self):
        """
        This is like the `draw` method of GraphicObject`s.
        :return: None
        """
        draw_rect(WINDOW_WIDTH - self.WIDTH, 0, self.WIDTH, WINDOW_HEIGHT, MODES_TO_COLORS[self.mode])
        # ^ the window rectangle itself
        if MainLoop.instance.is_paused:
            draw_pause_rectangles()

    def drag_object(self):
        """
        Drags the object that should be dragged around the screen.
        Essentially sets the objects coordinates to be the ones of the mouse.
        :return: None
        """
        if self.dragged_object is not None and not self.dragged_object.is_button:
            drag_x, drag_y = self.dragging_point
            mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
            self.dragged_object.x, self.dragged_object.y = mouse_x + drag_x, mouse_y + drag_y

        if isinstance(self.dragged_object, Ball):
            self.dragged_object.velocity.x = 0
            self.dragged_object.velocity.y = 0

    def start_object_view(self, graphics_object):
        """
        Starts viewing an object on the side window.
        Creates an `ObjectView` namedtuple which packs together the ip_layer required to view an object.
        :param graphics_object: A graphics object to view.
        :return: None
        """
        self.scrolled_view = 0

        sprite, text, buttons_id = graphics_object.start_viewing(self)
        if sprite is not None:
            sprite.update(*VIEWING_IMAGE_COORDINATES)
            MainLoop.instance.insert_to_loop(sprite.draw)

        x, y = VIEWING_TEXT_COORDINATES
        self.object_view = ObjectView(sprite, Text(text, x, y, max_width=SIDE_WINDOW_WIDTH), graphics_object)

        if buttons_id is not None:
            self.adjust_viewed_text_to_buttons(buttons_id + 1)

    def adjust_viewed_text_to_buttons(self, buttons_id):
        """
        This is called when the buttons of the viewed object are changed.
        The location of the viewed text is changed according to it.
        :return:
        """
        if self.object_view is None:
            raise WrongUsageError("Only call this in VIEW MODE")

        try:
            self.object_view.text.y = VIEWING_TEXT_COORDINATES[1] - ((len(self.buttons[buttons_id]) + 0.5) *
                                                                     DEFAULT_BUTTON_HEIGHT) - self.scrolled_view
        except KeyError:
            pass

    def end_object_view(self):
        """
        Removes the text object from the loop and ends the viewing of an object in the side window.
        if no object was viewed, does nothing.
        """
        if self.object_view is not None:
            self.object_view.viewed_object.end_viewing(self)
            MainLoop.instance.unregister_graphics_object(self.object_view.text)
            if self.object_view.sprite is not None:
                MainLoop.instance.remove_from_loop(self.object_view.sprite.draw)

            self.object_view = None
            self.scrolled_view = None

    def scroll_view(self, scroll_count):
        """
        Scrolls through the view of an object if it is too long to view all at once.
        This is called when the mouse wheel is scrolled.
        :return: None
        """
        if self.object_view is None:
            raise SomethingWentTerriblyWrongError(
                "Not supposed to get here!!! In VIEW_MODE the `self.object_view` is never None"
            )

        sprite, text_graphics, viewed_object = self.object_view
        if scroll_count < 0 or self.scrolled_view <= -scroll_count * PIXELS_PER_SCROLL:
            self.scrolled_view += scroll_count * PIXELS_PER_SCROLL

            sprite.y = VIEWING_IMAGE_COORDINATES[1] - self.scrolled_view
            self.adjust_viewed_text_to_buttons(self.showing_buttons_id)

            for buttons_id in self.buttons:
                for button in self.buttons[buttons_id]:
                    if not button.is_hidden:
                        button.y = button.initial_location[1] - self.scrolled_view

    def tab_through_selected(self, reverse=False):
        """
        This is called when the TAB key is pressed.
        It goes through the graphics objects one by one and selects them.
        Allows working without the mouse when there are not a lot of objects on the screen
        :return:
        """
        available_graphics_objects = [object_ for object_ in MainLoop.instance.graphics_objects
                                      if object_.is_pressable and object_.can_be_viewed]
        if not available_graphics_objects:
            return
        if reverse:
            available_graphics_objects = list(reversed(available_graphics_objects))

        try:
            index = available_graphics_objects.index(self.selected_object)
            self.selected_object = available_graphics_objects[index - 1]
        except ValueError:
            self.selected_object = available_graphics_objects[-1]

        self.set_mode(VIEW_MODE)

    def initiate_buttons(self):
        """
        Initiates the buttons in the window.
        This does not happen in init because when init is called here
        `MainWindow.main_window` is still uninitiated so it cannot register the graphics objects of the buttons.
        :return: None
        """
        self.buttons[MAIN_BUTTONS_ID] = [Button(*args, **kwargs) for args, kwargs in self.button_arguments]

    def set_mode(self, new_mode):
        """
        This is the correct way to set the `self.new_mode` trait of the side window.
        it handles all of the things one needs to do when switching between different modes.
        (especially VIEW_MODE)
        :return: None
        """
        if new_mode == VIEW_MODE:
            self.end_object_view()
            self.mode = new_mode
            self.hide_buttons(MAIN_BUTTONS_ID)
            if not self.selected_object.can_be_viewed:
                raise WrongUsageError(
                    "The new_mode should not be switched to view new_mode when the selected object cannot be viewed"
                )
            self.start_object_view(self.selected_object)

        else:
            self.mode = new_mode
            self.end_object_view()
            self.selected_object = None
            self.show_buttons(MAIN_BUTTONS_ID)

    def toggle_mode(self, mode):
        """
        Toggles to and from a mode!
        If the mode is already the `mode` given, switch to `SIMULATION_MODE`.
        :param mode: a mode to toggle to and from (SIMULATION_MODE, CONNECTING_MODE, etc...)
        :return: None
        """
        if self.mode == mode:
            self.set_mode(SIMULATION_MODE)
        else:
            self.set_mode(mode)

    @staticmethod
    def toggle_pause():
        """
        Toggling from pause back and fourth.
        This is done because when the keys are paired in the __init__ method `MainLoop.instance` is not yet initiated
        :return: None
        """
        MainLoop.instance.toggle_pause()

    def view_mode_at_press(self):
        """
        Happens when we are in viewing mode (or simulation mode) and we press our mouse.
        decides whether to start viewing a new graphics object or finish a previous one.
        """
        if not self.is_mouse_in_side_window():
            if self.selected_object is not None and self.selected_object.can_be_viewed:
                self.set_mode(VIEW_MODE)
            elif self.selected_object is None:
                self.set_mode(SIMULATION_MODE)
            else:  # if an an object that cannot be viewed is pressed
                pass

    def deleting_mode_at_press(self):
        """
        Happens when we press the screen in DELETING_MODE.
        Decides if to step out of the mode or to delete an object.
        :return: None
        """
        if self.selected_object is not None:
            self.delete(self.selected_object)
        self.set_mode(SIMULATION_MODE)

    def is_mouse_in_side_window(self):
        """Return whether or not the mouse is currently in the side window."""
        mouse_x, _ = MainWindow.main_window.get_mouse_location()
        return mouse_x > (WINDOW_WIDTH - self.WIDTH)

    def delete_all(self):
        """
        Deletes all of the objects and graphics objects that exist.
        Totally clears the screen.
        :return: None
        """
        MainLoop.instance.delete_all_graphics()
        self.selected_object = None
        self.dragged_object = None

        if self.is_asking_for_string:
            self.end_string_request()

        self.balls.clear()

    def delete(self, graphics_object):
        """
        Receives a graphics object, deletes it from the main loop and disconnects it (if it is a computer).
        :param graphics_object: a `GraphicsObject` to delete.
        :return: None
        """
        MainLoop.instance.unregister_graphics_object(graphics_object)
        self.selected_object = None
        self.dragged_object = None

    def hide_buttons(self, buttons_id=None):
        """
        make all of the buttons with a certain button_id hidden, if no group is given, hide all
        :param buttons_id: the buttons id of the buttons you want to hide.
        :return: None
        """
        if buttons_id is None:
            for other_buttons_id in self.buttons:
                self.hide_buttons(other_buttons_id)

        for button in self.buttons[buttons_id]:
            button.hide()

    def show_buttons(self, buttons_id):
        """
        make the buttons of a certain buttons_id is_showing, all other groups hidden.
        :param buttons_id: the ID of the buttons one wishes to show.
        :return: None
        """
        for button in self.buttons[buttons_id]:
            button.show()
        self.showing_buttons_id = buttons_id

    def end_string_request(self):
        """
        If the `UserInterface` Object currently is asking for user input (via the popup window), end that request,
        unregister the asking `PopupTextBox` popup window and set all variables accordingly.
        :return: None
        """
        self.is_asking_for_string = False
        self.active_window = None

    def ask_user_for(self, type_, window_text, action, error_msg="invalid input!!!"):
        """
        Pops up the little window that asks the user to insert something.
        Receives the text of the window, the type that the string should have, and an action to perform with the already
        casted string. (The parameter that the action will receives will be of type `type_`)
        :param type_: the type the inserted value should have (`float` / `int` / `IPAddress`)
        :param window_text: the string that will be displayed on the popup window
        :param action: a function that receives the casted input value and does something with it.
        :param error_msg: The msg to be displayed if the input is invalid
        :return: None
        """
        def try_casting_with_action(string):
            try:
                user_input_object = type_(string)
            except (ValueError, InvalidAddressError):
                self.end_string_request()
                PopupError(error_msg, self)
                return

            try:
                action(user_input_object)
            except PopupWindowWithThisError as err:
                PopupError(str(err), self)
                return

        self.is_asking_for_string = True
        PopupTextBox(window_text, self, try_casting_with_action)

    @staticmethod
    def key_from_string(string):
        """
        Receives a button-string and returns the key that should be pressed to activate that button
        for example:
         'connect all (^c)' -> `key_from_string` -> `(key.C, CTRL_MODIFIER)`
        :param string:
        :return:
        """
        if '(' not in string:
            return None

        _, modified_key = string.lower().split('(')
        modified_key, _ = modified_key.split(')')
        if modified_key.startswith('^'):
            return ord(modified_key[-1]), CTRL_MODIFIER

        modifiers = NO_MODIFIER
        if 'ctrl' in modified_key.split('+'):
            modifiers |= CTRL_MODIFIER
        if 'shift' in modified_key.split('+'):
            modifiers |= SHIFT_MODIFIER
        if 'alt' in modified_key.split('+'):
            modifiers |= ALT_MODIFIER
        return ord(modified_key[-1]), modifiers

    def add_buttons(self, dictionary):
        """
        Adds buttons to the side window according to requests of the viewed object.
        One plus the buttons_id is the button of the options
        :param dictionary: a `dict` of the form {button text: button action}
        :return: None
        """
        buttons_id = 0 if not self.buttons else max(self.buttons.keys()) + 1
        self.buttons[buttons_id] = [
            Button(
                *DEFAULT_BUTTON_LOCATION(len(dictionary) + 1),
                called_in_order(
                    with_args(self.hide_buttons, buttons_id),
                    with_args(self.show_buttons, buttons_id + 1),
                    with_args(self.adjust_viewed_text_to_buttons, buttons_id + 1),
                ),
                "back (backspace)",
                key=(key.BACKSPACE, NO_MODIFIER),
                start_hidden=True,
            ),

            *[
                Button(
                    *DEFAULT_BUTTON_LOCATION(i+1),
                    action,
                    string,
                    key=self.key_from_string(string),
                    start_hidden=True,
                )
                for i, (string, action) in enumerate(dictionary.items())
              ],
        ]

        self.buttons[buttons_id + 1] = [
            Button(
                *DEFAULT_BUTTON_LOCATION(1),
                called_in_order(
                    with_args(self.hide_buttons, buttons_id + 1),
                    with_args(self.show_buttons, buttons_id),
                    with_args(self.adjust_viewed_text_to_buttons, buttons_id),
                ),
                "options (enter)",
                key=(key.ENTER, NO_MODIFIER),
            ),
        ]
        self.showing_buttons_id = buttons_id + 1
        return buttons_id

    def remove_buttons(self, buttons_id):
        """
        Unregisters side-view added buttons by their ID. (Buttons that are added using the `self.add_buttons` method.)
        :param buttons_id: an integer returned by the `self.add_buttons` method
        :return: None
        """
        for button in self.buttons[buttons_id] + self.buttons[buttons_id + 1]:
            MainLoop.instance.unregister_graphics_object(button)
        del self.buttons[buttons_id]
        del self.buttons[buttons_id + 1]

    def register_window(self, window, *buttons):
        """
        Receives a window and adds it to the window list and make it known to the user interface
        object.
        :param window: a PopupWindow object
        :param buttons: the buttons that the
        window contains
        :return:
        """
        if self.popup_windows:
            window.x, window.y = map(sum, zip(self.popup_windows[-1].location, NEW_WINDOW_LOCATION_PADDING))

        self.popup_windows.append(window)
        self.active_window = window
        self.selected_object = window
        self.buttons[WINDOW_BUTTONS_ID] = self.buttons.get(WINDOW_BUTTONS_ID, []) + list(buttons)

        for button in buttons:
            MainLoop.instance.move_to_front(button)

        def remove_buttons():
            for button in buttons:
                self.buttons[WINDOW_BUTTONS_ID].remove(button)
                MainLoop.instance.unregister_graphics_object(button)
        window.remove_buttons = remove_buttons

    def unregister_window(self, window):
        """
        receives a window that is registered in the UI object and removes it, it will be ready to be deleted afterwards
        :param window: a `PopupWindow` object
        :return: None
        """
        if self.active_window is window:
            self.active_window = None
        if self.selected_object is window:
            self.selected_object = None

        try:
            self.popup_windows.remove(window)
        except ValueError:
            raise WrongUsageError("The window is not registered in the UserInterface!!!")

    def create_ball(self):
        self.balls.append(Ball(*MainWindow.main_window.get_mouse_location()))

    def toggle_screen_clearing(self):
        MainLoop.instance.is_clearing_screen = not MainLoop.instance.is_clearing_screen
