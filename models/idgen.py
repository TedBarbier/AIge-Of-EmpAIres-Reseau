class IdGenerator:

    def __init__(self, _id_ticket = 0):
        self.id_ticket = _id_ticket
        self.free_tickets = set()

    def give_ticket(self):
        ticket = None

        if len(self.free_tickets):
            ticket = self.free_tickets.pop()
        else:
            ticket = self.id_ticket
            self.id_ticket += 1

        return ticket
    
    def free_ticket(self, _id_ticket):
        self.free_tickets.add(_id_ticket)
    

    def __repr__(self):
        rep = f"c_id:{self.id_ticket} | free_tickets:"

        for id in self.free_tickets:
            rep += f" {id}"

        return rep
