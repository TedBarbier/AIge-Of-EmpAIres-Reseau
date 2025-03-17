class Storage:
    def __init__(self):
        self.resources = {"gold":0,"wood":0,"food":0}  #{'wood': 50, 'food': 30}

    def add_resource(self, resource_type, amount):
        if resource_type not in self.resources:
            self.resources[resource_type] = 0
        self.resources[resource_type] += amount

    def remove_resource(self, resource_type, amount):
        if resource_type not in self.resources or self.resources[resource_type] == 0:
            return 0  # Nothing to remove

        to_remove = min(amount, self.resources[resource_type])
        self.resources[resource_type] -= to_remove
        
        return to_remove  # Return the amount actually removed

    def lose_resource(self):
        resources = self.resources.copy()

        for resource, amount in self.resources.items():
            self.resources[resource] = 0
        
        return resources