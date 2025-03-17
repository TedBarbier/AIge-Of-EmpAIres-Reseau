import pygame
import math
from GLOBAL_VAR import TILE_SIZE_2D

# Shape Classes
class Shape:
    def collide_with(self, other):
        raise NotImplementedError("This method should be implemented by subclasses.")
class Point(Shape):
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def collide_with(self, other):
        if isinstance(other, Rectangle):
            return self._collide_with_rectangle(other)
        elif isinstance(other, Circle):
            return self._collide_with_circle(other)
        else:
            raise TypeError("Unsupported shape type for collision detection.")

    def _collide_with_rectangle(self, other):
        return not (
            self.x  < other.x or
            self.x > other.x + other.width or
            self.y  < other.y or
            self.y > other.y + other.height
        )

    def _collide_with_circle(self, circle):
        
        distance = math.sqrt((circle.x - self.x)**2 + (circle.y - self.y)**2)
        return distance < circle.radius 
class Rectangle(Shape):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height), 2)

    def collide_with(self, other):
        if isinstance(other, Rectangle):
            return self._collide_with_rectangle(other)
        elif isinstance(other, Circle):
            return self._collide_with_circle(other)
        else:
            raise TypeError("Unsupported shape type for collision detection.")

    def _collide_with_rectangle(self, other):
        return not (
            self.x + self.width <= other.x or
            self.x >= other.x + other.width or
            self.y + self.height <= other.y or
            self.y >= other.y + other.height
        )

    def _collide_with_circle(self, circle):
        closest_x = max(self.x, min(circle.x, self.x + self.width))
        closest_y = max(self.y, min(circle.y, self.y + self.height))
        distance = math.sqrt((circle.x - closest_x)**2 + (circle.y - closest_y)**2)
        return distance <= circle.radius

class Square(Rectangle):
    def __init__(self, x, y, half_ide):
        super().__init__(x - half_ide, y - half_ide, 2 * half_ide, 2 * half_ide)

class Circle(Shape):
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self, screen, color):
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius, 2)

    def collide_with(self, other):
        if isinstance(other, Circle):
            return self._collide_with_circle(other)
        elif isinstance(other, Rectangle):
            return other.collide_with(self)  # Reuse Rectangle's logic
        else:
            raise TypeError("Unsupported shape type for collision detection.")

    def _collide_with_circle(self, other):
        distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        return distance <= (self.radius + other.radius)

class RoundedSquare(Square):
    def __init__(self, x, y, half_side):
        super().__init__(x, y, half_side)
        self.corner_radius = TILE_SIZE_2D/8  # Radius of the rounded corners

    def draw(self, screen, color):
        # Draw the main rectangle body
        pygame.draw.rect(screen, color, (self.x + self.corner_radius, self.y, self.width - 2 * self.corner_radius, self.height), 0)
        pygame.draw.rect(screen, color, (self.x, self.y + self.corner_radius, self.width, self.height - 2 * self.corner_radius), 0)

        # Draw the four rounded corners
        pygame.draw.circle(screen, color, (self.x + self.corner_radius, self.y + self.corner_radius), self.corner_radius, 0)  # Top-left
        pygame.draw.circle(screen, color, (self.x + self.width - self.corner_radius, self.y + self.corner_radius), self.corner_radius, 0)  # Top-right
        pygame.draw.circle(screen, color, (self.x + self.corner_radius, self.y + self.height - self.corner_radius), self.corner_radius, 0)  # Bottom-left
        pygame.draw.circle(screen, color, (self.x + self.width - self.corner_radius, self.y + self.height - self.corner_radius), self.corner_radius, 0)  # Bottom-right

    def collide_with(self, other):
        if isinstance(other, Circle):
            return self._collide_with_circle(other)
        elif isinstance(other, Point):
            return self._collide_with_point(other)
        elif isinstance(other, Rectangle):
            return self._collide_with_rectangle(other)
        else:
            raise TypeError("Unsupported shape type for collision detection.")

    def _collide_with_point(self, point):
        # Check if the point is inside the rounded square (taking corners into account)
        rect_collision = (
            self.x + self.corner_radius 
            <= point.x <= self.x + self.width - self.corner_radius and
            self.y <= point.y <= self.y + self.height
        ) or (
            self.x <= point.x <= self.x + self.width and
            self.y + self.corner_radius <= point.y <= self.y + self.height - self.corner_radius
        )

        if rect_collision:
            return True

        # Check if the point is within the corner circles
        corner_points = [
            (self.x + self.corner_radius, self.y + self.corner_radius),  # Top-left
            (self.x + self.width - self.corner_radius, self.y + self.corner_radius),  # Top-right
            (self.x + self.corner_radius, self.y + self.height - self.corner_radius),  # Bottom-left
            (self.x + self.width - self.corner_radius, self.y + self.height - self.corner_radius)  # Bottom-right
        ]
        for cx, cy in corner_points:
            if math.sqrt((cx - point.x) ** 2 + (cy - point.y) ** 2) <= self.corner_radius:
                return True
        return False

    def _collide_with_circle(self, circle):
        # Check for collisions between a circle and the rounded square
        # Check collision with the main rectangle area
        if Rectangle(self.x + self.corner_radius, self.y, self.width - 2 * self.corner_radius, self.height).collide_with(circle):
            return True
        if Rectangle(self.x, self.y + self.corner_radius, self.width, self.height - 2 * self.corner_radius).collide_with(circle):
            return True

        # Check collision with the corner circles
        corner_points = [
            (self.x + self.corner_radius, self.y + self.corner_radius),  # Top-left
            (self.x + self.width - self.corner_radius, self.y + self.corner_radius),  # Top-right
            (self.x + self.corner_radius, self.y + self.height - self.corner_radius),  # Bottom-left
            (self.x + self.width - self.corner_radius, self.y + self.height - self.corner_radius)  # Bottom-right
        ]
        for cx, cy in corner_points:
            if math.sqrt((cx - circle.x) ** 2 + (cy - circle.y) ** 2) <= circle.radius:
                return True
        return False

SHAPE_MAPPING = {
    "Circle":Circle,
    "Rectangle":Rectangle,
    "Square":Square,
    "RoundedSquare":RoundedSquare
}