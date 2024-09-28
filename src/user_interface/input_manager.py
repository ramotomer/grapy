from typing import Callable, Any, Dict, List, Tuple

from dataclasses import dataclass

from consts import NO_MODIFIER


MouseAction_T = Callable[[int, int], Any]
MouseLocationCondition_T = Callable[[int, int], bool]


@dataclass
class KeyPress:
    key: int
    modifiers: int = NO_MODIFIER


class InputManager:
    def __init__(self) -> None:
        self._key_to_action: Dict[KeyPress, List[Callable[[], Any]]] = {}
        self._actions_on_mouse_press: List[Tuple[MouseAction_T, MouseLocationCondition_T]] = []

        self.mouse_x, self.mouse_y = 0, 0

    def register_key_action(self, key: int, modifiers: int, action: Callable[[], Any]) -> None:
        key_press = KeyPress(key, modifiers)
        self._key_to_action[key_press] = self._key_to_action.get(key_press, []) + [action]

    def register_mouse_action(self, action: MouseAction_T, location_condition: MouseLocationCondition_T = (lambda x, y: True)) -> None:
        self._actions_on_mouse_press.append((action, location_condition))

    def on_mouse_press(self):
        """
        Happens when the mouse is pressed.
        Decides what to do according to the mode we are now in.
        The choosing of a selected and dragged objects should be performed BEFORE this is called!
        :return: None
        """

        for action, location_condition in self._actions_on_mouse_press:
            if location_condition(self.mouse_x, self.mouse_y):
                action(self.mouse_x, self.mouse_y)

        # for button in reversed(reduce(concat, list(self.buttons.values()))):
        #     if not button.is_hidden and button.is_mouse_in():
        #         button.action()
        #         break
        # else:
        #     self.action_at_press_by_mode[self.mode]()

    def on_key_pressed(self, key: int, modifiers: int) -> None:

        # if isinstance(self.active_window, PopupTextBox):
        #     self.active_window.pressed(symbol, modifiers)
        # else:

        pressed_key = KeyPress(key, int(bin(modifiers)[2:][-4:], base=2))
        actions = self._key_to_action.get(pressed_key, [])
        for action in actions:
            action()

        # for button_id in sorted(list(self.buttons)):
        #     for button in self.buttons[button_id]:
        #         if button.key == modified_key:
        #             button.action()
        #             return
