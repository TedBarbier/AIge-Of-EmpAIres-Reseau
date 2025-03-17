import math
from AITools.formation import *
import random

def calc_depth_from_unit_num(unit_num):
    return math.ceil(math.sqrt(unit_num + 1) - 1)
GROUP_DISBANDED = 0xf
class Group:
    def __init__(self, units_id_list, linked_map=None):
        self.units_id_list = units_id_list
        self.linked_map = linked_map

        self.state = GROUP_IDLE
        self.entity_target_id = None

        # Initialize leader and formation
        self.init_leader_and_formation()

    def init_leader_and_formation(self):
        if not self.units_id_list:
            print("No units available to form a group.")
            return

        # Assign leader
        self.leader_id = self.units_id_list[0]
        leader = self.linked_map.get_entity_by_id(self.leader_id)
        leader.role_in_group = UNIT_LEADER
        leader.linked_group = self

        # Create formation
        self.formation = Formation(
            leader_id=self.leader_id,
            units_id_list=self.units_id_list,
            linked_map=self.linked_map
        )

    def reassign_leader_on_death(self):
        leader = self.linked_map.get_entity_by_id(self.leader_id)

        if leader is None or leader.is_dead():
            print(f"Leader {self.leader_id} is dead. Reassigning leader...")

            # Promote a new leader using the formation's method
            new_leader_id = self.formation.update_leader_on_death()
            if new_leader_id:
                self.leader_id = new_leader_id

                new_leader = self.linked_map.get_entity_by_id(self.leader_id)
                new_leader.role_in_group = UNIT_LEADER
                new_leader.linked_group = self
                print(f"New leader assigned: {self.leader_id}")
            else:
                print("No units left in the group. The group is disbanded.")
                self.state = GROUP_DISBANDED

    def move_to(self, position):
        leader = self.linked_map.get_entity_by_id(self.leader_id)
        if leader:
            leader.move_to(position)
            self.formation.update_positions(position)

    def attack_entity(self, entity_id):
        leader = self.linked_map.get_entity_by_id(self.leader_id)
        if leader:
            leader.attack_entity(entity_id)

    def try_attack(self):
        leader = self.linked_map.get_entity_by_id(self.leader_id)
        if not leader:
            return False

        self.formation.update_leader_direction(leader.direction)
        if leader.locked_with_target:
            self.formation.update_target(leader.entity_target_id)
            return True
        else:
            self.formation.update_target(None)
            return False

    def update(self):
        # Handle leader reassignment if needed
        self.reassign_leader_on_death()
        if self.state == GROUP_DISBANDED:
            return

        # Update formation behavior
        self.formation.update_direction()
        if not self.try_attack():
            self.formation.follow_leader()

        self.formation.update_units_state()
