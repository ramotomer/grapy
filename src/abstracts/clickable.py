from abc import ABC, abstractmethod


class Clickable(ABC):

    @abstractmethod
    def is_mouse_in(self, mouse_x: int, mouse_y: int) -> bool:
        ...

    @abstractmethod
    def on_click(self, mouse_x: int, mouse_y: int) -> None:
        ...
