class isoRange:
    def __init__(self, top, left, right, bottom, step = 1):
        
        self.top = top
        self.left = left
        self.right = right
        self.bottom = bottom
        self.step = step


    def __iter__(self):
        min_X, min_Y = self.left[1], self.top[0]
        max_X, max_Y = self.right[1], self.bottom[0]

        for current_Y in range(min_Y, max_Y + 1):
            for current_X in range(min_X, max_X + 1):
                yield current_Y, current_X
