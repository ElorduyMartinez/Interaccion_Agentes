from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from collections import deque
import random
import numpy as np
from typing import Optional, List, Dict, Tuple, Any

class IntersectionBuilding(Agent):
    """Static building agent that occupies space on the grid."""
    def __init__(self, model, position: Tuple[int, int]):
        super().__init__(model)
        self.color = "#87CEEB"  # Light blue color

    def step(self):
        """Buildings don't perform any actions."""
        pass

class IntersectionSpawnPoint(Agent):
    """Agent representing a vehicle spawn point."""
    def __init__(self, model, position: Tuple[int, int], direction: Tuple[int, int], spawn_id: int):
        super().__init__(model)
        self.direction = direction
        self.spawn_id = spawn_id
        self.color = "#FFFF00"  # Yellow color for spawn points
        self.position = position

    def step(self):
        """Spawn points don't perform any actions."""
        pass

class IntersectionLight(Agent):
    """Intelligent traffic light agent that adapts to approaching vehicles."""
    
    def __init__(self, model, position: Tuple[int, int], light_set: int):
        super().__init__(model)
        self.position = position
        self.light_set = light_set
        self.state = 'yellow'  # Default state
        self.color = "yellow"
        self.timer = 0
        self.approaching_cars = {}  # Track approaching cars and ETAs
        self.min_green_time = 3
        self.max_green_time = 10
        self.detection_radius = 3

    def get_nearby_cars(self):
        """Detect cars within detection radius."""
        nearby_cars = []
        x, y = self.position
        for dx in range(-self.detection_radius, self.detection_radius + 1):
            for dy in range(-self.detection_radius, self.detection_radius + 1):
                pos = (x + dx, y + dy)
                if (0 <= pos[0] < self.model.grid.width and 
                    0 <= pos[1] < self.model.grid.height):
                    cell_contents = self.model.grid.get_cell_list_contents(pos)
                    cars = [agent for agent in cell_contents if isinstance(agent, IntersectionCar)]
                    nearby_cars.extend(cars)
        return nearby_cars

    def update_traffic_schedule(self):
        """Update schedule based on approaching cars."""
        nearby_cars = self.get_nearby_cars()
        
        if not nearby_cars:
            if self.state != 'yellow':
                self.state = 'yellow'
                self.color = 'yellow'
            return
        
        # Process car proximity
        min_distance = float('inf')
        for car in nearby_cars:
            if car.path:
                distance = abs(car.position[0] - self.position[0]) + abs(car.position[1] - self.position[1])
                min_distance = min(min_distance, distance)
        
        # Update light state based on car proximity
        if min_distance < self.detection_radius and self.state == 'yellow':
            self.state = 'green'
            self.color = 'green'
            self.timer = 0
        
        # Manage light cycle
        if self.state == 'green':
            self.timer += 1
            if self.timer >= self.max_green_time:
                self.state = 'red'
                self.color = 'red'
                self.timer = 0
        elif self.state == 'red':
            self.timer += 1
            if self.timer >= self.min_green_time and not nearby_cars:
                self.state = 'yellow'
                self.color = 'yellow'
                self.timer = 0

    def step(self):
        """Execute traffic light step."""
        self.update_traffic_schedule()

class IntersectionCar(Agent):
    """Intelligent car agent with personality and emotional states."""
    
    def __init__(self, model):
        super().__init__(model)
        self.position: Optional[Tuple[int, int]] = None
        self.destination: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
        self.traffic_light_detection_range = 3
        
        # Personality types
        self.personality = random.choice([
            'cooperative',    # Prefers yielding
            'aggressive',    # Prefers pushing through
            'cautious',      # Prefers safe routes
            'opportunistic', # Maximizes personal gain
            'reckless'       # May ignore red lights if stressed
        ])
        
        # Emotional and behavioral attributes
        self.state = 'normal'
        self.happiness = 100
        self.stress = 0
        self.patience = self.get_initial_patience()
        self.waiting_time = 0
        self.color = self.get_initial_color()

    def get_initial_patience(self) -> int:
        """Set initial patience based on personality."""
        base_patience = random.randint(3, 8)
        modifiers = {
            'cooperative': 2,
            'aggressive': -2,
            'cautious': 3,
            'opportunistic': 0,
            'reckless': -3
        }
        return max(1, base_patience + modifiers[self.personality])

    def get_initial_color(self) -> str:
        """Set initial color based on personality."""
        return {
            'cooperative': 'blue',
            'aggressive': 'red',
            'cautious': 'green',
            'opportunistic': 'purple',
            'reckless': 'orange'
        }[self.personality]

    def find_path(self) -> Optional[List[Tuple[int, int]]]:
        """Find path to destination avoiding buildings and respecting traffic rules."""
        if not self.position or not self.destination:
            return None
        
        frontier = deque([[self.position]])
        visited = {self.position}
    
        while frontier:
            path = frontier.popleft()
            current = path[-1]
        
            if current == self.destination:
                return path
            
            for next_pos in self.get_neighbors(current):
                if next_pos in visited:
                    continue
                
                # Check if position contains a building
                cell_contents = self.model.grid.get_cell_list_contents(next_pos)
                if any(isinstance(agent, IntersectionBuilding) for agent in cell_contents):
                    continue
                
                visited.add(next_pos)
                new_path = list(path)
                new_path.append(next_pos)
                frontier.append(new_path)
                
        return None

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions based on personality."""
        x, y = pos
        possible_moves = []
        
        # Different movement patterns based on personality
        if self.personality == 'aggressive':
            # Aggressive drivers prefer direct routes
            if x < self.destination[0]:
                possible_moves.append((x+1, y))
            elif x > self.destination[0]:
                possible_moves.append((x-1, y))
            if y < self.destination[1]:
                possible_moves.append((x, y+1))
            elif y > self.destination[1]:
                possible_moves.append((x, y-1))
        else:
            # Other personalities consider all moves
            possible_moves = [
                (x+1, y), (x-1, y),
                (x, y+1), (x, y-1)
            ]
        
        # Filter moves within grid boundaries
        valid_moves = []
        for nx, ny in possible_moves:
            if 0 <= nx < self.model.grid.width and 0 <= ny < self.model.grid.height:
                valid_moves.append((nx, ny))
        
        return valid_moves

    def handle_traffic_light(self, next_pos: Tuple[int, int]) -> bool:
        """Handle interaction with traffic light at next position."""
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        traffic_light = next((agent for agent in cell_contents 
                            if isinstance(agent, IntersectionLight)), None)
        
        if not traffic_light:
            return True
            
        if traffic_light.state == 'green':
            return True
            
        if traffic_light.state == 'red':
            self.waiting_time += 1
            self.happiness = max(0, self.happiness - 5)
            self.stress += 2 if self.personality == 'aggressive' else 1
            return False
            
        if traffic_light.state == 'yellow':
            if self.personality == 'reckless':
                return random.random() < (self.stress / 100 + 0.3)
            return False
                
        return True

    def update_emotional_state(self) -> None:
        """Update emotional state based on multiple factors."""
        # Update stress based on personality
        stress_factor = 2 if self.personality == 'aggressive' else 1
        self.stress += self.waiting_time * stress_factor
        self.stress = min(100, max(0, self.stress))
        
        # Update state and color
        if self.happiness > 80 and self.stress < 30:
            self.state = 'happy'
            self.color = 'green'
        elif self.happiness < 30 or self.stress > 70:
            self.state = 'angry'
            self.color = 'red'
        elif self.waiting_time > self.patience:
            self.state = 'impatient'
            self.color = 'orange'
        else:
            self.state = 'normal'
            self.color = self.get_initial_color()

    def can_move_to(self, pos: Tuple[int, int]) -> bool:
        """Check if immediate movement to position is possible."""
        if not (0 <= pos[0] < self.model.grid.width and 
                0 <= pos[1] < self.model.grid.height):
            return False
        
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        
        # Check for buildings and other cars
        if any(isinstance(agent, (IntersectionBuilding, IntersectionCar)) 
               for agent in cell_contents):
            return False
            
        return True

    def step(self) -> None:
        """Execute one step of the car's movement."""
        self.update_emotional_state()
    
    # Check if we've reached the destination
        if self.position == self.destination:
            print(f"Car {self.unique_id} ({self.personality}) reached destination!")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
    
    # If no path exists or current path is blocked, recalculate
        if not self.path or (len(self.path) > 0 and not self.can_move_to(self.path[0])):
            new_path = self.find_path()
            if new_path:
                self.path = new_path[1:]  # Skip current position
            else:
                self.waiting_time += 1
                self.happiness = max(0, self.happiness - 5)
                self.stress = min(100, self.stress + 3)
                return

        if self.path:
            next_pos = self.path[0]
        
        # Check if we can move to the next position
            if self.can_move_to(next_pos):
            # Move agent
                self.model.grid.move_agent(self, next_pos)
                self.position = next_pos
                self.path.pop(0)
                self.waiting_time = 0
                self.happiness = min(100, self.happiness + 1)
                self.stress = max(0, self.stress - 1)
            else:
                self.waiting_time += 1
                self.happiness = max(0, self.happiness - 1)
                self.stress = min(100, self.stress + 1)

def get_average_happiness(model):
    """Calculate average happiness, handling case of no cars."""
    cars = [a for a in model.schedule.agents if isinstance(a, IntersectionCar)]
    if cars:
        return np.mean([car.happiness for car in cars])
    return 0

def get_average_stress(model):
    """Calculate average stress, handling case of no cars."""
    cars = [a for a in model.schedule.agents if isinstance(a, IntersectionCar)]
    if cars:
        return np.mean([car.stress for car in cars])
    return 0

def get_active_cars(model):
    """Count number of active cars."""
    return len([a for a in model.schedule.agents if isinstance(a, IntersectionCar)])

class IntersectionModel(Model):
    def __init__(self, width=24, height=24, spawn_rate=0.05):  
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.spawn_rate = spawn_rate
        
        # Initialize the environment
        self.setup_intersection()
        
        # Set up data collection with safe aggregation functions
        self.datacollector = DataCollector(
            model_reporters={
                "Active Cars": get_active_cars,
                "Average Happiness": get_average_happiness,
                "Average Stress": get_average_stress
            }
        )
        
        self.running = True

    def setup_intersection(self):
        """Set up the initial state of the intersection."""
        self.create_buildings()
        self.create_traffic_lights()
        self.create_spawn_points()

    def create_spawn_points(self):
        """Create spawn points at specified locations."""
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
            # Clear existing agents
            cell_contents = self.grid.get_cell_list_contents((x, y))
            for agent in cell_contents:
                self.grid.remove_agent(agent)
            
            # Create and place spawn point
            spawn_point = IntersectionSpawnPoint(self, (x, y), direction, spawn_id)
            self.schedule.add(spawn_point)
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
        
        # Clear and place buildings
        for (top_left, bottom_right) in buildings:
            for x in range(top_left[0], bottom_right[0] + 1):
                for y in range(bottom_right[1], top_left[1] + 1):
                    # Clear existing agents
                    cell_contents = self.grid.get_cell_list_contents((x, y))
                    for agent in cell_contents:
                        self.grid.remove_agent(agent)
                    
                    # Place new building
                    building = IntersectionBuilding(self, (x, y))
                    self.schedule.add(building)
                    self.grid.place_agent(building, (x, y))
        
        # Handle central building
        for x in range(13, 15):
            for y in range(9, 11):
                # Clear existing agents
                cell_contents = self.grid.get_cell_list_contents((x, y))
                for agent in cell_contents:
                    self.grid.remove_agent(agent)
                
                # Place central building
                building = IntersectionBuilding(self, (x, y))
                building.color = "brown"  # Special color for central building
                self.schedule.add(building)
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

        for set_idx, light_positions in enumerate(traffic_light_sets, 1):
            for pos in light_positions:
                # Clear existing agents
                cell_contents = self.grid.get_cell_list_contents(pos)
                for agent in cell_contents:
                    self.grid.remove_agent(agent)
                
                # Create and place traffic light
                traffic_light = IntersectionLight(self, pos, set_idx)
                self.schedule.add(traffic_light)
                self.grid.place_agent(traffic_light, pos)

    def spawn_new_cars(self):
        """Attempt to spawn new cars at spawn points."""
        spawn_points = [agent for agent in self.schedule.agents 
                    if isinstance(agent, IntersectionSpawnPoint)]
    
        for spawn_point in spawn_points:
         if random.random() < self.spawn_rate:
            # Check if spawn position is clear
                cell_contents = self.grid.get_cell_list_contents(spawn_point.position)
                if not any(isinstance(agent, IntersectionCar) for agent in cell_contents):
                # Create new car
                    car = IntersectionCar(self)
                
                # Choose random destination from other spawn points
                    possible_destinations = [p.position for p in spawn_points 
                                        if p.position != spawn_point.position]
                    if possible_destinations:
                        destination = random.choice(possible_destinations)
                    
                    # Set car position and destination
                        car.position = spawn_point.position
                        car.destination = destination
                        car.path = car.find_path()
                    
                        if car.path:  # Only add car if valid path exists
                            self.schedule.add(car)
                            self.grid.place_agent(car, spawn_point.position)
                            print(f"Car spawned at {spawn_point.position} heading to {destination}")

    def step(self):
        """Advance the model by one step."""
        self.spawn_new_cars()
        self.datacollector.collect(self)
        self.schedule.step()