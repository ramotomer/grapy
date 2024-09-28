from src.abstracts.graphics_object import GraphicsObject
from usefuls import distance
from src.main_window import MainWindow
from src.shape_drawing import draw_circle, draw_rect
from consts import *
from recordclass import recordclass


Vector = recordclass("Vector", "x y")


class Ball(GraphicsObject):
    def __init__(self, x, y, x_velocity=0, y_velocity=0, rad=20, color=LIGHT_BLUE, gravity=-0.5, bounciness=0.9):
        super(Ball, self).__init__(x, y, centered=True, is_pressable=True)
        self.radius = rad
        self.color = color

        self.velocity = Vector(x_velocity, y_velocity)
        self.gravity = gravity

        self.bounciness = bounciness

    def is_mouse_in(self):
        return distance(
            MainWindow.main_window.get_mouse_location(),
            self.location
        ) < self.radius

    def start_viewing(self, ui):
        return None, "Ball", None

    def end_viewing(self, ui):
        pass

    def draw(self):
        # draw_circle(*self.location, self.radius, self.color)
        draw_rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2, self.color)

    def move(self):
        self.move_by_velocity()
        self.apply_gravity()

        if self.hitting_ground():
            self.bounce()

    def mark_as_selected(self):
        draw_circle(self.x, self.y, self.radius * 1.5 + SELECTED_OBJECT_PADDING)

    def hitting_ground(self):
        return self.y - self.radius < 0 and self.velocity.y < 0

    def move_by_velocity(self):
        vx, vy = self.velocity
        self.x, self.y = self.x + vx, self.y + vy

    def apply_gravity(self):
        self.velocity.y += self.gravity

    def bounce(self):
        self.velocity.y *= -self.bounciness
