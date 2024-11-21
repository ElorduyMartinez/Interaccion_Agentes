# model.py
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from typing import Tuple, List

class Building(Agent):
    """Static building agent that occupies space on the grid."""
    def __init__(self, model, position: Tuple[int, int]):
        super().__init__(model)
        self.color = "#87CEEB"  # Light blue color

    def step(self):
        """Buildings don't perform any actions."""
        pass

class SpawnPoint(Agent):
    """Agent representing a vehicle spawn point."""
    def __init__(self, model, position: Tuple[int, int], direction: Tuple[int, int], spawn_id: int):
        super().__init__(model)
        self.direction = direction
        self.spawn_id = spawn_id
        self.color = "#FFFF00"  # Yellow color for spawn points

    def step(self):
        """Spawn points don't perform any actions."""
        pass

class TrafficLight(Agent):
    """Traffic light agent that controls traffic flow."""
    def __init__(self, model, position: Tuple[int, int], light_set: int):
        super().__init__(model)
        self.color = "#8B8000"  # Dark yellow
        self.light_set = light_set  # To identify which set of lights this belongs to
        
    def step(self):
        """Traffic lights will change states based on model rules."""
        pass

class IntersectionModel(Model):
    """Model representing a traffic intersection with buildings, spawn points, and traffic lights."""
    def __init__(self, width=24, height=24):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        
        # Initialize the environment
        self.setup_intersection()
        
        # Set up data collection
        self.datacollector = DataCollector(
            model_reporters={
                "spawn_points": lambda m: len([a for a in m.agents if isinstance(a, SpawnPoint)]),
                "buildings": lambda m: len([a for a in m.agents if isinstance(a, Building)]),
                "traffic_lights": lambda m: len([a for a in m.agents if isinstance(a, TrafficLight)])
            }
        )
        
        self.running = True

    def setup_intersection(self):
        """Set up the initial state of the intersection."""
        self.create_buildings()
        self.create_traffic_lights()
        self.create_spawn_points()

    def create_spawn_points(self):
        """Create spawn points at specified locations, replacing existing buildings."""
        spawn_points_data = [
            (2, 14, (1, 0), 1),   # 1
            (3, 21, (0, -1), 2),  # 2
            (3, 6, (0, -1), 3),   # 3
            (4, 12, (1, 0), 4),   # 4
            (4, 3, (0, 1), 5),    # 5
            (5, 17, (1, 0), 6),   # 6
            (8, 15, (-1, 0), 7),  # 7
            (9, 2, (0, 1), 8),    # 8
            (10, 19, (0, -1), 9), # 9
            (10, 12, (1, 0), 10), # 10
            (10, 7, (-1, 0), 11), # 11
            (17, 21, (0, -1), 12),# 12
            (17, 6, (0, -1), 13), # 13
            (17, 4, (-1, 0), 14), # 14
            (20, 18, (1, 0), 15), # 15
            (20, 15, (-1, 0), 16),# 16
            (20, 4, (0, 1), 17)   # 17
        ]
        
        for x, y, direction, spawn_id in spawn_points_data:
            # First remove any existing agents at this position
            cell_contents = self.grid.get_cell_list_contents((x, y))
            for agent in cell_contents:
                self.grid.remove_agent(agent)
            
            # Then create and place the spawn point
            spawn_point = SpawnPoint(self, (x, y), direction, spawn_id)
            self.grid.place_agent(spawn_point, (x, y))

    def create_buildings(self):
        """Create buildings with specified coordinates."""
        buildings = [
            ((2, 21), (5, 12)),   # First building
            ((2, 7), (5, 6)),     # Second building
            ((2, 3), (5, 2)),     # Third building
            ((8, 21), (11, 19)),  # Fourth building
            ((8, 16), (11, 12)),  # Fifth building
            ((8, 7), (11, 6)),    # Sixth building
            ((8, 3), (11, 2)),    # Seventh building
            ((16, 21), (21, 18)), # Eighth building
            ((16, 15), (21, 12)), # Ninth building
            ((16, 7), (17, 2)),   # Tenth building
            ((20, 7), (21, 2))    # Eleventh building
        ]
        
        # First clear all existing agents
        for (top_left, bottom_right) in buildings:
            for x in range(top_left[0], bottom_right[0] + 1):
                for y in range(bottom_right[1], top_left[1] + 1):
                    cell_contents = self.grid.get_cell_list_contents((x, y))
                    for agent in cell_contents:
                        self.grid.remove_agent(agent)
        
        # Then place new buildings
        for (top_left, bottom_right) in buildings:
            for x in range(top_left[0], bottom_right[0] + 1):
                for y in range(bottom_right[1], top_left[1] + 1):
                    building = Building(self, (x, y))
                    self.grid.place_agent(building, (x, y))
        
        # Handle central building (13,10 to 14,9)
        # First clear the area
        for x in range(13, 15):
            for y in range(9, 11):
                cell_contents = self.grid.get_cell_list_contents((x, y))
                for agent in cell_contents:
                    self.grid.remove_agent(agent)
        
        # Then place the central building
        for x in range(13, 15):
            for y in range(9, 11):
                building = Building(self, (x, y))
                building.color = "brown"
                self.grid.place_agent(building, (x, y))

    def create_traffic_lights(self):
        """Create traffic light sets at specified coordinates."""
        traffic_light_sets = [
            # Set 1
            [(0, 6), (1, 6)],
            # Set 2
            [(2, 4), (2, 5)],
            # Set 3
            [(5, 0), (5, 1)],
            # Set 4
            [(6, 2), (7, 2)],
            # Set 5
            [(6, 16), (7, 16)],
            # Set 6
            [(6, 21), (7, 21)],
            # Set 7
            [(8, 22), (8, 23)],
            # Set 8
            [(17, 8), (17, 9)],
            # Set 9
            [(18, 7), (19, 7)],
            # Set 10
            [(8, 17), (8, 18)]
        ]

        # Clear and place traffic lights for each set
        for set_idx, light_positions in enumerate(traffic_light_sets, 1):
            for pos in light_positions:
                # Clear existing agents
                cell_contents = self.grid.get_cell_list_contents(pos)
                for agent in cell_contents:
                    self.grid.remove_agent(agent)
                
                # Create and place traffic light
                traffic_light = TrafficLight(self, pos, set_idx)
                self.grid.place_agent(traffic_light, pos)

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")