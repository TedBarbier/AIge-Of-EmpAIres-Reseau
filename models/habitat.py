class Habitat:
    def __init__(self, capacity):
        self.capacity = capacity  # Maximum units this habitat can hold
        self.current_population = 0

    def add_population(self):
        if self.current_population < self.capacity:
            self.current_population += 1
            return True
        return False
    def remove_population(self):
        if self.current_population > 0:
            self.current_population -= 1
            return True
        return False 

    def available_space(self):
        return self.capacity - self.current_population
