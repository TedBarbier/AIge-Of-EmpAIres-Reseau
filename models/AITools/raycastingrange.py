from shapely.geometry import Point, Polygon

class rayCastingRange:
    def __init__(self, top, left, right, bottom, step = 1):

        self.top = top
        self.left = left
        self.right = right
        self.bottom = bottom

        self.step = step

        self.polygon = Polygon([(top[1], top[0]), (left[1], left[0]), (bottom[1], bottom[0]), (right[1], right[0])])

    def __iter__(self):
        min_X, min_Y = self.left[1], self.top[0]
        max_X, max_Y = self.right[1], self.bottom[0]
        for current_Y in range(min_Y, max_Y + 1):
            for current_X in range(min_X, max_X + 1):
                if self.polygon.contains(Point(current_X, current_Y)):
                    yield current_Y, current_X
